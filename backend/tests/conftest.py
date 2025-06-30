"""
Testing Configuration
"""

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.core.database import Base, get_db
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.models.family.family_model import Family
from app.main import app

# Use a shared in-memory database with a named URI
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared&uri=true"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# Create a fresh session for each test
async def override_get_db():
    """Override database dependency for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()


# Apply database override
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def event_loop_policy():
    """Configure the event loop policy for all tests."""
    policy = asyncio.get_event_loop_policy()
    return policy


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Set up the test database once for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Clean up after all tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
async def clear_tables():
    """Clear table data between tests."""
    yield

    # Delete all data after each test
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(name="client")
async def client_fixture():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def disable_rate_limits():
    """Disable rate limits for tests."""
    from app.api.core.limiter import limiter

    original_enabled = limiter.enabled
    limiter.enabled = False

    yield

    limiter.enabled = original_enabled


def mock_email_service(mocker, email_service_path: str, success: bool = True):
    """
    Helper function to mock email-sending services.

    Args:
        mocker: The pytest-mock mocker object.
        email_service_path: The import path of the email service to mock.
        success: Whether the mock should simulate a successful email send.

    Returns:
        The mocked email service.
    """
    mock_send = mocker.patch(email_service_path)
    if success:
        mock_send.return_value = {"message": "Verification email sent successfully"}
    else:
        mock_send.side_effect = Exception("SMTP connection failed")
    return mock_send


@pytest.fixture
async def seed_family_data():
    """Seed the test database with a botanical group and a family."""
    async with TestingSessionLocal() as session:
        # Create a botanical group
        group_id = uuid.uuid4()
        group = BotanicalGroup(
            id=group_id,
            name="testgroup",
            recommended_rotation_years=2,
        )
        session.add(group)
        await session.flush()
        # Create a family
        family_id = uuid.uuid4()
        family = Family(
            id=family_id,
            name="testfamily",
            botanical_group_id=group_id,
        )
        session.add(family)
        await session.commit()
        yield {
            "botanical_group_id": group_id,
            "family_id": family_id,
            "group_name": "testgroup",
            "family_name": "testfamily",
        }
