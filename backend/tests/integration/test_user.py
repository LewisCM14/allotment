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
            return_value=MagicMock(is_email_verified=False),
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


class TestPasswordReset:
    @pytest.mark.asyncio
    async def test_password_reset_user_not_found(self, client):
        """Test password reset request when user is not found."""
        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "nonexistent@example.com"},
        )

        # Should return success message even for non-existent users for security
        assert response.status_code == status.HTTP_200_OK
        assert "If your email exists" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_password_reset_unverified_email(self, client, mocker):
        """Test password reset request when user email is not verified."""
        # Register a user (will be unverified by default)
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        register_response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "unverified@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # Mock send_verification_email for the from_reset=True case
        with patch("app.api.v1.user.send_verification_email") as mock_send:
            response = await client.post(
                f"{PREFIX}/password-resets",
                json={"user_email": "unverified@example.com"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Your email is not verified" in response.json()["message"]
            # Verify that verification email was sent with from_reset=True
            mock_send.assert_called_once()
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs.get("from_reset") is True

    @pytest.mark.asyncio
    async def test_verify_email_from_password_reset_query_param(self, client, mocker):
        """Test email verification from password reset flow with query parameter."""
        # Register a user first
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        register_response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "reset-verify@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        user_id = register_response.json()["user_id"]

        # Create a verification token
        verification_token = create_token(user_id=user_id, token_type="verification")

        # Verify email with fromReset=true
        response = await client.post(
            f"{PREFIX}/email-verifications/{verification_token}?fromReset=true",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "You can now reset your password" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_reset_password_malformed_token(self, client):
        """Test password reset with malformed JWT token."""
        response = await client.post(
            f"{PREFIX}/password-resets/invalid-token-format",
            json={"new_password": "NewPassword123!"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_password_reset_exception_handling(self, client, mocker):
        """Test password reset request exception handling."""
        # Register a user first
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        register_response = await client.post(
            f"{PREFIX}",
            json={
                "user_email": "exception-test@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        # Verify the user's email first so we reach the UserUnitOfWork code
        verification_token = create_token(
            user_id=user_id, token_type="email_verification"
        )
        verify_response = await client.post(
            f"{PREFIX}/email-verifications/{verification_token}"
        )
        assert verify_response.status_code == status.HTTP_200_OK

        # Mock UserUnitOfWork to raise an exception
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.request_password_reset.side_effect = Exception(
                "Database error"
            )
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{PREFIX}/password-resets",
                json={"user_email": "exception-test@example.com"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "An unexpected error occurred during password reset request" in str(
                response.json()
            )

    @pytest.mark.asyncio
    async def test_password_reset_user_not_verified(self, client, mocker):
        """Test password reset for user whose email is not verified."""
        mock_user = MagicMock()
        mock_user.is_email_verified = False
        mock_user.user_email = "notverified@example.com"
        mock_user.user_id = 123
        mocker.patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            return_value=MagicMock(scalar_one_or_none=lambda: mock_user),
        )
        mocker.patch("app.api.v1.user.send_verification_email")
        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "notverified@example.com"},
        )
        assert response.status_code == 200
        assert "verification email" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_request_password_reset_unverified(self, client, mocker):
        _mock_verify = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "reset-unverified@example.com",
            "user_password": "TestPass123!@",
            "user_first_name": "NoVerify",
            "user_country_code": "GB",
        }
        register = await client.post(f"{PREFIX}", json=user_data)
        assert register.status_code == status.HTTP_201_CREATED

        # ignore the initial registration call
        _mock_verify.reset_mock()

        # now request reset
        resp = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": user_data["user_email"]},
        )
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert "not verified" in body["message"].lower()
        _mock_verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_verified(self, client, mocker):
        _mock_verify = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "reset-verified@example.com",
            "user_password": "TestPass123!@",
            "user_first_name": "DoVerify",
            "user_country_code": "GB",
        }
        reg = await client.post(f"{PREFIX}", json=user_data)
        user_id = reg.json()["user_id"]
        token = create_token(user_id=user_id, token_type="email_verification")
        verify = await client.post(f"{PREFIX}/email-verifications/{token}")
        assert verify.status_code == status.HTTP_200_OK

        _mock_reset = mock_email_service(
            mocker,
            "app.api.services.user.user_unit_of_work.send_password_reset_email",
        )

        resp = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": user_data["user_email"]},
        )
        assert resp.status_code == status.HTTP_200_OK
        msg = resp.json()["message"].lower()
        assert "password reset link" in msg
        _mock_reset.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, client):
        """Test requesting password reset for non-existent user returns generic message."""
        resp = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "nonexistent@example.com"},
        )
        assert resp.status_code == status.HTTP_200_OK
        msg = resp.json()["message"]
        assert "If your email exists in our system" in msg

    @pytest.mark.asyncio
    async def test_request_password_reset_handles_exception(self, client, mocker):
        """Test password reset request handles unexpected exceptions."""
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.side_effect = Exception("Unexpected database error")

        resp = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "test@example.com"},
        )
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "An unexpected error occurred during password reset request"
            in resp.json()["detail"][0]["msg"]
        )

    @pytest.mark.asyncio
    async def test_reset_password_and_login(self, client, mocker):
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        user_data = {
            "user_email": "do-reset@example.com",
            "user_password": "OldPass123!@",
            "user_first_name": "Reseter",
            "user_country_code": "GB",
        }
        reg = await client.post(f"{PREFIX}", json=user_data)
        user_id = reg.json()["user_id"]
        token_ver = create_token(user_id=user_id, token_type="email_verification")
        await client.post(f"{PREFIX}/email-verifications/{token_ver}")

        reset_token = create_token(user_id=user_id, token_type="reset")
        new_pass = "NewPass456!#"

        resp = await client.post(
            f"{PREFIX}/password-resets/{reset_token}",
            json={"new_password": new_pass},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "has been reset" in resp.json()["message"].lower()
        login = await client.post(
            f"{settings.API_PREFIX}/auth/token",
            json={"user_email": user_data["user_email"], "user_password": new_pass},
        )
        assert login.status_code == status.HTTP_200_OK
        data = login.json()
        assert (
            "access_token" in data
            and data["user_first_name"] == user_data["user_first_name"]
        )

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
        mocker.patch(
            "app.api.v1.user.validate_user_exists",
            side_effect=BaseApplicationError(
                message="A base error occurred", error_code="TEST_ERROR"
            ),
        )
        response = await client.post(
            f"{PREFIX}/password-resets",
            json={"user_email": "test@example.com"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert (
            "If your email exists in our system and is verified, you will receive a password reset link shortly."
            in response.text
        )

    @pytest.mark.asyncio
    async def test_password_reset_general_exception(self, client, mocker):
        mocker.patch(
            "app.api.core.auth.decode_token", side_effect=Exception("General error")
        )
        response = await client.post(
            f"{PREFIX}/password-resets/faketoken",
            json={"new_password": "NewValidPassword123!@"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Internal server error" in response.text
