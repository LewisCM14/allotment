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
