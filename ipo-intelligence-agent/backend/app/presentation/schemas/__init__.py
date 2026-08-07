"""API schemas for request/response validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

from app.domain.enums.enums import (
    Exchange,
    Sector,
    Industry,
    IPOStatus,
    AnalysisStatus,
    InvestmentStrategy,
    RiskLevel,
    TimeHorizon,
    SentimentLabel,
    AgentName,
    JobType,
    JobStatus,
    MemoryType,
    FailureCategory,
    Severity,
    LessonType,
    PredictionType,
)


# IPO Schemas
class IPOCreateRequest(BaseModel):
    """Request to create a new IPO."""
    symbol: str = Field(..., min_length=1, max_length=10, pattern="^[A-Z0-9.]+$")
    company_name: str = Field(..., min_length=1, max_length=255)
    exchange: Exchange
    sector: Sector = Sector.UNCLASSIFIED
    industry: Industry = Industry.OTHER
    status: IPOStatus = IPOStatus.ANNOUNCED
    expected_date: Optional[datetime] = None
    price_range_low: Optional[float] = Field(None, ge=0)
    price_range_high: Optional[float] = Field(None, ge=0)
    shares_offered: Optional[int] = Field(None, ge=0)
    underwriters: List[str] = []
    use_of_proceeds: str = ""
    prospectus_url: str = ""


class IPOStatusUpdateRequest(BaseModel):
    """Request to update IPO status."""
    status: IPOStatus


class IPORResponse(BaseModel):
    """IPO response model."""
    model_config = ConfigDict(from_attributes=True)
    
    symbol: str
    company_name: str
    exchange: str
    sector: str
    industry: str
    status: str
    expected_date: Optional[datetime] = None
    price_range: Optional[Dict[str, Optional[float]]] = None
    shares_offered: Optional[int] = None
    valuation: Optional[Dict[str, Optional[float]]] = None
    underwriters: List[str] = []
    lead_underwriter: str = ""


# Company Schemas
class CompanyProfileRequest(BaseModel):
    """Request to create company profile."""
    legal_name: str
    common_name: str
    description: str = ""
    business_model: str = ""
    sector: Sector
    industry: Industry
    headquarters: str = ""
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    website: str = ""
    ceo: str = ""
    cfo: str = ""
    chairman: str = ""
    board_members: List[str] = []
    major_shareholders: Dict[str, float] = {}
    competitors: List[str] = []
    competitive_advantages: List[str] = []
    risk_factors: List[str] = []
    key_products: List[str] = []
    target_markets: List[str] = []
    regulatory_environment: str = ""
    esg_score: Optional[float] = None


class CompanyProfileResponse(BaseModel):
    """Company profile response model."""
    model_config = ConfigDict(from_attributes=True)
    
    legal_name: str
    common_name: str
    description: str
    business_model: str
    sector: str
    industry: str
    headquarters: str
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    website: str
    ceo: str
    cfo: str
    chairman: str
    board_members: List[str] = []
    major_shareholders: Dict[str, float] = {}
    competitors: List[str] = []
    competitive_advantages: List[str] = []
    risk_factors: List[str] = []
    key_products: List[str] = []
    target_markets: List[str] = []
    regulatory_environment: str = ""
    esg_score: Optional[float] = None


# Analysis Schemas
class AnalysisRequest(BaseModel):
    """Request to start analysis."""
    symbol: str = Field(..., min_length=1, max_length=10, pattern="^[A-Z0-9.]+$")
    depth: str = Field("standard", pattern="^(standard|deep|comprehensive)$")
    user_id: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Analysis response model."""
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
    agent_results: Dict[str, Any] = {}
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


# Memory Schemas
class MemoryStoreRequest(BaseModel):
    """Request to store memory."""
    memory_type: MemoryType
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    ipo_symbol: Optional[str] = None
    analysis_id: Optional[UUID] = None


