"""
Unit tests for registration.py endpoints.
All dependencies are mocked. These tests cover logic, not integration.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
    EmailAlreadyRegisteredError,
    EmailVerificationError,
    InvalidTokenError,
)
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import MessageResponse, UserCreate
from app.api.v1 import registration


@pytest.mark.asyncio
class TestCreateUserEndpointUnit:
    async def test_create_user_success(self, mocker):
        """Test successful user registration."""
        # Mock dependencies
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = False

        # Mock UserUnitOfWork
        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = mock_user

        # Mock email service
        mock_send_email = mocker.patch(
            "app.api.v1.registration.send_verification_email"
        )

        # Mock token creation
        mocker.patch(
            "app.api.v1.registration.create_token",
            side_effect=["access_token", "refresh_token"],
        )

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        # Create test objects
        request = MagicMock(spec=Request)
        user = UserCreate(
            user_email="test@example.com",
            user_password="SecurePass123!",
            user_first_name="Test",
            user_country_code="GB",
        )
        # Mock database session
        db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        db.execute.return_value = mock_result

        # Call the endpoint
        result = await registration.create_user(request, user, db)

        # Assertions
        assert isinstance(result, TokenResponse)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        assert result.user_first_name == "Test"
        assert result.is_email_verified is False
        assert result.user_id == "test-user-id"

        # Verify email service was called
        mock_send_email.assert_called_once_with(
            user_email="test@example.com", user_id="test-user-id"
        )

    async def test_create_user_email_already_exists(self, mocker):
        """Test user registration when email already exists."""
        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        request = MagicMock(spec=Request)
        user = UserCreate(
            user_email="existing@example.com",
            user_password="SecurePass123!",
            user_first_name="Test",
            user_country_code="GB",
        )
        # Mock database session to return existing user
        db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Existing user
        db.execute.return_value = mock_result

        with pytest.raises(EmailAlreadyRegisteredError):
            await registration.create_user(request, user, db)

    async def test_create_user_uow_returns_none(self, mocker):
        """Test user registration when UserUnitOfWork returns None."""
        # Mock UserUnitOfWork to return None
        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = None

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        request = MagicMock(spec=Request)
        user = UserCreate(
            user_email="test@example.com",
            user_password="SecurePass123!",
            user_first_name="Test",
            user_country_code="GB",
        )
        # Mock database session
        db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        db.execute.return_value = mock_result

        with pytest.raises(BusinessLogicError) as exc_info:
            await registration.create_user(request, user, db)

        assert "Failed to create user" in str(exc_info.value)

    async def test_create_user_no_user_id(self, mocker):
        """Test user registration when created user has no user_id."""
        # Mock UserUnitOfWork to return user without user_id
        mock_user = MagicMock()
        mock_user.user_id = None
        mock_user.user_first_name = "Test"

        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = mock_user

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        request = MagicMock(spec=Request)
        user = UserCreate(
            user_email="test@example.com",
            user_password="SecurePass123!",
            user_first_name="Test",
            user_country_code="GB",
        )
        # Mock database session
        db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        db.execute.return_value = mock_result

        with pytest.raises(BusinessLogicError) as exc_info:
            await registration.create_user(request, user, db)

        assert "Failed to create user" in str(exc_info.value)

    async def test_create_user_base_application_error(self, mocker):
        """Test user registration with BaseApplicationError from UoW."""
        # Mock UserUnitOfWork to raise BaseApplicationError
        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.side_effect = BaseApplicationError(
            "Test error", "TEST_ERROR"
        )

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        request = MagicMock(spec=Request)
        user = UserCreate(
            user_email="test@example.com",
            user_password="SecurePass123!",
            user_first_name="Test",
            user_country_code="GB",
        )
        # Mock database session
        db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        db.execute.return_value = mock_result

        with pytest.raises(BaseApplicationError):
            await registration.create_user(request, user, db)

    async def test_create_user_general_exception(self, mocker):
        """Test user registration with general exception."""
        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        request = MagicMock(spec=Request)
        user = UserCreate(
            user_email="test@example.com",
            user_password="SecurePass123!",
            user_first_name="Test",
            user_country_code="GB",
        )
        # Mock database session to raise exception
        db = MagicMock(spec=AsyncSession)
        db.execute.side_effect = Exception("Database error")

        with pytest.raises(BusinessLogicError) as exc_info:
            await registration.create_user(request, user, db)

        assert "An unexpected error occurred during registration" in str(exc_info.value)

    async def test_create_user_email_service_failure(self, mocker):
        """Test user registration continues even when email service fails."""
        # Mock dependencies for successful user creation
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = False

        # Mock UserUnitOfWork
        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = mock_user

        # Mock email service to fail
        mock_send_email = mocker.patch(
            "app.api.v1.registration.send_verification_email",
            side_effect=Exception("Email service down"),
        )

        # Mock token creation
        mocker.patch(
            "app.api.v1.registration.create_token",
            side_effect=["access_token", "refresh_token"],
        )

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        request = MagicMock(spec=Request)
        user = UserCreate(
            user_email="test@example.com",
            user_password="SecurePass123!",
            user_first_name="Test",
            user_country_code="GB",
        )
        # Mock database session
        db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        db.execute.return_value = mock_result

        # Should not raise exception despite email failure
        result = await registration.create_user(request, user, db)

        # Registration should still succeed
        assert isinstance(result, TokenResponse)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"

        # Verify email service was attempted
        mock_send_email.assert_called_once()


@pytest.mark.asyncio
class TestVerifyEmailTokenEndpointUnit:
    async def test_verify_email_success(self, mocker):
        """Test successful email verification."""
        # Mock JWT decode
        mocker.patch(
            "app.api.v1.registration.jwt.decode", return_value={"sub": "test-user-id"}
        )

        # Mock UserUnitOfWork
        mock_user = MagicMock()
        mock_user.user_email = "test@example.com"
        mock_user.is_email_verified = True

        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.verify_email.return_value = mock_user

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.logger")

        db = MagicMock(spec=AsyncSession)

        result = await registration.verify_email_token("valid_token", False, db)

        assert isinstance(result, MessageResponse)
        assert result.message == "Email verified successfully"

    async def test_verify_email_from_reset_flow(self, mocker):
        """Test email verification from password reset flow."""
        # Mock JWT decode
        mocker.patch(
            "app.api.v1.registration.jwt.decode", return_value={"sub": "test-user-id"}
        )

        # Mock UserUnitOfWork
        mock_user = MagicMock()
        mock_user.user_email = "test@example.com"
        mock_user.is_email_verified = True

        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.verify_email.return_value = mock_user

        # Mock password reset email service
        mock_send_reset_email = mocker.patch(
            "app.api.v1.registration.send_password_reset_email"
        )

        # Mock token creation and settings
        mocker.patch("app.api.v1.registration.create_token", return_value="reset_token")
        mocker.patch(
            "app.api.v1.registration.settings.FRONTEND_URL", "http://localhost:3000"
        )

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.log_timing")
        mocker.patch("app.api.v1.registration.logger")

        db = MagicMock(spec=AsyncSession)

        result = await registration.verify_email_token("valid_token", True, db)

        assert isinstance(result, MessageResponse)
        assert "You can now reset your password" in result.message

        # Verify password reset email was sent
        mock_send_reset_email.assert_called_once_with(
            user_email="test@example.com",
            reset_url="http://localhost:3000/reset-password?token=reset_token",
        )

    async def test_verify_email_invalid_token(self, mocker):
        """Test email verification with invalid token."""
        # Mock JWT decode to raise exception
        mocker.patch(
            "app.api.v1.registration.jwt.decode", side_effect=Exception("Invalid token")
        )

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.logger")

        db = MagicMock(spec=AsyncSession)

        with pytest.raises(EmailVerificationError) as exc_info:
            await registration.verify_email_token("invalid_token", False, db)

        assert "Invalid verification token" in str(exc_info.value)

    async def test_verify_email_translate_token_exceptions(self, mocker):
        """Test that token exceptions are properly translated."""
        # Mock JWT decode to raise InvalidTokenError
        mocker.patch(
            "app.api.v1.registration.jwt.decode",
            side_effect=InvalidTokenError("Token error"),
        )

        # Mock context and logging
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "request_id"
        mocker.patch("app.api.v1.registration.request_id_ctx_var", mock_ctx)
        mocker.patch("app.api.v1.registration.logger")

        db = MagicMock(spec=AsyncSession)

        with pytest.raises(EmailVerificationError):
            await registration.verify_email_token("invalid_token", False, db)
