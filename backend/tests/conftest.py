"""Shared fixtures: API test client backed by in-memory SQLite."""

import asyncio
import os

# Make sure nothing in the app ever touches a real PostgreSQL during tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.session import get_db_session
from app.main import app
from app.models.domain import Base


@pytest.fixture
def api_client():
    """TestClient with the DB dependency overridden to a fresh in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(create_tables())

    async def override_get_db_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        # No context manager: lifespan would touch the real engine
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        asyncio.run(engine.dispose())
