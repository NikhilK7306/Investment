"""API router for IPO Analysis."""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.domain.enums.enums import (
    Exchange, Sector, Industry, IPOStatus,
    AnalysisStatus, InvestmentStrategy, RiskLevel,
    TimeHorizon, SentimentLabel, AgentName,
    JobType, JobStatus, MemoryType, FailureCategory,
    Severity, LessonType, PredictionType,
)
from app.application.use_cases.ipo_use_cases import (
    DiscoverIPOsUseCase,
    GetIPODetailsUseCase,
    GetUpcomingIPOsUseCase as ListUpcomingIPOsUseCase,
    SearchIPOsUseCase,
    GetRecentIPOsUseCase as GetRecentlyListedIPOsUseCase,
    CreateIPOUseCase,
    UpdateIPOStatusUseCase,
    GetCompanyProfileUseCase,
    CreateCompanyProfileUseCase,
    ListCompaniesBySectorUseCase,
    ListCompaniesByIndustryUseCase,
    CollectIPODataUseCase,
    GenerateReportUseCase,
    RunReflectionUseCase,
    VerifyOutcomesUseCase,
    GetJobStatusUseCase,
    GetPendingJobsUseCase,
    GetJobStatsUseCase,
)
from app.application.use_cases.analysis_use_cases import (
    AnalyzeIPOUseCase,
    GetAnalysisUseCase,
)
from app.application.use_cases.memory_use_cases import (
    StoreMemoryUseCase,
    SearchMemoryUseCase,
    GetRecentMemoryUseCase,
    CleanupMemoryUseCase,
    RecordFailureUseCase,
    FindSimilarFailuresUseCase,
    GetFailuresByCategoryUseCase,
    MarkFailureResolvedUseCase,
    GetUnresolvedFailuresUseCase,
    RecordSuccessUseCase,
    FindSuccessfulStrategiesUseCase,
    IncrementSuccessReuseUseCase,
    StoreKnowledgeUseCase,
    SearchKnowledgeUseCase,
    StoreBestPracticeUseCase,
    GetApplicablePracticesUseCase,
    IncrementPracticeUsageUseCase,
    RecordReflectionUseCase,
    GetReflectionsUseCase,
    SaveLessonUseCase,
    GetLessonsUseCase,
)
from app.infrastructure.repositories.sql_repositories import (
    SQLIPORepository,
    SQLCompanyRepository,
    SQLAnalysisRepository,
    SQLFinancialRepository,
    SQLPredictionRepository,
    SQLReportRepository,
    SQLMemoryRepository,
    SQLFailureMemoryRepository,
    SQLSuccessMemoryRepository,
    SQLKnowledgeMemoryRepository,
    SQLBestPracticeRepository,
    SQLReflectionMemoryRepository,
    SQLLessonRepository,
    SQLJobRepository,
    SQLUserRepository,
    SQLAPIKeyRepository,
)
from app.infrastructure.database.session import get_db_session

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


router = APIRouter(tags=["Analysis"])


# Dependency injection
async def get_ipo_repo():
    async with get_db_session() as session:
        yield SQLIPORepository(session)


async def get_company_repo():
    async with get_db_session() as session:
        yield SQLCompanyRepository(session)


async def get_analysis_repo():
    async with get_db_session() as session:
        yield SQLAnalysisRepository(session)


async def get_financial_repo():
    async with get_db_session() as session:
        yield SQLFinancialRepository(session)


async def get_prediction_repo():
    async with get_db_session() as session:
        yield SQLPredictionRepository(session)


async def get_report_repo():
    async with get_db_session() as session:
        yield SQLReportRepository(session)


async def get_job_repo():
    async with get_db_session() as session:
        yield SQLJobRepository(session)


# Use case factories
def get_analyze_use_case(
    ipo_repo=Depends(get_ipo_repo),
    company_repo=Depends(get_company_repo),
    financial_repo=Depends(get_financial_repo),
    analysis_repo=Depends(get_analysis_repo),
) -> AnalyzeIPOUseCase:
    return AnalyzeIPOUseCase(ipo_repo, company_repo, financial_repo, analysis_repo)


def get_get_analysis_use_case(analysis_repo=Depends(get_analysis_repo)) -> GetAnalysisUseCase:
    return GetAnalysisUseCase(analysis_repo)


def get_collect_use_case(job_repo=Depends(get_job_repo)) -> CollectIPODataUseCase:
    return CollectIPODataUseCase(job_repo)


def get_report_use_case(
    job_repo=Depends(get_job_repo),
    report_repo=Depends(get_report_repo),
    analysis_repo=Depends(get_analysis_repo),
    ipo_repo=Depends(get_ipo_repo),
    company_repo=Depends(get_company_repo),
    financial_repo=Depends(get_financial_repo),
) -> GenerateReportUseCase:
    return GenerateReportUseCase(
        job_repo=job_repo,
        report_repo=report_repo,
        analysis_repo=analysis_repo,
        ipo_repo=ipo_repo,
        company_repo=company_repo,
        financial_repo=financial_repo,
    )


