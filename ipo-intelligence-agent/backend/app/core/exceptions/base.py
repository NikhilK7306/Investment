"""Application exceptions."""

from typing import Any, Dict, Optional


class IPOIntelligenceError(Exception):
    """Base exception for IPO Intelligence Agent."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


# Configuration Errors
class ConfigurationError(IPOIntelligenceError):
    """Configuration related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details, 500)


class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing."""
    
    def __init__(self, config_key: str):
        super().__init__(
            f"Required configuration '{config_key}' is missing",
            {"config_key": config_key}
        )


# Database Errors
class DatabaseError(IPOIntelligenceError):
    """Database related errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        details = details or {}
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, "DATABASE_ERROR", details, 500)


class RecordNotFoundError(DatabaseError):
    """Record not found in database."""
    
    def __init__(self, entity_type: str, identifier: Any):
        super().__init__(
            f"{entity_type} not found",
            {"entity_type": entity_type, "identifier": str(identifier)},
        )
        self.status_code = 404


class DuplicateRecordError(DatabaseError):
    """Attempt to create duplicate record."""
    
    def __init__(self, entity_type: str, field: str, value: Any):
        super().__init__(
            f"{entity_type} with {field}={value} already exists",
            {"entity_type": entity_type, "field": field, "value": str(value)},
        )
        self.status_code = 409


