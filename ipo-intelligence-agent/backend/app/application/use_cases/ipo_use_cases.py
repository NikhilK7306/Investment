"""Use cases for IPO discovery and analysis orchestration."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.interfaces.repositories import IPORepository, JobRepository
from app.domain.enums.enums import (
    IPOStatus,
    Exchange,
    Sector,
    JobType,
    JobStatus,
    AgentName,
)
from app.domain.value_objects.value_objects import IPODetails
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


class DiscoverIPOsUseCase:
    """Use case for discovering IPOs."""

    def __init__(
        self,
        ipo_repo: IPORepository,
        job_repo: JobRepository,
    ):
        self.ipo_repo = ipo_repo
        self.job_repo = job_repo

    async def execute(
        self,
        sources: List[str] = None,
        lookahead_days: int = 90,
        min_market_cap: float = 0,
    ) -> Dict[str, Any]:
        """Execute IPO discovery."""
        # Create discovery job
        job_id = await self.job_repo.create_job(
            job_type=JobType.IPO_DISCOVERY,
            payload={
                "sources": sources or ["nasdaq", "nyse", "sec", "renaissance"],
                "lookahead_days": lookahead_days,
                "min_market_cap": min_market_cap,
            },
            priority=5,
        )

        # Run discovery agent
        discovery_agent = DiscoveryAgent()

        context = AgentContext(
            ipo_symbol="",
            analysis_id=job_id,
            parameters={
                "sources": sources or ["nasdaq", "nyse", "sec", "renaissance"],
                "lookahead_days": lookahead_days,
                "min_market_cap": min_market_cap,
            },
        )

        input_data = {
            "sources": sources or ["nasdaq", "nyse", "sec", "renaissance"],
            "lookahead_days": lookahead_days,
            "min_market_cap": min_market_cap,
        }

        result = await discovery_agent.run_with_retry(context, input_data)

        # Update job status
        if result.status == AgentStatus.COMPLETED:
            await self.job_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                result={"ipos_found": len(result.data) if result.data else 0},
            )
        else:
            await self.job_repo.update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                error=result.error,
            )

        return {
            "job_id": str(job_id),
            "result": result.to_dict() if hasattr(result, 'to_dict') else result.__dict__,
        }


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
        )


class GetIPODetailsUseCase:
    """Use case for getting IPO details."""

    def __init__(self, ipo_repo: IPORepository):
        self.ipo_repo = ipo_repo

    async def execute(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get IPO details by symbol."""
        ipo = await self.ipo_repo.get_by_symbol(symbol.upper())
        if ipo:
            return ipo.to_dict() if hasattr(ipo, 'to_dict') else ipo.__dict__
        return None


class SearchIPOsUseCase:
    """Use case for searching IPOs."""

    def __init__(self, ipo_repo: IPORepository):
        self.ipo_repo = ipo_repo

    async def execute(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search IPOs."""
        ipos = await self.ipo_repo.search(query, limit)
        return [ipo.to_dict() if hasattr(ipo, 'to_dict') else ipo.__dict__ for ipo in ipos]


class GetRecentIPOsUseCase:
    """Use case for getting recently listed IPOs."""

    def __init__(self, ipo_repo: IPORepository):
        self.ipo_repo = ipo_repo

    async def execute(self, days: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently listed IPOs."""
        ipos = await self.ipo_repo.get_recently_listed(days, limit)
        return [ipo.to_dict() if hasattr(ipo, 'to_dict') else ipo.__dict__ for ipo in ipos]


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
    """Use case for generating investment report."""

    def __init__(self, job_repo: JobRepository):
        self.job_repo = job_repo

    async def execute(
        self,
        symbol: str,
        analysis_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate investment research report."""
        job_id = await self.job_repo.create_job(
            job_type=JobType.REPORT_GENERATION,
            payload={"symbol": symbol, "analysis_results": analysis_results},
            priority=5,
        )

        report_agent = ReportGenerationAgent()

        context = AgentContext(
            ipo_symbol=symbol,
            analysis_id=job_id,
        )

        result = await report_agent.run_with_retry(context, analysis_results)

        if result.status == AgentStatus.COMPLETED:
            await self.job_repo.update_job_status(job_id, JobStatus.COMPLETED, result.data)
        else:
            await self.job_repo.update_job_status(job_id, JobStatus.FAILED, error=result.error)

        return {
            "job_id": str(job_id),
            "result": result.to_dict() if hasattr(result, 'to_dict') else result.__dict__,
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