def get_reflection_use_case(job_repo=Depends(get_job_repo)) -> RunReflectionUseCase:
    return RunReflectionUseCase(job_repo)


def get_verify_use_case(job_repo=Depends(get_job_repo)) -> VerifyOutcomesUseCase:
    return VerifyOutcomesUseCase(job_repo)


def get_job_status_use_case(job_repo=Depends(get_job_repo)) -> GetJobStatusUseCase:
    return GetJobStatusUseCase(job_repo)


def get_pending_jobs_use_case(job_repo=Depends(get_job_repo)) -> GetPendingJobsUseCase:
    return GetPendingJobsUseCase(job_repo)


def get_job_stats_use_case(job_repo=Depends(get_job_repo)) -> GetJobStatsUseCase:
    return GetJobStatsUseCase(job_repo)


# Request/Response Models
class AnalysisRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30, pattern="^[A-Z0-9.]+$")
    depth: str = Field("standard", pattern="^(standard|deep|comprehensive)$")
    user_id: Optional[str] = None


class DataCollectionRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    ipo_details: Dict[str, Any] = {}


class ReportRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=30)
    analysis_results: Optional[Dict[str, Any]] = None


class ReflectionRequest(BaseModel):
    min_delay_days: int = Field(30, ge=1, le=365)
    batch_size: int = Field(50, ge=1, le=200)


class OutcomeVerificationRequest(BaseModel):
    prediction_id: UUID
    actual_value: float


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    priority: int
    payload: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None


class JobStatsResponse(BaseModel):
    by_type: Dict[str, Dict[str, int]]
    total_pending: int
    total_running: int
    total_completed: int
    total_failed: int


class AnalysisResponse(BaseModel):
    job_id: str
    symbol: str
    status: str
    overall_score: Optional[float] = None
    confidence: Optional[float] = None
    recommendation: Optional[str] = None
    risk_level: Optional[str] = None
    time_horizon: Optional[str] = None
    bull_case: Optional[str] = None
    bear_case: Optional[str] = None
    key_risks: List[str] = []
    key_catalysts: List[str] = []
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_drivers: List[str] = []
    score_breakdown: Dict[str, float] = {}
    agent_results: Any = {}
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


def _analysis_to_response(result, symbol: str) -> AnalysisResponse:
    """Build API response from either an OverallAnalysis entity or stored dict."""
    expr = lambda key, default=None: (
        result.get(key, default) if isinstance(result, dict) else getattr(result, key, default)
    )

    def enum_str(value):
        return value.value if hasattr(value, "value") else (value or None)

    agent_results = expr("agent_results", {})
    if hasattr(agent_results, "__dataclass_fields__"):
        from dataclasses import asdict
        agent_results = asdict(agent_results)

    return AnalysisResponse(
        job_id=str(expr("id") or expr("analysis_id")),
        symbol=symbol,
        status=enum_str(expr("status")) or "unknown",
        overall_score=expr("overall_score"),
        confidence=expr("confidence"),
        recommendation=enum_str(expr("investment_strategy")),
        risk_level=enum_str(expr("risk_level")),
        time_horizon=enum_str(expr("time_horizon")),
        bull_case=expr("bull_case"),
        bear_case=expr("bear_case"),
        key_risks=expr("key_risks", []) or [],
        key_catalysts=expr("key_catalysts", []) or [],
        sentiment=enum_str(expr("sentiment")),
        sentiment_score=expr("sentiment_score"),
        sentiment_drivers=expr("sentiment_drivers", []) or [],
        score_breakdown=expr("score_breakdown", {}) or {},
        agent_results=agent_results,
        completed_at=expr("completed_at"),
        error=expr("error"),
    )


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_ipo(
    request: AnalysisRequest,
    use_case: AnalyzeIPOUseCase = Depends(get_analyze_use_case),
):
    """Start full IPO analysis pipeline."""
    result = await use_case.execute(
        symbol=request.symbol.upper(),
        depth=request.depth,
        user_id=request.user_id,
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return _analysis_to_response(result, request.symbol.upper())


@router.post("/collect", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def collect_data(
    request: DataCollectionRequest,
    use_case: CollectIPODataUseCase = Depends(get_collect_use_case),
):
    """Collect comprehensive data for IPO."""
    result = await use_case.execute(
        symbol=request.symbol.upper(),
        ipo_details=request.ipo_details,
    )

    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return AnalysisResponse(
        job_id=result["job_id"],
        symbol=request.symbol.upper(),
        status="pending",
    )


@router.post("/report", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    request: ReportRequest,
    use_case: GenerateReportUseCase = Depends(get_report_use_case),
):
    """Generate investment research report."""
    result = await use_case.execute(
        symbol=request.symbol.upper(),
        analysis_results=request.analysis_results,
    )

    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return AnalysisResponse(
        job_id=str(result["job_id"]),
        symbol=request.symbol.upper(),
        status="completed" if result.get("status") == "completed" else "pending",
        agent_results={"report": result.get("report", {}), "report_id": result.get("report_id")},
    )


@router.get("/reports", response_model=List[AnalysisResponse])
async def list_reports(
    limit: int = Query(50, ge=1, le=200),
    report_repo: SQLReportRepository = Depends(get_report_repo),
):
    """List recent reports across symbols."""
    reports = await report_repo.list_reports(limit=limit)
    return [
        AnalysisResponse(
            job_id=report.get("analysis_id", ""),
            symbol=report.get("symbol", ""),
            status="completed",
            overall_score=report.get("key_metrics", {}).get("overall_score"),
            recommendation=str(report.get("key_metrics", {}).get("recommendation", "")) or None,
            agent_results={"report": report},
        )
        for report in reports
    ]


@router.get("/report/{symbol}", response_model=AnalysisResponse)
async def get_latest_report(
    symbol: str,
    report_repo: SQLReportRepository = Depends(get_report_repo),
):
    """Get latest generated report for symbol."""
    report = await report_repo.get_latest_report(symbol.upper())
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {symbol}",
        )
    return AnalysisResponse(
        job_id=report.get("analysis_id", ""),
        symbol=symbol.upper(),
        status="completed",
        overall_score=report.get("key_metrics", {}).get("overall_score"),
        recommendation=str(report.get("key_metrics", {}).get("recommendation", "")) or None,
        agent_results={"report": report},
    )


@router.post("/reflection", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_reflection(
    request: ReflectionRequest,
    use_case: RunReflectionUseCase = Depends(get_reflection_use_case),
):
    """Run reflection cycle on past predictions."""
    result = await use_case.execute(
        min_delay_days=request.min_delay_days,
        batch_size=request.batch_size,
    )

    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return AnalysisResponse(
        job_id=result["job_id"],
        symbol="",
        status="pending",
    )


@router.post("/verify-outcome", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def verify_outcome(
    request: OutcomeVerificationRequest,
    use_case: VerifyOutcomesUseCase = Depends(get_verify_use_case),
):
    """Verify a prediction outcome."""
    result = await use_case.execute(
        prediction_id=request.prediction_id,
        actual_value=request.actual_value,
    )

    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return AnalysisResponse(
        job_id=result["job_id"],
        symbol="",
        status="pending",
    )


@router.get("/jobs", response_model=List[JobResponse])
async def get_pending_jobs(
    job_type: Optional[JobType] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    use_case: GetPendingJobsUseCase = Depends(get_pending_jobs_use_case),
):
    """Get pending jobs."""
    jobs = await use_case.execute(job_type=job_type, limit=limit)
    return [JobResponse(**job) for job in jobs]


@router.get("/jobs/stats", response_model=JobStatsResponse)
async def get_job_stats(
    use_case: GetJobStatsUseCase = Depends(get_job_stats_use_case),
):
    """Get job statistics."""
    stats = await use_case.execute()
    return JobStatsResponse(
        by_type=stats,
        total_pending=sum(v.get("queued", 0) + v.get("scheduled", 0) for v in stats.values()),
        total_running=sum(v.get("running", 0) for v in stats.values()),
        total_completed=sum(v.get("completed", 0) for v in stats.values()),
        total_failed=sum(v.get("failed", 0) for v in stats.values()),
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: UUID,
    use_case: GetJobStatusUseCase = Depends(get_job_status_use_case),
):
    """Get job status."""
    job = await use_case.execute(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**job)


@router.get("/results/{symbol}", response_model=AnalysisResponse)
async def get_analysis_result(
    symbol: str,
    use_case: GetAnalysisUseCase = Depends(get_get_analysis_use_case),
):
    """Get latest analysis result for symbol."""
    analysis = await use_case.get_latest(symbol.upper())
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis not found: {symbol}")

    return _analysis_to_response(analysis, symbol.upper())

    return AnalysisResponse(
        job_id=analysis.get("id", ""),
        symbol=symbol.upper(),
        status=analysis.get("status", "unknown"),
        overall_score=analysis.get("overall_score"),
        confidence=analysis.get("confidence"),
        recommendation=analysis.get("investment_strategy"),
        risk_level=analysis.get("risk_level"),
        time_horizon=analysis.get("time_horizon"),
        bull_case=analysis.get("bull_case"),
        bear_case=analysis.get("bear_case"),
        key_risks=analysis.get("key_risks", []),
        key_catalysts=analysis.get("key_catalysts", []),
        agent_results=analysis.get("agent_results", {}),
        completed_at=analysis.get("completed_at"),
    )


@router.get("/history/{symbol}", response_model=List[AnalysisResponse])
async def get_analysis_history(
    symbol: str,
    limit: int = Query(10, ge=1, le=50),
    use_case: GetAnalysisUseCase = Depends(get_get_analysis_use_case),
):
    """Get analysis history for symbol."""
    history = await use_case.get_history(symbol.upper(), limit=limit)
    return [_analysis_to_response(h, symbol.upper()) for h in history]