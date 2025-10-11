"""
    Database connection and session management.

    Production-ready async PostgreSQL setup with:
    - Connection pooling
    - Automatic session cleanup
    - Declarative base for models
    - Dependency injection for FastAPI
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from src.api.core.configs import settings


# Declarative base for all models
class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,  # SQL logging based on environment
    future=True,
    pool_size=10,  # Maximum number of connections in pool
    max_overflow=20,  # Maximum overflow connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using (detect stale connections)
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit (better for async)
    autocommit=False,  # Manual transaction control
    autoflush=False,  # Manual flush control
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
        Dependency for getting async database session.
        Automatically handles:
        - Session creation
        - Transaction management
        - Session cleanup
        - Error handling with rollback
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
        Initialize database - create all tables.
        WARNING: Only for development/testing!
        For production, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db() -> None:
    """
        Drop all tables from database.
        WARNING: Destructive operation! Only for testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def close_db() -> None:
    """
        Close database connection pool.
        Call on application shutdown to gracefully close connections.

        Usage:
            # In FastAPI lifespan
            @asynccontextmanager
            async def lifespan(app: FastAPI):
            yield
            await close_db()  # Cleanup on shutdown
    """
    await engine.dispose()
