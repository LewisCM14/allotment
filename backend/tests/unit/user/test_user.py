"""
Unit tests for user.py endpoints.
All dependencies are mocked. These tests cover logic, not integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
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
        # Mock UserUnitOfWork
        mock_uow = mocker.AsyncMock()
        mock_uow.send_verification_email_service = mocker.AsyncMock()

        # Mock the context manager
        mocker.patch(
            "app.api.v1.user.UserUnitOfWork",
            return_value=mocker.AsyncMock(
                __aenter__=mocker.AsyncMock(return_value=mock_uow),
                __aexit__=mocker.AsyncMock(return_value=None),
            ),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create request
        request_data = EmailRequest(user_email="test@example.com")

        # Call endpoint
        result = await user.request_verification_email(request_data, mock_db)

        # Assertions
        assert isinstance(result, MessageResponse)
        assert "Verification email sent successfully" in result.message
        mock_uow.send_verification_email_service.assert_called_once_with(
            "test@example.com"
        )

    async def test_request_verification_email_exception(self, mocker):
        """Test verification email request with exception."""
        # Mock UserUnitOfWork to raise an exception
        mock_uow = mocker.AsyncMock()
        mock_uow.send_verification_email_service = mocker.AsyncMock(
            side_effect=Exception("Email service error")
        )

        # Mock the context manager
        mocker.patch(
            "app.api.v1.user.UserUnitOfWork",
            return_value=mocker.AsyncMock(
                __aenter__=mocker.AsyncMock(return_value=mock_uow),
                __aexit__=mocker.AsyncMock(return_value=None),
            ),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create request
        request_data = EmailRequest(user_email="test@example.com")

        # Call endpoint - expect exception to be raised (not caught)
        with pytest.raises(Exception, match="Email service error"):
            await user.request_verification_email(request_data, mock_db)

        mock_uow.send_verification_email_service.assert_called_once_with(
            "test@example.com"
        )

    async def test_check_verification_status_success(self, mocker):
        """Test successful verification status check."""
        # Create mock response
        mock_verification_response = VerificationStatusResponse(
            is_email_verified=True, user_id="test-user-id"
        )

        # Mock UserUnitOfWork
        mock_uow = mocker.AsyncMock()
        mock_uow.get_verification_status_service = mocker.AsyncMock(
            return_value=mock_verification_response
        )

        # Mock the context manager
        mocker.patch(
            "app.api.v1.user.UserUnitOfWork",
            return_value=mocker.AsyncMock(
                __aenter__=mocker.AsyncMock(return_value=mock_uow),
                __aexit__=mocker.AsyncMock(return_value=None),
            ),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Call endpoint
        result = await user.check_verification_status("test@example.com", mock_db)

        # Assertions
        assert isinstance(result, VerificationStatusResponse)
        assert result.is_email_verified is True
        assert result.user_id == "test-user-id"
        mock_uow.get_verification_status_service.assert_called_once_with(
            "test@example.com"
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
        # Mock UserUnitOfWork to raise UserNotFoundError
        mock_uow = mocker.AsyncMock()
        mock_uow.send_verification_email_service = mocker.AsyncMock(
            side_effect=UserNotFoundError("User not found")
        )

        # Mock the context manager
        mocker.patch(
            "app.api.v1.user.UserUnitOfWork",
            return_value=mocker.AsyncMock(
                __aenter__=mocker.AsyncMock(return_value=mock_uow),
                __aexit__=mocker.AsyncMock(return_value=None),
            ),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Create request
        request_data = EmailRequest(user_email="nonexistent@example.com")

        # Call endpoint and expect exception to propagate
        with pytest.raises(UserNotFoundError):
            await user.request_verification_email(request_data, mock_db)

        mock_uow.send_verification_email_service.assert_called_once_with(
            "nonexistent@example.com"
        )

    async def test_check_verification_status_user_not_found(self, mocker):
        """Test verification status check when user not found."""
        # Mock UserUnitOfWork to raise UserNotFoundError
        mock_uow = mocker.AsyncMock()
        mock_uow.get_verification_status_service = mocker.AsyncMock(
            side_effect=UserNotFoundError("User not found")
        )

        # Mock the context manager
        mocker.patch(
            "app.api.v1.user.UserUnitOfWork",
            return_value=mocker.AsyncMock(
                __aenter__=mocker.AsyncMock(return_value=mock_uow),
                __aexit__=mocker.AsyncMock(return_value=None),
            ),
        )

        # Mock database session
        mock_db = mocker.MagicMock(spec=AsyncSession)

        # Call endpoint and expect exception to propagate
        with pytest.raises(UserNotFoundError):
            await user.check_verification_status("nonexistent@example.com", mock_db)

        mock_uow.get_verification_status_service.assert_called_once_with(
            "nonexistent@example.com"
        )

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
