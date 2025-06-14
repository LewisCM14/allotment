import pytest
from authlib.jose.errors import ExpiredTokenError as AuthlibExpiredTokenError
from authlib.jose.errors import JoseError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.middleware.error_handler import (
    safe_operation,
    translate_db_exceptions,
    translate_token_exceptions,
)
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    EmailAlreadyRegisteredError,
    ExpiredTokenError,
    InvalidTokenError,
)


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
