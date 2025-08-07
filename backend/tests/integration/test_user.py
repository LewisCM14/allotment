import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from app.api.core.auth_utils import create_token
from app.api.core.config import settings
from app.api.factories.user_factory import UserFactoryValidationError
from app.api.middleware.exception_handler import BaseApplicationError

AUTH_PREFIX = f"{settings.API_PREFIX}/auth"
USER_PREFIX = f"{settings.API_PREFIX}/users"


class TestVerificationStatus:
    @pytest.mark.asyncio
    async def test_check_verification_status_success(self, client, mocker):
        """Test checking verification status successfully."""
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.is_email_verified = True

        mocker.patch("app.api.v1.user.validate_user_exists", return_value=mock_user)

        response = await client.get(
            f"{USER_PREFIX}/verification-status",
            params={"user_email": "test@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_email_verified"] is True
        assert data["user_id"] == "test-user-id"


class TestPasswordReset:
    @pytest.mark.asyncio
    async def test_password_reset_user_not_found(self, client):
        """Test password reset request when user is not found."""
        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "nonexistent@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            "If your email exists in our system and is verified, you will receive a password reset link shortly."
            in response.json()["message"]
        )

    @pytest.mark.asyncio
    async def test_password_reset_unverified_email(self, client, mocker):
        """Test password reset for unverified email."""
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "unverified@example.com"
        mock_user.is_email_verified = False

        # Mock database query to return unverified user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.return_value = mock_result

        mock_send_email = mocker.patch("app.api.v1.auth.send_verification_email")

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "unverified@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "verification email has been sent" in response.json()["message"]
        mock_send_email.assert_called_once_with(
            user_email="unverified@example.com", user_id="test-user-id", from_reset=True
        )

    @pytest.mark.asyncio
    async def test_reset_password_malformed_token(self, client):
        """Test password reset with malformed token."""
        response = await client.post(
            f"{AUTH_PREFIX}/password-resets/malformed-token",
            json={"new_password": "NewPassword123!"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Internal server error" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_password_reset_exception_handling(self, client, mocker):
        """Test password reset exception handling in UoW."""
        # Mock database query to return verified user
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "verified@example.com"
        mock_user.is_email_verified = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.return_value = mock_result

        # Mock UoW to raise general exception
        mock_uow = mocker.patch("app.api.v1.auth.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.request_password_reset.side_effect = Exception("UoW error")

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "An unexpected error occurred during password reset request"
            in response.json()["detail"][0]["msg"]
        )

    @pytest.mark.asyncio
    async def test_request_password_reset_unverified(self, client, mocker):
        """Test requesting password reset for unverified user."""
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "unverified@example.com"
        mock_user.is_email_verified = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.return_value = mock_result

        mock_send_email = mocker.patch("app.api.v1.auth.send_verification_email")

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "unverified@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "verification email has been sent" in response.json()["message"]
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_verified(self, client, mocker):
        """Test requesting password reset for verified user."""
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "verified@example.com"
        mock_user.is_email_verified = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.return_value = mock_result

        mock_uow = mocker.patch("app.api.v1.auth.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.request_password_reset.return_value = {
            "status": "success",
            "message": "Password reset link sent",
        }

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Password reset link sent" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, client):
        """Test requesting password reset for non-existent user."""
        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "nonexistent@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            "If your email exists in our system and is verified, you will receive a password reset link shortly."
            in response.json()["message"]
        )

    @pytest.mark.asyncio
    async def test_request_password_reset_handles_exception(self, client, mocker):
        """Test password reset request handles general exceptions."""
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.side_effect = Exception("Database connection failed")

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "test@example.com"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "An unexpected error occurred during password reset request"
            in response.json()["detail"][0]["msg"]
        )

    @pytest.mark.asyncio
    async def test_reset_password_and_login(self, client, mocker):
        """Test successful password reset flow."""
        mock_uow = mocker.patch("app.api.v1.auth.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.return_value = None

        valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets/{valid_token}",
            json={"new_password": "NewPassword123!"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Password has been reset successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_reset_password_with_base_application_error_logging(
        self, client, mocker
    ):
        """Test password reset with BaseApplicationError logging."""
        from app.api.middleware.exception_handler import BaseApplicationError

        # Mock UserUnitOfWork to raise BaseApplicationError
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = BaseApplicationError(
                message="Reset failed", status_code=400, error_code="RESET_ERROR"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{AUTH_PREFIX}/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_reset_password_with_validation_error_logging(self, client, mocker):
        """Test password reset with UserFactoryValidationError logging."""
        # Mock UserUnitOfWork to raise UserFactoryValidationError
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = UserFactoryValidationError(
                field="password", message="Password too weak"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{AUTH_PREFIX}/password-resets/{valid_token}",
                json={"new_password": "weak"},
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_reset_password_with_invalid_token_error_logging(
        self, client, mocker
    ):
        """Test password reset with InvalidTokenError logging."""
        from app.api.middleware.exception_handler import InvalidTokenError

        # Mock UserUnitOfWork to raise InvalidTokenError
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = InvalidTokenError(
                "Invalid token"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{AUTH_PREFIX}/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_reset_password_with_general_exception_logging(self, client, mocker):
        """Test password reset with general exception logging."""
        # Mock UserUnitOfWork to raise general exception
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = Exception("Unexpected error")

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{AUTH_PREFIX}/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Internal server error" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_reset_password_success_logging(self, client, mocker):
        """Test successful password reset to cover success logging."""
        # Mock UserUnitOfWork to succeed
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.return_value = None  # Success

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{AUTH_PREFIX}/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Password has been reset successfully" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_base_application_error(self, client, mocker):
        """Test password reset request with BaseApplicationError."""
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.user_email = "verified@example.com"
        mock_user.is_email_verified = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.return_value = mock_result

        mock_uow = mocker.patch("app.api.v1.auth.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.request_password_reset.side_effect = BaseApplicationError(
            message="A base error occurred", error_code="TEST_ERROR"
        )

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "A base error occurred" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_password_reset_general_exception(self, client, mocker):
        """Test password reset with general exception during token decode."""
        mocker.patch(
            "app.api.core.auth_utils.decode_token",
            side_effect=Exception("General error"),
        )
        response = await client.post(
            f"{AUTH_PREFIX}/password-resets/faketoken",
            json={"new_password": "NewValidPassword123!@"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Internal server error" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_reset_password_token_decode_exception(self, client, mocker):
        """Test password reset when token decode raises exception."""
        mocker.patch(
            "app.api.core.auth_utils.decode_token",
            side_effect=Exception("Token decode failed"),
        )

        response = await client.post(
            f"{AUTH_PREFIX}/password-resets/invalid-token",
            json={"new_password": "NewPassword123!"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Internal server error" in response.json()["detail"][0]["msg"]


class TestUserProfile:
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, client, mocker):
        """Test getting user profile successfully."""
        # Mock the current user from JWT
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()
        mock_user.user_email = "test@example.com"
        mock_user.user_first_name = "Test"
        mock_user.user_country_code = "GB"
        mock_user.is_email_verified = True

        # Mock validate_user_exists at the auth_utils level since get_current_user calls it
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists", return_value=mock_user
        )
        mocker.patch("app.api.v1.user.get_current_user", return_value=mock_user)

        # Create a valid JWT token
        token = create_token(str(mock_user.user_id))

        response = await client.get(
            f"{USER_PREFIX}/profile",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == str(mock_user.user_id)
        assert data["user_email"] == "test@example.com"
        assert data["user_first_name"] == "Test"
        assert data["user_country_code"] == "GB"
        assert data["is_email_verified"] is True

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, client):
        """Test getting user profile without authentication."""
        response = await client.get(f"{USER_PREFIX}/profile")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, client, mocker):
        """Test updating user profile successfully."""
        # Mock the current user from JWT
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()
        mock_user.user_email = "test@example.com"
        mock_user.user_first_name = "Test"
        mock_user.user_country_code = "GB"
        mock_user.is_email_verified = True

        # Mock the updated user from UOW
        mock_updated_user = MagicMock()
        mock_updated_user.user_id = mock_user.user_id
        mock_updated_user.user_email = "test@example.com"
        mock_updated_user.user_first_name = "Updated Name"
        mock_updated_user.user_country_code = "US"
        mock_updated_user.is_email_verified = True

        mocker.patch("app.api.v1.user.get_current_user", return_value=mock_user)

        # Mock validate_user_exists at the auth_utils level since get_current_user calls it
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists", return_value=mock_user
        )

        # Mock the UserUnitOfWork
        mock_uow = AsyncMock()
        mock_uow.update_user_profile = AsyncMock(return_value=mock_updated_user)

        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow_class:
            mock_uow_class.return_value.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_class.return_value.__aexit__ = AsyncMock(return_value=None)

            # Create a valid JWT token
            token = create_token(str(mock_user.user_id))

            response = await client.put(
                f"{USER_PREFIX}/profile",
                json={
                    "user_first_name": "Updated Name",
                    "user_country_code": "US",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["user_id"] == str(mock_user.user_id)
            assert data["user_email"] == "test@example.com"
            assert data["user_first_name"] == "Updated Name"
            assert data["user_country_code"] == "US"
            assert data["is_email_verified"] is True

            # Verify the UOW was called with correct parameters
            mock_uow.update_user_profile.assert_called_once_with(
                user_id=str(mock_user.user_id),
                first_name="Updated Name",
                country_code="US",
            )

    @pytest.mark.asyncio
    async def test_update_user_profile_unauthorized(self, client):
        """Test updating user profile without authentication."""
        response = await client.put(
            f"{USER_PREFIX}/profile",
            json={
                "user_first_name": "Updated Name",
                "user_country_code": "US",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_profile_invalid_data(self, client, mocker):
        """Test updating user profile with invalid data."""
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()

        mocker.patch("app.api.v1.user.get_current_user", return_value=mock_user)

        # Mock validate_user_exists at the auth_utils level since get_current_user calls it
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists", return_value=mock_user
        )

        # Create a valid JWT token
        token = create_token(str(mock_user.user_id))

        response = await client.put(
            f"{USER_PREFIX}/profile",
            json={
                "user_first_name": "X",  # Too short
                "user_country_code": "USA",  # Too long
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_profile_invalid_country_code(self, client, mocker):
        """Test updating user profile with invalid country code only."""
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()

        mocker.patch("app.api.v1.user.get_current_user", return_value=mock_user)
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists", return_value=mock_user
        )

        token = create_token(str(mock_user.user_id))

        # Test with invalid country code (too long)
        response = await client.put(
            f"{USER_PREFIX}/profile",
            json={
                "user_first_name": "ValidName",
                "user_country_code": "USA",  # Should be 2 characters
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_profile_invalid_first_name(self, client, mocker):
        """Test updating user profile with invalid first name only."""
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()

        mocker.patch("app.api.v1.user.get_current_user", return_value=mock_user)
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists", return_value=mock_user
        )

        token = create_token(str(mock_user.user_id))

        # Test with invalid first name (too short)
        response = await client.put(
            f"{USER_PREFIX}/profile",
            json={
                "user_first_name": "A",  # Should be at least 2 characters
                "user_country_code": "US",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_profile_missing_required_fields(self, client, mocker):
        """Test updating user profile with missing required fields."""
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()

        mocker.patch("app.api.v1.user.get_current_user", return_value=mock_user)
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists", return_value=mock_user
        )

        token = create_token(str(mock_user.user_id))

        # Test with missing user_first_name
        response = await client.put(
            f"{USER_PREFIX}/profile",
            json={
                "user_country_code": "US",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test with missing user_country_code
        response = await client.put(
            f"{USER_PREFIX}/profile",
            json={
                "user_first_name": "ValidName",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_update_user_profile_authentication_enforcement(self, client, mocker):
        """Test that users can only update their own profile (authentication enforcement)."""
        mock_user = MagicMock()
        mock_user.user_id = uuid.uuid4()
        mock_user.user_email = "test@example.com"
        mock_user.user_first_name = "John"
        mock_user.user_country_code = "GB"

        # Mock the updated user
        mock_updated_user = MagicMock()
        mock_updated_user.user_id = mock_user.user_id
        mock_updated_user.user_email = "test@example.com"
        mock_updated_user.user_first_name = "Jane"
        mock_updated_user.user_country_code = "US"
        mock_updated_user.is_email_verified = True

        mocker.patch("app.api.v1.user.get_current_user", return_value=mock_user)
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists", return_value=mock_user
        )

        # Mock the UserUnitOfWork
        mock_uow = AsyncMock()
        mock_uow.update_user_profile = AsyncMock(return_value=mock_updated_user)

        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow_class:
            mock_uow_class.return_value.__aenter__ = AsyncMock(return_value=mock_uow)
            mock_uow_class.return_value.__aexit__ = AsyncMock(return_value=None)

            token = create_token(str(mock_user.user_id))

            response = await client.put(
                f"{USER_PREFIX}/profile",
                json={
                    "user_first_name": "Jane",
                    "user_country_code": "US",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify the UOW was called with the user ID from the token (ensuring security)
            mock_uow.update_user_profile.assert_called_once_with(
                user_id=str(
                    mock_user.user_id
                ),  # This ensures only the authenticated user's data is updated
                first_name="Jane",
                country_code="US",
            )
