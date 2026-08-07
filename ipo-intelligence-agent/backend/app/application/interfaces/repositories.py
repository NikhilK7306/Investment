"""Repository interfaces (ports) for data access."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from app.domain.value_objects.value_objects import (
    CompanyProfile,
    FinancialMetrics,
    IPODetails,
    InvestmentThesis,
    Prediction,
    RiskFactor,
    SentimentData,
    ScoreComponent,
    DataPoint,
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
from app.domain.enums.enums import (
    AgentName,
    MemoryType,
    PredictionType,
    Sector,
    Industry,
    Exchange,
    AnalysisStatus,
    JobType,
    JobStatus,
    LessonType,
)


class IORepository(ABC):
    """Base repository interface."""
    
    @abstractmethod
    async def save(self, entity) -> None:
        """Save entity."""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID."""
        pass


class IPORepository(IORepository):
    """IPO data repository."""
    
    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Optional[IPODetails]:
        """Get IPO by symbol."""
        pass
    
    @abstractmethod
    async def get_by_id(self, ipo_id: UUID) -> Optional[IPODetails]:
        """Get IPO by ID."""
        pass
    
    @abstractmethod
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
        """List upcoming IPOs with filters."""
        pass
    
    @abstractmethod
    async def count_upcoming(
        self,
        status: Optional[str] = None,
        exchange: Optional[Exchange] = None,
        sector: Optional[Sector] = None,
    ) -> int:
        """Count upcoming IPOs."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> List[IPODetails]:
        """Search IPOs by text query."""
        pass
    
    @abstractmethod
    async def get_recently_listed(
        self,
        days: int = 30,
        limit: int = 20,
    ) -> List[IPODetails]:
        """Get recently listed IPOs."""
        pass
    
    @abstractmethod
    async def update_status(self, symbol: str, status: str) -> bool:
        """Update IPO status."""
        pass


class CompanyRepository(IORepository):
    """Company profile repository."""
    
    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Optional[CompanyProfile]:
        """Get company by symbol."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[CompanyProfile]:
        """Get company by name."""
        pass
    
    @abstractmethod
    async def list_by_sector(
        self,
        sector: Sector,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CompanyProfile]:
        """List companies by sector."""
        pass
    
    @abstractmethod
    async def list_by_industry(
        self,
        industry: Industry,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CompanyProfile]:
        """List companies by industry."""
        pass


class FinancialRepository(IORepository):
    """Financial metrics repository."""
    
    @abstractmethod
    async def get_latest(self, symbol: str) -> Optional[FinancialMetrics]:
        """Get latest financial metrics."""
        pass
    
    @abstractmethod
    async def get_history(
        self,
        symbol: str,
        periods: int = 8,
    ) -> List[FinancialMetrics]:
        """Get financial history."""
        pass
    
    @abstractmethod
    async def get_by_period(
        self,
        symbol: str,
        period: str,
    ) -> Optional[FinancialMetrics]:
        """Get financials for specific period."""
        pass


class AnalysisRepository(IORepository):
    """Analysis results repository."""
    
    @abstractmethod
    async def save_analysis(
        self,
        symbol: str,
        analysis_data: Dict[str, Any],
    ) -> UUID:
        """Save complete analysis."""
        pass
    
    @abstractmethod
    async def get_latest_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest analysis for symbol."""
        pass
    
    @abstractmethod
    async def get_analysis_history(
        self,
        symbol: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get analysis history."""
        pass
    
    @abstractmethod
    async def get_analysis_by_id(self, analysis_id: UUID) -> Optional[Dict[str, Any]]:
        """Get analysis by ID."""
        pass
    
    @abstractmethod
    async def save_score_breakdown(
        self,
        analysis_id: UUID,
        components: List[ScoreComponent],
    ) -> None:
        """Save score breakdown."""
        pass
    
    @abstractmethod
    async def get_score_breakdown(
        self,
        analysis_id: UUID,
    ) -> List[ScoreComponent]:
        """Get score breakdown."""
        pass
    
    @abstractmethod
    async def save_risk_factors(
        self,
        analysis_id: UUID,
        risk_factors: List[RiskFactor],
    ) -> None:
        """Save risk factors."""
        pass
    
    @abstractmethod
    async def get_risk_factors(
        self,
        analysis_id: UUID,
    ) -> List[RiskFactor]:
        """Get risk factors."""
        pass
    
    @abstractmethod
    async def save_investment_thesis(
        self,
        analysis_id: UUID,
        thesis: InvestmentThesis,
    ) -> None:
        """Save investment thesis."""
        pass
    
    @abstractmethod
    async def get_investment_thesis(
        self,
        analysis_id: UUID,
    ) -> Optional[InvestmentThesis]:
        """Get investment thesis."""
        pass


