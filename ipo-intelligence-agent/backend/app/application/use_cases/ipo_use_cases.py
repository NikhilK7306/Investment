"""Use cases for IPO discovery and analysis orchestration."""

import logging
from dataclasses import replace
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.interfaces.repositories import (
    IPORepository,
    JobRepository,
    CompanyRepository,
    AnalysisRepository,
    ReportRepository,
    FinancialRepository,
)
from app.domain.enums.enums import (
    IPOStatus,
    Exchange,
    Sector,
    JobType,
    JobStatus,
    AgentName,
    AgentStatus,
)
from app.domain.value_objects.value_objects import IPODetails, CompanyProfile
from app.agents.base import AgentContext, AgentOrchestrator
from app.agents.discovery.agent import DiscoveryAgent
from app.agents.collection.agent import CollectionAgent
from app.agents.fundamental.agent import FundamentalAnalysisAgent
from app.agents.market.agent import MarketAnalysisAgent
from app.agents.risk.agent import RiskAnalysisAgent
from app.agents.sentiment.agent import SentimentAnalysisAgent
from app.agents.decision.agent import DecisionSupportAgent
from app.agents.report.agent import ReportGenerationAgent
from app.agents.memory_agent.agent import MemoryManagementAgent
from app.agents.reflection_agent.agent import ReflectionAgent
from app.core.exceptions.base import AgentError


def _flat_financials(metrics) -> Dict[str, Any]:
    """Flatten a FinancialMetrics VO into the simple shape the report agent uses."""
    from app.domain.value_objects.value_objects import Money, Percentage, Ratio

    def money(val):
        return val.amount if isinstance(val, Money) else val

    def pct(val):
        return val.to_decimal() if isinstance(val, Percentage) else val

    def ratio(val):
        return val.value if isinstance(val, Ratio) else val

    def present(val):
        return val if val is not None else None

    flat = {
        "period": getattr(metrics, "period", None) or "N/A",
        "revenue": money(getattr(metrics, "revenue", None)),
        "revenue_growth_yoy": pct(getattr(metrics, "revenue_growth_yoy", None)),
        "gross_profit": money(getattr(metrics, "gross_profit", None)),
        "gross_margin": pct(getattr(metrics, "gross_margin", None)),
        "operating_income": money(getattr(metrics, "operating_income", None)),
        "operating_margin": pct(getattr(metrics, "operating_margin", None)),
        "net_income": money(getattr(metrics, "net_income", None)),
        "net_margin": pct(getattr(metrics, "net_margin", None)),
        "ebitda": money(getattr(metrics, "ebitda", None)),
        "ebitda_margin": pct(getattr(metrics, "ebitda_margin", None)),
        "free_cash_flow": money(getattr(metrics, "free_cash_flow", None)),
        "fcf_margin": pct(getattr(metrics, "fcf_margin", None)),
        "cash_and_equivalents": money(getattr(metrics, "cash_and_equivalents", None)),
        "total_debt": money(getattr(metrics, "total_debt", None)),
        "total_equity": money(getattr(metrics, "total_equity", None)),
        "operating_cash_flow": money(getattr(metrics, "operating_cash_flow", None)),
        "debt_to_equity": ratio(getattr(metrics, "debt_to_equity", None)),
        "current_ratio": ratio(getattr(metrics, "current_ratio", None)),
        "roe": pct(getattr(metrics, "roe", None)),
        "roic": pct(getattr(metrics, "roic", None)),
    }
    return present({k: v for k, v in flat.items() if v is not None})


