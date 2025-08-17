from unittest.mock import MagicMock

import pytest

from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
    EmailAlreadyRegisteredError,
    EmailVerificationError,
)
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import MessageResponse, UserCreate
from app.api.v1 import registration
from tests.test_helpers import validate_token_response_schema


@pytest.mark.asyncio
class TestCreateUserEndpointUnit:
    async def test_create_user_success(
        self,
        mock_user,
        sample_user_data,
        mock_request_and_db,
        mock_email_in_unit_test,
        mock_token_creation,
        mocker,
    ):
        """Test successful user registration using standardized fixtures."""
        # Mock UserUnitOfWork to return our mock user
        mock_uow = mocker.AsyncMock()
        mock_uow.create_user.return_value = mock_user

        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        # Mock token creation for registration
        mocker.patch(
            "app.api.v1.registration.create_token",
            side_effect=["access_token", "refresh_token"],
        )

        # Create test objects
        user = UserCreate(**sample_user_data)

        # Mock database session to show no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        mock_request_and_db["db"].execute.return_value = mock_result

        # Call the endpoint
        result = await registration.create_user(
            mock_request_and_db["request"], user, mock_request_and_db["db"]
        )

        # Assertions using helper functions
        assert isinstance(result, TokenResponse)
        validate_token_response_schema(result.model_dump())
        assert result.user_first_name == mock_user.user_first_name
        assert result.is_email_verified == mock_user.is_email_verified
        assert result.user_id == str(mock_user.user_id)

        # Verify email service was called
        mock_email_in_unit_test.assert_called_once_with(
            user_email=sample_user_data["user_email"], user_id=str(mock_user.user_id)
        )

    async def test_create_user_email_already_exists(
        self, sample_user_data, mock_request_and_db, mocker
    ):
        """Test user registration when email already exists."""
        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        user = UserCreate(**sample_user_data)

        # Mock database session to return existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Existing user
        mock_request_and_db["db"].execute.return_value = mock_result

        with pytest.raises(EmailAlreadyRegisteredError):
            await registration.create_user(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

    async def test_create_user_uow_returns_none(
        self, sample_user_data, mock_request_and_db, mocker
    ):
        """Test user registration when UserUnitOfWork returns None."""
        # Mock UserUnitOfWork to return None
        mock_uow = mocker.AsyncMock()
        mock_uow.create_user.return_value = None

        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        user = UserCreate(**sample_user_data)

        # Mock database session to show no existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_request_and_db["db"].execute.return_value = mock_result

        with pytest.raises(BusinessLogicError) as exc_info:
            await registration.create_user(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

        assert "Failed to create user" in str(exc_info.value)

    async def test_create_user_no_user_id(
        self, sample_user_data, mock_request_and_db, mocker
    ):
        """Test user registration when created user has no user_id."""
        # Create a mock user without user_id
        mock_user = MagicMock()
        mock_user.user_id = None
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = False

        # Mock UserUnitOfWork to return user without ID
        mock_uow = mocker.AsyncMock()
        mock_uow.create_user.return_value = mock_user

        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        user = UserCreate(**sample_user_data)

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_request_and_db["db"].execute.return_value = mock_result

        with pytest.raises(BusinessLogicError) as exc_info:
            await registration.create_user(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

        assert "Failed to create user" in str(exc_info.value)

    async def test_create_user_base_application_error(
        self, sample_user_data, mock_request_and_db, mocker
    ):
        """Test user registration with BaseApplicationError from UoW."""
        # Mock UserUnitOfWork to raise BaseApplicationError
        error = BaseApplicationError("User creation failed", "USER_CREATE_ERROR")
        mock_uow = mocker.AsyncMock()
        mock_uow.create_user.side_effect = error

        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        user = UserCreate(**sample_user_data)

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_request_and_db["db"].execute.return_value = mock_result

        with pytest.raises(BaseApplicationError):
            await registration.create_user(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

    async def test_create_user_general_exception(
        self, sample_user_data, mock_request_and_db, mocker
    ):
        """Test user registration with general exception."""
        # Mock UserUnitOfWork to raise general exception
        mock_uow = mocker.AsyncMock()
        mock_uow.create_user.side_effect = Exception("Database connection failed")

        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        user = UserCreate(**sample_user_data)

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_request_and_db["db"].execute.return_value = mock_result

        with pytest.raises(BusinessLogicError) as exc_info:
            await registration.create_user(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

        assert "An unexpected error occurred during registration" in str(exc_info.value)

    async def test_create_user_email_service_failure(
        self, mock_user, sample_user_data, mock_request_and_db, mocker
    ):
        """Test user registration when email service fails."""
        # Mock UserUnitOfWork to succeed
        mock_uow = mocker.AsyncMock()
        mock_uow.create_user.return_value = mock_user

        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)

        # Mock email service to fail
        mocker.patch(
            "app.api.v1.registration.send_verification_email",
            side_effect=Exception("Email service unavailable"),
        )

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        # Mock token creation
        mocker.patch(
            "app.api.v1.registration.create_token",
            side_effect=["access_token", "refresh_token"],
        )

        user = UserCreate(**sample_user_data)

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_request_and_db["db"].execute.return_value = mock_result

        # Registration should still succeed even if email fails
        result = await registration.create_user(
            mock_request_and_db["request"], user, mock_request_and_db["db"]
        )

        assert isinstance(result, TokenResponse)
        assert result.user_id == str(mock_user.user_id)


@pytest.mark.asyncio
class TestVerifyEmailTokenEndpointUnit:
    async def test_verify_email_success(
        self,
        mock_user,
        token_factory,
        mock_request_and_db,
        mock_email_in_unit_test,
        mocker,
    ):
        """Test successful email verification."""
        verification_token = token_factory(
            token_type="email_verification", user_id=str(mock_user.user_id)
        )
        mocker.patch(
            "app.api.v1.registration.jwt.decode",
            return_value={"sub": str(mock_user.user_id)},
        )
        mock_uow = mocker.AsyncMock()
        mock_uow.verify_email.return_value = mock_user
        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.logger")
        result = await registration.verify_email_token(
            verification_token, from_reset=False, db=mock_request_and_db["db"]
        )
        assert isinstance(result, MessageResponse)
        assert result.message == "Email verified successfully"

    async def test_verify_email_from_reset_flow(
        self, mock_user, token_factory, mock_request_and_db, mocker
    ):
        """Test email verification from password reset flow."""
        verification_token = token_factory(
            token_type="email_verification", user_id=str(mock_user.user_id)
        )
        mocker.patch(
            "app.api.v1.registration.jwt.decode",
            return_value={"sub": str(mock_user.user_id)},
        )
        mock_uow = mocker.AsyncMock()
        mock_uow.verify_email.return_value = mock_user
        mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
        mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)
        mocker.patch("app.api.v1.registration.send_password_reset_email")
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.logger")
        result = await registration.verify_email_token(
            verification_token, from_reset=True, db=mock_request_and_db["db"]
        )
        assert isinstance(result, MessageResponse)
        assert "You can now reset your password" in result.message

    async def test_verify_email_invalid_token(self, mock_request_and_db, mocker):
        invalid_token = "invalid.token.format"
        mocker.patch(
            "app.api.v1.registration.jwt.decode",
            side_effect=Exception("Invalid token format"),
        )
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.logger")
        with pytest.raises(EmailVerificationError):
            await registration.verify_email_token(
                invalid_token, from_reset=False, db=mock_request_and_db["db"]
            )

    async def test_verify_email_translate_token_exceptions(
        self, mock_request_and_db, mocker
    ):
        invalid_token = "expired.token.format"
        from authlib.jose.errors import ExpiredTokenError as AuthlibExpiredTokenError

        mocker.patch(
            "app.api.v1.registration.jwt.decode", side_effect=AuthlibExpiredTokenError()
        )
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "test-request-id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.logger")
        with pytest.raises(EmailVerificationError):
            await registration.verify_email_token(
                invalid_token, from_reset=False, db=mock_request_and_db["db"]
            )
