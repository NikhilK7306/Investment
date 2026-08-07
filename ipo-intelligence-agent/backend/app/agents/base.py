"""Base agent class and common utilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from uuid import UUID, uuid4

from app.domain.enums.enums import AgentName, AgentStatus
from app.core.exceptions.base import AgentError, AgentExecutionError, AgentTimeoutError


T = TypeVar('T')
R = TypeVar('R')


@dataclass
class AgentContext:
    """Context passed to agents during execution."""
    ipo_symbol: str
    analysis_id: UUID
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    depth: str = "standard"
    parameters: Dict[str, Any] = field(default_factory=dict)
    previous_results: Dict[str, Any] = field(default_factory=dict)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None


@dataclass
class AgentResult(Generic[R]):
    """Result from agent execution."""
    agent_name: AgentName
    status: AgentStatus
    data: Optional[R] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name.value,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "error_type": self.error_type,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
        }


@dataclass
class AgentMetrics:
    """Agent performance metrics."""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    average_confidence: float = 0.0
    last_run: Optional[datetime] = None
    last_error: Optional[str] = None


class BaseAgent(ABC, Generic[T, R]):
    """Base class for all agents."""
    
    def __init__(
        self,
        name: AgentName,
        description: str,
        version: str = "1.0.0",
        max_retries: int = 3,
        timeout_seconds: int = 300,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._metrics = AgentMetrics()
        self._tools: Dict[str, Any] = {}
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Get system prompt for this agent."""
        pass
    
    @property
    @abstractmethod
    def available_tools(self) -> List[str]:
        """Get list of available tool names."""
        pass
    
    @abstractmethod
    async def execute(self, context: AgentContext, input_data: T) -> AgentResult[R]:
        """Execute agent with given context and input."""
        pass
    
    async def run_with_retry(
        self,
        context: AgentContext,
        input_data: T,
    ) -> AgentResult[R]:
        """Run agent with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await self._execute_with_timeout(context, input_data)
                
                if result.status == AgentStatus.COMPLETED:
                    self._update_metrics(result, success=True)
                    return result
                else:
                    last_error = result.error or "Unknown error"
                    
            except AgentTimeoutError as e:
                last_error = f"Timeout after {self.timeout_seconds}s"
                self._metrics.failed_runs += 1
                
            except Exception as e:
                last_error = str(e)
                self._metrics.failed_runs += 1
            
            # Wait before retry
            if attempt < self.max_retries:
                import asyncio
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        self._metrics.last_error = last_error
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            error=last_error,
            error_type="MAX_RETRIES_EXCEEDED",
            completed_at=datetime.utcnow(),
        )
    
    async def _execute_with_timeout(
        self,
        context: AgentContext,
        input_data: T,
    ) -> AgentResult[R]:
        """Execute with timeout."""
        import asyncio
        
        try:
            return await asyncio.wait_for(
                self.execute(context, input_data),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise AgentTimeoutError(self.name.value, self.timeout_seconds)
    
    def _update_metrics(self, result: AgentResult, success: bool) -> None:
        """Update agent metrics."""
        self._metrics.total_runs += 1
        self._metrics.last_run = datetime.utcnow()
        
        if success:
            self._metrics.successful_runs += 1
        else:
            self._metrics.failed_runs += 1
        
        if result.duration_ms > 0:
            self._metrics.total_duration_ms += result.duration_ms
        
        self._metrics.total_tokens += result.tokens_used
        self._metrics.total_cost_usd += result.cost_usd
        
        if result.confidence > 0:
            # Running average
            n = self._metrics.successful_runs
            self._metrics.average_confidence = (
                (self._metrics.average_confidence * (n - 1) + result.confidence) / n
            )
    
    def get_metrics(self) -> AgentMetrics:
        """Get agent metrics."""
        return self._metrics
    
    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool for this agent."""
        self._tools[name] = tool
    
    def get_tool(self, name: str) -> Any:
        """Get a registered tool."""
        return self._tools.get(name)