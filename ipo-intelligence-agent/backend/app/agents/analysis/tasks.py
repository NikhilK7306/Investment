"""Celery tasks for IPO analysis pipeline."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from celery import shared_task
from celery.utils.log import get_task_logger

from app.core.config.settings import get_settings
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.sql_repositories import (
    SQLAnalysisRepository,
    SQLIPORepository,
    SQLCompanyRepository,
    SQLFinancialRepository,
    SQLJobRepository,
)
from app.application.use_cases.analysis_use_cases import AnalyzeIPOUseCase
from app.application.use_cases.ipo_use_cases import (
    DiscoverIPOsUseCase,
    GenerateReportUseCase,
    CollectIPODataUseCase,
)
from app.agents.discovery.agent import DiscoveryAgent
from app.agents.collection.agent import CollectionAgent
from app.agents.report.agent import ReportGenerationAgent

logger = get_task_logger(__name__)

settings = get_settings()


def run_async(coro):
    """Run async function in Celery task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def discover_ipos_task(
    self,
    lookahead_days: int = 90,
    sources: Optional[List[str]] = None,
    min_market_cap: float = 0,
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task for IPO discovery."""
    logger.info(f"Starting IPO discovery task: lookahead={lookahead_days}, sources={sources}")
    
    async def _discover():
        sources = sources or ["nasdaq", "nyse", "sec", "renaissance", "investorgain"]
        async with get_db_session() as session:
            ipo_repo = SQLIPORepository(session)
            company_repo = SQLCompanyRepository(session)
            use_case = DiscoverIPOsUseCase(ipo_repo, company_repo)
            return await use_case.execute(
                sources=sources,
                lookahead_days=lookahead_days,
                min_market_cap=min_market_cap,
            )
    
    try:
        result = run_async(_discover())
        discovered_count = len(result)
        logger.info(f"IPO discovery completed: {discovered_count} IPOs found")
        return {
            "status": "completed",
            "discovered_count": discovered_count,
            "sources_used": sources,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception(f"IPO discovery failed: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def analyze_ipo_task(
    self,
    symbol: str,
    depth: str = "standard",
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task for full IPO analysis pipeline."""
    logger.info(f"Starting analysis task for {symbol} (depth={depth})")
    
    async def _analyze():
        async with get_db_session() as session:
            ipo_repo = SQLIPORepository(session)
            company_repo = SQLCompanyRepository(session)
            financial_repo = SQLFinancialRepository(session)
            analysis_repo = SQLAnalysisRepository(session)
            use_case = AnalyzeIPOUseCase(ipo_repo, company_repo, financial_repo, analysis_repo)
            return await use_case.execute(
                symbol=symbol.upper(),
                depth=depth,
                user_id=user_id,
            )
    
    try:
        result = run_async(_analyze())
        
        # Update job status if job_id provided
        if job_id:
            async def _update_job():
                async with get_db_session() as session:
                    job_repo = SQLJobRepository(session)
                    await job_repo.update_job_status(
                        job_id=UUID(job_id),
                        status="completed",
                        result={
                            "symbol": symbol,
                            "overall_score": result.overall_score,
                            "recommendation": result.investment_strategy.value,
                            "completed_at": datetime.utcnow().isoformat(),
                        },
                    )
            run_async(_update_job())
        
        logger.info(f"Analysis completed for {symbol}: score={result.overall_score}, rec={result.investment_strategy.value}")
        return {
            "status": "completed",
            "symbol": symbol,
            "overall_score": result.overall_score,
            "confidence": result.confidence,
            "recommendation": result.investment_strategy.value,
            "risk_level": result.risk_level.value,
            "time_horizon": result.time_horizon.value,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.exception(f"Analysis failed for {symbol}: {e}")
        if job_id:
            async def _update_job_failed():
                async with get_db_session() as session:
                    job_repo = SQLJobRepository(session)
                    await job_repo.update_job_status(
                        job_id=UUID(job_id),
                        status="failed",
                        error=str(e),
                    )
            run_async(_update_job_failed())
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def collect_ipo_data_task(
    self,
    symbol: str,
    ipo_details: Dict[str, Any],
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task for collecting IPO data."""
    logger.info(f"Starting data collection for {symbol}")
    
    async def _collect():
        async with get_db_session() as session:
            job_repo = SQLJobRepository(session)
            use_case = CollectIPODataUseCase(job_repo)
            return await use_case.execute(
                symbol=symbol.upper(),
                ipo_details=ipo_details,
            )
    
    try:
        result = run_async(_collect())
        logger.info(f"Data collection completed for {symbol}")
        return {
            "status": "completed",
            "symbol": symbol,
            "job_id": result.get("job_id"),
            "data_quality": result.get("result", {}).get("data", {}).get("data_quality_score", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception(f"Data collection failed for {symbol}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_report_task(
    self,
    symbol: str,
    analysis_results: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task for generating investment report."""
    logger.info(f"Starting report generation for {symbol}")
    
    async def _generate():
        async with get_db_session() as session:
            job_repo = SQLJobRepository(session)
            from app.infrastructure.repositories.sql_repositories import SQLReportRepository, SQLAnalysisRepository, SQLFinancialRepository
            report_repo = SQLReportRepository(session)
            analysis_repo = SQLAnalysisRepository(session)
            ipo_repo = SQLIPORepository(session)
            company_repo = SQLCompanyRepository(session)
            financial_repo = SQLFinancialRepository(session)
            
            use_case = GenerateReportUseCase(
                job_repo=job_repo,
                report_repo=report_repo,
                analysis_repo=analysis_repo,
                ipo_repo=ipo_repo,
                company_repo=company_repo,
                financial_repo=financial_repo,
            )
            return await use_case.execute(
                symbol=symbol.upper(),
                analysis_results=analysis_results,
            )
    
    try:
        result = run_async(_generate())
        logger.info(f"Report generation completed for {symbol}")
        return {
            "status": "completed",
            "symbol": symbol,
            "report_id": result.get("report_id"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception(f"Report generation failed for {symbol}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=1)
def run_reflection_task(
    self,
    min_delay_days: int = 30,
    batch_size: int = 50,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task for running reflection cycle."""
    logger.info(f"Starting reflection cycle (min_delay={min_delay_days}, batch={batch_size})")
    
    async def _reflect():
        async with get_db_session() as session:
            job_repo = SQLJobRepository(session)
            from app.application.use_cases.ipo_use_cases import RunReflectionUseCase
            use_case = RunReflectionUseCase(job_repo)
            return await use_case.execute(
                min_delay_days=min_delay_days,
                batch_size=batch_size,
            )
    
    try:
        result = run_async(_reflect())
        logger.info(f"Reflection cycle completed")
        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result.get("result", {}),
        }
    except Exception as e:
        logger.exception(f"Reflection cycle failed: {e}")
        raise self.retry(exc=e)


@shared_task
def verify_outcome_task(
    prediction_id: str,
    actual_value: float,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task for verifying prediction outcome."""
    logger.info(f"Verifying outcome for prediction {prediction_id}")
    
    async def _verify():
        async with get_db_session() as session:
            job_repo = SQLJobRepository(session)
            from app.application.use_cases.ipo_use_cases import VerifyOutcomesUseCase
            use_case = VerifyOutcomesUseCase(job_repo)
            return await use_case.execute(
                prediction_id=UUID(prediction_id),
                actual_value=actual_value,
            )
    
    try:
        result = run_async(_verify())
        logger.info(f"Outcome verification completed for {prediction_id}")
        return {
            "status": "completed",
            "prediction_id": prediction_id,
            "actual_value": actual_value,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception(f"Outcome verification failed for {prediction_id}: {e}")
        raise


# Periodic tasks for Celery Beat
@shared_task
def scheduled_ipo_discovery() -> Dict[str, Any]:
    """Scheduled task for daily IPO discovery."""
    logger.info("Running scheduled IPO discovery")
    return discover_ipos_task.delay(
        lookahead_days=90,
        sources=["nasdaq", "nyse", "sec", "renaissance", "investorgain"],
    )


@shared_task
def scheduled_ipo_discovery_india() -> Dict[str, Any]:
    """Scheduled task for daily Indian IPO discovery."""
    logger.info("Running scheduled Indian IPO discovery")
    return discover_ipos_task.delay(
        lookahead_days=90,
        sources=["investorgain", "nse_india", "bse_india", "sebi"],
        region="india",
    )


@shared_task
def scheduled_reflection() -> Dict[str, Any]:
    """Scheduled task for daily reflection cycle."""
    logger.info("Running scheduled reflection cycle")
    return run_reflection_task.delay(min_delay_days=30, batch_size=50)


@shared_task
def scheduled_data_refresh() -> Dict[str, Any]:
    """Scheduled task for refreshing data on active IPOs."""
    logger.info("Running scheduled data refresh")
    # This would query active IPOs and refresh their data
    # Implementation depends on business logic
    return {"status": "completed", "message": "Data refresh scheduled"}


@shared_task
def cleanup_old_jobs() -> Dict[str, Any]:
    """Scheduled task for cleaning up old completed/failed jobs."""
    logger.info("Running job cleanup")
    # Implementation would clean up old jobs from database
    return {"status": "completed", "message": "Job cleanup scheduled"}