"""
Test Helper Functions and Utilities
"""

from typing import Any, Dict, Optional


def validate_user_response_schema(user_data: Dict[str, Any]) -> None:
    """Validate that user response data conforms to expected schema."""
    required_fields = [
        "user_id",
        "user_email",
        "user_first_name",
        "user_country_code",
        "is_email_verified",
    ]
    for field in required_fields:
        assert field in user_data, f"Missing required field: {field}"

    assert isinstance(user_data["user_id"], str)
    assert isinstance(user_data["user_email"], str)
    assert isinstance(user_data["user_first_name"], str)
    assert isinstance(user_data["user_country_code"], str)
    assert isinstance(user_data["is_email_verified"], bool)


def validate_token_response_schema(token_data: Dict[str, Any]) -> None:
    """Validate that token response data conforms to expected schema."""
    required_fields = ["access_token", "refresh_token", "token_type"]
    for field in required_fields:
        assert field in token_data, f"Missing required field: {field}"

    assert isinstance(token_data["access_token"], str)
    assert isinstance(token_data["refresh_token"], str)
    assert token_data["token_type"] == "bearer"


def assert_http_error_response(
    response, expected_status: int, expected_message_contains: str = None
):
    """Assert that an HTTP response is an error with expected format."""
    assert response.status_code == expected_status

    if expected_message_contains:
        response_data = response.json()
        if "detail" in response_data and isinstance(response_data["detail"], list):
            error_msg = response_data["detail"][0]["msg"]
            assert expected_message_contains.lower() in error_msg.lower()
        else:
            assert expected_message_contains.lower() in str(response_data).lower()


def build_user_stub(
    mocker,
    user_id: Optional[str] = None,
    first_name: str = "Test",
    verified: bool = False,
):
    """Construct a lightweight user stub object."""
    user = mocker.MagicMock()
    user.user_id = user_id or "11111111-1111-1111-1111-111111111111"
    user.user_first_name = first_name
    user.is_email_verified = verified
    return user


def create_test_user_data(email_suffix: str = "", **overrides) -> Dict[str, Any]:
    """
    Create standardized test user data.

    Args:
        email_suffix: Suffix to add to email for uniqueness
        **overrides: Fields to override in the default data
    """
    base_data = {
        "user_email": f"test{email_suffix}@example.com",
        "user_password": "TestPass123!@",
        "user_first_name": "Test",
        "user_country_code": "GB",
    }
    base_data.update(overrides)
    return base_data


def setup_standard_unit_test_mocks(mocker):
    """
    Set up standard mocks for unit tests that don't need external dependencies.

    Returns:
        Dict containing common mock objects for reuse
    """
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


def create_mock_request_and_db(mocker):
    """Create standardized mock Request and AsyncSession objects."""
    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession

    return {
        "request": mocker.MagicMock(spec=Request),
        "db": mocker.MagicMock(spec=AsyncSession),
    }


def mock_user_uow(
    mocker,
    path: str = "app.api.v1.registration.UserUnitOfWork",
    methods: Optional[Dict[str, Any]] = None,
):
    """Unified helper to patch a UserUnitOfWork (or compatible) and configure async methods.

    Args:
        mocker: pytest-mock fixture
        path: import path to the UoW class
        methods: mapping of method name -> return value or side-effect callable
    Returns:
        The mocked UoW instance (AsyncMock) inside the context manager.
    """
    uow_cls = mocker.patch(path)
    uow = mocker.AsyncMock()
    if methods:
        for name, val in methods.items():
            setattr(
                uow,
                name,
                mocker.AsyncMock(side_effect=val)
                if callable(val)
                else mocker.AsyncMock(return_value=val),
            )
    uow_cls.return_value.__aenter__ = mocker.AsyncMock(return_value=uow)
    uow_cls.return_value.__aexit__ = mocker.AsyncMock(return_value=None)
    return uow


def make_user_model(
    *,
    user_id: Optional[str] = None,
    email: str = "test@example.com",
    password_hash: str = "hashed",
    first_name: str = "Test",
    country_code: str = "GB",
    verified: bool = False,
    registered_date=None,
    last_active_date=None,
):
    """Create a real User model instance for repository/UoW tests."""
    from uuid import UUID, uuid4

    from app.api.models.user.user_model import User

    u = User(
        user_email=email,
        user_password_hash=password_hash,
        user_first_name=first_name,
        user_country_code=country_code,
        is_email_verified=verified,
        registered_date=registered_date,
        last_active_date=last_active_date,
    )
    # If explicit UUID supplied as str, convert; else generate one (User model may auto-set elsewhere)
    if user_id:
        try:
            u.user_id = UUID(str(user_id))
        except Exception:  # noqa: BLE001
            u.user_id = uuid4()
    # Ensure a UUID exists for tests that access user_id before flush
    if getattr(u, "user_id", None) in (None, "None"):
        u.user_id = uuid4()
    return u


def make_user_allotment(
    *,
    user_allotment_id=None,
    user_id=None,
    postal_code: str = "AB12",
    width: float = 5.0,
    length: float = 10.0,
):
    """Create a UserAllotment model instance."""
    from uuid import UUID, uuid4

    from app.api.models.user.user_model import UserAllotment

    allotment = UserAllotment(
        user_allotment_id=UUID(str(user_allotment_id))
        if user_allotment_id
        else uuid4(),
        user_id=UUID(str(user_id)) if user_id else uuid4(),
        allotment_postal_zip_code=postal_code,
        allotment_width_meters=width,
        allotment_length_meters=length,
    )
    return allotment


def make_feed(name: str = "Feed", feed_id=None):
    from uuid import UUID, uuid4

    from app.api.models.grow_guide.guide_options_model import Feed

    f = Feed()
    f.feed_id = UUID(str(feed_id)) if feed_id else uuid4()
    f.feed_name = name
    return f


def make_day(name: str = "Monday", day_number: int = 1, day_id=None):
    from uuid import UUID, uuid4

    from app.api.models.grow_guide.calendar_model import Day

    d = Day()
    d.day_id = UUID(str(day_id)) if day_id else uuid4()
    d.day_name = name
    d.day_number = day_number
    return d


def make_user_feed_day(
    *,
    user_id=None,
    feed=None,
    day=None,
    feed_id=None,
    day_id=None,
    feed_name: str = "Feed",
    day_name: str = "Monday",
    day_number: int = 1,
):
    """Create a UserFeedDay instance with related feed & day objects.

    Args:
        user_id: UUID (str/UUID) for the user; generated if omitted.
        feed / day: Pre-built model objects (overrides id/name params if provided).
        feed_id / day_id: IDs to assign if creating related objects.
        feed_name / day_name / day_number: Attributes for related objects if created.
    """
    from uuid import UUID, uuid4

    from app.api.models.user.user_model import UserFeedDay

    ufd = UserFeedDay(
        user_id=UUID(str(user_id)) if user_id else uuid4(),
        feed_id=UUID(str(feed_id)) if feed_id else uuid4(),
        day_id=UUID(str(day_id)) if day_id else uuid4(),
    )
    # Relationships
    if feed is None:
        feed = make_feed(name=feed_name, feed_id=ufd.feed_id)
    if day is None:
        day = make_day(name=day_name, day_number=day_number, day_id=ufd.day_id)
    ufd.feed = feed
    ufd.day = day
    return ufd


def setup_auth_unit_test_mocks(
    mocker, mock_uow_path: str = "app.api.v1.auth.UserUnitOfWork"
):
    """Backward compatible thin wrapper pointing to mock_user_uow for auth endpoints."""
    return mock_user_uow(mocker, path=mock_uow_path)


def make_user_create_schema(
    *,
    email: str = "test@example.com",
    password: str = "TestPass123!@",
    first_name: str = "Test",
    country_code: str = "US",
):
    """Return a UserCreate pydantic schema instance.

    Centralized helper so tests avoid duplicating construction logic.
    """
    from app.api.schemas.user.user_schema import UserCreate

    return UserCreate(
        user_email=email,
        user_password=password,
        user_first_name=first_name,
        user_country_code=country_code,
    )


def build_sample_feeds(names: Optional[list[str]] = None):
    """Return a list of Feed model objects.

    Args:
        names: Optional list of feed names; if omitted a default small set is used.
    """
    if names is None:
        names = ["Tomato Feed", "General Feed", "Organic Compost"]
    return [make_feed(name) for name in names]


def build_week_days(names: Optional[list[str]] = None):
    """Return a list representing the 7 days with sequential day_number values."""
    if names is None:
        names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
    return [make_day(name=n, day_number=i + 1) for i, n in enumerate(names)]
