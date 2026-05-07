from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()


def ensure_async_pg_url(database_url: str) -> str:
    if "+asyncpg" in database_url:
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return database_url


def sync_database_url_for_scripts(database_url: str) -> str:
    """Strip async driver for sync DDL tooling (Alembic, init scripts)."""
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def create_async_engine_from_settings() -> AsyncEngine:
    return create_async_engine(
        ensure_async_pg_url(settings.database_url),
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=False,
    )


async_engine = create_async_engine_from_settings()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped session; rollback on exceptions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async_engine_for_lifespan = async_engine
