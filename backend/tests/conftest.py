import asyncio
import os
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient
from resend import exceptions as resend_exceptions
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.core.config import settings
from app.api.core.database import Base, get_db
from app.api.models.enums import LifecycleType
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.models.family.family_model import Family
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.repositories.user.user_repository import UserRepository
from app.api.services import email_service
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
    """Prevent real emails from being sent during tests."""
    # Override mail settings
    monkeypatch.setenv("RESEND_API_KEY_SEND", "re_test_key_1234567890")
    monkeypatch.setenv("MAIL_FROM", "test@resend.dev")

    # Mock Resend API
    class MockResendEmails:
        @staticmethod
        def send(params):
            return {"id": "test-email-id-12345"}

    class MockResend:
        Emails = MockResendEmails
        exceptions = resend_exceptions

    monkeypatch.setattr(email_service, "resend", MockResend)


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
            {"name": "brassicas", "rotation_years": 3},
            {"name": "legumes", "rotation_years": 2},
            {"name": "solanaceae", "rotation_years": 4},
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
                "brassicas": ["cabbage", "broccoli", "kale"],
                "legumes": ["peas", "beans", "lentils"],
                "solanaceae": ["tomatoes", "peppers", "eggplant"],
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

    from app.api.models.user.user_model import User

    async with TestingSessionLocal() as session:
        user_id = uuid.uuid4()

        user = User(
            user_id=user_id,
            user_email=sample_user_data["user_email"],
            user_password_hash="dummy_hash",  # Will be set properly below
            user_first_name=sample_user_data["user_first_name"],
            user_country_code=sample_user_data["user_country_code"],
            is_email_verified=False,
            registered_date=datetime.now(timezone.utc),
            last_active_date=datetime.now(timezone.utc),
        )

        # Use the model's set_password method to properly hash the password
        user.set_password(sample_user_data["user_password"])

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
async def integration_auth_headers(user_in_database):
    """Generate authorization headers for integration tests with a real user in database."""
    import uuid

    from app.api.core.auth_utils import create_token

    # Convert the string UUID to UUID object and back to hex format for token
    user_uuid = uuid.UUID(user_in_database["user_id"])
    token = create_token(user_uuid.hex)  # Use hex format (no dashes) for token
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


@pytest.fixture
async def seed_lifecycle_data():
    """Seed the test database with lifecycle data."""
    from app.api.models.grow_guide.guide_options_model import Lifecycle

    async with TestingSessionLocal() as session:
        lifecycles_data = [
            {"name": LifecycleType.ANNUAL, "productivity_years": 1},
            {"name": LifecycleType.BIENNIAL, "productivity_years": 2},
            {"name": LifecycleType.PERENNIAL, "productivity_years": 10},
        ]

        created_lifecycles = []
        for lifecycle_data in lifecycles_data:
            lifecycle_id = uuid.uuid4()
            lifecycle = Lifecycle(
                lifecycle_id=lifecycle_id,
                lifecycle_name=lifecycle_data["name"],
                productivity_years=lifecycle_data["productivity_years"],
            )
            session.add(lifecycle)
            created_lifecycles.append(
                {
                    "id": lifecycle_id,
                    "name": lifecycle_data["name"],
                    "productivity_years": lifecycle_data["productivity_years"],
                }
            )

        await session.commit()
        yield created_lifecycles


@pytest.fixture
async def seed_planting_conditions_data():
    """Seed the test database with planting conditions data."""
    from app.api.models.grow_guide.guide_options_model import PlantingConditions

    async with TestingSessionLocal() as session:
        conditions_data = [
            "Full Sun",
            "Partial Shade",
            "Full Shade",
            "Sheltered",
        ]

        created_conditions = []
        for condition_name in conditions_data:
            condition_id = uuid.uuid4()
            condition = PlantingConditions(
                planting_condition_id=condition_id,
                planting_condition=condition_name,
            )
            session.add(condition)
            created_conditions.append(
                {
                    "id": condition_id,
                    "name": condition_name,
                }
            )

        await session.commit()
        yield created_conditions