def _to_int(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _to_float(value):
    if value is None or isinstance(value, (int, float)):
        return value
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _default_scores(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fill None numeric score fields so report formatting never crashes."""
    result = dict(data)
    for key in (
        "overall_score", "confidence", "financial_strength_score",
        "growth_potential_score", "market_opportunity_score",
        "management_quality_score", "risk_level_score", "sentiment_score",
    ):
        if result.get(key) is None:
            result[key] = 0.0
    return result


def _sanitize_report(value: Any) -> Any:
    """Recursively convert non-JSON-serializable values (Decimal etc)."""
    from decimal import Decimal
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, dict):
        return {str(k): _sanitize_report(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_report(v) for v in value]
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return repr(value)


class DiscoverIPOsUseCase:
    """Use case for discovering IPOs."""

    DEFAULT_SOURCES = ["nasdaq", "sec", "investorgain"]

    def __init__(
        self,
        ipo_repo: IPORepository,
        company_repo: CompanyRepository,
    ):
        self.ipo_repo = ipo_repo
        self.company_repo = company_repo

    async def execute(
        self,
        sources: List[str] = None,
        lookahead_days: int = 90,
        min_market_cap: float = 0,
    ) -> List[IPODetails]:
        """Execute IPO discovery and persist results."""
        sources = sources or self.DEFAULT_SOURCES

        # Run discovery agent
        discovery_agent = DiscoveryAgent()

        context = AgentContext(
            ipo_symbol="",
            analysis_id=None,
            parameters={
                "sources": sources,
                "lookahead_days": lookahead_days,
                "min_market_cap": min_market_cap,
            },
        )

        input_data = {
            "sources": sources,
            "lookahead_days": lookahead_days,
            "min_market_cap": min_market_cap,
        }

        result = await discovery_agent.run_with_retry(context, input_data)

        if result.status not in (AgentStatus.COMPLETED, AgentStatus.PARTIAL):
            return []

        saved = []
        for ipo in result.data or []:
            try:
                # Upsert company profile first (ipos.company_id is a required FK)
                company = await self.company_repo.get_by_symbol(ipo.symbol)
                if company is None:
                    company = CompanyProfile(
                        legal_name=ipo.company_name,
                        common_name=ipo.company_name,
                        description="",
                        business_model="",
                        ticker=ipo.symbol,
                        exchange=ipo.exchange,
                        sector=ipo.sector,
                        industry=ipo.industry,
                    )
                    company_id = await self.company_repo.save(company)
                else:
                    company_id = company.id

                # Skip IPOs we already know about
                if await self.ipo_repo.get_by_symbol(ipo.symbol):
                    continue

                await self.ipo_repo.save(replace(ipo, company_id=company_id))
                saved.append(ipo)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "Skipping IPO %s: %s", getattr(ipo, "symbol", "?"), e
                )
                continue

        return saved


class GetUpcomingIPOsUseCase:
    """Use case for getting upcoming IPOs."""

    def __init__(self, ipo_repo: IPORepository):
        self.ipo_repo = ipo_repo

    async def execute(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        exchange: Optional[Exchange] = None,
        sector: Optional[Sector] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        region: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> List[IPODetails]:
        """Get upcoming IPOs with filters."""
        return await self.ipo_repo.list_upcoming(
            limit=limit,
            offset=offset,
            status=status,
            exchange=exchange,
            sector=sector,
            from_date=from_date,
            to_date=to_date,
            region=region,
            phase=phase,
        )


class GetIPODetailsUseCase:
    """Use case for getting IPO details."""

    def __init__(self, ipo_repo: IPORepository):
        self.ipo_repo = ipo_repo

    async def execute(self, symbol: str) -> Optional[IPODetails]:
        """Get IPO details by symbol."""
        return await self.ipo_repo.get_by_symbol(symbol.upper())


class SearchIPOsUseCase:
    """Use case for searching IPOs."""

    def __init__(self, ipo_repo: IPORepository):
        self.ipo_repo = ipo_repo

    async def execute(self, query: str, limit: int = 20) -> List[IPODetails]:
        """Search IPOs."""
        return await self.ipo_repo.search(query, limit)


class GetRecentIPOsUseCase:
    """Use case for getting recently listed IPOs."""

    def __init__(self, ipo_repo: IPORepository):
        self.ipo_repo = ipo_repo

    async def execute(self, days: int = 30, limit: int = 20) -> List[IPODetails]:
        """Get recently listed IPOs."""
        return await self.ipo_repo.get_recently_listed(days, limit)


class AnalyzeIPOUseCase:
    """Use case for orchestrating full IPO analysis."""

    def __init__(
        self,
        ipo_repo: IPORepository,
        job_repo: JobRepository,
    ):
        self.ipo_repo = ipo_repo
        self.job_repo = job_repo

    async def execute(
        self,
        symbol: str,
        depth: str = "standard",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute full IPO analysis pipeline."""
        # Create analysis job
        job_id = await self.job_repo.create_job(
            job_type=JobType.DATA_COLLECTION,
            payload={
                "symbol": symbol,
                "depth": depth,
                "user_id": user_id,
            },
            priority=10,
        )

        # Get IPO details
        ipo = await self.ipo_repo.get_by_symbol(symbol.upper())
        if not ipo:
            await self.job_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error=f"IPO {symbol} not found",
            )
            return {"error": f"IPO {symbol} not found"}

        # Initialize orchestrator
        orchestrator = AgentOrchestrator()

        # Register all agents
        agents = [
            CollectionAgent(),
            FundamentalAnalysisAgent(),
            MarketAnalysisAgent(),
            RiskAnalysisAgent(),
            SentimentAnalysisAgent(),
            DecisionSupportAgent(),
            ReportGenerationAgent(),
            MemoryManagementAgent(),
        ]
        for agent in agents:
            orchestrator.register_agent(agent)

        # Set execution order: collection -> parallel analysis -> decision -> report -> memory
        orchestrator.set_execution_order([
            [AgentName.COLLECTION],
            [AgentName.FUNDAMENTAL, AgentName.MARKET, AgentName.RISK, AgentName.SENTIMENT],
            [AgentName.DECISION],
            [AgentName.REPORT],
            [AgentName.MEMORY],
        ])

        # Create context
        context = AgentContext(
            ipo_symbol=symbol.upper(),
            analysis_id=job_id,
            user_id=user_id,
            depth=depth,
        )

        # Run workflow
        try:
            await self.job_repo.update_job_status(job_id, JobStatus.RUNNING)

            results = await orchestrator.execute_workflow(context, {"ipo": ipo.__dict__ if hasattr(ipo, '__dict__') else ipo})

            # Update job
            await self.job_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                result={
                    "agents_completed": len([r for r in results.values() if r.status == AgentStatus.COMPLETED]),
                    "agents_failed": len([r for r in results.values() if r.status == AgentStatus.FAILED]),
                },
            )

            return {
                "job_id": str(job_id),
                "symbol": symbol,
                "results": {k: v.to_dict() for k, v in results.items()},
            }

        except Exception as e:
            await self.job_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error=str(e),
            )
            return {"error": str(e)}


