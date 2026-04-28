"""Shared pytest fixtures."""

import os
from pathlib import Path

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("JWT_SECRET_KEY", "x" * 32)

import pytest
import pytest_asyncio
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import database
from app.database import get_session
from app.logging import configure_logging
from app.main import create_app
from app.models import Base


def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    """Enable foreign key enforcement for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest_asyncio.fixture
async def db_session(tmp_path: Path):
    """Create a fresh SQLite schema for each test."""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite+aiosqlite:///{db_path}"
    database.configure_database(database_url)
    assert database.engine is not None
    event.listen(database.engine.sync_engine, "connect", _set_sqlite_pragma)
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        database.engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await database.dispose_database()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession):
    """Async HTTP client wired to the in-process FastAPI app."""
    configure_logging()
    app = create_app()
    assert database.engine is not None
    session_factory = async_sessionmaker(
        database.engine, expire_on_commit=False, class_=AsyncSession
    )

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mocked_openrouter():
    """Enable respx mocking for OpenRouter tests."""
    with respx.mock(assert_all_called=False) as router:
        yield router
