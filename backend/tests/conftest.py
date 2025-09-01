import asyncio
import os
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.core.config import settings
from app.api.core.database import Base, get_db
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.models.family.family_model import Family
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.repositories.user.user_repository import UserRepository
from app.main import app
from tests.test_helpers import (
    make_user_allotment,
    make_user_create_schema,
    make_user_feed_day,
    make_user_model,
)

os.environ.setdefault("LOG_TO_FILE", "false")

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
def disable_file_logging():
    """Disable file logging during tests to prevent log file generation."""
    # Store original value
    original_log_to_file = os.environ.get("LOG_TO_FILE")

    # Disable file logging for tests
    os.environ["LOG_TO_FILE"] = "false"

    yield

    # Restore original value
    if original_log_to_file is not None:
        os.environ["LOG_TO_FILE"] = original_log_to_file
    else:
        os.environ.pop("LOG_TO_FILE", None)


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
    try:
        yield
    finally:
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
def prevent_real_emails(monkeypatch):
    """Prevent real emails from being sent during tests by overriding mail config."""
    # Override mail settings to prevent real email sending
    monkeypatch.setenv("MAIL_USERNAME", "test@example.com")
    monkeypatch.setenv("MAIL_PASSWORD", "test_password")

    # Mock the mail client at module level to prevent actual SMTP connections
    # Import inside the function to avoid import order issues
    import app.api.services.email_service

    class MockFastMail:
        async def send_message(self, message):
            # Do nothing - just return successfully
            pass

    monkeypatch.setattr(app.api.services.email_service, "mail_client", MockFastMail())


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
            botanical_group_id=group_id,
            botanical_group_name="testgroup",
            rotate_years=2,
        )
        session.add(group)
        await session.flush()
        # Create a family
        family_id = uuid.uuid4()
        family = Family(
            family_id=family_id,
            family_name="testfamily",
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


@pytest.fixture
async def seed_day_data():
    """Seed the test database with day data."""
    async with TestingSessionLocal() as session:
        days_data = [
            {"day_number": 1, "name": "Mon"},
            {"day_number": 2, "name": "Tue"},
            {"day_number": 3, "name": "Wed"},
            {"day_number": 4, "name": "Thu"},
            {"day_number": 5, "name": "Fri"},
            {"day_number": 6, "name": "Sat"},
            {"day_number": 7, "name": "Sun"},
        ]

        created_days = []
        for day_data in days_data:
            day_id = uuid.uuid4()
            day = Day(
                day_id=day_id,
                day_number=day_data["day_number"],
                day_name=day_data["name"],
            )
            session.add(day)
            created_days.append(
                {
                    "id": day_id,
                    "day_number": day_data["day_number"],
                    "name": day_data["name"],
                }
            )

        await session.commit()
        yield created_days


@pytest.fixture
async def seed_feed_data():
    """Seed the test database with feed data."""
    async with TestingSessionLocal() as session:
        feeds_data = [
            "Tomato Feed",
            "General Purpose Feed",
            "Organic Compost",
            "Liquid Fertilizer",
            "Bone Meal",
        ]

        created_feeds = []
        for feed_name in feeds_data:
            feed_id = uuid.uuid4()
            feed = Feed(
                feed_id=feed_id,
                feed_name=feed_name,
            )
            session.add(feed)
            created_feeds.append(
                {
                    "id": feed_id,
                    "name": feed_name,
                }
            )

        await session.commit()
        yield created_feeds


@pytest.fixture
async def seed_grow_guide_data(seed_day_data, seed_feed_data):
    """Seed the test database with both day and feed data."""
    yield {
        "days": seed_day_data,
        "feeds": seed_feed_data,
    }


@pytest.fixture
async def complete_family_seed_data():
    """Seed comprehensive family data with relationships."""
    async with TestingSessionLocal() as session:
        # Create multiple botanical groups
        groups_data = [
            {"name": "Brassicas", "rotation_years": 3},
            {"name": "Legumes", "rotation_years": 2},
            {"name": "Solanaceae", "rotation_years": 4},
        ]

        created_groups = []
        created_families = []

        for group_data in groups_data:
            group_id = uuid.uuid4()
            group = BotanicalGroup(
                botanical_group_id=group_id,
                botanical_group_name=group_data["name"],
                rotate_years=group_data["rotation_years"],
            )
            session.add(group)
            created_groups.append(
                {
                    "id": group_id,
                    "name": group_data["name"],
                    "recommended_rotation_years": group_data["rotation_years"],
                }
            )

            # Add families for each group
            families_per_group = {
                "Brassicas": ["Cabbage", "Broccoli", "Kale"],
                "Legumes": ["Peas", "Beans", "Lentils"],
                "Solanaceae": ["Tomatoes", "Peppers", "Eggplant"],
            }

            for family_name in families_per_group.get(group_data["name"], []):
                family_id = uuid.uuid4()
                family = Family(
                    family_id=family_id,
                    family_name=family_name,
                    botanical_group_id=group_id,
                )
                session.add(family)
                created_families.append(
                    {
                        "id": family_id,
                        "name": family_name,
                        "botanical_group_id": group_id,
                        "botanical_group_name": group_data["name"],
                    }
                )

        await session.commit()
        yield {
            "botanical_groups": created_groups,
            "families": created_families,
        }


@pytest.fixture
async def user_in_database(sample_user_data):
    """Create a user directly in the database without going through API."""
    import uuid
    from datetime import datetime, timezone

    from app.api.core.auth_utils import hash_password
    from app.api.models.user.user_model import User

    async with TestingSessionLocal() as session:
        user_id = uuid.uuid4()
        hashed_password = hash_password(sample_user_data["user_password"])

        user = User(
            user_id=user_id,
            user_email=sample_user_data["user_email"],
            user_password=hashed_password,
            user_first_name=sample_user_data["user_first_name"],
            user_country_code=sample_user_data["user_country_code"],
            is_email_verified=False,
            registered_date=datetime.now(timezone.utc),
            last_active_date=datetime.now(timezone.utc),
        )

        session.add(user)
        await session.commit()

        user_data = {
            "user_id": str(user_id),
            "user_email": sample_user_data["user_email"],
            "user_first_name": sample_user_data["user_first_name"],
            "user_country_code": sample_user_data["user_country_code"],
            "is_email_verified": False,
        }
        user_data.update(sample_user_data)  # Include password for login tests
        yield user_data


@pytest.fixture
async def verified_user_in_database(user_in_database):
    """Create a verified user directly in the database."""
    from sqlalchemy import update

    from app.api.models.user.user_model import User

    async with TestingSessionLocal() as session:
        # Update the user to be verified
        await session.execute(
            update(User)
            .where(User.user_id == user_in_database["user_id"])
            .values(is_email_verified=True)
        )
        await session.commit()

        user_data = user_in_database.copy()
        user_data["is_email_verified"] = True
        yield user_data


@pytest.fixture
def sample_user_data():
    """Standard user data for testing."""
    return {
        "user_email": "test@example.com",
        "user_password": "TestPass123!@",
        "user_first_name": "Test",
        "user_country_code": "GB",
    }


@pytest.fixture
def sample_user_data_variant():
    """Alternative user data for testing multiple users."""
    return {
        "user_email": "test2@example.com",
        "user_password": "TestPass123!@",
        "user_first_name": "TestUser",
        "user_country_code": "US",
    }


@pytest.fixture
async def registered_user(client, mocker, sample_user_data):
    """Create and return a registered user with tokens."""
    # Mock email service to prevent actual emails
    mock_email_service(mocker, "app.api.v1.registration.send_verification_email")

    response = await client.post(
        f"{settings.API_PREFIX}/registration",
        json=sample_user_data,
    )
    assert response.status_code == status.HTTP_201_CREATED

    user_data = response.json()
    user_data.update(sample_user_data)  # Include original data
    return user_data


@pytest.fixture
def mock_user():
    """Create a mock user object for unit testing."""
    import uuid
    from unittest.mock import MagicMock

    mock_user = MagicMock()
    mock_user.user_id = uuid.uuid4()
    mock_user.user_email = "test@example.com"
    mock_user.user_first_name = "Test"
    mock_user.user_country_code = "GB"
    mock_user.is_email_verified = True
    return mock_user


@pytest.fixture
def auth_headers(mock_user):
    """Generate authorization headers for API requests."""
    from app.api.core.auth_utils import create_token

    token = create_token(str(mock_user.user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def api_endpoints():
    """Common API endpoint paths."""
    return {
        "auth": f"{settings.API_PREFIX}/auth",
        "users": f"{settings.API_PREFIX}/users",
        "registration": f"{settings.API_PREFIX}/registration",
        "families": f"{settings.API_PREFIX}/families",
        "health": f"{settings.API_PREFIX}/health",
        "user_preferences": f"{settings.API_PREFIX}/user-preferences",
        "user_allotments": f"{settings.API_PREFIX}/user-allotments",
    }


@pytest.fixture
def token_factory():
    """Factory for creating various types of tokens."""
    import uuid

    from app.api.core.auth_utils import create_token

    def _create_token(token_type="access", user_id=None):
        if user_id is None:
            user_id = str(uuid.uuid4())
        return create_token(user_id=user_id, token_type=token_type)

    return _create_token


@pytest.fixture
def mock_uow_factory():
    """Factory for creating mocked Unit of Work instances."""

    def _create_mock_uow(mocker, uow_path, methods=None):
        mock_uow = mocker.AsyncMock()

        if methods:
            for method_name, return_value in methods.items():
                if callable(return_value):
                    setattr(
                        mock_uow,
                        method_name,
                        mocker.AsyncMock(side_effect=return_value),
                    )
                else:
                    setattr(
                        mock_uow,
                        method_name,
                        mocker.AsyncMock(return_value=return_value),
                    )

        mock_uow_class = mocker.patch(uow_path)
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        return mock_uow

    return _create_mock_uow


@pytest.fixture
def mock_request_and_db(mocker):
    """Create standardized mock Request and AsyncSession objects for unit tests."""
    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession

    return {
        "request": mocker.MagicMock(spec=Request),
        "db": mocker.MagicMock(spec=AsyncSession),
    }


@pytest.fixture
def standard_unit_mocks(mocker):
    """Set up standard mocks for unit tests that don't need external dependencies."""
    mocks = {}

    # Mock logging and timing
    mocks["log_timing"] = mocker.patch("app.api.v1.auth.log_timing")
    mocks["logger"] = mocker.patch("app.api.v1.auth.logger")

    # Mock request context
    mock_ctx = mocker.MagicMock()
    mock_ctx.get.return_value = "test-request-id"
    mocks["request_ctx"] = mocker.patch("app.api.v1.auth.request_id_ctx_var", mock_ctx)

    # Mock safe_operation context manager
    mock_safe_operation = mocker.patch(
        "app.api.middleware.error_handler.safe_operation"
    )
    mock_safe_operation.return_value.__aenter__.return_value = None
    mock_safe_operation.return_value.__aexit__.return_value = False
    mocks["safe_operation"] = mock_safe_operation

    return mocks


@pytest.fixture
def mock_email_in_unit_test(mocker):
    """Mock email service for unit tests."""
    return mocker.patch("app.api.v1.registration.send_verification_email")


@pytest.fixture
def mock_token_creation(mocker):
    """Mock token creation functions."""
    return mocker.patch(
        "app.api.v1.auth.create_token", side_effect=["access_token", "refresh_token"]
    )


@pytest.fixture
def sample_user_login_data():
    """Standard login data for auth unit tests."""
    return {"user_email": "test@example.com", "user_password": "SecurePass123!"}


@pytest.fixture
def user_payload_factory(sample_user_data):
    """Factory to build a registration payload with optional overrides and unique email."""
    import uuid as _uuid

    def _build(**overrides):
        payload = sample_user_data.copy()
        # ensure uniqueness unless caller provides explicit email
        if "user_email" not in overrides:
            payload["user_email"] = f"{_uuid.uuid4().hex[:8]}@example.com"
        payload.update(overrides)
        return payload

    return _build


@pytest.fixture
def login_helper(client):
    """Helper to perform login and return the raw response."""

    async def _login(email: str, password: str):
        return await client.post(
            f"{settings.API_PREFIX}/auth/token",
            json={"user_email": email, "user_password": password},
        )

    return _login


@pytest.fixture
def user_factory(client, mocker, user_payload_factory):
    """Async factory to register a user (mocking email) and return the response."""

    async def _create(payload=None):
        if payload is None:
            payload = user_payload_factory()
        # mock email each call (idempotent)
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        return await client.post(f"{settings.API_PREFIX}/registration", json=payload)

    return _create


@pytest.fixture
def tokens_factory(user_factory, login_helper):
    """Provision user then login; returns (registration_json, login_json)."""

    async def _provision(payload=None):
        reg_resp = await user_factory(payload)
        assert reg_resp.status_code == 201
        reg_json = reg_resp.json()
        pwd = payload["user_password"] if payload else "TestPass123!@"
        login_resp = await login_helper(reg_json["user_email"], pwd)
        assert login_resp.status_code == 200
        return reg_json, login_resp.json()

    return _provision


@pytest.fixture
def register_user(client, mocker):
    """Return an async factory that registers a user and yields Authorization headers.

    Args:
        prefix: Optional string to prefix the generated unique email for readability.

    Returns:
        async function(prefix:str="user") -> dict  (Authorization header)
    """

    async def _register(prefix: str = "user") -> dict:
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "user_email": email,
            "user_password": "SecurePass123!",
            "user_first_name": "TestUser",
            "user_country_code": "US",
        }
        resp = await client.post(f"{settings.API_PREFIX}/registration", json=payload)
        assert resp.status_code == status.HTTP_201_CREATED
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _register


@pytest.fixture
def suppress_logging(monkeypatch):
    """Suppress structlog output for noisy error-path tests by replacing get_logger."""
    import structlog as _structlog

    real_get = _structlog.get_logger
    monkeypatch.setattr(
        _structlog, "get_logger", lambda *a, **k: real_get("test-suppressed")
    )
    yield
    monkeypatch.setattr(_structlog, "get_logger", real_get)


@pytest.fixture
def reset_health_state():
    """Reset internal health module resource state before & after a test."""
    import app.api.v1.health as health_mod

    orig = health_mod._previous_resources_state.copy()
    health_mod._previous_resources_state = {k: False for k in orig.keys()}
    # Run test
    yield
    # Restore original state
    health_mod._previous_resources_state = {k: False for k in orig.keys()}


@pytest.fixture
def mock_db():
    """Provide an AsyncSession mock for repository/unit tests that don't hit the DB."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_db):
    """Instantiate UserRepository bound to mocked DB session."""
    return UserRepository(db=mock_db)


@pytest.fixture
def sample_user():
    """Real User model instance (unpersisted) for unit tests."""
    return make_user_model(
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        country_code="US",
    )


@pytest.fixture
def sample_allotment():
    """Real UserAllotment model instance (unpersisted)."""
    return make_user_allotment(postal_code="12345", width=10.0, length=10.0)


@pytest.fixture
def sample_user_feed_day():
    """UserFeedDay linking a feed/day for preference tests (unpersisted)."""
    return make_user_feed_day(feed_name="tomato feed", day_name="mon", day_number=1)


@pytest.fixture
def sample_user_create():
    """UserCreate schema instance for user creation/unit tests."""
    return make_user_create_schema(
        email="test@example.com",
        password="test_password",
        first_name="Test",
        country_code="US",
    )