class CollectIPODataUseCase:
    """Use case for collecting IPO data."""

    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def execute(
        self,
        symbol: str,
        ipo_details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Collect comprehensive data for IPO."""
        job_id = await self.job_repo.create_job(
            job_type=JobType.DATA_COLLECTION,
            payload={"symbol": symbol, "ipo_details": ipo_details},
            priority=10,
        )

        collection_agent = CollectionAgent()

        context = AgentContext(
            ipo_symbol=symbol,
            analysis_id=job_id,
        )

        input_data = {"ipo_details": ipo_details}

        result = await collection_agent.run_with_retry(context, input_data)

        if result.status == AgentStatus.COMPLETED:
            await self.job_repo.update_job_status(job_id, JobStatus.COMPLETED, result.data)
        else:
            await self.job_repo.update_job_status(job_id, JobStatus.FAILED, error=result.error)

        return {
            "job_id": str(job_id),
            "result": result.to_dict() if hasattr(result, 'to_dict') else result.__dict__,
        }


class GenerateReportUseCase:
    """Use case for generating and persisting investment reports."""

    def __init__(
        self,
        job_repo: JobRepository,
        report_repo: Optional[ReportRepository] = None,
        analysis_repo: Optional[AnalysisRepository] = None,
        ipo_repo: Optional[IPORepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        financial_repo: Optional[FinancialRepository] = None,
    ):
        self.job_repo = job_repo
        self.report_repo = report_repo
        self.analysis_repo = analysis_repo
        self.ipo_repo = ipo_repo
        self.company_repo = company_repo
        self.financial_repo = financial_repo

    async def execute(
        self,
        symbol: str,
        analysis_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate investment research report from the latest stored analysis."""
        symbol = symbol.upper()
        job_id = await self.job_repo.create_job(
            job_type=JobType.REPORT_GENERATION,
            payload={"symbol": symbol},
            priority=5,
        )

        context = AgentContext(
            ipo_symbol=symbol,
            analysis_id=job_id,
        )

        # Load the latest analysis if no results were passed in
        stored = None
        if self.analysis_repo is not None:
            stored = await self.analysis_repo.get_latest_analysis(symbol)

        try:
            input_data = await self._build_input_data(symbol, stored or {})
            report_agent = ReportGenerationAgent()
            result = await report_agent.run_with_retry(context, input_data)

            report_id = None
            if result.status == AgentStatus.COMPLETED:
                report_payload = (result.data or {}).get("report") or result.data
                if self.report_repo is not None and report_payload:
                    analysis_id = (stored or {}).get("id")
                    saved = await self.report_repo.save_report(
                        symbol=symbol,
                        analysis_id=analysis_id or job_id,
                        report_data=_sanitize_report(report_payload),
                    )
                    report_id = saved.get("id") if isinstance(saved, dict) else str(saved)
                await self.job_repo.update_job_status(
                    job_id, JobStatus.COMPLETED, _sanitize_report(result.data or {})
                )
                return {
                    "job_id": str(job_id),
                    "status": JobStatus.COMPLETED.value,
                    "report": report_payload or {},
                    "report_id": report_id,
                }

            error = result.error or "Unknown error"
            await self.job_repo.update_job_status(job_id, JobStatus.FAILED, error=error)
            return {
                "job_id": str(job_id),
                "status": JobStatus.FAILED.value,
                "error": error,
            }
        except Exception as e:
            await self.job_repo.update_job_status(job_id, JobStatus.FAILED, error=str(e))
            return {
                "job_id": str(job_id),
                "status": JobStatus.FAILED.value,
                "error": str(e),
            }

    @staticmethod
    def _ipo_details_for_report(ipo) -> Dict[str, Any]:
        """Remap IPODetails into the key shape the report agent expects."""
        source = ipo.to_dict() if hasattr(ipo, 'to_dict') else {}

        def money_to_float(value):
            if value is None:
                return None
            raw = value.amount if hasattr(value, "amount") else value
            if isinstance(raw, str):
                try:
                    raw = float(raw.replace("$", "").replace(",", "").split()[0])
                except (ValueError, IndexError):
                    return None
            return float(raw)

        price_range = source.get("price_range") or {}
        valuation = source.get("valuation") or {}
        details = {
            "symbol": source.get("symbol", ""),
            "company_name": source.get("company_name", ""),
            "expected_price_low": money_to_float(price_range.get("low")),
            "expected_price_high": money_to_float(price_range.get("high")),
            "shares_offered": _to_int(source.get("shares_offered")),
            "expected_raise": money_to_float(source.get("expected_raise")),
            "greenshoe_option": source.get("greenshoe_option", False),
            "greenshoe_shares": _to_int(source.get("greenshoe_shares")),
            "expected_valuation_low": money_to_float(valuation.get("equity_value")),
            "expected_valuation_high": money_to_float(valuation.get("enterprise_value")),
            "post_money_valuation": money_to_float(valuation.get("equity_value")),
            "lead_underwriters": [source.get("lead_underwriter")] if source.get("lead_underwriter") else [],
            "co_managers": source.get("unders", []),
            "lockup_expiry": source.get("lockup_expiry"),
            "lockup_days": _to_int(source.get("lockup_period_days")),
            "insider_shares_pct": _to_float(source.get("insider_shares_pct")),
            "prospectus_url": source.get("prospectus_url"),
        }
        result = {}
        for k, v in details.items():
            if v is None:
                continue
            if k == "greenshoe_option" and v is False:
                continue
            result[k] = v
        return result

    async def _build_input_data(
        self,
        symbol: str,
        stored: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build the input dict the report agent expects."""
        ipo_details = {}
        if self.ipo_repo is not None:
            ipo = await self.ipo_repo.get_by_symbol(symbol)
            if ipo:
                ipo_details = self._ipo_details_for_report(ipo)

        company_profile = {}
        if self.company_repo is not None:
            company = await self.company_repo.get_by_symbol(symbol)
            if company:
                company_profile = (
                    company.to_dict() if hasattr(company, 'to_dict') else {}
                )

        financials = {"statements": []}
        if self.financial_repo is not None:
            history = await self.financial_repo.get_history(symbol, periods=8)
            for metrics in history:
                financials["statements"].append(
                    _flat_financials(metrics)
                )

        overall_analysis = _default_scores(stored or {})

        # Split stored agent_results (list of dicts) back into per-agent inputs
        by_agent: Dict[str, Any] = {}
        raw_agent_results = stored.get("agent_results") if stored else None
        if isinstance(raw_agent_results, list):
            for entry in raw_agent_results:
                name = entry.get("agent_name") if isinstance(entry, dict) else None
                if name:
                    by_agent[name] = entry

        def agent_data(agent_name: str) -> Dict[str, Any]:
            entry = by_agent.get(agent_name) or {}
            if isinstance(entry, dict):
                return entry.get("data") if isinstance(entry.get("data"), dict) else {}
            return {}

        return {
            "overall_analysis": overall_analysis,
            "fundamental_analysis": agent_data("fundamental"),
            "market_analysis": agent_data("market"),
            "risk_analysis": agent_data("risk"),
            "sentiment_analysis": agent_data("sentiment"),
            "ipo_details": ipo_details,
            "company_profile": company_profile,
            "financials": financials,
            "public_comps": [],
        }


class RunReflectionUseCase:
    """Use case for running reflection cycle."""

    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def execute(
        self,
        min_delay_days: int = 30,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """Run reflection on past predictions."""
        job_id = await self.job_repo.create_job(
            job_type=JobType.REFLECTION_RUN,
            payload={"min_delay_days": min_delay_days, "batch_size": batch_size},
            priority=1,
        )

        reflection_agent = ReflectionAgent()

        context = AgentContext(
            ipo_symbol="",
            analysis_id=job_id,
        )

        input_data = {
            "operation": "run_reflection",
            "min_delay_days": min_delay_days,
            "batch_size": batch_size,
        }

        result = await reflection_agent.run_with_retry(context, input_data)

        if result.status == AgentStatus.COMPLETED:
            await self.job_repo.update_job_status(job_id, JobStatus.COMPLETED, result.data)
        else:
            await self.job_repo.update_job_status(job_id, JobStatus.FAILED, error=result.error)

        return {
            "job_id": str(job_id),
            "result": result.to_dict() if hasattr(result, 'to_dict') else result.__dict__,
        }


class VerifyOutcomesUseCase:
    """Use case for verifying prediction outcomes."""

    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def execute(
        self,
        prediction_id: UUID,
        actual_value: float,
    ) -> Dict[str, Any]:
        """Verify a single prediction outcome."""
        job_id = await self.job_repo.create_job(
            job_type=JobType.OUTCOME_VERIFICATION,
            payload={"prediction_id": str(prediction_id), "actual_value": actual_value},
            priority=5,
        )

        reflection_agent = ReflectionAgent()

        context = AgentContext(
            ipo_symbol="",
            analysis_id=job_id,
        )

        input_data = {
            "operation": "verify_outcome",
            "prediction_id": str(prediction_id),
            "actual_value": actual_value,
        }

        result = await reflection_agent.run_with_retry(context, input_data)

        if result.status == AgentStatus.COMPLETED:
            await self.job_repo.update_job_status(job_id, JobStatus.COMPLETED, result.data)
        else:
            await self.job_repo.update_job_status(job_id, JobStatus.FAILED, error=result.error)

        return {
            "job_id": str(job_id),
            "result": result.to_dict() if hasattr(result, 'to_dict') else result.__dict__,
        }


class GetJobStatusUseCase:
    """Use case for getting job status."""

    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def execute(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job status."""
        return await self.job_repo.get_job(job_id)


class GetPendingJobsUseCase:
    """Use case for getting pending jobs."""

    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def execute(
        self,
        job_type: Optional[JobType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get pending jobs."""
        return await self.job_repo.get_pending_jobs(job_type, limit)


class GetJobStatsUseCase:
    """Use case for getting job statistics."""

    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def execute(self) -> Dict[str, Any]:
        """Get job statistics."""
        return await self.job_repo.get_job_stats()


class CreateIPOUseCase:
    """Stub use case for creating an IPO."""

    def __init__(self, ipo_repo, company_repo):
        self.ipo_repo = ipo_repo
        self.company_repo = company_repo

    async def execute(self, **kwargs):
        """Execute the use case."""
        raise NotImplementedError("CreateIPOUseCase not yet implemented")


class UpdateIPOStatusUseCase:
    """Stub use case for updating IPO status."""

    def __init__(self, ipo_repo):
        self.ipo_repo = ipo_repo

    async def execute(self, symbol: str, status: str) -> bool:
        """Execute the use case."""
        return await self.ipo_repo.update_status(symbol, status)


class GetCompanyProfileUseCase:
    """Stub use case for getting a company profile."""

    def __init__(self, company_repo):
        self.company_repo = company_repo

    async def execute(self, symbol: str):
        """Execute the use case."""
        return await self.company_repo.get_by_symbol(symbol)


class CreateCompanyProfileUseCase:
    """Stub use case for creating a company profile."""

    def __init__(self, company_repo):
        self.company_repo = company_repo

    async def execute(self, **kwargs):
        """Execute the use case."""
        raise NotImplementedError("CreateCompanyProfileUseCase not yet implemented")


class ListCompaniesBySectorUseCase:
    """Stub use case for listing companies by sector."""

    def __init__(self, company_repo):
        self.company_repo = company_repo

    async def execute(self, sector, limit=50, offset=0):
        """Execute the use case."""
        return await self.company_repo.list_by_sector(sector, limit, offset)


class ListCompaniesByIndustryUseCase:
    """Stub use case for listing companies by industry."""

    def __init__(self, company_repo):
        self.company_repo = company_repo

    async def execute(self, industry, limit=50, offset=0):
        """Execute the use case."""
        return await self.company_repo.list_by_industry(industry, limit, offset)