class PredictionRepository(IORepository):
    """Prediction repository."""
    
    @abstractmethod
    async def save_prediction(
        self,
        prediction: Prediction,
    ) -> UUID:
        """Save prediction."""
        pass
    
    @abstractmethod
    async def get_predictions_for_ipo(
        self,
        symbol: str,
        prediction_type: Optional[PredictionType] = None,
    ) -> List[Prediction]:
        """Get predictions for IPO."""
        pass
    
    @abstractmethod
    async def get_pending_verification(
        self,
        limit: int = 100,
    ) -> List[Prediction]:
        """Get predictions pending verification."""
        pass
    
    @abstractmethod
    async def update_outcome(
        self,
        prediction_id: UUID,
        actual_value: float,
        status: str,
    ) -> bool:
        """Update prediction with actual outcome."""
        pass


class ReportRepository(IORepository):
    """Report repository."""
    
    @abstractmethod
    async def save_report(
        self,
        symbol: str,
        analysis_id: UUID,
        content: str,
        format: str = "markdown",
        sections: Optional[List[str]] = None,
    ) -> UUID:
        """Save generated report."""
        pass
    
    @abstractmethod
    async def get_latest_report(
        self,
        symbol: str,
        format: str = "markdown",
    ) -> Optional[str]:
        """Get latest report for symbol."""
        pass
    
    @abstractmethod
    async def get_report_by_id(
        self,
        report_id: UUID,
    ) -> Optional[str]:
        """Get report by ID."""
        pass


