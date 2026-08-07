"""Prometheus metrics configuration."""

from functools import wraps
from typing import Callable, Optional
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
import time
import structlog

from app.core.config.settings import get_settings


logger = structlog.get_logger(__name__)


class MetricsManager:
    """Centralized metrics management."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or REGISTRY
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize all metrics."""
        
        # HTTP Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )
        
        self.http_request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry,
        )
        
        self.http_request_size = Histogram(
            "http_request_size_bytes",
            "HTTP request size in bytes",
            ["method", "endpoint"],
            registry=self.registry,
        )
        
        self.http_response_size = Histogram(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "endpoint"],
            registry=self.registry,
        )
        
        # Agent Metrics
        self.agent_runs_total = Counter(
            "agent_runs_total",
            "Total agent executions",
            ["agent_name", "status"],
            registry=self.registry,
        )
        
        self.agent_execution_duration = Histogram(
            "agent_execution_duration_seconds",
            "Agent execution duration",
            ["agent_name"],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600],
            registry=self.registry,
        )
        
        self.agent_errors_total = Counter(
            "agent_errors_total",
            "Total agent errors",
            ["agent_name", "error_type"],
            registry=self.registry,
        )
        
        # Analysis Metrics
        self.analysis_requests_total = Counter(
            "analysis_requests_total",
            "Total analysis requests",
            ["ipo_symbol", "status"],
            registry=self.registry,
        )
        
        self.analysis_score = Histogram(
            "analysis_score",
            "IPO analysis scores",
            ["ipo_symbol"],
            buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            registry=self.registry,
        )
        
        self.analysis_duration = Histogram(
            "analysis_duration_seconds",
            "Analysis duration",
            ["ipo_symbol"],
            buckets=[10, 30, 60, 120, 300, 600],
            registry=self.registry,
        )
        
        # Memory Metrics
        self.memory_operations_total = Counter(
            "memory_operations_total",
            "Total memory operations",
            ["memory_type", "operation", "status"],
            registry=self.registry,
        )
        
        self.memory_entries = Gauge(
            "memory_entries",
            "Number of entries in memory",
            ["memory_type"],
            registry=self.registry,
        )
        
        self.memory_search_duration = Histogram(
            "memory_search_duration_seconds",
            "Memory search duration",
            ["memory_type"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry,
        )
        
        # Reflection Metrics
        self.reflection_runs_total = Counter(
            "reflection_runs_total",
            "Total reflection runs",
            ["status"],
            registry=self.registry,
        )
        
        self.prediction_accuracy = Gauge(
            "prediction_accuracy",
            "Prediction accuracy percentage",
            ["ipo_symbol"],
            registry=self.registry,
        )
        
        self.lessons_learned = Counter(
            "lessons_learned_total",
            "Total lessons learned",
            ["lesson_type"],
            registry=self.registry,
        )
        
        # Failure/Success Memory Metrics
        self.failure_memory_entries = Gauge(
            "failure_memory_entries",
            "Number of failure memory entries",
            registry=self.registry,
        )
        
        self.success_memory_entries = Gauge(
            "success_memory_entries",
            "Number of success memory entries",
            registry=self.registry,
        )
        
        self.failure_avoided = Counter(
            "failure_avoided_total",
            "Failures avoided by checking failure memory",
            ["failure_type"],
            registry=self.registry,
        )
        
        self.success_reused = Counter(
            "success_reused_total",
            "Success patterns reused",
            ["success_type"],
            registry=self.registry,
        )
        
        # External API Metrics
        self.external_api_requests = Counter(
            "external_api_requests_total",
            "External API requests",
            ["provider", "endpoint", "status"],
            registry=self.registry,
        )
        
        self.external_api_duration = Histogram(
            "external_api_duration_seconds",
            "External API request duration",
            ["provider", "endpoint"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry,
        )
        
        self.external_api_rate_limited = Counter(
            "external_api_rate_limited_total",
            "External API rate limit hits",
            ["provider"],
            registry=self.registry,
        )
        
        # Database Metrics
        self.db_query_duration = Histogram(
            "db_query_duration_seconds",
            "Database query duration",
            ["operation", "table"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
            registry=self.registry,
        )
        
        self.db_pool_size = Gauge(
            "db_pool_size",
            "Database connection pool size",
            ["state"],
            registry=self.registry,
        )
        
        self.db_errors = Counter(
            "db_errors_total",
            "Database errors",
            ["operation", "error_type"],
            registry=self.registry,
        )
        
        # Cache Metrics
        self.cache_operations = Counter(
            "cache_operations_total",
            "Cache operations",
            ["operation", "status"],
            registry=self.registry,
        )
        
        self.cache_hit_ratio = Gauge(
            "cache_hit_ratio",
            "Cache hit ratio",
            registry=self.registry,
        )
        
        # Queue Metrics
        self.queue_size = Gauge(
            "queue_size",
            "Queue size",
            ["queue_name"],
            registry=self.registry,
        )
        
        self.queue_job_duration = Histogram(
            "queue_job_duration_seconds",
            "Queue job duration",
            ["queue_name", "job_type"],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600],
            registry=self.registry,
        )
        
        self.queue_jobs_total = Counter(
            "queue_jobs_total",
            "Total queue jobs",
            ["queue_name", "job_type", "status"],
            registry=self.registry,
        )
        
        # Business Metrics
        self.active_ipos = Gauge(
            "active_ipos",
            "Number of active IPOs being tracked",
            registry=self.registry,
        )
        
        self.completed_analyses = Gauge(
            "completed_analyses",
            "Total completed analyses",
            registry=self.registry,
        )
        
        self.average_score = Gauge(
            "average_ipo_score",
            "Average IPO score across all analyses",
            registry=self.registry,
        )
        
        self.accuracy_rate = Gauge(
            "prediction_accuracy_rate",
            "Overall prediction accuracy rate",
            registry=self.registry,
        )
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: int = 0,
        response_size: int = 0,
    ):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status=str(status_code)
        ).inc()
        self.http_request_duration.labels(
            method=method, endpoint=endpoint
        ).observe(duration)
        if request_size:
            self.http_request_size.labels(
                method=method, endpoint=endpoint
            ).observe(request_size)
        if response_size:
            self.http_response_size.labels(
                method=method, endpoint=endpoint
            ).observe(response_size)
    
    def record_agent_run(self, agent_name: str, status: str, duration: float):
        """Record agent execution metrics."""
        self.agent_runs_total.labels(agent_name=agent_name, status=status).inc()
        self.agent_execution_duration.labels(agent_name=agent_name).observe(duration)
    
    def record_agent_error(self, agent_name: str, error_type: str):
        """Record agent error."""
        self.agent_errors_total.labels(agent_name=agent_name, error_type=error_type).inc()
    
    def record_analysis(self, ipo_symbol: str, score: float, duration: float, status: str):
        """Record analysis metrics."""
        self.analysis_requests_total.labels(ipo_symbol=ipo_symbol, status=status).inc()
        self.analysis_score.labels(ipo_symbol=ipo_symbol).observe(score)
        self.analysis_duration.labels(ipo_symbol=ipo_symbol).observe(duration)
    
    def record_memory_operation(
        self,
        memory_type: str,
        operation: str,
        status: str,
        duration: float = 0,
    ):
        """Record memory operation metrics."""
        self.memory_operations_total.labels(
            memory_type=memory_type, operation=operation, status=status
        ).inc()
        if duration:
            self.memory_search_duration.labels(memory_type=memory_type).observe(duration)
    
    def set_memory_entries(self, memory_type: str, count: int):
        """Set memory entries gauge."""
        self.memory_entries.labels(memory_type=memory_type).set(count)
    
    def record_reflection(self, status: str):
        """Record reflection run."""
        self.reflection_runs_total.labels(status=status).inc()
    
    def set_prediction_accuracy(self, ipo_symbol: str, accuracy: float):
        """Set prediction accuracy."""
        self.prediction_accuracy.labels(ipo_symbol=ipo_symbol).set(accuracy)
    
    def record_lesson(self, lesson_type: str):
        """Record lesson learned."""
        self.lessons_learned.labels(lesson_type=lesson_type).inc()
    
    def record_failure_avoided(self, failure_type: str):
        """Record failure avoided."""
        self.failure_avoided.labels(failure_type=failure_type).inc()
    
    def record_success_reused(self, success_type: str):
        """Record success reused."""
        self.success_reused.labels(success_type=success_type).inc()
    
    def record_external_api(
        self,
        provider: str,
        endpoint: str,
        status: str,
        duration: float,
    ):
        """Record external API call."""
        self.external_api_requests.labels(
            provider=provider, endpoint=endpoint, status=status
        ).inc()
        self.external_api_duration.labels(
            provider=provider, endpoint=endpoint
        ).observe(duration)
    
    def record_rate_limit(self, provider: str):
        """Record rate limit hit."""
        self.external_api_rate_limited.labels(provider=provider).inc()
    
    def record_db_query(self, operation: str, table: str, duration: float):
        """Record database query."""
        self.db_query_duration.labels(operation=operation, table=table).observe(duration)
    
    def set_db_pool(self, active: int, idle: int):
        """Set database pool metrics."""
        self.db_pool_size.labels(state="active").set(active)
        self.db_pool_size.labels(state="idle").set(idle)
    
    def record_db_error(self, operation: str, error_type: str):
        """Record database error."""
        self.db_errors.labels(operation=operation, error_type=error_type).inc()
    
    def record_cache(self, operation: str, hit: bool):
        """Record cache operation."""
        self.cache_operations.labels(
            operation=operation, status="hit" if hit else "miss"
        ).inc()
    
    def set_cache_hit_ratio(self, ratio: float):
        """Set cache hit ratio."""
        self.cache_hit_ratio.set(ratio)
    
    def set_queue_size(self, queue_name: str, size: int):
        """Set queue size."""
        self.queue_size.labels(queue_name=queue_name).set(size)
    
    def record_queue_job(
        self,
        queue_name: str,
        job_type: str,
        status: str,
        duration: float = 0,
    ):
        """Record queue job metrics."""
        self.queue_jobs_total.labels(
            queue_name=queue_name, job_type=job_type, status=status
        ).inc()
        if duration:
            self.queue_job_duration.labels(
                queue_name=queue_name, job_type=job_type
            ).observe(duration)
    
    def set_active_ipos(self, count: int):
        """Set active IPOs count."""
        self.active_ipos.set(count)
    
    def set_completed_analyses(self, count: int):
        """Set completed analyses count."""
        self.completed_analyses.set(count)
    
    def set_average_score(self, score: float):
        """Set average score."""
        self.average_score.set(score)
    
    def set_accuracy_rate(self, rate: float):
        """Set accuracy rate."""
        self.accuracy_rate.set(rate)


