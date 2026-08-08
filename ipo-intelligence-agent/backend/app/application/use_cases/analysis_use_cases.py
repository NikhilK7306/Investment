"""Use cases for IPO analysis."""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.interfaces.repositories import (
    AnalysisRepository,
    FinancialRepository,
    IPORepository,
    CompanyRepository,
    ReportRepository,
)
from app.domain.entities.entities import OverallAnalysis
from app.domain.value_objects.value_objects import (
    FinancialMetrics,
    InvestmentThesis,
    RiskFactor,
    SentimentData,
    ScoreComponent,
    Money,
    Percentage,
    Ratio,
)
from app.domain.enums.enums import (
    AnalysisStatus,
    InvestmentStrategy,
    RiskLevel,
    SentimentLabel,
    TimeHorizon,
    AgentName,
    AgentStatus,
)
from app.agents.base import AgentContext
from app.agents.fundamental.agent import FundamentalAnalysisAgent
from app.agents.market.agent import MarketAnalysisAgent
from app.agents.sentiment.agent import SentimentAnalysisAgent
from app.agents.risk.agent import RiskAnalysisAgent
from app.agents.decision.agent import DecisionSupportAgent


class AnalyzeIPOUseCase:
    """Use case for analyzing an IPO."""

    @staticmethod
    def _sanitize(value: Any) -> Any:
        """Recursively convert non-JSON-serializable values (Decimal etc)."""
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, dict):
            return {str(k): AnalyzeIPOUseCase._sanitize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [AnalyzeIPOUseCase._sanitize(v) for v in value]
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        return repr(value)

    def __init__(
        self,
        ipo_repo: IPORepository,
        company_repo: CompanyRepository,
        financial_repo: FinancialRepository,
        analysis_repo: AnalysisRepository,
    ):
        self.ipo_repo = ipo_repo
        self.company_repo = company_repo
        self.financial_repo = financial_repo
        self.analysis_repo = analysis_repo

    async def execute(
        self,
        symbol: str,
        depth: str = "standard",
        user_id: Optional[str] = None,
    ) -> OverallAnalysis:
        """Execute full IPO analysis by orchestrating the analysis agents."""
        # Get IPO and company data
        ipo = await self.ipo_repo.get_by_symbol(symbol)
        company = await self.company_repo.get_by_symbol(symbol)
        financials = await self.financial_repo.get_history(symbol, periods=8)

        if not ipo:
            raise ValueError(f"IPO not found for symbol: {symbol}")

        # Create analysis record (in-flight RUNNING state)
        analysis_id = await self.analysis_repo.save_analysis(
            symbol=symbol,
            analysis_data={
                "status": AnalysisStatus.RUNNING,
                "model_version": "2.0.0",
            }
        )

        try:
            overall_analysis = await self._run_agent_pipeline(
                symbol=symbol,
                analysis_id=analysis_id,
                company=company.to_dict() if company else {},
                financials=financials,
                depth=depth,
                user_id=user_id,
            )
        except Exception as e:
            # Update analysis with error
            await self.analysis_repo.save_analysis(symbol, {
                "status": AnalysisStatus.FAILED,
                "error": str(e),
                "completed_at": datetime.utcnow(),
            })
            raise

        # Update analysis with results
        await self.analysis_repo.save_analysis(symbol, {
            "status": overall_analysis.status,
            "overall_score": overall_analysis.overall_score,
            "confidence": overall_analysis.confidence,
            "financial_strength_score": overall_analysis.financial_strength_score,
            "growth_potential_score": overall_analysis.growth_potential_score,
            "market_opportunity_score": overall_analysis.market_opportunity_score,
            "management_quality_score": overall_analysis.management_quality_score,
            "risk_level_score": overall_analysis.risk_level_score,
            "score_breakdown": overall_analysis.score_breakdown,
            "bull_case": overall_analysis.bull_case,
            "bear_case": overall_analysis.bear_case,
            "key_risks": overall_analysis.key_risks,
            "key_catalysts": overall_analysis.key_catalysts,
            "investment_strategy": overall_analysis.investment_strategy,
            "time_horizon": overall_analysis.time_horizon,
            "risk_level": overall_analysis.risk_level,
            "risk_factors": overall_analysis.risk_factors,
            "sentiment": overall_analysis.sentiment,
            "sentiment_score": overall_analysis.sentiment_score,
            "sentiment_drivers": overall_analysis.sentiment_drivers,
            "agent_results": overall_analysis.agent_results,
            "model_version": overall_analysis.model_version,
            "completed_at": datetime.utcnow(),
        })

        return overall_analysis

    @staticmethod
    def _serialize_metrics(metrics: FinancialMetrics) -> Dict[str, Any]:
        """Convert FinancialMetrics into the plain-dict shape agents expect."""
        def money(val):
            return float(val.amount) if isinstance(val, Money) else val

        def pct(val):
            return val.to_decimal() if isinstance(val, Percentage) else val

        def ratio(val):
            return float(val.value) if isinstance(val, Ratio) else val

        fields = {
            "revenue": ("revenue", money),
            "revenue_growth_yoy": ("revenue_growth_yoy", pct),
            "revenue_growth_qoq": ("revenue_growth_qoq", pct),
            "gross_profit": ("gross_profit", money),
            "gross_margin": ("gross_margin", pct),
            "operating_income": ("operating_income", money),
            "operating_margin": ("operating_margin", pct),
            "net_income": ("net_income", money),
            "net_margin": ("net_margin", pct),
            "ebitda": ("ebitda", money),
            "ebitda_margin": ("ebitda_margin", pct),
            "free_cash_flow": ("free_cash_flow", money),
            "fcf_margin": ("fcf_margin", pct),
            "total_assets": ("total_assets", money),
            "total_liabilities": ("total_liabilities", money),
            "total_equity": ("total_equity", money),
            "cash_and_equivalents": ("cash_and_equivalents", money),
            "total_debt": ("total_debt", money),
            "operating_cash_flow": ("operating_cash_flow", money),
            "debt_to_equity": ("debt_to_equity", ratio),
            "current_ratio": ("current_ratio", ratio),
            "quick_ratio": ("quick_ratio", ratio),
            "roe": ("roe", pct),
            "roa": ("roa", pct),
            "roic": ("roic", pct),
            "pe_ratio": ("pe_ratio", ratio),
            "ps_ratio": ("ps_ratio", ratio),
            "ev_ebitda": ("ev_ebitda", ratio),
            "ev_revenue": ("ev_revenue", ratio),
            "revenue_cagr_3y": ("revenue_cagr_3y", pct),
            "revenue_cagr_5y": ("revenue_cagr_5y", pct),
            "fcf_conversion": ("fcf_conversion", pct),
            "period": ("period", lambda v: v),
            "as_of_date": ("as_of_date", lambda v: v.isoformat() if v else None),
        }

        result = {}
        for key, (attr, fn) in fields.items():
            val = getattr(metrics, attr, None)
            result[key] = fn(val) if val is not None else None
        return result

    async def _run_agent_pipeline(
        self,
        symbol: str,
        analysis_id: UUID,
        company: Dict[str, Any],
        financials: List[FinancialMetrics],
        depth: str,
        user_id: Optional[str],
    ) -> OverallAnalysis:
        """Run the fundamental/market/sentiment/risk agents, then synthesize."""
        context = AgentContext(
            ipo_symbol=symbol.upper(),
            analysis_id=analysis_id,
            user_id=user_id,
            depth=depth,
        )

        serialized_financials = [self._serialize_metrics(m) for m in financials if m]
        industry_data = {
            "market_cagr": 0.12,
            "lifecycle": "growth",
            "tailwinds": ["Sector tailwinds", "Rising investor interest"],
            "headwinds": [],
        }

        agent_specs = [
            ("fundamental", FundamentalAnalysisAgent(), {
                "financials": serialized_financials,
                "company_profile": company,
                "public_comps": [],
            }),
            ("market", MarketAnalysisAgent(), {
                "company_profile": company,
                "industry_data": industry_data,
                "competitors": [],
                "financials": serialized_financials,
            }),
            ("sentiment", SentimentAnalysisAgent(), {
                "news": [],
                "analyst_reports": [],
                "social_media": [],
                "alternative_data": [],
                "institutional_flows": [],
            }),
            ("risk", RiskAnalysisAgent(), {
                "financials": serialized_financials,
                "company_profile": company,
                "market_analysis": {},
                "competitive_analysis": {},
                "legal_data": {},
                "ipo_details": {},
            }),
        ]

        gathered = await asyncio.gather(
            *(agent.run_with_retry(context, data) for _, agent, data in agent_specs)
        )
        agent_map = {
            name: result
            for (name, _, _), result in zip(agent_specs, gathered)
        }

        # Synthesize with the Decision agent using whatever completed
        key_names = {
            "fundamental": "fundamental_analysis",
            "market": "market_analysis",
            "risk": "risk_analysis",
            "sentiment": "sentiment_analysis",
        }
        decision_input = {}
        for name, key in key_names.items():
            result = agent_map[name]
            decision_input[key] = (result.data or {}) if result.status == AgentStatus.COMPLETED else {}

        decision_result = await DecisionSupportAgent().run_with_retry(context, decision_input)
        if decision_result.status != AgentStatus.COMPLETED or not decision_result.data:
            raise RuntimeError(
                f"Decision agent failed: {decision_result.error or 'unknown error'}"
            )

        decision_data = decision_result.data
        thesis = decision_data.get("investment_thesis", {})
        pillar_scores = decision_data.get("pillar_scores", {})

        sentiment_data = agent_map["sentiment"].data or {}
        sentiment_score = float(sentiment_data.get("composite_score", 0.0))
        sentiment_label = SentimentLabel(
            sentiment_data.get("composite_label", SentimentLabel.NEUTRAL.value)
        )

        return OverallAnalysis(
            id=analysis_id,
            ipo_id=UUID(int=0),
            status=AnalysisStatus.COMPLETED,
            overall_score=float(decision_data.get("overall_score", 50.0)),
            confidence=float(decision_data.get("confidence", 0.5)),
            financial_strength_score=float(pillar_scores.get("fundamental", 50.0)),
            growth_potential_score=float(pillar_scores.get("market", 50.0)),
            market_opportunity_score=float(pillar_scores.get("market", 50.0)),
            management_quality_score=50.0,
            risk_level_score=float(pillar_scores.get("risk", 50.0)),
            score_breakdown={
                "financial_strength": round(float(pillar_scores.get("fundamental", 50.0)), 1),
                "growth_potential": round(float(pillar_scores.get("market", 50.0)), 1),
                "market_opportunity": round(float(pillar_scores.get("market", 50.0)), 1),
                "management_quality": 50.0,
                "risk_level": round(float(pillar_scores.get("risk", 50.0)), 1),
            },
            bull_case=str(thesis.get("bull_case", "No bull case generated")),
            bear_case=str(thesis.get("bear_case", "No bear case generated")),
            key_risks=thesis.get("key_risks", []) or [],
            key_catalysts=thesis.get("key_catalysts", []) or [],
            investment_strategy=InvestmentStrategy(decision_data.get("recommendation", "watch")),
            time_horizon=TimeHorizon(decision_data.get("time_horizon", TimeHorizon.MEDIUM_TERM.value)),
            risk_level=RiskLevel(decision_data.get("risk_level", RiskLevel.MODERATE.value)),
            risk_factors=[],
            sentiment=sentiment_label,
            sentiment_score=round(sentiment_score, 3),
            sentiment_drivers=sentiment_data.get("themes", [])[:5] if isinstance(sentiment_data.get("themes"), list) else [],
            agent_results=[self._sanitize(r.to_dict()) for r in agent_map.values() if r.status == AgentStatus.COMPLETED],
            completed_at=datetime.utcnow(),
            model_version="2.0.0",
        )


class GetAnalysisUseCase:
    """Use case for getting analysis results."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def get_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest analysis for symbol."""
        return await self.analysis_repo.get_latest_analysis(symbol)

    async def get_history(
        self,
        symbol: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get analysis history."""
        return await self.analysis_repo.get_analysis_history(symbol, limit)

    async def get_by_id(self, analysis_id: UUID) -> Optional[Dict[str, Any]]:
        """Get analysis by ID."""
        return await self.analysis_repo.get_analysis_by_id(analysis_id)


class SaveAnalysisUseCase:
    """Use case for saving analysis results."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def execute(
        self,
        symbol: str,
        analysis_data: Dict[str, Any],
    ) -> UUID:
        """Save analysis."""
        return await self.analysis_repo.save_analysis(symbol, analysis_data)


class SaveScoreBreakdownUseCase:
    """Use case for saving score breakdown."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def execute(
        self,
        analysis_id: UUID,
        components: List[ScoreComponent],
    ) -> None:
        """Save score breakdown."""
        await self.analysis_repo.save_score_breakdown(analysis_id, components)


class GetScoreBreakdownUseCase:
    """Use case for getting score breakdown."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def execute(self, analysis_id: UUID) -> List[ScoreComponent]:
        """Get score breakdown."""
        return await self.analysis_repo.get_score_breakdown(analysis_id)


class SaveRiskFactorsUseCase:
    """Use case for saving risk factors."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def execute(
        self,
        analysis_id: UUID,
        risk_factors: List[RiskFactor],
    ) -> None:
        """Save risk factors."""
        await self.analysis_repo.save_risk_factors(analysis_id, risk_factors)


class GetRiskFactorsUseCase:
    """Use case for getting risk factors."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def execute(self, analysis_id: UUID) -> List[RiskFactor]:
        """Get risk factors."""
        return await self.analysis_repo.get_risk_factors(analysis_id)


class SaveInvestmentThesisUseCase:
    """Use case for saving investment thesis."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def execute(
        self,
        analysis_id: UUID,
        thesis: InvestmentThesis,
    ) -> None:
        """Save investment thesis."""
        await self.analysis_repo.save_investment_thesis(analysis_id, thesis)


class GetInvestmentThesisUseCase:
    """Use case for getting investment thesis."""

    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    async def execute(self, analysis_id: UUID) -> Optional[InvestmentThesis]:
        """Get investment thesis."""
        return await self.analysis_repo.get_investment_thesis(analysis_id)


class GetFinancialsUseCase:
    """Use case for getting financial data."""

    def __init__(self, financial_repo: FinancialRepository):
        self.financial_repo = financial_repo

    async def get_latest(self, symbol: str) -> Optional[FinancialMetrics]:
        """Get latest financial metrics."""
        return await self.financial_repo.get_latest(symbol)

    async def get_history(
        self,
        symbol: str,
        periods: int = 8,
    ) -> List[FinancialMetrics]:
        """Get financial history."""
        return await self.financial_repo.get_history(symbol, periods)

    async def get_by_period(
        self,
        symbol: str,
        period: str,
    ) -> Optional[FinancialMetrics]:
        """Get financials for specific period."""
        return await self.financial_repo.get_by_period(symbol, period)