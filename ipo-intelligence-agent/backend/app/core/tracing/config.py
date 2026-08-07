"""OpenTelemetry tracing configuration."""

import os
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import Status, StatusCode

from app.core.config.settings import get_settings


_tracer_provider: Optional[TracerProvider] = None


def setup_tracing(
    app=None,
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
) -> TracerProvider:
    """Setup OpenTelemetry tracing."""
    global _tracer_provider
    
    settings = get_settings()
    
    if not settings.enable_opentelemetry:
        return None
    
    service_name = service_name or settings.otel_service_name
    service_version = service_version or settings.app_version
    
    # Create resource
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": settings.app_env,
    })
    
    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    
    # Setup exporters
    if settings.otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otlp_endpoint,
            insecure=settings.otlp_insecure,
        )
        _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Add console exporter for development
    if settings.is_development:
        _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    
    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)
    
    # Auto-instrument libraries
    _setup_instrumentation(app)
    
    return _tracer_provider


def _setup_instrumentation(app=None) -> None:
    """Setup auto-instrumentation for libraries."""
    settings = get_settings()
    
    # FastAPI
    if app:
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=_tracer_provider,
            excluded_urls="/health,/metrics,/docs,/redoc,/openapi.json",
        )
    
    # SQLAlchemy
    SQLAlchemyInstrumentor().instrument(
        tracer_provider=_tracer_provider,
        enable_commenter=True,
        commenter_options={},
    )
    
    # Redis
    RedisInstrumentor().instrument(tracer_provider=_tracer_provider)
    
    # Celery
    CeleryInstrumentor().instrument(tracer_provider=_tracer_provider)
    
    # HTTP clients
    HTTPXClientInstrumentor().instrument(tracer_provider=_tracer_provider)
    RequestsInstrumentor().instrument(tracer_provider=_tracer_provider)


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """Context manager for creating traced spans."""
    tracer = get_tracer("app")
    
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attributes(attributes: dict) -> None:
    """Add attributes to current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def record_exception(exception: Exception) -> None:
    """Record exception in current span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


def get_current_span() -> Optional[trace.Span]:
    """Get current active span."""
    return trace.get_current_span()


def get_trace_id() -> Optional[str]:
    """Get current trace ID as hex string."""
    span = get_current_span()
    if span and span.get_span_context():
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """Get current span ID as hex string."""
    span = get_current_span()
    if span and span.get_span_context():
        return format(span.get_span_context().span_id, "016x")
    return None


class TracedOperation:
    """Context manager for traced operations with automatic error handling."""
    
    def __init__(
        self,
        operation_name: str,
        attributes: Optional[dict] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    ):
        self.operation_name = operation_name
        self.attributes = attributes or {}
        self.kind = kind
        self.span = None
    
    def __enter__(self):
        tracer = get_tracer("app")
        self.span = tracer.start_span(self.operation_name, kind=self.kind)
        
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.span.record_exception(exc_val)
            self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
        else:
            self.span.set_status(Status(StatusCode.OK))
        
        self.span.end()
        return False


def trace_agent_operation(agent_name: str, operation: str):
    """Decorator to trace agent operations."""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_span(
                f"agent.{agent_name}.{operation}",
                attributes={"agent.name": agent_name, "agent.operation": operation},
                kind=trace.SpanKind.INTERNAL,
            ) as span:
                span.set_attribute("agent.input_args", str(args)[:500])
                span.set_attribute("agent.input_kwargs", str(kwargs)[:500])
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("agent.output_type", type(result).__name__)
                    return result
                except Exception as e:
                    span.set_attribute("agent.error", str(e))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_span(
                f"agent.{agent_name}.{operation}",
                attributes={"agent.name": agent_name, "agent.operation": operation},
                kind=trace.SpanKind.INTERNAL,
            ) as span:
                span.set_attribute("agent.input_args", str(args)[:500])
                span.set_attribute("agent.input_kwargs", str(kwargs)[:500])
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("agent.output_type", type(result).__name__)
                    return result
                except Exception as e:
                    span.set_attribute("agent.error", str(e))
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def trace_llm_call(provider: str, model: str):
    """Decorator to trace LLM calls."""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_span(
                f"llm.{provider}.{model}",
                attributes={
                    "llm.provider": provider,
                    "llm.model": model,
                    "llm.operation": "completion",
                },
                kind=trace.SpanKind.CLIENT,
            ) as span:
                # Extract prompt info if available
                if args:
                    span.set_attribute("llm.prompt.length", len(str(args[0])))
                
                try:
                    result = await func(*args, **kwargs)
                    if hasattr(result, "usage"):
                        span.set_attribute("llm.usage.prompt_tokens", result.usage.prompt_tokens)
                        span.set_attribute("llm.usage.completion_tokens", result.usage.completion_tokens)
                        span.set_attribute("llm.usage.total_tokens", result.usage.total_tokens)
                    return result
                except Exception as e:
                    span.set_attribute("llm.error", str(e))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_span(
                f"llm.{provider}.{model}",
                attributes={
                    "llm.provider": provider,
                    "llm.model": model,
                    "llm.operation": "completion",
                },
                kind=trace.SpanKind.CLIENT,
            ) as span:
                if args:
                    span.set_attribute("llm.prompt.length", len(str(args[0])))
                
                try:
                    result = func(*args, **kwargs)
                    if hasattr(result, "usage"):
                        span.set_attribute("llm.usage.prompt_tokens", result.usage.prompt_tokens)
                        span.set_attribute("llm.usage.completion_tokens", result.usage.completion_tokens)
                        span.set_attribute("llm.usage.total_tokens", result.usage.total_tokens)
                    return result
                except Exception as e:
                    span.set_attribute("llm.error", str(e))
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def trace_database_operation(operation: str, table: str):
    """Decorator to trace database operations."""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with trace_span(
                f"db.{operation}.{table}",
                attributes={
                    "db.operation": operation,
                    "db.table": table,
                    "db.system": "postgresql",
                },
                kind=trace.SpanKind.CLIENT,
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    if hasattr(result, "__len__"):
                        span.set_attribute("db.rows_affected", len(result))
                    return result
                except Exception as e:
                    span.set_attribute("db.error", str(e))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with trace_span(
                f"db.{operation}.{table}",
                attributes={
                    "db.operation": operation,
                    "db.table": table,
                    "db.system": "postgresql",
                },
                kind=trace.SpanKind.CLIENT,
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    if hasattr(result, "__len__"):
                        span.set_attribute("db.rows_affected", len(result))
                    return result
                except Exception as e:
                    span.set_attribute("db.error", str(e))
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator