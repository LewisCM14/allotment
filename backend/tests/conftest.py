"""
Testing Configuration
"""

import asyncio
import os
import stat

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.core.config import settings
from app.api.core.database import Base, get_db
from app.main import app

# Use a file-based SQLite database to ensures database is shared between connections
TEST_DB_FILE = os.getenv("TEST_DB_FILE", "/tmp/test_db.sqlite3")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"


# Generate real RSA keys for testing
def generate_test_keys():
    """Generate RSA keys for testing purposes."""
    try:
        # Generate a private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        # Get private key in PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Get public key in PEM format
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem, public_pem
    except Exception as e:
        print(f"Error generating test keys: {e}")
        # Fallback to simple strings that will be mocked
        return b"test-private-key", b"test-public-key"


PRIVATE_KEY, PUBLIC_KEY = generate_test_keys()
settings.PRIVATE_KEY = PRIVATE_KEY
settings.PUBLIC_KEY = PUBLIC_KEY

# Remove test database file if it exists
if os.path.exists(TEST_DB_FILE):
    os.unlink(TEST_DB_FILE)

# Ensure the directory and file have the correct permissions
os.umask(0)
open(TEST_DB_FILE, "a").close()
os.chmod(TEST_DB_FILE, stat.S_IWUSR | stat.S_IRUSR)

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
    """Create tables once at session start and clean up after tests."""
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

    # Drop all tables and dispose of the engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Ensure the test database file is removed
    if os.path.exists(TEST_DB_FILE):
        os.unlink(TEST_DB_FILE)
        print(f"Removed test database file: {TEST_DB_FILE}")


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
