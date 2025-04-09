"""
Testing Configuration
"""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.core.database import Base, get_db
from app.main import app

# Use a file-based SQLite database to ensures database is shared between connections
TEST_DB_FILE = "test_db.sqlite3"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

# Remove test database file if it exists
if os.path.exists(TEST_DB_FILE):
    os.unlink(TEST_DB_FILE)

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

# Global variable to store the session across requests
_db_session = None


async def override_get_db():
    """Override database dependency for testing."""
    global _db_session
    if _db_session is None:
        _db_session = TestingSessionLocal()

    try:
        yield _db_session
    except Exception:
        await _db_session.rollback()
        raise


# Apply database override
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop_policy():
    """Return the event loop policy to use in the test session."""
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create tables once at session start."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = result.scalars().all()
        print(f"Created tables: {tables}")

    yield

    # Clean up at the end of all tests
    global _db_session
    if _db_session is not None:
        await _db_session.close()
        _db_session = None

    # Close and remove the test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    if os.path.exists(TEST_DB_FILE):
        os.unlink(TEST_DB_FILE)


@pytest.fixture(scope="function", autouse=True)
async def clear_tables():
    """Clear table data between tests."""
    yield

    global _db_session
    if _db_session is not None:
        async with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())


@pytest.fixture(name="client")
def client_fixture():
    """Create a test client."""
    with TestClient(app) as client:
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
