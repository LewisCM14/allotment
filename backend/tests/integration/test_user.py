import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from app.api.core.auth import create_token
from app.api.core.config import settings
from app.api.factories.user_factory import UserFactoryValidationError
from app.api.middleware.exception_handler import BaseApplicationError
from tests.conftest import mock_email_service

PREFIX = f"{settings.API_PREFIX}/users"


class TestUserRegistration:
    @pytest.mark.asyncio
    async def test_register_user(self, client, mocker):
        """Test user registration endpoint."""
        _mock_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "test@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "John",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        _mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_with_user_creation_failure(self, client, mocker):
        """Test user registration when user creation fails."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = None

        response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "test-fail@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create user" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_register_user_with_no_user_id(self, client, mocker):
        """Test user registration when created user has no user_id."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        mock_user = mocker.MagicMock()
        mock_user.user_id = None
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = False

        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = mock_user

        response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "test-no-id@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create user" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_register_user_handles_general_exception(self, client, mocker):
        """Test user registration handles unexpected exceptions."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.side_effect = Exception("Unexpected database error")

        response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "test-exception@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "An unexpected error occurred during registration"
            in response.json()["detail"][0]["msg"]
        )

    @pytest.mark.asyncio
    async def test_register_user_email_service_failure_with_logging(
        self, client, mocker, caplog
    ):
        """Test that email service failure is properly logged but doesn't break registration."""
        # Mock the email service to fail
        mock_send_email = mocker.patch(
            "app.api.v1.user.send_verification_email",
            side_effect=Exception("Email service unavailable"),
        )

        response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "email-fail@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        # Registration should still succeed even if email fails
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert "user_id" in data

        # Verify email service was called
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_email_service_exception(self, client, mocker):
        """Test user registration when the email service fails."""
        mocker.patch(
            "app.api.v1.user.send_verification_email",
            side_effect=Exception("Email service down"),
        )

        response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "email-service-fail@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        # The user should still be created, and a token returned.
        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_register_user_general_exception(self, client, mocker):
        """Test user registration handles general exceptions during user creation."""
        mocker.patch("app.api.v1.user.send_verification_email")
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.side_effect = Exception("Database is on fire")
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{PREFIX}",
                json={
                    "user_email": "general-exception@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "An unexpected error occurred during registration" in str(
                response.json()
            )

    @pytest.mark.asyncio
    async def test_register_user_creation_returns_none(self, client, mocker):
        """Test user registration when user creation returns None."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.return_value = None
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{PREFIX}",
                json={
                    "user_email": "none-user@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create user" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_register_user_creation_no_user_id(self, client, mocker):
        """Test user registration when created user has no user_id."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        mock_user = MagicMock()
        mock_user.user_id = None
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.return_value = mock_user
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{PREFIX}",
                json={
                    "user_email": "no-id@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create user" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_register_user_base_application_error(self, client, mocker):
        """Test user registration with a BaseApplicationError from the UoW."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.side_effect = BaseApplicationError(
                message="A specific business logic error occurred",
                error_code="TEST_ERROR",
            )
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{PREFIX}",
                json={
                    "user_email": "base-app-error@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "A specific business logic error occurred" in str(response.json())

    @pytest.mark.asyncio
    async def test_register_user_with_email_already_registered(self, client, mocker):
        """Test user registration when email is already registered."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        # Mock database query to return an existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Existing user
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.return_value = mock_result

        response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "existing@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"][0]["msg"]


