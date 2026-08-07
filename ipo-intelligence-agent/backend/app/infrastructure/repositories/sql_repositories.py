"""Repository implementations for data access."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.interfaces.repositories import (
    IPORepository,
    CompanyRepository,
    FinancialRepository,
    AnalysisRepository,
    PredictionRepository,
    ReportRepository,
    MemoryRepository,
    FailureMemoryRepository,
    SuccessMemoryRepository,
    KnowledgeMemoryRepository,
    BestPracticeRepository,
    ReflectionMemoryRepository,
    LessonRepository,
    JobRepository,
    UserRepository,
    APIKeyRepository,
)
from app.domain.enums.enums import (
    IPOStatus,
    Exchange,
    Sector,
    Industry,
    AgentName,
    MemoryType,
    PredictionType,
    OutcomeStatus,
    LessonType,
    JobType,
    JobStatus,
)
from app.domain.entities.entities import (
    MemoryEntry,
    FailureMemory,
    SuccessMemory,
    KnowledgeMemory,
    BestPracticeMemory,
    ReflectionMemory,
    Lesson,
)
from app.domain.value_objects.value_objects import (
    IPODetails,
    CompanyProfile,
    FinancialMetrics,
    InvestmentThesis,
    Prediction,
    RiskFactor,
    SentimentData,
    ScoreComponent,
    DataPoint,
)
from app.infrastructure.database.models import (
    CompanyModel,
    FinancialStatementModel,
    IPOModel,
    AnalysisModel,
    PredictionModel,
    ReportModel,
    ExperienceMemoryModel,
    FailureMemoryModel,
    SuccessMemoryModel,
    KnowledgeMemoryModel,
    BestPracticeMemoryModel,
    ReflectionMemoryModel,
    LessonModel,
    JobModel,
    UserModel,
    APIKeyModel,
)
from app.domain.value_objects.value_objects import Money, Percentage, Ratio, PriceRange, Valuation


class SQLIPORepository(IPORepository):
    """SQL implementation of IPO repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, ipo: IPODetails) -> None:
        """Save IPO."""
        model = IPOModel(
            symbol=ipo.symbol,
            company_id=ipo.company_id,
            company_name=ipo.company_name,
            exchange=ipo.exchange,
            sector=ipo.sector,
            industry=ipo.industry,
            status=self._to_status(ipo.status),
            announced_date=ipo.announced_date,
            filed_date=ipo.filing_date,
            priced_date=ipo.pricing_date,
            listed_date=ipo.listed_date,
            withdrawn_date=ipo.withdrawn_date,
            expected_date=ipo.expected_date,
            expected_price_low=ipo.price_range.low.amount if ipo.price_range and ipo.price_range.low else None,
            expected_price_high=ipo.price_range.high.amount if ipo.price_range and ipo.price_range.high else None,
            priced_price=ipo.offer_price.amount if ipo.offer_price else None,
            shares_offered=ipo.shares_offered,
            overallotment_option=ipo.greenshoe_option,
            overallotment_shares=ipo.greenshoe_shares,
            lead_underwriters=[ipo.lead_underwriter] if ipo.lead_underwriter else list(ipo.underwriters),
            lockup_expiry=ipo.lockup_expiry,
            lockup_days=ipo.lockup_period_days,
            prospectus_url=ipo.prospectus_url,
        )
        self.session.add(model)
        await self.session.flush()

    @staticmethod
    def _to_status(status) -> IPOStatus:
        """Normalize IPO status string/enum to IPOStatus enum."""
        if isinstance(status, IPOStatus):
            return status
        if not status:
            return IPOStatus.ANNOUNCED
        try:
            return IPOStatus(str(status).lower())
        except ValueError:
            try:
                return IPOStatus[str(status).upper()]
            except KeyError:
                return IPOStatus.ANNOUNCED

    async def delete(self, entity_id: UUID) -> bool:
        result = await self.session.execute(
            select(IPOModel).where(IPOModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            return True
        return False

    async def get_by_symbol(self, symbol: str) -> Optional[IPODetails]:
        """Get IPO by symbol."""
        result = await self.session.execute(
            select(IPOModel).where(IPOModel.symbol == symbol.upper())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_id(self, ipo_id: UUID) -> Optional[IPODetails]:
        """Get IPO by ID."""
        result = await self.session.execute(
            select(IPOModel).where(IPOModel.id == ipo_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_upcoming(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        exchange: Optional[Exchange] = None,
        sector: Optional[Sector] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[IPODetails]:
        """List upcoming IPOs."""
        query = select(IPOModel)

        conditions = []
        if status:
            conditions.append(IPOModel.status == self._to_status(status))
        if exchange:
            conditions.append(IPOModel.exchange == exchange)
        if sector:
            conditions.append(IPOModel.sector == sector)
        if from_date:
            conditions.append(IPOModel.expected_date >= from_date)
        if to_date:
            conditions.append(IPOModel.expected_date <= to_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(IPOModel.expected_date.asc().nullslast()).limit(limit).offset(offset)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def count_upcoming(
        self,
        status: Optional[str] = None,
        exchange: Optional[Exchange] = None,
        sector: Optional[Sector] = None,
    ) -> int:
        """Count upcoming IPOs."""
        query = select(func.count(IPOModel.id))

        conditions = []
        if status:
            conditions.append(IPOModel.status == self._to_status(status))
        if exchange:
            conditions.append(IPOModel.exchange == exchange)
        if sector:
            conditions.append(IPOModel.sector == sector)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def search(self, query: str, limit: int = 20) -> List[IPODetails]:
        """Search IPOs by text query."""
        search_term = f"%{query}%"
        result = await self.session.execute(
            select(IPOModel)
            .where(
                or_(
                    IPOModel.symbol.ilike(search_term),
                    IPOModel.company_name.ilike(search_term),
                )
            )
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_recently_listed(
        self,
        days: int = 30,
        limit: int = 20,
    ) -> List[IPODetails]:
        """Get recently listed IPOs."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(IPOModel)
            .where(
                and_(
                    IPOModel.status == IPOStatus.LISTED,
                    IPOModel.listed_date >= cutoff,
                )
            )
            .order_by(desc(IPOModel.listed_date))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update_status(self, symbol: str, status: str) -> bool:
        """Update IPO status."""
        result = await self.session.execute(
            select(IPOModel).where(IPOModel.symbol == symbol.upper())
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = self._to_status(status)
            model.updated_at = datetime.utcnow()
            return True
        return False

    def _to_entity(self, model: IPOModel) -> IPODetails:
        """Convert model to entity."""
        price_range = None
        if model.expected_price_low is not None and model.expected_price_high is not None:
            price_range = PriceRange(
                low=Money(model.expected_price_low, "USD"),
                high=Money(model.expected_price_high, "USD"),
            )
        elif model.expected_price_low is not None:
            price_range = PriceRange(
                low=Money(model.expected_price_low, "USD"),
                high=Money(model.expected_price_low, "USD"),
            )

        offer_price = Money(model.priced_price, "USD") if model.priced_price is not None else None

        valuation = None
        if model.priced_valuation is not None:
            valuation = Valuation(
                enterprise_value=Money(model.priced_valuation, "USD"),
                equity_value=Money(model.priced_valuation, "USD"),
                price_per_share=model.priced_price or 0,
                shares_outstanding=model.shares_offered or 0,
            )

        status = model.status.value if hasattr(model.status, 'value') else model.status

        return IPODetails(
            symbol=model.symbol,
            company_name=model.company_name,
            exchange=model.exchange,
            sector=model.sector,
            industry=model.industry,
            expected_date=model.expected_date,
            announced_date=model.announced_date,
            filing_date=model.filed_date,
            pricing_date=model.priced_date,
            listed_date=model.listed_date,
            withdrawn_date=model.withdrawn_date,
            status=status,
            shares_offered=model.shares_offered,
            price_range=price_range,
            offer_price=offer_price,
            valuation=valuation,
            underwriters=model.co_managers or [],
            lead_underwriter=", ".join(model.lead_underwriters or [])[:255],
            lockup_period_days=model.lockup_days,
            lockup_expiry=model.lockup_expiry,
            greenshoe_option=model.overallotment_option,
            greenshoe_shares=model.overallotment_shares,
            prospectus_url=model.prospectus_url or "",
            company_id=model.company_id,
        )


class SQLCompanyRepository(CompanyRepository):
    """SQL implementation of company repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, company: CompanyProfile) -> UUID:
        """Save company profile and return its id."""
        model = CompanyModel(
            legal_name=company.legal_name,
            common_name=company.common_name,
            ticker=(company.ticker or company.common_name).upper(),
            exchange=company.exchange,
            sector=company.sector,
            industry=company.industry,
            description=company.description,
            business_model=company.business_model,
            competitive_advantage="; ".join(company.competitive_advantages or []),
            headquarters=company.headquarters,
            employee_count=company.employee_count,
            website=company.website,
            ceo=company.ceo,
            cfo=company.cfo,
            board_members=company.board_members,
            major_shareholders=company.major_shareholders,
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_by_symbol(self, symbol: str) -> Optional[CompanyProfile]:
        """Get company by symbol."""
        result = await self.session.execute(
            select(CompanyModel).where(CompanyModel.ticker == symbol.upper())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def delete(self, entity_id: UUID) -> bool:
        """Delete company by ID."""
        result = await self.session.execute(
            select(CompanyModel).where(CompanyModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            return True
        return False

    async def get_by_name(self, name: str) -> Optional[CompanyProfile]:
        """Get company by name."""
        result = await self.session.execute(
            select(CompanyModel).where(CompanyModel.common_name.ilike(f"%{name}%"))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_sector(
        self,
        sector: Sector,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CompanyProfile]:
        """List companies by sector."""
        result = await self.session.execute(
            select(CompanyModel)
            .where(CompanyModel.sector == sector)
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def list_by_industry(
        self,
        industry: Industry,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CompanyProfile]:
        """List companies by industry."""
        result = await self.session.execute(
            select(CompanyModel)
            .where(CompanyModel.industry == industry)
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: CompanyModel) -> CompanyProfile:
        """Convert model to entity."""
        competitive_advantages = [model.competitive_advantage] if model.competitive_advantage else []
        return CompanyProfile(
            id=model.id,
            ticker=model.ticker,
            exchange=model.exchange,
            legal_name=model.legal_name,
            common_name=model.common_name,
            description=model.description or "",
            business_model=model.business_model or "",
            sector=model.sector,
            industry=model.industry,
            headquarters=model.headquarters or "",
            employee_count=model.employee_count,
            website=model.website or "",
            ceo=model.ceo or "",
            cfo=model.cfo or "",
            board_members=model.board_members or [],
            major_shareholders=model.major_shareholders or {},
            competitive_advantages=competitive_advantages,
        )


class SQLFinancialRepository(FinancialRepository):
    """SQL implementation of financial repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest(self, symbol: str) -> Optional[FinancialMetrics]:
        """Get latest financial metrics."""
        # Get company first
        company_result = await self.session.execute(
            select(CompanyModel).where(CompanyModel.ticker == symbol.upper())
        )
        company = company_result.scalar_one_or_none()
        if not company:
            return None

        # Get latest financial statement
        stmt_result = await self.session.execute(
            select(FinancialStatementModel)
            .where(FinancialStatementModel.company_id == company.id)
            .order_by(desc(FinancialStatementModel.period_end))
            .limit(1)
        )
        stmt = stmt_result.scalar_one_or_none()
        if not stmt:
            return None

        return self._to_metrics(stmt)

    async def get_history(
        self,
        symbol: str,
        periods: int = 8,
    ) -> List[FinancialMetrics]:
        """Get financial history."""
        company_result = await self.session.execute(
            select(CompanyModel).where(CompanyModel.ticker == symbol.upper())
        )
        company = company_result.scalar_one_or_none()
        if not company:
            return []

        stmt_result = await self.session.execute(
            select(FinancialStatementModel)
            .where(FinancialStatementModel.company_id == company.id)
            .order_by(desc(FinancialStatementModel.period_end))
            .limit(periods)
        )
        statements = stmt_result.scalars().all()
        return [self._to_metrics(s) for s in statements]

    async def get_by_period(
        self,
        symbol: str,
        period: str,
    ) -> Optional[FinancialMetrics]:
        """Get financials for specific period."""
        company_result = await self.session.execute(
            select(CompanyModel).where(CompanyModel.ticker == symbol.upper())
        )
        company = company_result.scalar_one_or_none()
        if not company:
            return None

        stmt_result = await self.session.execute(
            select(FinancialStatementModel)
            .where(
                and_(
                    FinancialStatementModel.company_id == company.id,
                    FinancialStatementModel.period_type == period,
                )
            )
            .order_by(desc(FinancialStatementModel.period_end))
            .limit(1)
        )
        stmt = stmt_result.scalar_one_or_none()
        return self._to_metrics(stmt) if stmt else None

    def _to_metrics(self, stmt: FinancialStatementModel) -> FinancialMetrics:
        """Convert statement to metrics."""
        def money(val):
            return Money(val, "USD") if val is not None else None

        def pct(val):
            return Percentage.from_decimal(float(val)) if val is not None else None

        def ratio(val, name):
            return Ratio(val, name) if val is not None else None

        return FinancialMetrics(
            revenue=money(stmt.revenue),
            revenue_growth_yoy=pct(stmt.revenue_growth_yoy),
            revenue_growth_qoq=pct(stmt.revenue_growth_qoq),
            gross_profit=money(stmt.gross_profit),
            gross_margin=pct(stmt.gross_margin),
            operating_income=money(stmt.operating_income),
            operating_margin=pct(stmt.operating_margin),
            net_income=money(stmt.net_income),
            net_margin=pct(stmt.net_margin),
            ebitda=money(stmt.ebitda),
            ebitda_margin=pct(stmt.ebitda_margin) if stmt.ebitda_margin else None,
            free_cash_flow=money(stmt.free_cash_flow),
            fcf_margin=pct(stmt.fcf_margin) if stmt.fcf_margin else None,
            total_assets=money(stmt.total_assets),
            total_liabilities=money(stmt.total_liabilities),
            total_equity=money(stmt.total_equity),
            total_debt=money(stmt.total_debt),
            cash_and_equivalents=money(stmt.cash_and_equivalents),
            debt_to_equity=ratio(stmt.debt_to_equity, "Debt/Equity") if stmt.debt_to_equity else None,
            current_ratio=ratio(stmt.current_ratio, "Current Ratio") if stmt.current_ratio else None,
            quick_ratio=ratio(stmt.quick_ratio, "Quick Ratio") if stmt.quick_ratio else None,
            roe=pct(stmt.roe),
            roa=pct(stmt.roa),
            roic=pct(stmt.roic),
        )


class SQLAnalysisRepository(AnalysisRepository):
    """SQL implementation of analysis repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_analysis(
        self,
        symbol: str,
        analysis_data: Dict[str, Any],
    ) -> UUID:
        """Save complete analysis."""
        # Get company
        company_result = await self.session.execute(
            select(CompanyModel).where(CompanyModel.ticker == symbol.upper())
        )
        company = company_result.scalar_one_or_none()

        model = AnalysisModel(
            company_id=company.id if company else None,
            symbol=symbol.upper(),
            status=analysis_data.get("status", AnalysisStatus.COMPLETED),
            overall_score=analysis_data.get("overall_score", 0),
            confidence=analysis_data.get("confidence", 0),
            financial_strength_score=analysis_data.get("financial_strength_score", 0),
            growth_potential_score=analysis_data.get("growth_potential_score", 0),
            market_opportunity_score=analysis_data.get("market_opportunity_score", 0),
            management_quality_score=analysis_data.get("management_quality_score", 0),
            risk_level_score=analysis_data.get("risk_level_score", 0),
            score_breakdown=analysis_data.get("score_breakdown", {}),
            bull_case=analysis_data.get("bull_case", ""),
            bear_case=analysis_data.get("bear_case", ""),
            key_risks=analysis_data.get("key_risks", []),
            key_catalysts=analysis_data.get("key_catalysts", []),
            investment_strategy=analysis_data.get("investment_strategy", InvestmentStrategy.WATCH),
            time_horizon=analysis_data.get("time_horizon", TimeHorizon.MEDIUM_TERM),
            risk_level=analysis_data.get("risk_level", RiskLevel.MODERATE),
            risk_factors=analysis_data.get("risk_factors", []),
            sentiment=analysis_data.get("sentiment", SentimentLabel.NEUTRAL),
            sentiment_score=analysis_data.get("sentiment_score", 0),
            sentiment_drivers=analysis_data.get("sentiment_drivers", []),
            agent_results=analysis_data.get("agent_results", {}),
            model_version=analysis_data.get("model_version", "1.0.0"),
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_latest_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest analysis for symbol."""
        result = await self.session.execute(
            select(AnalysisModel)
            .where(AnalysisModel.symbol == symbol.upper())
            .order_by(desc(AnalysisModel.created_at))
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_dict(model) if model else None

    async def get_analysis_history(
        self,
        symbol: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get analysis history."""
        result = await self.session.execute(
            select(AnalysisModel)
            .where(AnalysisModel.symbol == symbol.upper())
            .order_by(desc(AnalysisModel.created_at))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_dict(m) for m in models]

    async def get_analysis_by_id(self, analysis_id: UUID) -> Optional[Dict[str, Any]]:
        """Get analysis by ID."""
        result = await self.session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        return self._to_dict(model) if model else None

    async def save_score_breakdown(
        self,
        analysis_id: UUID,
        components: List[ScoreComponent],
    ) -> None:
        """Save score breakdown."""
        result = await self.session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.score_breakdown = [c.to_dict() for c in components]

    async def get_score_breakdown(self, analysis_id: UUID) -> List[ScoreComponent]:
        """Get score breakdown."""
        result = await self.session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        if model and model.score_breakdown:
            return [ScoreComponent(**c) for c in model.score_breakdown]
        return []

    async def save_risk_factors(
        self,
        analysis_id: UUID,
        risk_factors: List[RiskFactor],
    ) -> None:
        """Save risk factors."""
        result = await self.session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.risk_factors = [r.to_dict() for r in risk_factors]

    async def get_risk_factors(self, analysis_id: UUID) -> List[RiskFactor]:
        """Get risk factors."""
        result = await self.session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        if model and model.risk_factors:
            return [RiskFactor(**r) for r in model.risk_factors]
        return []

    async def save_investment_thesis(
        self,
        analysis_id: UUID,
        thesis: InvestmentThesis,
    ) -> None:
        """Save investment thesis."""
        result = await self.session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.bull_case = thesis.bull_case
            model.bear_case = thesis.bear_case
            model.key_risks = thesis.key_risks
            model.key_catalysts = thesis.catalysts

    async def get_investment_thesis(self, analysis_id: UUID) -> Optional[InvestmentThesis]:
        """Get investment thesis."""
        result = await self.session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return InvestmentThesis(
                bull_case=model.bull_case or "",
                bear_case=model.bear_case or "",
                key_drivers=model.key_catalysts or [],
                key_risks=model.key_risks or [],
                catalysts=model.key_catalysts or [],
                assumptions=[],
            )
        return None

    def _to_dict(self, model: AnalysisModel) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(model.id),
            "symbol": model.symbol,
            "status": model.status.value if hasattr(model.status, 'value') else model.status,
            "overall_score": model.overall_score,
            "confidence": model.confidence,
            "financial_strength_score": model.financial_strength_score,
            "growth_potential_score": model.growth_potential_score,
            "market_opportunity_score": model.market_opportunity_score,
            "management_quality_score": model.management_quality_score,
            "risk_level_score": model.risk_level_score,
            "score_breakdown": model.score_breakdown,
            "bull_case": model.bull_case,
            "bear_case": model.bear_case,
            "key_risks": model.key_risks,
            "key_catalysts": model.key_catalysts,
            "investment_strategy": model.investment_strategy.value if hasattr(model.investment_strategy, 'value') else model.investment_strategy,
            "time_horizon": model.time_horizon.value if hasattr(model.time_horizon, 'value') else model.time_horizon,
            "risk_level": model.risk_level.value if hasattr(model.risk_level, 'value') else model.risk_level,
            "risk_factors": model.risk_factors,
            "sentiment": model.sentiment.value if hasattr(model.sentiment, 'value') else model.sentiment,
            "sentiment_score": model.sentiment_score,
            "sentiment_drivers": model.sentiment_drivers,
            "agent_results": model.agent_results,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "model_version": model.model_version,
        }


class SQLPredictionRepository(PredictionRepository):
    """SQL implementation of prediction repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_prediction(self, prediction: Prediction) -> UUID:
        """Save prediction."""
        model = PredictionModel(
            symbol=prediction.metadata.get("symbol", ""),
            analysis_id=prediction.metadata.get("analysis_id"),
            prediction_type=prediction.prediction_type,
            predicted_value=prediction.predicted_value,
            lower_bound=prediction.lower_bound,
            upper_bound=prediction.upper_bound,
            confidence=prediction.confidence,
            time_horizon=prediction.time_horizon,
            methodology=prediction.methodology,
            assumptions=prediction.assumptions,
            status=OutcomeStatus.PENDING,
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_predictions_for_ipo(
        self,
        symbol: str,
        prediction_type: Optional[PredictionType] = None,
    ) -> List[Prediction]:
        """Get predictions for IPO."""
        query = select(PredictionModel).where(PredictionModel.symbol == symbol.upper())
        if prediction_type:
            query = query.where(PredictionModel.prediction_type == prediction_type)
        query = query.order_by(desc(PredictionModel.created_at))

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_pending_verification(self, limit: int = 100) -> List[Prediction]:
        """Get predictions pending verification."""
        result = await self.session.execute(
            select(PredictionModel)
            .where(PredictionModel.status == OutcomeStatus.PENDING)
            .order_by(PredictionModel.created_at)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def update_outcome(
        self,
        prediction_id: UUID,
        actual_value: float,
        status: str,
    ) -> bool:
        """Update prediction with actual outcome."""
        result = await self.session.execute(
            select(PredictionModel).where(PredictionModel.id == prediction_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.actual_value = actual_value
            model.status = status
            model.verified_at = datetime.utcnow()
            return True
        return False

    def _to_entity(self, model: PredictionModel) -> Prediction:
        """Convert model to entity."""
        return Prediction(
            prediction_type=model.prediction_type.value if hasattr(model.prediction_type, 'value') else model.prediction_type,
            predicted_value=model.predicted_value,
            lower_bound=model.lower_bound,
            upper_bound=model.upper_bound,
            confidence=model.confidence,
            time_horizon=model.time_horizon,
            methodology=model.methodology,
            assumptions=model.assumptions or [],
            created_at=model.created_at,
        )


class SQLReportRepository(ReportRepository):
    """SQL implementation of report repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_report(
        self,
        symbol: str,
        analysis_id: UUID,
        content: str,
        format: str = "markdown",
        sections: Optional[List[str]] = None,
    ) -> UUID:
        """Save generated report."""
        model = ReportModel(
            symbol=symbol.upper(),
            analysis_id=analysis_id,
            content=content,
            format=format,
            sections=sections or [],
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_latest_report(
        self,
        symbol: str,
        format: str = "markdown",
    ) -> Optional[str]:
        """Get latest report for symbol."""
        result = await self.session.execute(
            select(ReportModel)
            .where(
                and_(
                    ReportModel.symbol == symbol.upper(),
                    ReportModel.format == format,
                )
            )
            .order_by(desc(ReportModel.created_at))
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return model.content if model else None

    async def get_report_by_id(self, report_id: UUID) -> Optional[str]:
        """Get report by ID."""
        result = await self.session.execute(
            select(ReportModel).where(ReportModel.id == report_id)
        )
        model = result.scalar_one_or_none()
        return model.content if model else None


class SQLMemoryRepository(MemoryRepository):
    """SQL implementation of memory repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def store(
        self,
        memory_type: MemoryType,
        content: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ipo_symbol: Optional[str] = None,
        analysis_id: Optional[UUID] = None,
    ) -> UUID:
        """Store memory entry."""
        if memory_type == MemoryType.EXPERIENCE:
            model = ExperienceMemoryModel(
                ipo_symbol=ipo_symbol or "",
                situation_description=content.get("situation", ""),
                prediction_made=content.get("prediction", ""),
                actual_outcome=content.get("outcome", ""),
                learning=content.get("learning", ""),
                accuracy=content.get("accuracy", 0),
                prediction_id=content.get("prediction_id"),
                outcome_id=content.get("outcome_id"),
                confidence_at_prediction=content.get("confidence", 0),
                time_to_outcome_days=content.get("time_to_outcome"),
                metadata=metadata or {},
            )
        elif memory_type == MemoryType.FAILURE:
            model = FailureMemoryModel(
                failure_id=content.get("failure_id", ""),
                agent_name=content.get("agent_name", AgentName.FUNDAMENTAL),
                error_type=content.get("error_type", ""),
                error_message=content.get("error_message", ""),
                stack_trace=content.get("stack_trace", ""),
                root_cause=content.get("root_cause", ""),
                attempted_fix=content.get("attempted_fix", ""),
                resolved=content.get("resolved", False),
                resolution=content.get("resolution", ""),
                confidence=content.get("confidence", 0),
                category=content.get("category", FailureCategory.UNKNOWN),
                severity=content.get("severity", Severity.MEDIUM),
                similarity_hash=content.get("similarity_hash", ""),
                ipo_symbol=ipo_symbol,
                analysis_id=analysis_id,
                metadata=metadata or {},
            )
        elif memory_type == MemoryType.SUCCESS:
            model = SuccessMemoryModel(
                success_id=content.get("success_id", ""),
                agent_name=content.get("agent_name", AgentName.FUNDAMENTAL),
                strategy_description=content.get("strategy", ""),
                prompt_used=content.get("prompt", ""),
                tool_sequence=content.get("tools", []),
                api_sequence=content.get("apis", []),
                confidence=content.get("confidence", 0),
                success_rate=content.get("success_rate", 0),
                context_hash=content.get("context_hash", ""),
                ipo_symbol=ipo_symbol,
                analysis_id=analysis_id,
                metadata=metadata or {},
            )
        elif memory_type == MemoryType.KNOWLEDGE:
            model = KnowledgeMemoryModel(
                concept=content.get("concept", ""),
                description=content.get("description", ""),
                evidence=content.get("evidence", []),
                confidence=content.get("confidence", 0),
                domain=content.get("domain", ""),
                tags=content.get("tags", []),
                metadata=metadata or {},
            )
        elif memory_type == MemoryType.BEST_PRACTICE:
            model = BestPracticeMemoryModel(
                practice_name=content.get("practice_name", ""),
                description=content.get("description", ""),
                applicable_context=content.get("context", {}),
                success_rate=content.get("success_rate", 0),
                tags=content.get("tags", []),
                metadata=metadata or {},
            )
        elif memory_type == MemoryType.REFLECTION:
            model = ReflectionMemoryModel(
                prediction_id=content.get("prediction_id"),
                ipo_symbol=content.get("ipo_symbol", ""),
                prediction_type=content.get("prediction_type", PredictionType.PRICE_CHANGE_1M),
                predicted_value=content.get("predicted_value", 0),
                actual_value=content.get("actual_value", 0),
                accuracy=content.get("accuracy", 0),
                error=content.get("error", 0),
                mistakes_identified=content.get("mistakes", []),
                correct_assumptions=content.get("correct", []),
                missing_factors=content.get("missing", []),
                lessons_extracted=content.get("lessons", []),
                prompt_improvements=content.get("prompt_improvements", []),
                strategy_changes=content.get("strategy_changes", []),
                knowledge_updates=content.get("knowledge_updates", []),
            )
        else:
            # Generic memory entry
            model = ExperienceMemoryModel(
                ipo_symbol=ipo_symbol or "",
                situation_description=str(content),
                metadata=metadata or {},
            )

        self.session.add(model)
        await self.session.flush()
        return model.id

    async def search(
        self,
        memory_type: MemoryType,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.75,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[MemoryEntry, float]]:
        """Search memory by semantic similarity."""
        # In production, use pgvector for similarity search
        # For now, return empty list
        return []

    async def get_by_id(
        self,
        memory_type: MemoryType,
        entry_id: UUID,
    ) -> Optional[MemoryEntry]:
        """Get memory entry by ID."""
        # Implementation depends on memory type
        return None

    async def get_recent(
        self,
        memory_type: MemoryType,
        limit: int = 100,
        ipo_symbol: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Get recent memory entries."""
        return []

    async def delete_old_entries(
        self,
        memory_type: MemoryType,
        older_than_days: int,
    ) -> int:
        """Delete old memory entries."""
        return 0


class SQLFailureMemoryRepository(FailureMemoryRepository):
    """SQL implementation of failure memory repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_similar(
        self,
        error_message: str,
        agent_name: AgentName,
        threshold: float = 0.8,
        limit: int = 5,
    ) -> List[Tuple[FailureMemory, float]]:
        """Find similar failures."""
        # Compute similarity hash
        import hashlib
        similarity_hash = hashlib.md5(f"{agent_name.value}:{error_message[:200]}".encode()).hexdigest()[:16]

        result = await self.session.execute(
            select(FailureMemoryModel)
            .where(
                and_(
                    FailureMemoryModel.agent_name == agent_name,
                    FailureMemoryModel.similarity_hash == similarity_hash,
                )
            )
            .order_by(desc(FailureMemoryModel.last_occurrence))
            .limit(limit)
        )
        models = result.scalars().all()
        return [(self._to_entity(m), 1.0) for m in models]

    async def get_by_category(
        self,
        category: str,
        limit: int = 50,
    ) -> List[FailureMemory]:
        """Get failures by category."""
        result = await self.session.execute(
            select(FailureMemoryModel)
            .where(FailureMemoryModel.category == category)
            .order_by(desc(FailureMemoryModel.last_occurrence))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def mark_resolved(
        self,
        failure_id: UUID,
        resolution: str,
    ) -> bool:
        """Mark failure as resolved."""
        result = await self.session.execute(
            select(FailureMemoryModel).where(FailureMemoryModel.id == failure_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.resolved = True
            model.resolution = resolution
            return True
        return False

    async def get_unresolved(
        self,
        agent_name: Optional[AgentName] = None,
        limit: int = 100,
    ) -> List[FailureMemory]:
        """Get unresolved failures."""
        query = select(FailureMemoryModel).where(FailureMemoryModel.resolved == False)
        if agent_name:
            query = query.where(FailureMemoryModel.agent_name == agent_name)
        query = query.order_by(desc(FailureMemoryModel.last_occurrence)).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: FailureMemoryModel) -> FailureMemory:
        """Convert model to entity."""
        return FailureMemory(
            id=model.id,
            memory_type=MemoryType.FAILURE.value,
            content=model.error_message,
            metadata=model.metadata,
            created_at=model.created_at,
            failure_id=model.failure_id,
            agent_name=model.agent_name,
            error_type=model.error_type,
            error_message=model.error_message,
            stack_trace=model.stack_trace,
            root_cause=model.root_cause,
            attempted_fix=model.attempted_fix,
            resolved=model.resolved,
            resolution=model.resolution,
            confidence=model.confidence,
            category=model.category.value if hasattr(model.category, 'value') else model.category,
            severity=model.severity.value if hasattr(model.severity, 'value') else model.severity,
            occurrences=model.occurrences,
            similarity_hash=model.similarity_hash,
            last_occurrence=model.last_occurrence,
        )


class SQLSuccessMemoryRepository(SuccessMemoryRepository):
    """SQL implementation of success memory repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_successful_strategies(
        self,
        context: Dict[str, Any],
        agent_name: AgentName,
        threshold: float = 0.75,
        limit: int = 5,
    ) -> List[Tuple[SuccessMemory, float]]:
        """Find successful strategies for context."""
        # Simple context matching by hash
        import hashlib
        import json
        context_hash = hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:16]

        result = await self.session.execute(
            select(SuccessMemoryModel)
            .where(
                and_(
                    SuccessMemoryModel.agent_name == agent_name,
                    SuccessMemoryModel.context_hash == context_hash,
                )
            )
            .order_by(desc(SuccessMemoryModel.confidence * SuccessMemoryModel.success_rate))
            .limit(limit)
        )
        models = result.scalars().all()
        return [(self._to_entity(m), 1.0) for m in models]

    async def get_by_strategy(
        self,
        strategy: str,
        agent_name: AgentName,
        limit: int = 20,
    ) -> List[SuccessMemory]:
        """Get successes by strategy."""
        result = await self.session.execute(
            select(SuccessMemoryModel)
            .where(
                and_(
                    SuccessMemoryModel.agent_name == agent_name,
                    SuccessMemoryModel.strategy_description.ilike(f"%{strategy}%"),
                )
            )
            .order_by(desc(SuccessMemoryModel.confidence))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def increment_reuse_count(self, success_id: UUID) -> bool:
        """Increment reuse count."""
        result = await self.session.execute(
            select(SuccessMemoryModel).where(SuccessMemoryModel.id == success_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.reuse_count += 1
            model.last_reused = datetime.utcnow()
            return True
        return False

    def _to_entity(self, model: SuccessMemoryModel) -> SuccessMemory:
        """Convert model to entity."""
        return SuccessMemory(
            id=model.id,
            memory_type=MemoryType.SUCCESS.value,
            content=model.strategy_description,
            metadata=model.metadata,
            created_at=model.created_at,
            success_id=model.success_id,
            agent_name=model.agent_name,
            strategy_description=model.strategy_description,
            prompt_used=model.prompt_used,
            tool_sequence=model.tool_sequence or [],
            api_sequence=model.api_sequence or [],
            confidence=model.confidence,
            success_rate=model.success_rate,
            context_hash=model.context_hash,
            reuse_count=model.reuse_count,
            last_reused=model.last_reused,
        )


class SQLKnowledgeMemoryRepository(KnowledgeMemoryRepository):
    """SQL implementation of knowledge memory repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_concept(
        self,
        concept: str,
        domain: Optional[str] = None,
    ) -> Optional[KnowledgeMemory]:
        """Get knowledge by concept."""
        query = select(KnowledgeMemoryModel).where(KnowledgeMemoryModel.concept == concept)
        if domain:
            query = query.where(KnowledgeMemoryModel.domain == domain)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def search_concepts(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeMemory, float]]:
        """Search knowledge concepts."""
        # In production, use pgvector
        return []

    async def get_by_domain(
        self,
        domain: str,
        limit: int = 50,
    ) -> List[KnowledgeMemory]:
        """Get knowledge by domain."""
        result = await self.session.execute(
            select(KnowledgeMemoryModel)
            .where(KnowledgeMemoryModel.domain == domain)
            .order_by(desc(KnowledgeMemoryModel.confidence))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: KnowledgeMemoryModel) -> KnowledgeMemory:
        """Convert model to entity."""
        return KnowledgeMemory(
            id=model.id,
            memory_type=MemoryType.KNOWLEDGE.value,
            content=model.description,
            metadata=model.metadata,
            created_at=model.created_at,
            concept=model.concept,
            description=model.description,
            evidence=model.evidence or [],
            confidence=model.confidence,
            domain=model.domain,
            tags=model.tags or [],
            version=model.version,
            supersedes=model.supersedes,
        )


class SQLBestPracticeRepository(BestPracticeRepository):
    """SQL implementation of best practice repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_applicable_practices(
        self,
        context: Dict[str, Any],
        limit: int = 10,
    ) -> List[BestPracticeMemory]:
        """Get best practices applicable to context."""
        # Simple tag matching
        tags = context.get("tags", [])
        query = select(BestPracticeMemoryModel)
        if tags:
            # Match any tag
            query = query.where(BestPracticeMemoryModel.tags.op("&&")(tags))
        query = query.order_by(desc(BestPracticeMemoryModel.success_rate)).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def increment_usage(self, practice_id: UUID) -> bool:
        """Increment usage count."""
        result = await self.session.execute(
            select(BestPracticeMemoryModel).where(BestPracticeMemoryModel.id == practice_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.usage_count += 1
            model.last_used = datetime.utcnow()
            return True
        return False

    def _to_entity(self, model: BestPracticeMemoryModel) -> BestPracticeMemory:
        """Convert model to entity."""
        return BestPracticeMemory(
            id=model.id,
            memory_type=MemoryType.BEST_PRACTICE.value,
            content=model.description,
            metadata=model.metadata,
            created_at=model.created_at,
            practice_name=model.practice_name,
            description=model.description,
            applicable_context=model.applicable_context or {},
            success_rate=model.success_rate,
            usage_count=model.usage_count,
            last_used=model.last_used,
            tags=model.tags or [],
            version=model.version,
        )


class SQLReflectionMemoryRepository(ReflectionMemoryRepository):
    """SQL implementation of reflection memory repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_prediction(
        self,
        prediction_id: UUID,
    ) -> Optional[ReflectionMemory]:
        """Get reflection by prediction ID."""
        result = await self.session.execute(
            select(ReflectionMemoryModel).where(ReflectionMemoryModel.prediction_id == prediction_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_ipo(
        self,
        ipo_symbol: str,
        limit: int = 20,
    ) -> List[ReflectionMemory]:
        """Get reflections for IPO."""
        result = await self.session.execute(
            select(ReflectionMemoryModel)
            .where(ReflectionMemoryModel.ipo_symbol == ipo_symbol.upper())
            .order_by(desc(ReflectionMemoryModel.created_at))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_unprocessed(self, limit: int = 50) -> List[ReflectionMemory]:
        """Get unprocessed reflections."""
        result = await self.session.execute(
            select(ReflectionMemoryModel)
            .where(ReflectionMemoryModel.processed == False)
            .order_by(ReflectionMemoryModel.created_at)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: ReflectionMemoryModel) -> ReflectionMemory:
        """Convert model to entity."""
        return ReflectionMemory(
            id=model.id,
            memory_type=MemoryType.REFLECTION.value,
            content=f"Reflection on {model.prediction_type}",
            metadata={},
            created_at=model.created_at,
            prediction_id=model.prediction_id,
            ipo_symbol=model.ipo_symbol,
            prediction_type=model.prediction_type,
            predicted_value=model.predicted_value,
            actual_value=model.actual_value,
            accuracy=model.accuracy,
            error=model.error,
            mistakes_identified=model.mistakes_identified or [],
            correct_assumptions=model.correct_assumptions or [],
            missing_factors=model.missing_factors or [],
            lessons_extracted=model.lessons_extracted or [],
            prompt_improvements=model.prompt_improvements or [],
            strategy_changes=model.strategy_changes or [],
            knowledge_updates=model.knowledge_updates or [],
            processed=model.processed,
        )


class SQLLessonRepository(LessonRepository):
    """SQL implementation of lesson repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, lesson: Lesson) -> UUID:
        """Save lesson."""
        model = LessonModel(
            lesson_type=lesson.lesson_type,
            title=lesson.title,
            description=lesson.description,
            do=lesson.do,
            dont=lesson.dont,
            best_practices=lesson.best_practices,
            anti_patterns=lesson.anti_patterns,
            known_bugs=lesson.known_bugs,
            prompt_improvements=lesson.prompt_improvements,
            confidence=lesson.confidence,
            evidence=lesson.evidence,
            applicable_agents=lesson.applicable_agents,
            tags=lesson.tags,
            version=lesson.version,
            supersedes=lesson.supersedes,
            metadata=lesson.metadata or {},
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_by_id(self, lesson_id: UUID) -> Optional[Lesson]:
        """Get lesson by ID."""
        result = await self.session.execute(
            select(LessonModel).where(LessonModel.id == lesson_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_type(
        self,
        lesson_type: LessonType,
        limit: int = 50,
    ) -> List[Lesson]:
        """Get lessons by type."""
        result = await self.session.execute(
            select(LessonModel)
            .where(LessonModel.lesson_type == lesson_type)
            .order_by(desc(LessonModel.confidence))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_applicable(
        self,
        agent_name: AgentName,
        context: Dict[str, Any],
        limit: int = 10,
    ) -> List[Lesson]:
        """Get applicable lessons for agent and context."""
        result = await self.session.execute(
            select(LessonModel)
            .where(LessonModel.applicable_agents.contains([agent_name]))
            .order_by(desc(LessonModel.confidence))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def search(self, query: str, limit: int = 20) -> List[Lesson]:
        """Search lessons by text."""
        search_term = f"%{query}%"
        result = await self.session.execute(
            select(LessonModel)
            .where(
                or_(
                    LessonModel.title.ilike(search_term),
                    LessonModel.description.ilike(search_term),
                )
            )
            .order_by(desc(LessonModel.confidence))
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: LessonModel) -> Lesson:
        """Convert model to entity."""
        return Lesson(
            id=model.id,
            lesson_type=model.lesson_type,
            title=model.title,
            description=model.description,
            do=model.do or [],
            dont=model.dont or [],
            best_practices=model.best_practices or [],
            anti_patterns=model.anti_patterns or [],
            known_bugs=model.known_bugs or [],
            prompt_improvements=model.prompt_improvements or [],
            confidence=model.confidence,
            evidence=model.evidence or [],
            applicable_agents=model.applicable_agents or [],
            tags=model.tags or [],
            version=model.version,
            supersedes=model.supersedes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLJobRepository(JobRepository):
    """SQL implementation of job repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, entity) -> None:
        self.session.add(entity)

    async def delete(self, entity_id: UUID) -> bool:
        result = await self.session.execute(
            select(JobModel).where(JobModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            return True
        return False

    async def create_job(
        self,
        job_type: JobType,
        payload: Dict[str, Any],
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
    ) -> UUID:
        """Create new job."""
        model = JobModel(
            job_type=job_type,
            payload=payload,
            priority=priority,
            scheduled_at=scheduled_at or datetime.utcnow(),
            status=JobStatus.QUEUED if not scheduled_at or scheduled_at <= datetime.utcnow() else JobStatus.SCHEDULED,
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_job(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        result = await self.session.execute(
            select(JobModel).where(JobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return {
                "id": str(model.id),
                "job_type": model.job_type.value,
                "status": model.status.value,
                "priority": model.priority,
                "payload": model.payload,
                "result": model.result,
                "error": model.error,
                "retry_count": model.retry_count,
                "scheduled_at": model.scheduled_at.isoformat() if model.scheduled_at else None,
                "started_at": model.started_at.isoformat() if model.started_at else None,
                "completed_at": model.completed_at.isoformat() if model.completed_at else None,
                "worker_id": model.worker_id,
            }
        return None

    async def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update job status."""
        result = await self.session.execute(
            select(JobModel).where(JobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.status = status
            if result:
                model.result = result
            if error:
                model.error = error
            if status == JobStatus.RUNNING:
                model.started_at = datetime.utcnow()
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                model.completed_at = datetime.utcnow()
            return True
        return False

    async def get_pending_jobs(
        self,
        job_type: Optional[JobType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get pending jobs."""
        query = select(JobModel).where(
            JobModel.status.in_([JobStatus.QUEUED, JobStatus.SCHEDULED])
        )
        if job_type:
            query = query.where(JobModel.job_type == job_type)
        query = query.order_by(JobModel.priority.desc(), JobModel.scheduled_at).limit(limit)

        result = await self.session.execute(query)
        models = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "job_type": m.job_type.value,
                "status": m.status.value,
                "priority": m.priority,
                "payload": m.payload,
                "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
            }
            for m in models
        ]

    async def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics."""
        result = await self.session.execute(
            select(
                JobModel.job_type,
                JobModel.status,
                func.count(JobModel.id),
            )
            .group_by(JobModel.job_type, JobModel.status)
        )
        stats = {}
        for job_type, status, count in result.all():
            if job_type.value not in stats:
                stats[job_type.value] = {}
            stats[job_type.value][status.value] = count
        return stats


class SQLUserRepository(UserRepository):
    """SQL implementation of user repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return {
                "id": str(model.id),
                "email": model.email,
                "full_name": model.full_name,
                "is_active": model.is_active,
                "is_superuser": model.is_superuser,
                "roles": model.roles,
                "permissions": model.permissions,
                "last_login": model.last_login.isoformat() if model.last_login else None,
            }
        return None

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        if model:
            return {
                "id": str(model.id),
                "email": model.email,
                "password_hash": model.password_hash,
                "full_name": model.full_name,
                "is_active": model.is_active,
                "is_superuser": model.is_superuser,
                "roles": model.roles,
                "permissions": model.permissions,
            }
        return None

    async def create_user(
        self,
        email: str,
        password_hash: str,
        roles: List[str],
        permissions: List[str],
    ) -> UUID:
        """Create new user."""
        model = UserModel(
            email=email.lower(),
            password_hash=password_hash,
            roles=roles,
            permissions=permissions,
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def update_user(
        self,
        user_id: UUID,
        updates: Dict[str, Any],
    ) -> bool:
        """Update user."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            for key, value in updates.items():
                if hasattr(model, key):
                    setattr(model, key, value)
            model.updated_at = datetime.utcnow()
            return True
        return False


class SQLAPIKeyRepository(APIKeyRepository):
    """SQL implementation of API key repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_key(
        self,
        user_id: UUID,
        name: str,
        key_hash: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None,
    ) -> UUID:
        """Create API key."""
        model = APIKeyModel(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            scopes=scopes,
            expires_at=expires_at,
        )
        self.session.add(model)
        await self.session.flush()
        return model.id

    async def get_key(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash."""
        result = await self.session.execute(
            select(APIKeyModel).where(APIKeyModel.key_hash == key_hash)
        )
        model = result.scalar_one_or_none()
        if model:
            return {
                "id": str(model.id),
                "user_id": str(model.user_id),
                "name": model.name,
                "scopes": model.scopes,
                "is_active": model.is_active,
                "expires_at": model.expires_at.isoformat() if model.expires_at else None,
            }
        return None

    async def revoke_key(self, key_id: UUID) -> bool:
        """Revoke API key."""
        result = await self.session.execute(
            select(APIKeyModel).where(APIKeyModel.id == key_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.is_active = False
            return True
        return False

    async def list_keys(self, user_id: UUID) -> List[Dict[str, Any]]:
        """List user's API keys."""
        result = await self.session.execute(
            select(APIKeyModel).where(APIKeyModel.user_id == user_id)
        )
        models = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "name": m.name,
                "scopes": m.scopes,
                "is_active": m.is_active,
                "expires_at": m.expires_at.isoformat() if m.expires_at else None,
                "last_used": m.last_used.isoformat() if m.last_used else None,
                "created_at": m.created_at.isoformat(),
            }
            for m in models
        ]


# Need to add the missing AnalysisModel and ReportModel to models.py
# Let me add them inline here for completeness