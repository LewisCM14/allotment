"""
Unit tests for user.py endpoints.
All dependencies are mocked. These tests cover logic, not integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.exception_handler import (
    BaseApplicationError,
    UserNotFoundError,
)
from app.api.schemas.user.user_schema import (
    EmailRequest,
    MessageResponse,
    UserProfileResponse,
    UserProfileUpdate,
    VerificationStatusResponse,
)
from app.api.v1 import user


@pytest.mark.asyncio
class TestUserEndpointsUnit:
    """Unit tests for user endpoints with all dependencies mocked."""

    async def test_request_verification_email_success(self, mocker):
        """Test successful verification email request."""
        # Mock dependencies
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "test@example.com"

        # Mock validate_user_exists
        mock_validate = mocker.patch(
            "app.api.v1.user.validate_user_exists", return_value=mock_user
        )

        # Mock email service
        mock_send_email = mocker.patch("app.api.v1.user.send_verification_email")

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create request
        request_data = EmailRequest(user_email="test@example.com")

        # Call endpoint
        result = await user.request_verification_email(request_data, mock_db)

        # Assertions
        assert isinstance(result, MessageResponse)
        assert result.message == "Verification email sent successfully"
        mock_validate.assert_called_once_with(
            db_session=mock_db, user_model=user.User, user_email="test@example.com"
        )
        mock_send_email.assert_called_once_with(
            user_email="test@example.com", user_id="test-user-id"
        )

    async def test_request_verification_email_exception(self, mocker):
        """Test verification email request with exception."""
        # Mock dependencies
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "test@example.com"

        # Mock validate_user_exists
        mock_validate = mocker.patch(
            "app.api.v1.user.validate_user_exists", return_value=mock_user
        )

        # Mock email service to raise exception
        mock_send_email = mocker.patch(
            "app.api.v1.user.send_verification_email",
            side_effect=Exception("Email service error"),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create request
        request_data = EmailRequest(user_email="test@example.com")

        # Call endpoint
        result = await user.request_verification_email(request_data, mock_db)

        # Assertions
        assert isinstance(result, MessageResponse)
        assert result.message == "Internal server error"
        mock_validate.assert_called_once()
        mock_send_email.assert_called_once()

    async def test_check_verification_status_success(self, mocker):
        """Test successful verification status check."""
        # Mock user
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.is_email_verified = True

        # Mock validate_user_exists
        mock_validate = mocker.patch(
            "app.api.v1.user.validate_user_exists", return_value=mock_user
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Call endpoint
        result = await user.check_verification_status("test@example.com", mock_db)

        # Assertions
        assert isinstance(result, VerificationStatusResponse)
        assert result.is_email_verified is True
        assert result.user_id == "test-user-id"
        mock_validate.assert_called_once_with(
            db_session=mock_db, user_model=user.User, user_email="test@example.com"
        )

    async def test_get_user_profile_success(self, mocker):
        """Test successful user profile retrieval."""
        # Mock current user
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "test@example.com"
        mock_user.user_first_name = "Test"
        mock_user.user_country_code = "GB"
        mock_user.is_email_verified = True

        # Call endpoint
        result = await user.get_user_profile(mock_user)

        # Assertions
        assert isinstance(result, UserProfileResponse)
        assert result.user_id == "test-user-id"
        assert result.user_email == "test@example.com"
        assert result.user_first_name == "Test"
        assert result.user_country_code == "GB"
        assert result.is_email_verified is True

    async def test_update_user_profile_success(self, mocker):
        """Test successful user profile update."""
        # Mock current user
        mock_current_user = MagicMock()
        mock_current_user.user_id = "test-user-id"

        # Mock updated user from UOW
        mock_updated_user = MagicMock()
        mock_updated_user.user_id = "test-user-id"
        mock_updated_user.user_email = "test@example.com"
        mock_updated_user.user_first_name = "Updated Name"
        mock_updated_user.user_country_code = "US"
        mock_updated_user.is_email_verified = False

        # Mock UserUnitOfWork
        mock_uow_instance = AsyncMock()
        mock_uow_instance.update_user_profile = AsyncMock(
            return_value=mock_updated_user
        )
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
        mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create update request
        profile_update = UserProfileUpdate(
            user_first_name="Updated Name", user_country_code="US"
        )

        # Call endpoint
        result = await user.update_user_profile(
            profile_update, mock_current_user, mock_db
        )

        # Assertions
        assert isinstance(result, UserProfileResponse)
        assert result.user_id == "test-user-id"
        assert result.user_email == "test@example.com"
        assert result.user_first_name == "Updated Name"
        assert result.user_country_code == "US"
        assert result.is_email_verified is False

        # Verify UOW was called correctly
        mock_uow_instance.update_user_profile.assert_called_once_with(
            user_id="test-user-id", first_name="Updated Name", country_code="US"
        )

    async def test_request_verification_email_user_not_found(self, mocker):
        """Test verification email request when user not found."""
        # Mock validate_user_exists to raise UserNotFoundError
        mock_validate = mocker.patch(
            "app.api.v1.user.validate_user_exists",
            side_effect=UserNotFoundError("User not found"),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create request
        request_data = EmailRequest(user_email="nonexistent@example.com")

        # Call endpoint and expect exception to propagate
        with pytest.raises(UserNotFoundError):
            await user.request_verification_email(request_data, mock_db)

        mock_validate.assert_called_once()

    async def test_check_verification_status_user_not_found(self, mocker):
        """Test verification status check when user not found."""
        # Mock validate_user_exists to raise UserNotFoundError
        mock_validate = mocker.patch(
            "app.api.v1.user.validate_user_exists",
            side_effect=UserNotFoundError("User not found"),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Call endpoint and expect exception to propagate
        with pytest.raises(UserNotFoundError):
            await user.check_verification_status("nonexistent@example.com", mock_db)

        mock_validate.assert_called_once()

    async def test_update_user_profile_uow_error(self, mocker):
        """Test user profile update with UOW error."""
        # Mock current user
        mock_current_user = MagicMock()
        mock_current_user.user_id = "test-user-id"

        # Mock UserUnitOfWork to raise an exception
        mock_uow_instance = AsyncMock()
        mock_uow_instance.update_user_profile = AsyncMock(
            side_effect=BaseApplicationError(
                "Update failed", status_code=400, error_code="UPDATE_ERROR"
            )
        )
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow.return_value.__aenter__ = AsyncMock(return_value=mock_uow_instance)
        mock_uow.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create update request
        profile_update = UserProfileUpdate(
            user_first_name="Updated Name", user_country_code="US"
        )

        # Call endpoint and expect exception to propagate
        with pytest.raises(BaseApplicationError):
            await user.update_user_profile(profile_update, mock_current_user, mock_db)
