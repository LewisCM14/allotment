"""
Testing Configuration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.core.database import Base, get_db
from app.main import app

# Use aiosqlite for async SQLite support
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Create async session factory
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db():
    """Override database dependency for testing."""
    async with TestingSessionLocal() as session:
        yield session


# Apply database override
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="module", name="client")
def _client():
    """Creates a FastAPI test client."""
    return TestClient(app)