@pytest.fixture
async def seed_frequency_data(seed_day_data):
    """Seed the test database with frequency data and default watering day mappings.

    Depends on day data so we can create FrequencyDefaultDay rows for deterministic tests.
    Daily -> all days
    Weekly -> Sunday only
    Monthly -> Sunday only (placeholder until monthly logic is defined)
    """
    from app.api.models.grow_guide.guide_options_model import (
        Frequency,
        FrequencyDefaultDay,
    )

    async with TestingSessionLocal() as session:
        frequencies_data = [
            {"name": "Daily", "days_per_year": 365},
            {"name": "Weekly", "days_per_year": 52},
            {"name": "Monthly", "days_per_year": 12},
        ]

        created_frequencies = []
        frequency_id_map = {}
        for freq_data in frequencies_data:
            freq_id = uuid.uuid4()
            frequency = Frequency(
                frequency_id=freq_id,
                frequency_name=freq_data["name"],
                frequency_days_per_year=freq_data["days_per_year"],
            )
            session.add(frequency)
            created_frequencies.append(
                {
                    "id": freq_id,
                    "name": freq_data["name"],
                    "days_per_year": freq_data["days_per_year"],
                }
            )
            frequency_id_map[freq_data["name"]] = freq_id

        await session.flush()

        # Build default day mappings
        # seed_day_data list ordered Mon..Sun
        day_ids_ordered = [d["id"] for d in seed_day_data]
        daily_id = frequency_id_map["Daily"]
        weekly_id = frequency_id_map["Weekly"]
        monthly_id = frequency_id_map["Monthly"]

        default_rows = []
        # Daily: all 7
        for d_id in day_ids_ordered:
            default_rows.append(FrequencyDefaultDay(frequency_id=daily_id, day_id=d_id))
        # Weekly: Sunday (day_number 7)
        default_rows.append(
            FrequencyDefaultDay(frequency_id=weekly_id, day_id=day_ids_ordered[-1])
        )
        # Monthly: Sunday (placeholder)
        default_rows.append(
            FrequencyDefaultDay(frequency_id=monthly_id, day_id=day_ids_ordered[-1])
        )

        session.add_all(default_rows)
        await session.commit()
        yield created_frequencies


@pytest.fixture
async def seed_week_data():
    """Seed the test database with week data."""
    from app.api.models.grow_guide.calendar_model import Month, Week

    async with TestingSessionLocal() as session:
        # First create some months
        months_data = [
            {"number": 1, "name": "January"},
            {"number": 2, "name": "February"},
            {"number": 12, "name": "December"},
        ]

        created_months = []
        for month_data in months_data:
            month_id = uuid.uuid4()
            month = Month(
                month_id=month_id,
                month_number=month_data["number"],
                month_name=month_data["name"],
            )
            session.add(month)
            created_months.append({"id": month_id, **month_data})

        await session.flush()

        # Create some test weeks
        weeks_data = [
            {
                "number": 1,
                "start_date": "01/01",
                "end_date": "07/01",
                "start_month_id": created_months[0]["id"],
            },
            {
                "number": 2,
                "start_date": "08/01",
                "end_date": "14/01",
                "start_month_id": created_months[0]["id"],
            },
            {
                "number": 52,
                "start_date": "25/12",
                "end_date": "31/12",
                "start_month_id": created_months[2]["id"],
            },
        ]

        created_weeks = []
        for week_data in weeks_data:
            week_id = uuid.uuid4()
            week = Week(
                week_id=week_id,
                week_number=week_data["number"],
                start_month_id=week_data["start_month_id"],
                week_start_date=week_data["start_date"],
                week_end_date=week_data["end_date"],
            )
            session.add(week)
            created_weeks.append(
                {
                    "id": week_id,
                    "number": week_data["number"],
                    "start_date": week_data["start_date"],
                    "end_date": week_data["end_date"],
                }
            )

        await session.commit()
        yield created_weeks


@pytest.fixture(scope="class")
async def authenticated_user():
    """Create an authenticated user for testing."""
    from datetime import datetime, timezone

    from app.api.models.user.user_model import User

    async with TestingSessionLocal() as session:
        user_id = uuid.uuid4()
        # Use a unique email for each test class to avoid conflicts
        unique_email = f"test-{user_id.hex[:8]}@example.com"
        user = User(
            user_id=user_id,
            user_email=unique_email,
            user_password_hash="dummy_hash",  # Will be set properly below
            user_first_name="Test",
            user_country_code="GB",
            is_email_verified=True,
            registered_date=datetime.now(timezone.utc),
            last_active_date=datetime.now(timezone.utc),
        )

        # Use the model's set_password method to properly hash the password
        user.set_password("testpass123")

        session.add(user)
        await session.commit()
        yield user


@pytest.fixture
async def seed_variety_data(
    user_in_database,
    seed_lifecycle_data,
    seed_planting_conditions_data,
    complete_family_seed_data,
    seed_frequency_data,
    seed_week_data,
):
    """Seed the test database with variety data."""
    import uuid

    from app.api.models.grow_guide.variety_model import Variety

    async with TestingSessionLocal() as session:
        variety_id = uuid.uuid4()
        variety = Variety(
            variety_id=variety_id,
            owner_user_id=uuid.UUID(user_in_database["user_id"]),
            variety_name="Test Tomato",
            family_id=complete_family_seed_data["families"][0]["id"],  # Tomato family
            lifecycle_id=seed_lifecycle_data[0]["id"],  # Annual
            sow_week_start_id=seed_week_data[0]["id"],  # Week 1
            sow_week_end_id=seed_week_data[1]["id"],  # Week 2
            planting_conditions_id=seed_planting_conditions_data[0]["id"],  # Full Sun
            soil_ph=6.5,
            plant_depth_cm=2,
            plant_space_cm=30,
            water_frequency_id=seed_frequency_data[0]["id"],  # Daily
            high_temp_degrees=30,
            high_temp_water_frequency_id=seed_frequency_data[0]["id"],  # Daily
            harvest_week_start_id=seed_week_data[1]["id"],  # Week 2
            harvest_week_end_id=seed_week_data[2]["id"],  # Week 3
            is_public=False,
        )
        session.add(variety)
        await session.commit()

        yield {
            "variety_id": variety_id,
            "variety_name": "Test Tomato",
            "owner_user_id": uuid.UUID(user_in_database["user_id"]),
            # Provide nested structures to help tests build payloads without re-querying metadata
            "family": {
                "family_id": str(complete_family_seed_data["families"][0]["id"]),
            },
            "lifecycle": {
                "lifecycle_id": str(seed_lifecycle_data[0]["id"]),
            },
            "sow_week_start_id": str(seed_week_data[0]["id"]),
            "sow_week_end_id": str(seed_week_data[1]["id"]),
            "planting_conditions": {
                "planting_condition_id": str(seed_planting_conditions_data[0]["id"]),
            },
            "soil_ph": 6.5,
            "plant_depth_cm": 2,
            "plant_space_cm": 30,
            "water_frequency": {
                "frequency_id": str(seed_frequency_data[0]["id"]),
            },
            "high_temp_degrees": 30,
            "high_temp_water_frequency": {
                "frequency_id": str(seed_frequency_data[0]["id"]),
            },
            "harvest_week_start_id": str(seed_week_data[1]["id"]),
            "harvest_week_end_id": str(seed_week_data[2]["id"]),
        }


@pytest.fixture
async def seed_public_variety_data(
    seed_lifecycle_data,
    seed_planting_conditions_data,
    complete_family_seed_data,
    seed_frequency_data,
    seed_week_data,
):
    """Seed the test database with public variety data."""
    from datetime import datetime, timezone

    from app.api.models.grow_guide.variety_model import Variety
    from app.api.models.user.user_model import User

    async with TestingSessionLocal() as session:
        # Create a user for the public variety
        user_id = uuid.uuid4()
        user = User(
            user_id=user_id,
            user_email="public@example.com",
            user_password_hash="dummy_hash",  # Will be set properly below
            user_first_name="Public",
            user_country_code="GB",
            is_email_verified=True,
            registered_date=datetime.now(timezone.utc),
            last_active_date=datetime.now(timezone.utc),
        )

        # Use the model's set_password method to properly hash the password
        user.set_password("testpass123")

        session.add(user)

        variety_id = uuid.uuid4()
        variety = Variety(
            variety_id=variety_id,
            owner_user_id=user_id,
            variety_name="Public Tomato",
            family_id=complete_family_seed_data["families"][0]["id"],  # Tomato family
            lifecycle_id=seed_lifecycle_data[0]["id"],  # Annual
            sow_week_start_id=seed_week_data[0]["id"],  # Week 1
            sow_week_end_id=seed_week_data[1]["id"],  # Week 2
            planting_conditions_id=seed_planting_conditions_data[0]["id"],  # Full Sun
            soil_ph=6.5,
            plant_depth_cm=2,
            plant_space_cm=30,
            water_frequency_id=seed_frequency_data[0]["id"],  # Daily
            high_temp_degrees=30,
            high_temp_water_frequency_id=seed_frequency_data[0]["id"],  # Daily
            harvest_week_start_id=seed_week_data[1]["id"],  # Week 2
            harvest_week_end_id=seed_week_data[2]["id"],  # Week 3
            is_public=True,
        )
        session.add(variety)
        await session.commit()

        yield {
            "variety_id": variety_id,
            "variety_name": "Public Tomato",
            "owner_user_id": user_id,
        }
