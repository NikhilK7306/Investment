"""Database configuration and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, pool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config.settings import get_settings
from app.infrastructure.database.models import Base


class DatabaseManager:
    """Manage database connections and sessions."""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._settings = get_settings()
    
    def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._engine is not None:
            return
        
        # Create async engine
        self._engine = create_async_engine(
            self._settings.database_url,
            pool_size=self._settings.database_pool_size,
            max_overflow=self._settings.database_max_overflow,
            pool_timeout=self._settings.database_pool_timeout,
            pool_recycle=self._settings.database_pool_recycle,
            pool_pre_ping=True,
            echo=self._settings.database_echo,
            poolclass=NullPool if self._settings.is_testing else pool.AsyncAdaptedQueuePool,
        )
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        
        # Add event listeners
        self._setup_event_listeners()
    
    def _setup_event_listeners(self) -> None:
        """Setup SQLAlchemy event listeners for monitoring."""
        from app.core.metrics.prometheus import get_metrics_manager
        
        @event.listens_for(self._engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            import time
            conn.info.setdefault('query_start_time', []).append(time.perf_counter())
        
        @event.listens_for(self._engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            import time
            start_times = conn.info.get('query_start_time', [])
            if start_times:
                start_time = start_times.pop()
                duration = time.perf_counter() - start_time
                
                # Determine operation type and table
                operation = statement.strip().split()[0].upper()
                table = "unknown"
                if " " in statement:
                    parts = statement.strip().split()
                    for i, part in enumerate(parts):
                        if part.upper() in ("FROM", "INTO", "UPDATE", "JOIN"):
                            if i + 1 < len(parts):
                                table = parts[i + 1].strip('",\'`')
                                break
                
                metrics = get_metrics_manager()
                metrics.record_db_query(operation, table, duration)
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            self.initialize()
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory."""
        if self._session_factory is None:
            self.initialize()
        return self._session_factory
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if self._session_factory is None:
            self.initialize()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with explicit transaction control."""
        if self._session_factory is None:
            self.initialize()
        
        async with self._session_factory() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception:
            return False


# Global database manager
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    db_manager = get_database_manager()
    async with db_manager.session() as session:
        yield session


@asynccontextmanager
async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database transaction."""
    db_manager = get_database_manager()
    async with db_manager.transaction() as session:
        yield session


# Initialize on import
def init_database() -> None:
    """Initialize database connection."""
    get_database_manager().initialize()


def close_database() -> None:
    """Close database connection."""
    global _db_manager
    if _db_manager:
        import asyncio
        asyncio.create_task(_db_manager.close())
        _db_manager = None