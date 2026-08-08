"""API router for Memory & Reflection systems."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.domain.enums.enums import (
    MemoryType, AgentName, FailureCategory, Severity,
    LessonType, PredictionType,
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
    SQLMemoryRepository,
    SQLFailureMemoryRepository,
    SQLSuccessMemoryRepository,
    SQLKnowledgeMemoryRepository,
    SQLBestPracticeRepository,
    SQLReflectionMemoryRepository,
    SQLLessonRepository,
)
from app.infrastructure.database.session import get_db_session

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


router = APIRouter(tags=["Memory & Reflection"])


# Dependency injection
async def get_memory_repo():
    async with get_db_session() as session:
        yield SQLMemoryRepository(session)


async def get_failure_repo():
    async with get_db_session() as session:
        yield SQLFailureMemoryRepository(session)


async def get_success_repo():
    async with get_db_session() as session:
        yield SQLSuccessMemoryRepository(session)


async def get_knowledge_repo():
    async with get_db_session() as session:
        yield SQLKnowledgeMemoryRepository(session)


async def get_practice_repo():
    async with get_db_session() as session:
        yield SQLBestPracticeRepository(session)


async def get_reflection_repo():
    async with get_db_session() as session:
        yield SQLReflectionMemoryRepository(session)


async def get_lesson_repo():
    async with get_db_session() as session:
        yield SQLLessonRepository(session)


# Use case factories
def get_store_memory_use_case(repo=Depends(get_memory_repo)) -> StoreMemoryUseCase:
    return StoreMemoryUseCase(repo)


def get_search_memory_use_case(repo=Depends(get_memory_repo)) -> SearchMemoryUseCase:
    return SearchMemoryUseCase(repo)


def get_recent_memory_use_case(repo=Depends(get_memory_repo)) -> GetRecentMemoryUseCase:
    return GetRecentMemoryUseCase(repo)


def get_cleanup_memory_use_case(repo=Depends(get_memory_repo)) -> CleanupMemoryUseCase:
    return CleanupMemoryUseCase(repo)


def get_record_failure_use_case(repo=Depends(get_failure_repo)) -> RecordFailureUseCase:
    return RecordFailureUseCase(repo)


def get_find_similar_failures_use_case(repo=Depends(get_failure_repo)) -> FindSimilarFailuresUseCase:
    return FindSimilarFailuresUseCase(repo)


def get_failures_by_category_use_case(repo=Depends(get_failure_repo)) -> GetFailuresByCategoryUseCase:
    return GetFailuresByCategoryUseCase(repo)


def get_mark_failure_resolved_use_case(repo=Depends(get_failure_repo)) -> MarkFailureResolvedUseCase:
    return MarkFailureResolvedUseCase(repo)


def get_unresolved_failures_use_case(repo=Depends(get_failure_repo)) -> GetUnresolvedFailuresUseCase:
    return GetUnresolvedFailuresUseCase(repo)


def get_record_success_use_case(repo=Depends(get_success_repo)) -> RecordSuccessUseCase:
    return RecordSuccessUseCase(repo)


def get_find_successful_strategies_use_case(repo=Depends(get_success_repo)) -> FindSuccessfulStrategiesUseCase:
    return FindSuccessfulStrategiesUseCase(repo)


def get_increment_success_reuse_use_case(repo=Depends(get_success_repo)) -> IncrementSuccessReuseUseCase:
    return IncrementSuccessReuseUseCase(repo)


def get_store_knowledge_use_case(repo=Depends(get_knowledge_repo)) -> StoreKnowledgeUseCase:
    return StoreKnowledgeUseCase(repo)


def get_search_knowledge_use_case(repo=Depends(get_knowledge_repo)) -> SearchKnowledgeUseCase:
    return SearchKnowledgeUseCase(repo)


def get_store_best_practice_use_case(repo=Depends(get_practice_repo)) -> StoreBestPracticeUseCase:
    return StoreBestPracticeUseCase(repo)


def get_applicable_practices_use_case(repo=Depends(get_practice_repo)) -> GetApplicablePracticesUseCase:
    return GetApplicablePracticesUseCase(repo)


def get_increment_practice_usage_use_case(repo=Depends(get_practice_repo)) -> IncrementPracticeUsageUseCase:
    return IncrementPracticeUsageUseCase(repo)


def get_record_reflection_use_case(repo=Depends(get_reflection_repo)) -> RecordReflectionUseCase:
    return RecordReflectionUseCase(repo)


def get_reflections_use_case(repo=Depends(get_reflection_repo)) -> GetReflectionsUseCase:
    return GetReflectionsUseCase(repo)


def get_save_lesson_use_case(repo=Depends(get_lesson_repo)) -> SaveLessonUseCase:
    return SaveLessonUseCase(repo)


def get_lessons_use_case(repo=Depends(get_lesson_repo)) -> GetLessonsUseCase:
    return GetLessonsUseCase(repo)


# Request/Response Models
class MemoryStoreRequest(BaseModel):
    memory_type: MemoryType
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    ipo_symbol: Optional[str] = None
    analysis_id: Optional[UUID] = None


class MemoryStoreResponse(BaseModel):
    entry_id: str
    stored: bool


class MemorySearchRequest(BaseModel):
    memory_type: MemoryType
    query_embedding: List[float]
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.75, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None


class MemorySearchResult(BaseModel):
    entry: Dict[str, Any]
    similarity: float


class MemorySearchResponse(BaseModel):
    results: List[MemorySearchResult]


class FailureRecordRequest(BaseModel):
    agent_name: AgentName
    error_type: str
    error_message: str
    stack_trace: str = ""
    root_cause: str = ""
    attempted_fix: str = ""
    category: FailureCategory = FailureCategory.UNKNOWN
    severity: Severity = Severity.MEDIUM
    ipo_symbol: Optional[str] = None
    analysis_id: Optional[UUID] = None


class FailureRecordResponse(BaseModel):
    failure_id: str
    recorded: bool
    existing: bool = False


class FailureSearchRequest(BaseModel):
    error_message: str
    agent_name: AgentName
    threshold: float = Field(0.8, ge=0.0, le=1.0)
    limit: int = Field(5, ge=1, le=20)


class FailureResponse(BaseModel):
    failure_id: str
    agent_name: str
    error_type: str
    error_message: str
    root_cause: str
    attempted_fix: str
    resolved: bool
    resolution: str
    category: str
    severity: str
    occurrences: int
    last_occurrence: datetime
    ipo_symbol: Optional[str] = None


class SuccessRecordRequest(BaseModel):
    agent_name: AgentName
    strategy_description: str
    prompt_used: str = ""
    tool_sequence: List[str] = []
    api_sequence: List[str] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    success_rate: float = Field(1.0, ge=0.0, le=1.0)
    context: Dict[str, Any] = {}
    ipo_symbol: Optional[str] = None
    analysis_id: Optional[UUID] = None


class SuccessRecordResponse(BaseModel):
    success_id: str
    recorded: bool


class SuccessResponse(BaseModel):
    success_id: str
    agent_name: str
    strategy_description: str
    prompt_used: str
    tool_sequence: List[str]
    api_sequence: List[str]
    confidence: float
    success_rate: float
    reuse_count: int
    context: Dict[str, Any] = {}
    ipo_symbol: Optional[str] = None


class SuccessSearchRequest(BaseModel):
    context: Dict[str, Any]
    agent_name: AgentName
    threshold: float = Field(0.75, ge=0.0, le=1.0)
    limit: int = Field(5, ge=1, le=20)


class KnowledgeStoreRequest(BaseModel):
    concept: str = Field(..., min_length=1, max_length=255)
    description: str
    evidence: List[Dict[str, Any]] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    domain: str = ""
    tags: List[str] = []


class KnowledgeResponse(BaseModel):
    concept: str
    description: str
    evidence: List[Dict[str, Any]]
    confidence: float
    domain: str
    tags: List[str]
    version: int


class BestPracticeStoreRequest(BaseModel):
    practice_name: str = Field(..., min_length=1, max_length=255)
    description: str
    applicable_context: Dict[str, Any] = {}
    success_rate: float = Field(0.0, ge=0.0, le=1.0)
    tags: List[str] = []


class BestPracticeResponse(BaseModel):
    practice_id: str
    practice_name: str
    description: str
    applicable_context: Dict[str, Any]
    success_rate: float
    usage_count: int
    tags: List[str]
    version: int


class ReflectionRecordRequest(BaseModel):
    prediction_id: UUID
    ipo_symbol: str
    prediction_type: PredictionType
    predicted_value: float
    actual_value: float
    accuracy: float = Field(..., ge=0.0, le=1.0)
    mistakes_identified: List[str] = []
    correct_assumptions: List[str] = []
    missing_factors: List[str] = []
    lessons_extracted: List[str] = []
    prompt_improvements: List[str] = []
    strategy_changes: List[str] = []
    knowledge_updates: List[str] = []


class ReflectionResponse(BaseModel):
    reflection_id: str
    recorded: bool


class ReflectionItem(BaseModel):
    prediction_id: str
    ipo_symbol: str
    prediction_type: str
    predicted_value: float
    actual_value: float
    accuracy: float
    error: float
    mistakes_identified: List[str]
    correct_assumptions: List[str]
    missing_factors: List[str]
    lessons_extracted: List[str]
    prompt_improvements: List[str]
    strategy_changes: List[str]
    knowledge_updates: List[str]
    processed: bool
    created_at: datetime


class LessonSaveRequest(BaseModel):
    lesson_type: LessonType
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    do: List[str] = []
    dont: List[str] = []
    best_practices: List[str] = []
    anti_patterns: List[str] = []
    known_bugs: List[str] = []
    prompt_improvements: List[str] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evidence: List[Dict[str, Any]] = []
    applicable_agents: List[AgentName] = []
    tags: List[str] = []


class LessonResponse(BaseModel):
    id: str
    lesson_type: str
    title: str
    description: str
    do: List[str]
    dont: List[str]
    best_practices: List[str]
    anti_patterns: List[str]
    known_bugs: List[str]
    prompt_improvements: List[str]
    confidence: float
    evidence: List[Dict[str, Any]]
    applicable_agents: List[str]
    tags: List[str]
    version: int
    created_at: datetime
    updated_at: datetime


class LessonSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(20, ge=1, le=100)


# Endpoints
@router.post("/store", response_model=MemoryStoreResponse, status_code=status.HTTP_201_CREATED)
async def store_memory(
    request: MemoryStoreRequest,
    use_case: StoreMemoryUseCase = Depends(get_store_memory_use_case),
):
    """Store a memory entry."""
    entry_id = await use_case.execute(
        memory_type=request.memory_type,
        content=request.content,
        embedding=request.embedding,
        metadata=request.metadata,
        ipo_symbol=request.ipo_symbol,
        analysis_id=request.analysis_id,
    )
    return MemoryStoreResponse(entry_id=str(entry_id), stored=True)


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(
    request: MemorySearchRequest,
    use_case: SearchMemoryUseCase = Depends(get_search_memory_use_case),
):
    """Search memory by semantic similarity."""
    results = await use_case.execute(
        memory_type=request.memory_type,
        query_embedding=request.query_embedding,
        limit=request.limit,
        threshold=request.threshold,
        filters=request.filters,
    )
    return MemorySearchResponse(
        results=[MemorySearchResult(entry=e[0].__dict__, similarity=e[1]) for e in results]
    )


@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_memory(
    memory_type: MemoryType = Query(...),
    limit: int = Query(100, ge=1, le=1000),
    ipo_symbol: Optional[str] = Query(None),
    use_case: GetRecentMemoryUseCase = Depends(get_recent_memory_use_case),
):
    """Get recent memory entries."""
    entries = await use_case.execute(
        memory_type=memory_type,
        limit=limit,
        ipo_symbol=ipo_symbol,
    )
    return [e.__dict__ for e in entries]


@router.post("/cleanup", response_model=Dict[str, int])
async def cleanup_memory(
    memory_type: MemoryType = Query(...),
    older_than_days: int = Query(365, ge=1),
    use_case: CleanupMemoryUseCase = Depends(get_cleanup_memory_use_case),
):
    """Clean up old memory entries."""
    counts = await use_case.execute(memory_type=memory_type, older_than_days=older_than_days)
    return counts


# Failure Memory Endpoints
@router.post("/failures", response_model=FailureRecordResponse, status_code=status.HTTP_201_CREATED)
async def record_failure(
    request: FailureRecordRequest,
    use_case: RecordFailureUseCase = Depends(get_record_failure_use_case),
):
    """Record a failure."""
    failure = await use_case.execute(
        agent_name=request.agent_name,
        error_type=request.error_type,
        error_message=request.error_message,
        stack_trace=request.stack_trace,
        root_cause=request.root_cause,
        attempted_fix=request.attempted_fix,
        category=request.category,
        severity=request.severity,
        ipo_symbol=request.ipo_symbol,
        analysis_id=request.analysis_id,
    )
    return FailureRecordResponse(
        failure_id=failure.failure_id,
        recorded=True,
        existing=failure.occurrences > 1,
    )


@router.post("/failures/search", response_model=List[FailureResponse])
async def search_failures(
    request: FailureSearchRequest,
    use_case: FindSimilarFailuresUseCase = Depends(get_find_similar_failures_use_case),
):
    """Find similar failures."""
    results = await use_case.execute(
        error_message=request.error_message,
        agent_name=request.agent_name,
        threshold=request.threshold,
        limit=request.limit,
    )
    return [
        FailureResponse(
            failure_id=f[0].failure_id,
            agent_name=f[0].agent_name.value,
            error_type=f[0].error_type,
            error_message=f[0].error_message,
            root_cause=f[0].root_cause,
            attempted_fix=f[0].attempted_fix,
            resolved=f[0].resolved,
            resolution=f[0].resolution,
            category=f[0].category.value,
            severity=f[0].severity.value,
            occurrences=f[0].occurrences,
            last_occurrence=f[0].last_occurrence,
            ipo_symbol=f[0].metadata.get("ipo_symbol") if f[0].metadata else None,
        )
        for f in results
    ]


@router.get("/failures/category/{category}", response_model=List[FailureResponse])
async def get_failures_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=200),
    use_case: GetFailuresByCategoryUseCase = Depends(get_failures_by_category_use_case),
):
    """Get failures by category."""
    failures = await use_case.execute(category=category, limit=limit)
    return [
        FailureResponse(
            failure_id=f.failure_id,
            agent_name=f.agent_name.value,
            error_type=f.error_type,
            error_message=f.error_message,
            root_cause=f.root_cause,
            attempted_fix=f.attempted_fix,
            resolved=f.resolved,
            resolution=f.resolution,
            category=f.category.value,
            severity=f.severity.value,
            occurrences=f.occurrences,
            last_occurrence=f.last_occurrence,
            ipo_symbol=f.metadata.get("ipo_symbol") if f.metadata else None,
        )
        for f in failures
    ]


@router.post("/failures/{failure_id}/resolve", response_model=Dict[str, bool])
async def mark_failure_resolved(
    failure_id: UUID,
    resolution: str,
    use_case: MarkFailureResolvedUseCase = Depends(get_mark_failure_resolved_use_case),
):
    """Mark a failure as resolved."""
    success = await use_case.execute(failure_id=failure_id, resolution=resolution)
    return {"success": success}


@router.get("/failures/unresolved", response_model=List[FailureResponse])
async def get_unresolved_failures(
    agent_name: Optional[AgentName] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    use_case: GetUnresolvedFailuresUseCase = Depends(get_unresolved_failures_use_case),
):
    """Get unresolved failures."""
    failures = await use_case.execute(agent_name=agent_name, limit=limit)
    return [
        FailureResponse(
            failure_id=f.failure_id,
            agent_name=f.agent_name.value,
            error_type=f.error_type,
            error_message=f.error_message,
            root_cause=f.root_cause,
            attempted_fix=f.attempted_fix,
            resolved=f.resolved,
            resolution=f.resolution,
            category=f.category.value,
            severity=f.severity.value,
            occurrences=f.occurrences,
            last_occurrence=f.last_occurrence,
            ipo_symbol=f.metadata.get("ipo_symbol") if f.metadata else None,
        )
        for f in failures
    ]


@router.get("/failures", response_model=List[FailureResponse])
async def list_failures(
    limit: int = Query(100, ge=1, le=500),
    repo: SQLFailureMemoryRepository = Depends(get_failure_repo),
):
    """List all failures (newest first)."""
    failures = await repo.list_all(limit=limit)
    return [
        FailureResponse(
            failure_id=f.failure_id,
            agent_name=f.agent_name.value if hasattr(f.agent_name, "value") else str(f.agent_name),
            error_type=f.error_type,
            error_message=f.error_message,
            root_cause=f.root_cause,
            attempted_fix=f.attempted_fix,
            resolved=f.resolved,
            resolution=f.resolution,
            category=f.category.value if hasattr(f.category, "value") else str(f.category),
            severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            occurrences=f.occurrences,
            last_occurrence=f.last_occurrence,
            ipo_symbol=f.metadata.get("ipo_symbol") if f.metadata else None,
        )
        for f in failures
    ]


# Success Memory Endpoints
@router.post("/successes", response_model=SuccessRecordResponse, status_code=status.HTTP_201_CREATED)
async def record_success(
    request: SuccessRecordRequest,
    use_case: RecordSuccessUseCase = Depends(get_record_success_use_case),
):
    """Record a successful strategy."""
    success = await use_case.execute(
        agent_name=request.agent_name,
        strategy_description=request.strategy_description,
        prompt_used=request.prompt_used,
        tool_sequence=request.tool_sequence,
        api_sequence=request.api_sequence,
        confidence=request.confidence,
        success_rate=request.success_rate,
        context=request.context,
        ipo_symbol=request.ipo_symbol,
        analysis_id=request.analysis_id,
    )
    return SuccessRecordResponse(success_id=success.success_id, recorded=True)


@router.post("/successes/search", response_model=List[Dict[str, Any]])
async def search_successes(
    request: SuccessSearchRequest,
    use_case: FindSuccessfulStrategiesUseCase = Depends(get_find_successful_strategies_use_case),
):
    """Find successful strategies for context."""
    results = await use_case.execute(
        context=request.context,
        agent_name=request.agent_name,
        threshold=request.threshold,
        limit=request.limit,
    )
    return [{"success": r[0].__dict__, "similarity": r[1]} for r in results]


@router.get("/successes", response_model=List[SuccessResponse])
async def list_successes(
    limit: int = Query(100, ge=1, le=500),
    repo: SQLSuccessMemoryRepository = Depends(get_success_repo),
):
    """List all successful strategies (newest first)."""
    successes = await repo.list_all(limit=limit)
    return [
        SuccessResponse(
            success_id=s.success_id,
            agent_name=s.agent_name.value if hasattr(s.agent_name, "value") else str(s.agent_name),
            strategy_description=s.strategy_description,
            prompt_used=s.prompt_used,
            tool_sequence=s.tool_sequence or [],
            api_sequence=s.api_sequence or [],
            confidence=s.confidence,
            success_rate=s.success_rate,
            reuse_count=s.reuse_count,
            context=(s.metadata or {}).get("context", {}) if isinstance((s.metadata or {}).get("context", {}), dict) else {},
            ipo_symbol=(s.metadata or {}).get("ipo_symbol"),
        )
        for s in successes
    ]


@router.post("/successes/{success_id}/reuse", response_model=Dict[str, bool])
async def increment_success_reuse(
    success_id: UUID,
    use_case: IncrementSuccessReuseUseCase = Depends(get_increment_success_reuse_use_case),
):
    """Increment success reuse count."""
    success = await use_case.execute(success_id=success_id)
    return {"success": success}


# Knowledge Memory Endpoints
@router.post("/knowledge", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def store_knowledge(
    request: KnowledgeStoreRequest,
    use_case: StoreKnowledgeUseCase = Depends(get_store_knowledge_use_case),
):
    """Store knowledge."""
    knowledge = await use_case.execute(
        concept=request.concept,
        description=request.description,
        evidence=request.evidence,
        confidence=request.confidence,
        domain=request.domain,
        tags=request.tags,
    )
    return KnowledgeResponse(
        concept=knowledge.concept,
        description=knowledge.description,
        evidence=knowledge.evidence,
        confidence=knowledge.confidence,
        domain=knowledge.domain,
        tags=knowledge.tags,
        version=knowledge.version,
    )


@router.get("/knowledge/concept/{concept}", response_model=Optional[KnowledgeResponse])
async def get_knowledge_by_concept(
    concept: str,
    domain: Optional[str] = Query(None),
    use_case: SearchKnowledgeUseCase = Depends(get_search_knowledge_use_case),
):
    """Get knowledge by concept."""
    knowledge = await use_case.get_by_concept(concept=concept, domain=domain)
    if not knowledge:
        return None
    return KnowledgeResponse(
        concept=knowledge.concept,
        description=knowledge.description,
        evidence=knowledge.evidence,
        confidence=knowledge.confidence,
        domain=knowledge.domain,
        tags=knowledge.tags,
        version=knowledge.version,
    )


@router.post("/knowledge/search", response_model=List[KnowledgeResponse])
async def search_knowledge(
    query_embedding: List[float],
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    use_case: SearchKnowledgeUseCase = Depends(get_search_knowledge_use_case),
):
    """Search knowledge concepts."""
    results = await use_case.search_concepts(query_embedding=query_embedding, limit=limit, threshold=threshold)
    return [
        KnowledgeResponse(
            concept=k[0].concept,
            description=k[0].description,
            evidence=k[0].evidence,
            confidence=k[0].confidence,
            domain=k[0].domain,
            tags=k[0].tags,
            version=k[0].version,
        )
        for k in results
    ]


@router.get("/knowledge/domain/{domain}", response_model=List[KnowledgeResponse])
async def get_knowledge_by_domain(
    domain: str,
    limit: int = Query(50, ge=1, le=200),
    use_case: SearchKnowledgeUseCase = Depends(get_search_knowledge_use_case),
):
    """Get knowledge by domain."""
    knowledge = await use_case.get_by_domain(domain=domain, limit=limit)
    return [
        KnowledgeResponse(
            concept=k.concept,
            description=k.description,
            evidence=k.evidence,
            confidence=k.confidence,
            domain=k.domain,
            tags=k.tags,
            version=k.version,
        )
        for k in knowledge
    ]


@router.get("/knowledge", response_model=List[KnowledgeResponse])
async def list_knowledge(
    limit: int = Query(100, ge=1, le=500),
    repo: SQLKnowledgeMemoryRepository = Depends(get_knowledge_repo),
):
    """List all knowledge concepts (newest first)."""
    knowledge = await repo.list_all(limit=limit)
    return [
        KnowledgeResponse(
            concept=k.concept,
            description=k.description,
            evidence=k.evidence or [],
            confidence=k.confidence,
            domain=k.domain,
            tags=k.tags,
            version=k.version,
        )
        for k in knowledge
    ]


# Best Practice Endpoints
@router.post("/best-practices", response_model=BestPracticeResponse, status_code=status.HTTP_201_CREATED)
async def store_best_practice(
    request: BestPracticeStoreRequest,
    use_case: StoreBestPracticeUseCase = Depends(get_store_best_practice_use_case),
):
    """Store a best practice."""
    practice = await use_case.execute(
        practice_name=request.practice_name,
        description=request.description,
        applicable_context=request.applicable_context,
        success_rate=request.success_rate,
        tags=request.tags,
    )
    return BestPracticeResponse(
        practice_id=str(practice.id),
        practice_name=practice.practice_name,
        description=practice.description,
        applicable_context=practice.applicable_context,
        success_rate=practice.success_rate,
        usage_count=practice.usage_count,
        tags=practice.tags,
        version=practice.version,
    )


@router.post("/best-practices/applicable", response_model=List[BestPracticeResponse])
async def get_applicable_practices(
    context: Dict[str, Any],
    limit: int = Query(10, ge=1, le=50),
    use_case: GetApplicablePracticesUseCase = Depends(get_applicable_practices_use_case),
):
    """Get best practices applicable to context."""
    practices = await use_case.execute(context=context, limit=limit)
    return [
        BestPracticeResponse(
            practice_id=str(p.id),
            practice_name=p.practice_name,
            description=p.description,
            applicable_context=p.applicable_context,
            success_rate=p.success_rate,
            usage_count=p.usage_count,
            tags=p.tags,
            version=p.version,
        )
        for p in practices
    ]


@router.get("/best-practices", response_model=List[BestPracticeResponse])
async def list_best_practices(
    limit: int = Query(100, ge=1, le=500),
    repo: SQLBestPracticeRepository = Depends(get_practice_repo),
):
    """List all best practices (newest first)."""
    practices = await repo.list_all(limit=limit)
    return [
        BestPracticeResponse(
            practice_id=str(p.id),
            practice_name=p.practice_name,
            description=p.description,
            applicable_context=p.applicable_context or {},
            success_rate=p.success_rate,
            usage_count=p.usage_count,
            tags=p.tags,
            version=p.version,
        )
        for p in practices
    ]


@router.post("/best-practices/{practice_id}/use", response_model=Dict[str, bool])
async def increment_practice_usage(
    practice_id: UUID,
    use_case: IncrementPracticeUsageUseCase = Depends(get_increment_practice_usage_use_case),
):
    """Increment best practice usage count."""
    success = await use_case.execute(practice_id=practice_id)
    return {"success": success}


# Reflection Endpoints
@router.post("/reflections", response_model=ReflectionResponse, status_code=status.HTTP_201_CREATED)
async def record_reflection(
    request: ReflectionRecordRequest,
    use_case: RecordReflectionUseCase = Depends(get_record_reflection_use_case),
):
    """Record a reflection after outcome verification."""
    reflection = await use_case.execute(
        prediction_id=request.prediction_id,
        ipo_symbol=request.ipo_symbol,
        prediction_type=request.prediction_type,
        predicted_value=request.predicted_value,
        actual_value=request.actual_value,
        accuracy=request.accuracy,
        mistakes_identified=request.mistakes_identified,
        correct_assumptions=request.correct_assumptions,
        missing_factors=request.missing_factors,
        lessons_extracted=request.lessons_extracted,
        prompt_improvements=request.prompt_improvements,
        strategy_changes=request.strategy_changes,
        knowledge_updates=request.knowledge_updates,
    )
    return ReflectionResponse(reflection_id=str(reflection.id), recorded=True)


@router.get("/reflections/prediction/{prediction_id}", response_model=Optional[ReflectionItem])
async def get_reflection_by_prediction(
    prediction_id: UUID,
    use_case: GetReflectionsUseCase = Depends(get_reflections_use_case),
):
    """Get reflection by prediction ID."""
    reflection = await use_case.get_by_prediction(prediction_id=prediction_id)
    if not reflection:
        return None
    return ReflectionItem(
        prediction_id=str(reflection.prediction_id),
        ipo_symbol=reflection.ipo_symbol,
        prediction_type=reflection.prediction_type.value,
        predicted_value=reflection.predicted_value,
        actual_value=reflection.actual_value,
        accuracy=reflection.accuracy,
        error=reflection.error,
        mistakes_identified=reflection.mistakes_identified,
        correct_assumptions=reflection.correct_assumptions,
        missing_factors=reflection.missing_factors,
        lessons_extracted=reflection.lessons_extracted,
        prompt_improvements=reflection.prompt_improvements,
        strategy_changes=reflection.strategy_changes,
        knowledge_updates=reflection.knowledge_updates,
        processed=reflection.processed,
        created_at=reflection.created_at,
    )


@router.get("/reflections/ipo/{ipo_symbol}", response_model=List[ReflectionItem])
async def get_reflections_by_ipo(
    ipo_symbol: str,
    limit: int = Query(20, ge=1, le=100),
    use_case: GetReflectionsUseCase = Depends(get_reflections_use_case),
):
    """Get reflections for an IPO."""
    reflections = await use_case.get_by_ipo(ipo_symbol=ipo_symbol.upper(), limit=limit)
    return [
        ReflectionItem(
            prediction_id=str(r.prediction_id),
            ipo_symbol=r.ipo_symbol,
            prediction_type=r.prediction_type.value,
            predicted_value=r.predicted_value,
            actual_value=r.actual_value,
            accuracy=r.accuracy,
            error=r.error,
            mistakes_identified=r.mistakes_identified,
            correct_assumptions=r.correct_assumptions,
            missing_factors=r.missing_factors,
            lessons_extracted=r.lessons_extracted,
            prompt_improvements=r.prompt_improvements,
            strategy_changes=r.strategy_changes,
            knowledge_updates=r.knowledge_updates,
            processed=r.processed,
            created_at=r.created_at,
        )
        for r in reflections
    ]


@router.get("/reflections/unprocessed", response_model=List[ReflectionItem])
async def get_unprocessed_reflections(
    limit: int = Query(50, ge=1, le=200),
    use_case: GetReflectionsUseCase = Depends(get_reflections_use_case),
):
    """Get unprocessed reflections."""
    reflections = await use_case.get_unprocessed(limit=limit)
    return [
        ReflectionItem(
            prediction_id=str(r.prediction_id),
            ipo_symbol=r.ipo_symbol,
            prediction_type=r.prediction_type.value,
            predicted_value=r.predicted_value,
            actual_value=r.actual_value,
            accuracy=r.accuracy,
            error=r.error,
            mistakes_identified=r.mistakes_identified,
            correct_assumptions=r.correct_assumptions,
            missing_factors=r.missing_factors,
            lessons_extracted=r.lessons_extracted,
            prompt_improvements=r.prompt_improvements,
            strategy_changes=r.strategy_changes,
            knowledge_updates=r.knowledge_updates,
            processed=r.processed,
            created_at=r.created_at,
        )
        for r in reflections
    ]


@router.get("/reflections", response_model=List[ReflectionItem])
async def list_reflections(
    limit: int = Query(100, ge=1, le=500),
    repo: SQLReflectionMemoryRepository = Depends(get_reflection_repo),
):
    """List all reflections (newest first)."""
    reflections = await repo.list_all(limit=limit)
    return [
        ReflectionItem(
            prediction_id=str(r.prediction_id),
            ipo_symbol=r.ipo_symbol,
            prediction_type=r.prediction_type.value if hasattr(r.prediction_type, "value") else str(r.prediction_type),
            predicted_value=r.predicted_value,
            actual_value=r.actual_value,
            accuracy=r.accuracy,
            error=r.error,
            mistakes_identified=r.mistakes_identified,
            correct_assumptions=r.correct_assumptions,
            missing_factors=r.missing_factors,
            lessons_extracted=r.lessons_extracted,
            prompt_improvements=r.prompt_improvements,
            strategy_changes=r.strategy_changes,
            knowledge_updates=r.knowledge_updates,
            processed=r.processed,
            created_at=r.created_at,
        )
        for r in reflections
    ]


# Lesson Endpoints
@router.post("/lessons", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def save_lesson(
    request: LessonSaveRequest,
    use_case: SaveLessonUseCase = Depends(get_save_lesson_use_case),
):
    """Save a lesson."""
    lesson_id = await use_case.execute(
        lesson_type=request.lesson_type,
        title=request.title,
        description=request.description,
        do=request.do,
        dont=request.dont,
        best_practices=request.best_practices,
        anti_patterns=request.anti_patterns,
        known_bugs=request.known_bugs,
        prompt_improvements=request.prompt_improvements,
        confidence=request.confidence,
        evidence=request.evidence,
        applicable_agents=request.applicable_agents,
        tags=request.tags,
    )
    return {"lesson_id": str(lesson_id)}


@router.get("/lessons", response_model=List[LessonResponse])
async def list_lessons(
    limit: int = Query(100, ge=1, le=500),
    repo: SQLLessonRepository = Depends(get_lesson_repo),
):
    """List all lessons (newest first)."""
    lessons = await repo.list_all(limit=limit)
    return [
        LessonResponse(
            id=str(l.id),
            lesson_type=l.lesson_type.value if hasattr(l.lesson_type, "value") else str(l.lesson_type),
            title=l.title,
            description=l.description,
            do=l.do,
            dont=l.dont,
            best_practices=l.best_practices,
            anti_patterns=l.anti_patterns,
            known_bugs=l.known_bugs,
            prompt_improvements=l.prompt_improvements,
            confidence=l.confidence,
            evidence=l.evidence,
            applicable_agents=[a.value for a in l.applicable_agents],
            tags=l.tags,
            version=l.version,
            created_at=l.created_at,
            updated_at=l.updated_at,
        )
        for l in lessons
    ]


@router.get("/lessons/{lesson_id}", response_model=Optional[LessonResponse])
async def get_lesson(
    lesson_id: UUID,
    use_case: GetLessonsUseCase = Depends(get_lessons_use_case),
):
    """Get lesson by ID."""
    lesson = await use_case.get_by_id(lesson_id)
    if not lesson:
        return None
    return LessonResponse(
        id=str(lesson.id),
        lesson_type=lesson.lesson_type.value,
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
        applicable_agents=[a.value for a in lesson.applicable_agents],
        tags=lesson.tags,
        version=lesson.version,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@router.get("/lessons/type/{lesson_type}", response_model=List[LessonResponse])
async def get_lessons_by_type(
    lesson_type: LessonType,
    limit: int = Query(50, ge=1, le=200),
    use_case: GetLessonsUseCase = Depends(get_lessons_use_case),
):
    """Get lessons by type."""
    lessons = await use_case.get_by_type(lesson_type=lesson_type, limit=limit)
    return [
        LessonResponse(
            id=str(l.id),
            lesson_type=l.lesson_type.value,
            title=l.title,
            description=l.description,
            do=l.do,
            dont=l.dont,
            best_practices=l.best_practices,
            anti_patterns=l.anti_patterns,
            known_bugs=l.known_bugs,
            prompt_improvements=l.prompt_improvements,
            confidence=l.confidence,
            evidence=l.evidence,
            applicable_agents=[a.value for a in l.applicable_agents],
            tags=l.tags,
            version=l.version,
            created_at=l.created_at,
            updated_at=l.updated_at,
        )
        for l in lessons
    ]


@router.post("/lessons/applicable", response_model=List[LessonResponse])
async def get_applicable_lessons(
    agent_name: AgentName,
    context: Dict[str, Any],
    limit: int = Query(10, ge=1, le=50),
    use_case: GetLessonsUseCase = Depends(get_lessons_use_case),
):
    """Get applicable lessons for agent and context."""
    lessons = await use_case.get_applicable(agent_name=agent_name, context=context, limit=limit)
    return [
        LessonResponse(
            id=str(l.id),
            lesson_type=l.lesson_type.value,
            title=l.title,
            description=l.description,
            do=l.do,
            dont=l.dont,
            best_practices=l.best_practices,
            anti_patterns=l.anti_patterns,
            known_bugs=l.known_bugs,
            prompt_improvements=l.prompt_improvements,
            confidence=l.confidence,
            evidence=l.evidence,
            applicable_agents=[a.value for a in l.applicable_agents],
            tags=l.tags,
            version=l.version,
            created_at=l.created_at,
            updated_at=l.updated_at,
        )
        for l in lessons
    ]


@router.post("/lessons/search", response_model=List[LessonResponse])
async def search_lessons(
    request: LessonSearchRequest,
    use_case: GetLessonsUseCase = Depends(get_lessons_use_case),
):
    """Search lessons by text."""
    lessons = await use_case.search(query=request.query, limit=request.limit)
    return [
        LessonResponse(
            id=str(l.id),
            lesson_type=l.lesson_type.value,
            title=l.title,
            description=l.description,
            do=l.do,
            dont=l.dont,
            best_practices=l.best_practices,
            anti_patterns=l.anti_patterns,
            known_bugs=l.known_bugs,
            prompt_improvements=l.prompt_improvements,
            confidence=l.confidence,
            evidence=l.evidence,
            applicable_agents=[a.value for a in l.applicable_agents],
            tags=l.tags,
            version=l.version,
            created_at=l.created_at,
            updated_at=l.updated_at,
        )
        for l in lessons
    ]