class TestEmailVerification:
    @pytest.mark.asyncio
    async def test_verify_email(self, client, mocker):
        """Test verifying a user's email."""
        mock_send_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "verify@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Verify",
            "user_country_code": "GB",
        }

        # Register user first
        register_response = await client.post(f"{PREFIX}", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        # Generate a valid JWT token for email verification
        from app.api.core.auth import create_token

        token = create_token(user_id=user_id)

        verify_response = await client.post(f"{PREFIX}/email-verifications/{token}")

        assert verify_response.status_code == status.HTTP_200_OK
        assert verify_response.json()["message"] == "Email verified successfully"

        mock_send_email.assert_called_once_with(
            user_email=user_data["user_email"], user_id=user_id
        )

    @pytest.mark.asyncio
    async def test_verify_email_from_reset_flow(self, client, mocker):
        """Test verifying email with fromReset=true returns specific message."""
        mock_send_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "verify-reset@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "VerifyReset",
            "user_country_code": "GB",
        }
        register_response = await client.post(f"{PREFIX}", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        token = create_token(user_id=user_id, token_type="email_verification")

        verify_response = await client.post(
            f"{PREFIX}/email-verifications/{token}?fromReset=true"
        )

        assert verify_response.status_code == status.HTTP_200_OK
        assert "You can now reset your password" in verify_response.json()["message"]

        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token_format(self, client):
        """Test email verification with malformed JWT token."""
        invalid_token = "invalid.token"

        response = await client.post(f"{PREFIX}/email-verifications/{invalid_token}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification token" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_verify_email_expired_token(self, client, mocker):
        """Test email verification with expired token."""
        mock_jwt_decode = mocker.patch("app.api.v1.user.jwt.decode")
        mock_jwt_decode.side_effect = Exception("Token expired")

        expired_token = "expired.jwt.token"

        response = await client.post(f"{PREFIX}/email-verifications/{expired_token}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification token" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_verify_email_invalid_user(self, client, mocker):
        """Test verifying an email for a non-existent user."""
        mock_send_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        # Create a valid token for a non-existent user ID
        invalid_user_id = "00000000-0000-0000-0000-000000000000"
        invalid_token = create_token(user_id=invalid_user_id)

        response = await client.post(f"{PREFIX}/email-verifications/{invalid_token}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock_send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found_patch(self, client, mocker):
        """Test email verification for non-existent user (patch style)."""
        mocker.patch("app.api.v1.user.jwt.decode", return_value={"sub": "notfound"})
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        from app.api.middleware.exception_handler import UserNotFoundError

        mock_uow_instance.verify_email.side_effect = UserNotFoundError("User not found")
        response = await client.post(f"{PREFIX}/email-verifications/validtoken")
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client, mocker):
        """Test email verification with invalid token (decode error)."""
        mocker.patch(
            "app.api.v1.user.jwt.decode", side_effect=Exception("decode error")
        )
        response = await client.post(f"{PREFIX}/email-verifications/invalidtoken")
        assert response.status_code == 400
        assert "verification token" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_decode_error(self, client, mocker):
        """Test email verification with decode error."""
        mocker.patch(
            "app.api.v1.user.jwt.decode", side_effect=Exception("decode error")
        )
        response = await client.post(f"{PREFIX}/email-verifications/badtoken")
        assert response.status_code == 400
        assert "verification token" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found(self, client, mocker):
        """Test email verification for non-existent user."""
        mocker.patch("app.api.v1.user.jwt.decode", return_value={"sub": "notfound"})
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        from app.api.middleware.exception_handler import UserNotFoundError

        mock_uow_instance.verify_email.side_effect = UserNotFoundError("User not found")
        response = await client.post(f"{PREFIX}/email-verifications/validtoken")
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_request_verification_email_general_exception(self, client, mocker):
        """Test requesting verification email with a general exception."""
        mocker.patch(
            "app.api.v1.user.validate_user_exists",
            return_value=MagicMock(user_id="test-id", is_email_verified=False),
        )
        mocker.patch(
            "app.api.v1.user.send_verification_email",
            side_effect=Exception("Something broke"),
        )

        response = await client.post(
            f"{PREFIX}/email-verifications",
            json={"user_email": "test@example.com"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "Internal server error" in response.text

    @pytest.mark.asyncio
    async def test_request_verification_email_success(self, client, mocker):
        """Test successful verification email request."""
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.is_email_verified = False

        mocker.patch("app.api.v1.user.validate_user_exists", return_value=mock_user)
        mock_send_email = mocker.patch("app.api.v1.user.send_verification_email")

        response = await client.post(
            f"{PREFIX}/email-verifications",
            json={"user_email": "test@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Verification email sent successfully" in response.json()["message"]
        mock_send_email.assert_called_once_with(
            user_email="test@example.com", user_id="test-user-id"
        )


class TestVerificationStatus:
    @pytest.mark.asyncio
    async def test_check_verification_status_success(self, client, mocker):
        """Test checking verification status successfully."""
        mock_user = MagicMock()
        mock_user.user_id = "test-user-id"
        mock_user.is_email_verified = True

        mocker.patch("app.api.v1.user.validate_user_exists", return_value=mock_user)

        response = await client.get(
            f"{PREFIX}/verification-status", params={"user_email": "test@example.com"}
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
            f"{PREFIX}/password-resets",
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

        mock_send_email = mocker.patch("app.api.v1.user.send_verification_email")

        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "unverified@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "verification email has been sent" in response.json()["message"]
        mock_send_email.assert_called_once_with(
            user_email="unverified@example.com", user_id="test-user-id", from_reset=True
        )

    @pytest.mark.asyncio
    async def test_verify_email_from_password_reset_query_param(self, client, mocker):
        """Test email verification with fromReset query parameter."""
        mock_send_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "reset-verify@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "ResetVerify",
            "user_country_code": "GB",
        }
        register_response = await client.post(f"{PREFIX}", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        token = create_token(user_id=user_id, token_type="email_verification")

        verify_response = await client.post(
            f"{PREFIX}/email-verifications/{token}?fromReset=true"
        )

        assert verify_response.status_code == status.HTTP_200_OK
        assert "You can now reset your password" in verify_response.json()["message"]

        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_malformed_token(self, client):
        """Test password reset with malformed token."""
        response = await client.post(
            f"{PREFIX}/password-resets/malformed-token",
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
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.request_password_reset.side_effect = Exception("UoW error")

        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "An unexpected error occurred during password reset request"
            in response.json()["detail"][0]["msg"]
        )

    @pytest.mark.asyncio
    async def test_password_reset_user_not_verified(self, client, mocker):
        """Test password reset for user with unverified email."""
        # Create user with unverified email
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        user_data = {
            "user_email": "unverified@example.com",
            "user_password": "TestPass123!@",
            "user_first_name": "Unverified",
            "user_country_code": "GB",
        }
        await client.post(f"{PREFIX}", json=user_data)

        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "unverified@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "verification email has been sent" in response.json()["message"]

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

        mock_send_email = mocker.patch("app.api.v1.user.send_verification_email")

        response = await client.post(
            f"{PREFIX}/password-resets",
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

        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.request_password_reset.return_value = {
            "status": "success",
            "message": "Password reset link sent",
        }

        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Password reset link sent" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, client):
        """Test requesting password reset for non-existent user."""
        response = await client.post(
            f"{PREFIX}/password-resets",
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
            f"{PREFIX}/password-resets",
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
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.return_value = None

        valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

        response = await client.post(
            f"{PREFIX}/password-resets/{valid_token}",
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
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = BaseApplicationError(
                message="Reset failed", status_code=400, error_code="RESET_ERROR"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_reset_password_with_validation_error_logging(self, client, mocker):
        """Test password reset with UserFactoryValidationError logging."""
        # Mock UserUnitOfWork to raise UserFactoryValidationError
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = UserFactoryValidationError(
                field="password", message="Password too weak"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/password-resets/{valid_token}",
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
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = InvalidTokenError(
                "Invalid token"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_reset_password_with_general_exception_logging(self, client, mocker):
        """Test password reset with general exception logging."""
        # Mock UserUnitOfWork to raise general exception
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = Exception("Unexpected error")

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Internal server error" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_reset_password_success_logging(self, client, mocker):
        """Test successful password reset to cover success logging."""
        # Mock UserUnitOfWork to succeed
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.return_value = None  # Success

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/password-resets/{valid_token}",
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

        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.request_password_reset.side_effect = BaseApplicationError(
            message="A base error occurred", error_code="TEST_ERROR"
        )

        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "A base error occurred" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_password_reset_general_exception(self, client, mocker):
        """Test password reset with general exception during token decode."""
        mocker.patch(
            "app.api.core.auth.decode_token", side_effect=Exception("General error")
        )
        response = await client.post(
            f"{PREFIX}/password-resets/faketoken",
            json={"new_password": "NewValidPassword123!@"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Internal server error" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_reset_password_token_decode_exception(self, client, mocker):
        """Test password reset when token decode raises exception."""
        mocker.patch(
            "app.api.core.auth.decode_token",
            side_effect=Exception("Token decode failed"),
        )

        response = await client.post(
            f"{PREFIX}/password-resets/invalid-token",
            json={"new_password": "NewPassword123!"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Internal server error" in response.json()["detail"][0]["msg"]
