"""FastAPI application entry point for IPO Intelligence Agent."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config.settings import get_settings
from app.core.logging.config import configure_logging as setup_logging
from app.core.tracing.config import setup_tracing
from app.core.metrics.prometheus import setup_metrics
from app.infrastructure.database.session import init_database, close_database
from app.presentation.api import ipos, analysis, memory, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    
    # Setup logging
    setup_logging()
    
    # Setup tracing (middleware is set up in create_app)
    if settings.enable_opentelemetry:
        setup_tracing(app=app)
    
    # Initialize database
    init_database()
    
    yield
    
    # Cleanup
    await close_database()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="IPO Intelligence Agent API",
        description="Autonomous multi-agent AI system for IPO investment intelligence",
        version=settings.app_version,
        docs_url=settings.docs_url if not settings.is_production else None,
        redoc_url=settings.redoc_url if not settings.is_production else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup Prometheus metrics
    if settings.enable_prometheus:
        setup_metrics(app, settings)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )
    
    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        from app.infrastructure.database.session import get_database_manager
        db_manager = get_database_manager()
        db_healthy = await db_manager.health_check()
        return {
            "status": "ready" if db_healthy else "not_ready",
            "database": "connected" if db_healthy else "disconnected",
        }
    
    # Include routers
    app.include_router(ipos.router, prefix="/api/v1/ipos", tags=["IPOs"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory & Reflection"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if settings.is_production else 1,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )