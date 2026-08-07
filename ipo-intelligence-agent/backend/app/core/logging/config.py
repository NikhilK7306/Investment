"""Structured logging configuration."""

import sys
import json
import logging
import logging.config
from typing import Any, Dict, Optional
from datetime import datetime

import structlog
from structlog.stdlib import ProcessorFormatter
from structlog.processors import (
    TimeStamper,
    add_log_level,
    StackInfoRenderer,
    format_exc_info,
    UnicodeDecoder,
    CallsiteParameterAdder,
    CallsiteParameter,
)

from app.core.config.settings import get_settings


def get_log_level() -> int:
    """Get log level from settings."""
    settings = get_settings()
    return getattr(logging, settings.log_level.upper(), logging.INFO)


def get_log_format() -> str:
    """Get log format from settings."""
    settings = get_settings()
    return settings.log_format.lower()


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    log_level = get_log_level()
    log_format = get_log_format()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_log_level,
            TimeStamper(fmt="iso", utc=True),
            CallsiteParameterAdder(
                parameters=[
                    CallsiteParameter.FUNC_NAME,
                    CallsiteParameter.LINENO,
                    CallsiteParameter.MODULE,
                ]
            ),
            StackInfoRenderer(),
            format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": [
                    structlog.contextvars.merge_contextvars,
                    add_log_level,
                    TimeStamper(fmt="iso", utc=True),
                ],
            },
            "console": {
                "()": ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": [
                    structlog.contextvars.merge_contextvars,
                    add_log_level,
                    TimeStamper(fmt="iso", utc=True),
                ],
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json" if log_format == "json" else "console",
                "level": log_level,
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": True,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": logging.WARNING,
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "handlers": ["console"],
                "level": logging.WARNING,
                "propagate": False,
            },
            "celery": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "prefect": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
        },
    }
    
    # Add file handler if configured
    if settings.log_file:
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": settings.log_file,
            "maxBytes": settings.log_max_size_mb * 1024 * 1024,
            "backupCount": settings.log_backup_count,
            "formatter": "json" if log_format == "json" else "console",
            "level": log_level,
        }
        for logger_config in logging_config["loggers"].values():
            logger_config["handlers"].append("file")
    
    logging.config.dictConfig(logging_config)


def format_exc_info(logger, name, event_dict):
    """Format exception info for logging."""
    if "exc_info" in event_dict:
        exc_info = event_dict.pop("exc_info")
        if exc_info:
            event_dict["exception"] = structlog.processors.format_exc_info(
                logger, name, {"exc_info": exc_info}
            )
    return event_dict


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin to add logging capabilities to classes."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__ + "." + self.__class__.__name__)
        return self._logger


def log_execution_time(logger: structlog.BoundLogger, operation: str):
    """Decorator to log execution time of functions."""
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            logger.debug(f"Starting {operation}")
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start
                logger.info(
                    f"Completed {operation}",
                    operation=operation,
                    duration_ms=round(duration * 1000, 2),
                    status="success",
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                logger.error(
                    f"Failed {operation}",
                    operation=operation,
                    duration_ms=round(duration * 1000, 2),
                    status="error",
                    error=str(e),
                    exc_info=True,
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            logger.debug(f"Starting {operation}")
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                logger.info(
                    f"Completed {operation}",
                    operation=operation,
                    duration_ms=round(duration * 1000, 2),
                    status="success",
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start
                logger.error(
                    f"Failed {operation}",
                    operation=operation,
                    duration_ms=round(duration * 1000, 2),
                    status="error",
                    error=str(e),
                    exc_info=True,
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_agent_action(
    logger: structlog.BoundLogger,
    agent_name: str,
    action: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """Log agent action with standardized format."""
    log_data = {
        "agent": agent_name,
        "action": action,
        "status": status,
    }
    
    if details:
        log_data["details"] = details
    
    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)
    
    if status == "success":
        logger.info(f"Agent {agent_name} {action} completed", **log_data)
    elif status == "error":
        logger.error(f"Agent {agent_name} {action} failed", **log_data)
    else:
        logger.warning(f"Agent {agent_name} {action} {status}", **log_data)


def log_analysis_event(
    logger: structlog.BoundLogger,
    ipo_symbol: str,
    event: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log analysis events with standardized format."""
    log_data = {
        "ipo_symbol": ipo_symbol,
        "event": event,
    }
    
    if data:
        log_data.update(data)
    
    logger.info(f"Analysis event: {event} for {ipo_symbol}", **log_data)


def log_memory_operation(
    logger: structlog.BoundLogger,
    memory_type: str,
    operation: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Log memory operations."""
    log_data = {
        "memory_type": memory_type,
        "operation": operation,
        "status": status,
    }
    
    if details:
        log_data["details"] = details
    
    if status == "success":
        logger.debug(f"Memory {memory_type} {operation} succeeded", **log_data)
    elif status == "error":
        logger.error(f"Memory {memory_type} {operation} failed", **log_data)
    else:
        logger.info(f"Memory {memory_type} {operation} {status}", **log_data)


def log_reflection_event(
    logger: structlog.BoundLogger,
    event: str,
    prediction_id: Optional[str] = None,
    ipo_symbol: Optional[str] = None,
    accuracy: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Log reflection engine events."""
    log_data = {"event": event}
    
    if prediction_id:
        log_data["prediction_id"] = prediction_id
    if ipo_symbol:
        log_data["ipo_symbol"] = ipo_symbol
    if accuracy is not None:
        log_data["accuracy"] = accuracy
    if details:
        log_data["details"] = details
    
    logger.info(f"Reflection event: {event}", **log_data)


def log_failure_event(
    logger: structlog.BoundLogger,
    failure_id: str,
    agent_name: str,
    error_type: str,
    error_message: str,
    root_cause: Optional[str] = None,
    resolved: bool = False,
) -> None:
    """Log failure memory events."""
    log_data = {
        "failure_id": failure_id,
        "agent": agent_name,
        "error_type": error_type,
        "error_message": error_message,
        "resolved": resolved,
    }
    
    if root_cause:
        log_data["root_cause"] = root_cause
    
    if resolved:
        logger.info(f"Failure {failure_id} resolved", **log_data)
    else:
        logger.warning(f"Failure {failure_id} recorded", **log_data)


def log_success_event(
    logger: structlog.BoundLogger,
    success_id: str,
    agent_name: str,
    strategy: str,
    confidence: float,
    reused: bool = False,
) -> None:
    """Log success memory events."""
    log_data = {
        "success_id": success_id,
        "agent": agent_name,
        "strategy": strategy,
        "confidence": confidence,
        "reused": reused,
    }
    
    if reused:
        logger.info(f"Success pattern {success_id} reused", **log_data)
    else:
        logger.info(f"Success pattern {success_id} recorded", **log_data)