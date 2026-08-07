"""Base agent class and interfaces."""

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
class AgentResult(Generic[T]):
    """Result from agent execution."""
    agent_name: AgentName
    status: AgentStatus
    data: Optional[T] = None
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
        self._prompt_template: str = ""
        self._system_prompt: str = ""
    
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
    
    def _update_metrics(self, result: AgentResult[R], success: bool) -> None:
        """Update agent metrics."""
        self._metrics.total_runs += 1
        if success:
            self._metrics.successful_runs += 1
        else:
            self._metrics.failed_runs += 1
        
        self._metrics.total_duration_ms += result.duration_ms
        self._metrics.total_tokens += result.tokens_used
        self._metrics.total_cost_usd += result.cost_usd
        
        # Update average confidence
        if self._metrics.total_runs > 0:
            total_conf = (
                self._metrics.average_confidence * (self._metrics.total_runs - 1)
                + result.confidence
            )
            self._metrics.average_confidence = total_conf / self._metrics.total_runs
        
        self._metrics.last_run = datetime.utcnow()
    
    def get_metrics(self) -> AgentMetrics:
        """Get agent metrics."""
        return self._metrics
    
    def reset_metrics(self) -> None:
        """Reset agent metrics."""
        self._metrics = AgentMetrics()
    
    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool for this agent."""
        self._tools[name] = tool
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Get registered tool."""
        return self._tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools
    
    def validate_input(self, input_data: T) -> bool:
        """Validate input data. Override in subclasses."""
        return True
    
    def validate_output(self, output: R) -> bool:
        """Validate output data. Override in subclasses."""
        return True
    
    async def pre_execute(self, context: AgentContext, input_data: T) -> None:
        """Pre-execution hook. Override in subclasses."""
        pass
    
    async def post_execute(
        self,
        context: AgentContext,
        input_data: T,
        result: AgentResult[R],
    ) -> None:
        """Post-execution hook. Override in subclasses."""
        pass
    
    async def on_error(
        self,
        context: AgentContext,
        input_data: T,
        error: Exception,
    ) -> None:
        """Error handler hook. Override in subclasses."""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name.value}, version={self.version})"


class AgentState:
    """Shared state for agent orchestration."""
    
    def __init__(self):
        self.ipo_symbol: str = ""
        self.analysis_id: UUID = uuid4()
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.depth: str = "standard"
        self.parameters: Dict[str, Any] = {}
        self.results: Dict[str, AgentResult] = {}
        self.errors: List[Dict[str, Any]] = []
        self.memory: Dict[str, Any] = {}
        self.trace_id: Optional[str] = None
        self.started_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
    
    def add_result(self, agent_name: AgentName, result: AgentResult) -> None:
        """Add agent result."""
        self.results[agent_name.value] = result
        self.updated_at = datetime.utcnow()
    
    def get_result(self, agent_name: AgentName) -> Optional[AgentResult]:
        """Get agent result."""
        return self.results.get(agent_name.value)
    
    def has_result(self, agent_name: AgentName) -> bool:
        """Check if agent has result."""
        return agent_name.value in self.results
    
    def add_error(self, agent_name: AgentName, error: str, error_type: str) -> None:
        """Add error."""
        self.errors.append({
            "agent": agent_name.value,
            "error": error,
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.updated_at = datetime.utcnow()
    
    def set_memory(self, key: str, value: Any) -> None:
        """Set memory value."""
        self.memory[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_memory(self, key: str, default: Any = None) -> Any:
        """Get memory value."""
        return self.memory.get(key, default)
    
    def to_context(self) -> AgentContext:
        """Convert to agent context."""
        return AgentContext(
            ipo_symbol=self.ipo_symbol,
            analysis_id=self.analysis_id,
            user_id=self.user_id,
            session_id=self.session_id,
            depth=self.depth,
            parameters=self.parameters,
            previous_results={k: v.to_dict() for k, v in self.results.items()},
            memory_context=self.memory,
            trace_id=self.trace_id,
        )


class AgentOrchestrator:
    """Orchestrates multiple agents in sequence or parallel."""
    
    def __init__(self):
        self._agents: Dict[AgentName, BaseAgent] = {}
        self._execution_order: List[List[AgentName]] = []  # Parallel groups
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent."""
        self._agents[agent.name] = agent
    
    def set_execution_order(self, order: List[List[AgentName]]) -> None:
        """Set execution order (parallel groups)."""
        self._execution_order = order
    
    def get_agent(self, name: AgentName) -> Optional[BaseAgent]:
        """Get registered agent."""
        return self._agents.get(name)
    
    async def execute_sequential(
        self,
        context: AgentContext,
        input_data: Any,
        agent_names: List[AgentName],
    ) -> Dict[AgentName, AgentResult]:
        """Execute agents sequentially."""
        results = {}
        current_input = input_data
        
        for agent_name in agent_names:
            agent = self._agents.get(agent_name)
            if not agent:
                raise ValueError(f"Agent {agent_name} not registered")
            
            agent_context = AgentContext(
                **context.__dict__,
                previous_results={
                    k: v.to_dict() for k, v in results.items()
                },
            )
            
            result = await agent.run_with_retry(agent_context, current_input)
            results[agent_name] = result
            
            if result.status == AgentStatus.FAILED:
                # Decide whether to continue or stop
                break
            
            # Pass result to next agent
            current_input = result.data
        
        return results
    
    async def execute_parallel(
        self,
        context: AgentContext,
        input_data: Any,
        agent_names: List[AgentName],
    ) -> Dict[AgentName, AgentResult]:
        """Execute agents in parallel."""
        import asyncio
        
        async def run_agent(agent_name: AgentName):
            agent = self._agents.get(agent_name)
            if not agent:
                return agent_name, AgentResult(
                    agent_name=agent_name,
                    status=AgentStatus.FAILED,
                    error=f"Agent {agent_name} not registered",
                )
            
            agent_context = AgentContext(
                **context.__dict__,
                previous_results={
                    k: v.to_dict() for k, v in context.previous_results.items()
                },
            )
            
            result = await agent.run_with_retry(agent_context, input_data)
            return agent_name, result
        
        tasks = [run_agent(name) for name in agent_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = {}
        for result in results:
            if isinstance(result, Exception):
                # Handle exception
                pass
            else:
                agent_name, agent_result = result
                final_results[agent_name] = agent_result
        
        return final_results
    
    async def execute_workflow(
        self,
        context: AgentContext,
        input_data: Any,
    ) -> Dict[AgentName, AgentResult]:
        """Execute full workflow based on execution order."""
        all_results = {}
        
        for parallel_group in self._execution_order:
            if len(parallel_group) == 1:
                # Sequential
                results = await self.execute_sequential(
                    context,
                    input_data,
                    parallel_group,
                )
            else:
                # Parallel
                results = await self.execute_parallel(
                    context,
                    input_data,
                    parallel_group,
                )
            
            all_results.update(results)
            
            # Update context for next group
            context.previous_results = {
                k: v.to_dict() for k, v in all_results.items()
            }
        
        return all_results