# Validation Errors
class ValidationError(IPOIntelligenceError):
    """Input validation error."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, "VALIDATION_ERROR", details, 422)


class InvalidInputError(ValidationError):
    """Invalid input provided."""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            f"Invalid value for {field}: {reason}",
            field=field,
            value=value,
            details={"reason": reason}
        )


# Authentication/Authorization Errors
class AuthenticationError(IPOIntelligenceError):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details, 401)


class AuthorizationError(IPOIntelligenceError):
    """Authorization failed."""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details, 403)


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    
    def __init__(self):
        super().__init__("Token has expired", {"reason": "expired"})


class InvalidTokenError(AuthenticationError):
    """JWT token is invalid."""
    
    def __init__(self, reason: str = "Invalid token"):
        super().__init__(reason, {"reason": reason})


# Agent Errors
class AgentError(IPOIntelligenceError):
    """Base agent error."""
    
    def __init__(
        self,
        message: str,
        agent_name: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        details = details or {}
        details["agent_name"] = agent_name
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, "AGENT_ERROR", details, 500)


class AgentExecutionError(AgentError):
    """Agent execution failed."""
    
    def __init__(
        self,
        agent_name: str,
        step: str,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            f"Agent {agent_name} failed at step '{step}': {message}",
            agent_name,
            {"step": step},
            original_error,
        )


class AgentTimeoutError(AgentError):
    """Agent execution timed out."""
    
    def __init__(self, agent_name: str, timeout_seconds: int):
        super().__init__(
            f"Agent {agent_name} timed out after {timeout_seconds} seconds",
            agent_name,
            {"timeout_seconds": timeout_seconds},
        )


class AgentValidationError(AgentError):
    """Agent output validation failed."""
    
    def __init__(self, agent_name: str, validation_errors: list):
        super().__init__(
            f"Agent {agent_name} produced invalid output",
            agent_name,
            {"validation_errors": validation_errors},
        )


# External Service Errors
class ExternalServiceError(IPOIntelligenceError):
    """External service error."""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["service_name"] = service_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(
            f"External service '{service_name}' error: {message}",
            "EXTERNAL_SERVICE_ERROR",
            details,
            502,
        )


class RateLimitError(ExternalServiceError):
    """Rate limit exceeded."""
    
    def __init__(self, service_name: str, retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            service_name,
            "Rate limit exceeded",
            429,
            details,
        )
        self.status_code = 429


class ServiceUnavailableError(ExternalServiceError):
    """Service temporarily unavailable."""
    
    def __init__(self, service_name: str, message: str = "Service unavailable"):
        super().__init__(service_name, message, 503)
        self.status_code = 503


# Analysis Errors
class AnalysisError(IPOIntelligenceError):
    """Analysis process error."""
    
    def __init__(
        self,
        message: str,
        ipo_symbol: Optional[str] = None,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if ipo_symbol:
            details["ipo_symbol"] = ipo_symbol
        if stage:
            details["stage"] = stage
        super().__init__(message, "ANALYSIS_ERROR", details, 500)


class InsufficientDataError(AnalysisError):
    """Insufficient data for analysis."""
    
    def __init__(self, ipo_symbol: str, missing_data: list):
        super().__init__(
            f"Insufficient data for {ipo_symbol} analysis",
            ipo_symbol=ipo_symbol,
            stage="data_validation",
            details={"missing_data": missing_data},
        )
        self.status_code = 422


class ScoringError(AnalysisError):
    """Scoring calculation error."""
    
    def __init__(self, ipo_symbol: str, component: str, message: str):
        super().__init__(
            f"Scoring error for {ipo_symbol} in {component}: {message}",
            ipo_symbol=ipo_symbol,
            stage="scoring",
            details={"component": component},
        )


# Memory Errors
class MemoryError(IPOIntelligenceError):
    """Memory system error."""
    
    def __init__(
        self,
        message: str,
        memory_type: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["memory_type"] = memory_type
        super().__init__(message, "MEMORY_ERROR", details, 500)


class MemoryNotFoundError(MemoryError):
    """Memory entry not found."""
    
    def __init__(self, memory_type: str, key: str):
        super().__init__(
            f"{memory_type} memory not found for key: {key}",
            memory_type,
            {"key": key},
        )
        self.status_code = 404


# Reflection Errors
class ReflectionError(IPOIntelligenceError):
    """Reflection engine error."""
    
    def __init__(
        self,
        message: str,
        prediction_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if prediction_id:
            details["prediction_id"] = prediction_id
        super().__init__(message, "REFLECTION_ERROR", details, 500)


# Task/Job Errors
class JobError(IPOIntelligenceError):
    """Background job error."""
    
    def __init__(
        self,
        message: str,
        job_id: str,
        job_type: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details.update({"job_id": job_id, "job_type": job_type})
        super().__init__(message, "JOB_ERROR", details, 500)


class JobNotFoundError(JobError):
    """Job not found."""
    
    def __init__(self, job_id: str):
        super().__init__(
            f"Job {job_id} not found",
            job_id=job_id,
            job_type="unknown",
        )
        self.status_code = 404


# WebSocket Errors
class WebSocketError(IPOIntelligenceError):
    """WebSocket error."""
    
    def __init__(self, message: str, connection_id: Optional[str] = None):
        details = {"connection_id": connection_id} if connection_id else {}
        super().__init__(message, "WEBSOCKET_ERROR", details, 500)


# File Errors
class FileError(IPOIntelligenceError):
    """File operation error."""
    
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if operation:
            details["operation"] = operation
        super().__init__(message, "FILE_ERROR", details, 500)


class FileTooLargeError(FileError):
    """File exceeds maximum size."""
    
    def __init__(self, filename: str, size_mb: float, max_size_mb: float):
        super().__init__(
            f"File {filename} ({size_mb:.1f}MB) exceeds maximum size ({max_size_mb}MB)",
            filename=filename,
            operation="upload",
        )
        self.status_code = 413


class InvalidFileTypeError(FileError):
    """Invalid file type."""
    
    def __init__(self, filename: str, allowed_types: list):
        super().__init__(
            f"File {filename} has invalid type. Allowed: {', '.join(allowed_types)}",
            filename=filename,
            operation="upload",
        )
        self.status_code = 415


# Data Pipeline Errors
class PipelineError(IPOIntelligenceError):
    """Data pipeline error."""
    
    def __init__(
        self,
        message: str,
        pipeline_name: str,
        stage: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details.update({"pipeline_name": pipeline_name, "stage": stage})
        super().__init__(message, "PIPELINE_ERROR", details, 500)


# Model Errors
class ModelError(IPOIntelligenceError):
    """AI/ML model error."""
    
    def __init__(
        self,
        message: str,
        model_name: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["model_name"] = model_name
        super().__init__(message, "MODEL_ERROR", details, 500)


class ModelNotLoadedError(ModelError):
    """Model not loaded."""
    
    def __init__(self, model_name: str):
        super().__init__(
            f"Model {model_name} is not loaded",
            model_name,
            {"reason": "not_loaded"},
        )


class InferenceError(ModelError):
    """Model inference failed."""
    
    def __init__(self, model_name: str, message: str):
        super().__init__(
            f"Inference failed for {model_name}: {message}",
            model_name,
            {"reason": "inference_failed"},
        )


# Vector Database Errors
class VectorDBError(IPOIntelligenceError):
    """Vector database error."""
    
    def __init__(
        self,
        message: str,
        operation: str,
        collection: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["operation"] = operation
        if collection:
            details["collection"] = collection
        super().__init__(message, "VECTOR_DB_ERROR", details, 500)


# Alert Errors
class AlertError(IPOIntelligenceError):
    """Alert/notification error."""
    
    def __init__(self, message: str, alert_type: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["alert_type"] = alert_type
        super().__init__(message, "ALERT_ERROR", details, 500)