class MemoryRepository(ABC):
    """Memory repository interface."""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def search(
        self,
        memory_type: MemoryType,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.75,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[MemoryEntry, float]]:
        """Search memory by semantic similarity."""
        pass
    
    @abstractmethod
    async def get_by_id(
        self,
        memory_type: MemoryType,
        entry_id: UUID,
    ) -> Optional[MemoryEntry]:
        """Get memory entry by ID."""
        pass
    
    @abstractmethod
    async def get_recent(
        self,
        memory_type: MemoryType,
        limit: int = 100,
        ipo_symbol: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Get recent memory entries."""
        pass
    
    @abstractmethod
    async def delete_old_entries(
        self,
        memory_type: MemoryType,
        older_than_days: int,
    ) -> int:
        """Delete old memory entries."""
        pass


class FailureMemoryRepository(MemoryRepository):
    """Failure memory repository."""
    
    @abstractmethod
    async def find_similar(
        self,
        error_message: str,
        agent_name: AgentName,
        threshold: float = 0.8,
        limit: int = 5,
    ) -> List[Tuple[FailureMemory, float]]:
        """Find similar failures."""
        pass
    
    @abstractmethod
    async def get_by_category(
        self,
        category: str,
        limit: int = 50,
    ) -> List[FailureMemory]:
        """Get failures by category."""
        pass
    
    @abstractmethod
    async def mark_resolved(
        self,
        failure_id: UUID,
        resolution: str,
    ) -> bool:
        """Mark failure as resolved."""
        pass
    
    @abstractmethod
    async def get_unresolved(
        self,
        agent_name: Optional[AgentName] = None,
        limit: int = 100,
    ) -> List[FailureMemory]:
        """Get unresolved failures."""
        pass


class SuccessMemoryRepository(MemoryRepository):
    """Success memory repository."""
    
    @abstractmethod
    async def find_successful_strategies(
        self,
        context: Dict[str, Any],
        agent_name: AgentName,
        threshold: float = 0.75,
        limit: int = 5,
    ) -> List[Tuple[SuccessMemory, float]]:
        """Find successful strategies for context."""
        pass
    
    @abstractmethod
    async def get_by_strategy(
        self,
        strategy: str,
        agent_name: AgentName,
        limit: int = 20,
    ) -> List[SuccessMemory]:
        """Get successes by strategy."""
        pass
    
    @abstractmethod
    async def increment_reuse_count(
        self,
        success_id: UUID,
    ) -> bool:
        """Increment reuse count."""
        pass


class KnowledgeMemoryRepository(MemoryRepository):
    """Knowledge memory repository."""
    
    @abstractmethod
    async def get_by_concept(
        self,
        concept: str,
        domain: Optional[str] = None,
    ) -> Optional[KnowledgeMemory]:
        """Get knowledge by concept."""
        pass
    
    @abstractmethod
    async def search_concepts(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Tuple[KnowledgeMemory, float]]:
        """Search knowledge concepts."""
        pass
    
    @abstractmethod
    async def get_by_domain(
        self,
        domain: str,
        limit: int = 50,
    ) -> List[KnowledgeMemory]:
        """Get knowledge by domain."""
        pass


class BestPracticeRepository(MemoryRepository):
    """Best practice memory repository."""
    
    @abstractmethod
    async def get_applicable_practices(
        self,
        context: Dict[str, Any],
        limit: int = 10,
    ) -> List[BestPracticeMemory]:
        """Get best practices applicable to context."""
        pass
    
    @abstractmethod
    async def increment_usage(
        self,
        practice_id: UUID,
    ) -> bool:
        """Increment usage count."""
        pass


class ReflectionMemoryRepository(MemoryRepository):
    """Reflection memory repository."""
    
    @abstractmethod
    async def get_by_prediction(
        self,
        prediction_id: UUID,
    ) -> Optional[ReflectionMemory]:
        """Get reflection by prediction ID."""
        pass
    
    @abstractmethod
    async def get_by_ipo(
        self,
        ipo_symbol: str,
        limit: int = 20,
    ) -> List[ReflectionMemory]:
        """Get reflections for IPO."""
        pass
    
    @abstractmethod
    async def get_unprocessed(
        self,
        limit: int = 50,
    ) -> List[ReflectionMemory]:
        """Get unprocessed reflections."""
        pass


class LessonRepository(IORepository):
    """Lesson learned repository."""
    
    @abstractmethod
    async def save(self, lesson: Lesson) -> UUID:
        """Save lesson."""
        pass
    
    @abstractmethod
    async def get_by_id(self, lesson_id: UUID) -> Optional[Lesson]:
        """Get lesson by ID."""
        pass
    
    @abstractmethod
    async def get_by_type(
        self,
        lesson_type: LessonType,
        limit: int = 50,
    ) -> List[Lesson]:
        """Get lessons by type."""
        pass
    
    @abstractmethod
    async def get_applicable(
        self,
        agent_name: AgentName,
        context: Dict[str, Any],
        limit: int = 10,
    ) -> List[Lesson]:
        """Get applicable lessons for agent and context."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Lesson]:
        """Search lessons by text."""
        pass


class JobRepository(IORepository):
    """Background job repository."""
    
    @abstractmethod
    async def create_job(
        self,
        job_type: JobType,
        payload: Dict[str, Any],
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
    ) -> UUID:
        """Create new job."""
        pass
    
    @abstractmethod
    async def get_job(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        pass
    
    @abstractmethod
    async def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update job status."""
        pass
    
    @abstractmethod
    async def get_pending_jobs(
        self,
        job_type: Optional[JobType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get pending jobs."""
        pass
    
    @abstractmethod
    async def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics."""
        pass


class UserRepository(IORepository):
    """User repository."""
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def create_user(
        self,
        email: str,
        password_hash: str,
        roles: List[str],
        permissions: List[str],
    ) -> UUID:
        """Create new user."""
        pass
    
    @abstractmethod
    async def update_user(
        self,
        user_id: UUID,
        updates: Dict[str, Any],
    ) -> bool:
        """Update user."""
        pass


class APIKeyRepository(IORepository):
    """API key repository."""
    
    @abstractmethod
    async def create_key(
        self,
        user_id: UUID,
        name: str,
        key_hash: str,
        scopes: List[str],
        expires_at: Optional[datetime] = None,
    ) -> UUID:
        """Create API key."""
        pass
    
    @abstractmethod
    async def get_key(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash."""
        pass
    
    @abstractmethod
    async def revoke_key(self, key_id: UUID) -> bool:
        """Revoke API key."""
        pass
    
    @abstractmethod
    async def list_keys(self, user_id: UUID) -> List[Dict[str, Any]]:
        """List user's API keys."""
        pass