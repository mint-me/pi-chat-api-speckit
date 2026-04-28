"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None
_configured_url: str | None = None


def configure_database(database_url: str) -> None:
    """Configure the global async engine and session factory."""
    global SessionLocal, _configured_url, engine
    if _configured_url == database_url and engine is not None and SessionLocal is not None:
        return
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    _configured_url = database_url


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the configured session factory."""
    if SessionLocal is None:
        configure_database(get_settings().database_url)
    assert SessionLocal is not None
    return SessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for FastAPI dependencies."""
    async with get_session_factory()() as session:
        yield session


async def dispose_database() -> None:
    """Dispose the configured engine and clear the globals."""
    global SessionLocal, _configured_url, engine
    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None
    _configured_url = None
