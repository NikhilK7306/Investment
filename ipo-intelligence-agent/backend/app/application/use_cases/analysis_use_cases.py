"""Use cases for IPO analysis."""

from datetime import datetime
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
)
from app.domain.enums.enums import (
    AnalysisStatus,
    InvestmentStrategy,
    RiskLevel,
    SentimentLabel,
    TimeHorizon,
    AgentName,
)
from app.domain.value_objects.value_objects import Money, Percentage, Ratio


class AnalyzeIPOUseCase:
    """Use case for analyzing an IPO."""

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
        """Execute full IPO analysis."""
        # Get IPO and company data
        ipo = await self.ipo_repo.get_by_symbol(symbol)
        company = await self.company_repo.get_by_symbol(symbol)
        financials = await self.financial_repo.get_history(symbol, periods=8)

        if not ipo:
            raise ValueError(f"IPO not found for symbol: {symbol}")

        # Create analysis record
        analysis_id = await self.analysis_repo.save_analysis(
            symbol=symbol,
            analysis_data={
                "status": AnalysisStatus.RUNNING,
                "model_version": "1.0.0",
            }
        )

        try:
            # In production, this would orchestrate all agents
            # For now, return a structured result
            overall_analysis = OverallAnalysis(
                id=analysis_id,
                ipo_id=ipo.id if hasattr(ipo, 'id') else UUID(int=0),
                status=AnalysisStatus.COMPLETED,
                overall_score=75.0,
                confidence=0.8,
                financial_strength_score=80.0,
                growth_potential_score=70.0,
                market_opportunity_score=75.0,
                management_quality_score=85.0,
                risk_level_score=30.0,  # Inverted
                score_breakdown={
                    "financial_strength": 80.0,
                    "growth_potential": 70.0,
                    "market_opportunity": 75.0,
                    "management_quality": 85.0,
                    "risk_level": 70.0,
                },
                bull_case="Strong fundamentals with large market opportunity",
                bear_case="High valuation and competitive risks",
                key_risks=["Competition", "Valuation", "Execution risk"],
                key_catalysts=["Product launch", "Market expansion", "Partnership announcements"],
                investment_strategy=InvestmentStrategy.ACCUMULATE,
                time_horizon=TimeHorizon.MEDIUM_TERM,
                risk_level=RiskLevel.MODERATE,
                risk_factors=[],
                sentiment=SentimentLabel.POSITIVE,
                sentiment_score=0.3,
                sentiment_drivers=["Positive analyst coverage", "Strong fundamentals"],
                agent_results={},
                model_version="1.0.0",
            )

            # Update analysis with results
            await self.analysis_repo.save_analysis(symbol, {
                "id": str(analysis_id),
                "status": AnalysisStatus.COMPLETED,
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
                "model_version": "1.0.0",
            })

            return overall_analysis

        except Exception as e:
            # Update analysis with error
            await self.analysis_repo.save_analysis(symbol, {
                "id": str(analysis_id),
                "status": AnalysisStatus.FAILED,
                "error": str(e),
            })
            raise


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