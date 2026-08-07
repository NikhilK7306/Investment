"""Domain events for event-driven architecture."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, List
from uuid import UUID, uuid4

from app.domain.enums.enums import (
    IPOStatus,
    AgentName,
    AnalysisStatus,
    JobType,
    JobStatus,
    OutcomeStatus,
    LessonType,
)


@dataclass
class DomainEvent:
    """Base domain event."""
    event_id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    aggregate_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_id": str(self.aggregate_id),
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }


@dataclass
class IPODiscoveredEvent(DomainEvent):
    """Event fired when a new IPO is discovered."""
    event_type: str = "ipo.discovered"
    symbol: str = ""
    company_name: str = ""
    exchange: str = ""
    expected_date: Optional[datetime] = None
    price_range_low: Optional[float] = None
    price_range_high: Optional[float] = None
    sector: str = ""
    industry: str = ""
    source: str = ""


@dataclass
class IPOStatusChangedEvent(DomainEvent):
    """Event fired when IPO status changes."""
    event_type: str = "ipo.status_changed"
    symbol: str = ""
    old_status: IPOStatus = IPOStatus.ANNOUNCED
    new_status: IPOStatus = IPOStatus.ANNOUNCED
    reason: str = ""


@dataclass
class IPODataCollectedEvent(DomainEvent):
    """Event fired when IPO data collection completes."""
    event_type: str = "ipo.data_collected"
    symbol: str = ""
    data_sources: List[str] = field(default_factory=list)
    financial_data: bool = False
    news_data: bool = False
    social_data: bool = False
    alternative_data: bool = False
    quality_score: float = 0.0


@dataclass
class AnalysisStartedEvent(DomainEvent):
    """Event fired when analysis starts."""
    event_type: str = "analysis.started"
    symbol: str = ""
    analysis_id: UUID = field(default_factory=uuid4)
    requested_by: str = ""
    depth: str = "standard"
    agents: List[AgentName] = field(default_factory=list)


@dataclass
class AgentAnalysisCompletedEvent(DomainEvent):
    """Event fired when an agent completes analysis."""
    event_type: str = "analysis.agent_completed"
    symbol: str = ""
    analysis_id: UUID = field(default_factory=uuid4)
    agent_name: AgentName = AgentName.FUNDAMENTAL
    status: AnalysisStatus = AnalysisStatus.COMPLETED
    score: float = 0.0
    confidence: float = 0.0
    duration_seconds: float = 0.0


@dataclass
class OverallAnalysisCompletedEvent(DomainEvent):
    """Event fired when overall analysis completes."""
    event_type: str = "analysis.completed"
    symbol: str = ""
    analysis_id: UUID = field(default_factory=uuid4)
    overall_score: float = 0.0
    confidence: float = 0.0
    investment_strategy: str = ""
    risk_level: str = ""
    duration_seconds: float = 0.0


@dataclass
class AnalysisFailedEvent(DomainEvent):
    """Event fired when analysis fails."""
    event_type: str = "analysis.failed"
    symbol: str = ""
    analysis_id: UUID = field(default_factory=uuid4)
    agent_name: Optional[AgentName] = None
    error: str = ""
    error_type: str = ""
    retry_count: int = 0


@dataclass
class ReportGeneratedEvent(DomainEvent):
    """Event fired when report is generated."""
    event_type: str = "report.generated"
    symbol: str = ""
    analysis_id: UUID = field(default_factory=uuid4)
    report_id: UUID = field(default_factory=uuid4)
    format: str = "markdown"
    sections: List[str] = field(default_factory=list)


@dataclass
class MemoryStoredEvent(DomainEvent):
    """Event fired when memory is stored."""
    event_type: str = "memory.stored"
    memory_type: str = ""
    entry_id: UUID = field(default_factory=uuid4)
    ipo_symbol: Optional[str] = None
    content_hash: str = ""


@dataclass
class FailureRecordedEvent(DomainEvent):
    """Event fired when failure is recorded."""
    event_type: str = "failure.recorded"
    failure_id: str = ""
    agent_name: AgentName = AgentName.FUNDAMENTAL
    error_type: str = ""
    category: str = ""
    severity: str = ""
    ipo_symbol: Optional[str] = None
    analysis_id: Optional[UUID] = None


@dataclass
class FailureResolvedEvent(DomainEvent):
    """Event fired when failure is resolved."""
    event_type: str = "failure.resolved"
    failure_id: str = ""
    resolution: str = ""


@dataclass
class SuccessRecordedEvent(DomainEvent):
    """Event fired when success pattern is recorded."""
    event_type: str = "success.recorded"
    success_id: str = ""
    agent_name: AgentName = AgentName.FUNDAMENTAL
    strategy: str = ""
    confidence: float = 0.0
    ipo_symbol: Optional[str] = None


@dataclass
class ReflectionCompletedEvent(DomainEvent):
    """Event fired when reflection completes."""
    event_type: str = "reflection.completed"
    prediction_id: UUID = field(default_factory=uuid4)
    ipo_symbol: str = ""
    accuracy: float = 0.0
    lessons_learned: int = 0
    prompt_improvements: int = 0
    knowledge_updates: int = 0


@dataclass
class OutcomeVerifiedEvent(DomainEvent):
    """Event fired when prediction outcome is verified."""
    event_type: str = "outcome.verified"
    prediction_id: UUID = field(default_factory=uuid4)
    ipo_symbol: str = ""
    prediction_type: str = ""
    predicted_value: float = 0.0
    actual_value: float = 0.0
    accuracy: float = 0.0
    status: OutcomeStatus = OutcomeStatus.VERIFIED


@dataclass
class LessonExtractedEvent(DomainEvent):
    """Event fired when lesson is extracted."""
    event_type: str = "lesson.extracted"
    lesson_id: UUID = field(default_factory=uuid4)
    lesson_type: LessonType = LessonType.BEST_PRACTICE
    title: str = ""
    confidence: float = 0.0
    applicable_agents: List[AgentName] = field(default_factory=list)


@dataclass
class JobQueuedEvent(DomainEvent):
    """Event fired when job is queued."""
    event_type: str = "job.queued"
    job_id: UUID = field(default_factory=uuid4)
    job_type: JobType = JobType.DATA_COLLECTION
    priority: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobStartedEvent(DomainEvent):
    """Event fired when job starts."""
    event_type: str = "job.started"
    job_id: UUID = field(default_factory=uuid4)
    job_type: JobType = JobType.DATA_COLLECTION
    worker_id: str = ""


@dataclass
class JobCompletedEvent(DomainEvent):
    """Event fired when job completes."""
    event_type: str = "job.completed"
    job_id: UUID = field(default_factory=uuid4)
    job_type: JobType = JobType.DATA_COLLECTION
    status: JobStatus = JobStatus.COMPLETED
    duration_seconds: float = 0.0
    result: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobFailedEvent(DomainEvent):
    """Event fired when job fails."""
    event_type: str = "job.failed"
    job_id: UUID = field(default_factory=uuid4)
    job_type: JobType = JobType.DATA_COLLECTION
    error: str = ""
    retry_count: int = 0
    will_retry: bool = True


@dataclass
class UserQueryEvent(DomainEvent):
    """Event fired when user queries the system."""
    event_type: str = "user.query"
    user_id: str = ""
    query: str = ""
    session_id: str = ""
    query_type: str = ""


@dataclass
class AlertTriggeredEvent(DomainEvent):
    """Event fired when alert is triggered."""
    event_type: str = "alert.triggered"
    alert_type: str = ""
    severity: str = ""
    message: str = ""
    ipo_symbol: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Event publisher interface
class EventPublisher:
    """Interface for publishing domain events."""
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single event."""
        raise NotImplementedError
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        raise NotImplementedError


class InMemoryEventPublisher(EventPublisher):
    """In-memory event publisher for development/testing."""
    
    def __init__(self):
        self._handlers: Dict[str, List[callable]] = {}
        self._published_events: List[DomainEvent] = []
    
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish event to subscribers."""
        self._published_events.append(event)
        
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if hasattr(handler, '__await__'):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # Log error but don't fail
                pass
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)
    
    def get_published_events(self) -> List[DomainEvent]:
        """Get all published events (for testing)."""
        return self._published_events.copy()
    
    def clear(self) -> None:
        """Clear published events."""
        self._published_events.clear()


# Global event publisher instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get global event publisher."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = InMemoryEventPublisher()
    return _event_publisher


def set_event_publisher(publisher: EventPublisher) -> None:
    """Set global event publisher."""
    global _event_publisher
    _event_publisher = publisher