class MemorySearchRequest(BaseModel):
    """Request to search memory."""
    memory_type: MemoryType
    query_embedding: List[float]
    limit: int = Field(10, ge=1, le=100)
    threshold: float = Field(0.75, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None


class MemorySearchResult(BaseModel):
    """Memory search result."""
    entry: Dict[str, Any]
    similarity: float


class MemorySearchResponse(BaseModel):
    """Memory search response."""
    results: List[MemorySearchResult]


# Failure Memory Schemas
class FailureRecordRequest(BaseModel):
    """Request to record a failure."""
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
    """Failure record response."""
    failure_id: str
    recorded: bool
    existing: bool = False


class FailureSearchRequest(BaseModel):
    """Request to search failures."""
    error_message: str
    agent_name: AgentName
    threshold: float = Field(0.8, ge=0.0, le=1.0)
    limit: int = Field(5, ge=1, le=20)


class FailureResponse(BaseModel):
    """Failure response model."""
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


# Success Memory Schemas
class SuccessRecordRequest(BaseModel):
    """Request to record a success."""
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
    """Success record response."""
    success_id: str
    recorded: bool


class SuccessSearchRequest(BaseModel):
    """Request to search successful strategies."""
    context: Dict[str, Any]
    agent_name: AgentName
    threshold: float = Field(0.75, ge=0.0, le=1.0)
    limit: int = Field(5, ge=1, le=20)


# Knowledge Memory Schemas
class KnowledgeStoreRequest(BaseModel):
    """Request to store knowledge."""
    concept: str = Field(..., min_length=1, max_length=255)
    description: str
    evidence: List[Dict[str, Any]] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    domain: str = ""
    tags: List[str] = []


class KnowledgeResponse(BaseModel):
    """Knowledge response model."""
    concept: str
    description: str
    evidence: List[Dict[str, Any]]
    confidence: float
    domain: str
    tags: List[str]
    version: int


# Best Practice Schemas
class BestPracticeStoreRequest(BaseModel):
    """Request to store best practice."""
    practice_name: str = Field(..., min_length=1, max_length=255)
    description: str
    applicable_context: Dict[str, Any] = {}
    success_rate: float = Field(0.0, ge=0.0, le=1.0)
    tags: List[str] = []


class BestPracticeResponse(BaseModel):
    """Best practice response model."""
    practice_id: str
    practice_name: str
    description: str
    applicable_context: Dict[str, Any]
    success_rate: float
    usage_count: int
    tags: List[str]
    version: int


# Reflection Schemas
class ReflectionRecordRequest(BaseModel):
    """Request to record a reflection."""
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
    """Reflection response model."""
    reflection_id: str
    recorded: bool


class ReflectionItem(BaseModel):
    """Reflection item for listing."""
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


# Lesson Schemas
class LessonSaveRequest(BaseModel):
    """Request to save a lesson."""
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
    """Lesson response model."""
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
    """Request to search lessons."""
    query: str = Field(..., min_length=1)
    limit: int = Field(20, ge=1, le=100)


# Job Schemas
class JobResponse(BaseModel):
    """Job response model."""
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
    """Job statistics response."""
    by_type: Dict[str, Dict[str, int]]
    total_pending: int
    total_running: int
    total_completed: int
    total_failed: int


# Generic Response Schemas
class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str = "Operation completed successfully"


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    limit: int
    offset: int


# Health Check
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    database: str
    timestamp: datetime


# WebSocket Schemas
class WSMessage(BaseModel):
    """WebSocket message."""
    type: str
    payload: Dict[str, Any]


class WSSubscribeRequest(BaseModel):
    """WebSocket subscribe request."""
    channels: List[str]


class WSAnalysisUpdate(BaseModel):
    """WebSocket analysis update."""
    analysis_id: str
    symbol: str
    agent: str
    status: str
    progress: float
    data: Optional[Dict[str, Any]] = None


# Chart Data
class ChartDataPoint(BaseModel):
    """Chart data point."""
    x: Any
    y: float
    label: Optional[str] = None


class ChartDataset(BaseModel):
    """Chart dataset."""
    label: str
    data: List[ChartDataPoint]
    backgroundColor: Optional[str] = None
    borderColor: Optional[str] = None


class ChartConfig(BaseModel):
    """Chart configuration."""
    type: str  # line, bar, radar, scatter, funnel
    title: str
    data: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None


# Report Schemas
class ReportRequest(BaseModel):
    """Report generation request."""
    symbol: str
    format: str = Field("markdown", pattern="^(markdown|html|pdf|json)$")


class ReportResponse(BaseModel):
    """Report response."""
    report_id: str
    symbol: str
    format: str
    content: str
    generated_at: datetime