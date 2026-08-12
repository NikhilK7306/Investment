"""Application configuration settings."""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "IPO Intelligence Agent"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    timeout: int = 300

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ipo_intelligence",
        description="PostgreSQL async connection URL",
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    database_echo: bool = False

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_max_connections: int = 50
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    # Vector Database
    vector_db_type: str = "pgvector"  # pgvector, chroma, weaviate, pinecone
    vector_db_url: str = ""
    vector_db_api_key: str = ""
    vector_db_index_name: str = "ipo_embeddings"
    embedding_dimension: int = 3072

    # AI Models
    openai_api_key: str = ""
    openai_organization: str = ""
    openai_default_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-large"

    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-3-5-sonnet-20241022"

    google_ai_api_key: str = ""
    google_ai_default_model: str = "gemini-1.5-pro"

    llama_model_path: str = ""
    llama_n_ctx: int = 8192
    llama_n_gpu_layers: int = -1

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: List[str] = ["json"]
    celery_timezone: str = "UTC"
    celery_enable_utc: bool = True
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 3600
    celery_task_soft_time_limit: int = 3000
    celery_worker_prefetch_multiplier: int = 4
    celery_worker_max_tasks_per_child: int = 1000

    # Prefect
    prefect_api_url: str = ""
    prefect_api_key: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = ""
    log_max_size_mb: int = 100
    log_backup_count: int = 10

    # Security
    secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT secret key",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # File Storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    allowed_extensions: List[str] = [".pdf", ".xlsx", ".csv", ".txt", ".json"]

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True

    # Webhooks
    webhook_secret: str = ""
    webhook_retry_attempts: int = 3
    webhook_timeout_seconds: int = 30

    # External APIs
    sec_edgar_user_agent: str = "IPO Intelligence Agent/1.0"
    alpha_vantage_api_key: str = ""
    yfinance_enabled: bool = True
    openbb_enabled: bool = True

    # News/Sentiment APIs
    newsapi_key: str = ""
    fmp_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    twitter_bearer_token: str = ""

    # Indian IPO Sources
    nse_api_key: str = ""
    bse_api_key: str = ""
    sebi_api_access: str = ""

    # Analysis Settings
    default_analysis_depth: str = "standard"  # standard, deep, comprehensive
    max_concurrent_analyses: int = 10
    analysis_timeout_seconds: int = 300
    scoring_weights: dict = Field(
        default_factory=lambda: {
            "financial_strength": 0.25,
            "growth_potential": 0.25,
            "market_opportunity": 0.20,
            "management_quality": 0.15,
            "risk_level": 0.15,
        }
    )

    # Memory Settings
    short_term_memory_ttl_hours: int = 24
    long_term_memory_retention_days: int = 365
    vector_memory_similarity_threshold: float = 0.75
    max_memory_entries_per_type: int = 10000

    # Reflection Settings
    reflection_enabled: bool = True
    reflection_interval_hours: int = 24
    min_predictions_for_reflection: int = 5
    accuracy_threshold_for_learning: float = 0.6

    # Monitoring
    enable_prometheus: bool = True
    enable_opentelemetry: bool = True
    otel_service_name: str = "ipo-intelligence-agent"
    otlp_endpoint: str = "http://localhost:4317"
    otlp_insecure: bool = True
    prometheus_port: int = 9090

    # LLM Configuration
    default_llm_provider: str = "openai"  # openai, anthropic, google
    openai_default_model: str = "gpt-4o"
    anthropic_default_model: str = "claude-3-5-sonnet-20241022"
    google_ai_default_model: str = "gemini-1.5-pro"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    llm_request_timeout: int = 60
    llm_max_retries: int = 3

    # Features
    enable_discovery_agent: bool = True
    enable_collection_agent: bool = True
    enable_fundamental_agent: bool = True
    enable_market_agent: bool = True
    enable_risk_agent: bool = True
    enable_sentiment_agent: bool = True
    enable_decision_agent: bool = True
    enable_report_agent: bool = True
    enable_memory_agent: bool = True
    enable_reflection_agent: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_testing(self) -> bool:
        return self.app_env.lower() == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()