# Global metrics manager
_metrics_manager: Optional[MetricsManager] = None


def get_metrics_manager() -> MetricsManager:
    """Get global metrics manager instance."""
    global _metrics_manager
    if _metrics_manager is None:
        _metrics_manager = MetricsManager()
    return _metrics_manager


def init_metrics(registry: Optional[CollectorRegistry] = None) -> MetricsManager:
    """Initialize global metrics manager."""
    global _metrics_manager
    _metrics_manager = MetricsManager(registry)
    return _metrics_manager


def get_metrics() -> bytes:
    """Get Prometheus metrics output."""
    return generate_latest(get_metrics_manager().registry)


def setup_metrics(app, settings=None):
    """Setup Prometheus metrics for the FastAPI application."""
    init_metrics()
    app.add_middleware(metrics_middleware())


def metrics_middleware():
    """ASGI middleware for metrics collection."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    
    class MetricsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next: Callable):
            start_time = time.time()
            
            # Get endpoint name from route
            endpoint = request.url.path
            if hasattr(request, "scope") and "route" in request.scope:
                route = request.scope["route"]
                if hasattr(route, "path"):
                    endpoint = route.path
            
            response = await call_next(request)
            
            duration = time.time() - start_time
            
            metrics = get_metrics_manager()
            metrics.record_http_request(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
                duration=duration,
            )
            
            return response
    
    return MetricsMiddleware


def track_agent_metrics(agent_name: str):
    """Decorator to track agent execution metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            metrics = get_metrics_manager()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_agent_run(agent_name, "success", duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_agent_run(agent_name, "error", duration)
                metrics.record_agent_error(agent_name, type(e).__name__)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            metrics = get_metrics_manager()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_agent_run(agent_name, "success", duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_agent_run(agent_name, "error", duration)
                metrics.record_agent_error(agent_name, type(e).__name__)
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def track_analysis_metrics(ipo_symbol: str):
    """Decorator to track analysis metrics."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            metrics = get_metrics_manager()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                score = getattr(result, "overall_score", 0) if result else 0
                metrics.record_analysis(ipo_symbol, score, duration, "success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_analysis(ipo_symbol, 0, duration, "error")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            metrics = get_metrics_manager()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                score = getattr(result, "overall_score", 0) if result else 0
                metrics.record_analysis(ipo_symbol, score, duration, "success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_analysis(ipo_symbol, 0, duration, "error")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator