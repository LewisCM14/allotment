import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from authlib.jose.errors import ExpiredTokenError as AuthlibExpiredTokenError
from authlib.jose.errors import JoseError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.api.middleware.error_handler import (
    handle_route_exceptions,
    safe_operation,
    translate_db_exceptions,
    translate_token_exceptions,
    validate_user_exists,
)
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    EmailAlreadyRegisteredError,
    ExpiredTokenError,
    InvalidTokenError,
    UserNotFoundError,
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from app.api.middleware.exception_handler import BaseApplicationError

Base = declarative_base()


class RealUser(Base):
    __tablename__ = "users"
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_email: Mapped[str] = mapped_column()


class DummyBaseApplicationError(BaseApplicationError):
    def __init__(self):
        super().__init__(message="dummy", error_code=123)
        self.status_code = 400
    def __str__(self):
        return "DummyBaseApplicationError"


class TestTranslateDbExceptions:
    @pytest.mark.asyncio
    async def test_translate_db_exceptions_integrity_error(self):
        """Test that IntegrityError is translated to EmailAlreadyRegisteredError."""

        @translate_db_exceptions
        async def mock_db_function():
            raise IntegrityError(
                "(sqlite3.IntegrityError) UNIQUE constraint failed: user.email",
                None,
                None,
            )

        with pytest.raises(EmailAlreadyRegisteredError):
            await mock_db_function()

    @pytest.mark.asyncio
    async def test_translate_db_exceptions_sqlalchemy_error(self):
        """Test that SQLAlchemyError is translated to BusinessLogicError."""

        @translate_db_exceptions
        async def mock_db_function():
            raise SQLAlchemyError("Database error")

        with pytest.raises(BusinessLogicError):
            await mock_db_function()


class TestTranslateTokenExceptions:
    @pytest.mark.asyncio
    async def test_translate_token_exceptions_expired_token(self):
        """Test that AuthlibExpiredTokenError is translated to ExpiredTokenError."""

        @translate_token_exceptions
        async def mock_token_function():
            raise AuthlibExpiredTokenError()

        with pytest.raises(ExpiredTokenError):
            await mock_token_function()

    @pytest.mark.asyncio
    async def test_translate_token_exceptions_jose_error(self):
        """Test that JoseError is translated to InvalidTokenError."""

        @translate_token_exceptions
        async def mock_token_function():
            raise JoseError("Invalid token")

        with pytest.raises(InvalidTokenError):
            await mock_token_function()


class TestSafeOperation:
    @pytest.mark.asyncio
    async def test_safe_operation_handles_exception(self, caplog):
        """Test that safe_operation logs and raises BusinessLogicError."""
        log_context = {"operation": "test_operation"}

        with pytest.raises(BusinessLogicError):
            async with safe_operation("test_operation", log_context):
                raise ValueError("Test error")

        assert "Error during test_operation" in caplog.text

    @pytest.mark.asyncio
    async def test_safe_operation_success(self):
        """Test that safe_operation allows successful operations to complete."""
        log_context = {"operation": "test_operation"}
        result = None

        async with safe_operation("test_operation", log_context):
            result = "success"

        assert result == "success"


@pytest.mark.asyncio
async def test_validate_user_exists_by_email_found():
    user = RealUser(user_id=uuid.uuid4(), user_email="foo@bar.com")
    mock_session = AsyncMock()
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)
    result = await validate_user_exists(mock_session, RealUser, user_email="foo@bar.com")
    assert result is user


@pytest.mark.asyncio
async def test_validate_user_exists_by_email_not_found():
    mock_session = AsyncMock()
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    with pytest.raises(UserNotFoundError):
        await validate_user_exists(mock_session, RealUser, user_email="foo@bar.com")


@pytest.mark.asyncio
async def test_validate_user_exists_by_id_invalid():
    mock_session = AsyncMock()
    with pytest.raises(ValueError):
        await validate_user_exists(mock_session, RealUser, user_id="not-a-uuid")


@pytest.mark.asyncio
async def test_validate_user_exists_no_args():
    mock_session = AsyncMock()
    with pytest.raises(ValueError):
        await validate_user_exists(mock_session, RealUser)


def test_handle_route_exceptions_base_application_error(caplog):
    log_context = {"foo": "bar"}
    error = DummyBaseApplicationError()
    handle_route_exceptions("op", log_context, error)
    assert "op failed: DummyBaseApplicationError" in caplog.text


def test_handle_route_exceptions_other_error(caplog):
    log_context = {"foo": "bar"}
    error = ValueError("fail")
    try:
        handle_route_exceptions("op", log_context, error)
    except BusinessLogicError as e:
        assert str(e) == "An unexpected error occurred"
    else:
        assert False, "BusinessLogicError not raised"
    assert "Unhandled exception during op" in caplog.text
