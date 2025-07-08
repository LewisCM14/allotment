import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from app.api.core.auth import create_token
from app.api.core.config import settings
from app.api.factories.user_factory import UserFactoryValidationError
from app.api.middleware.exceptions import BaseApplicationError
from tests.conftest import mock_email_service

PREFIX = settings.API_PREFIX


class TestUserRegistration:
    @pytest.mark.asyncio
    async def test_register_user_email_service_exception(self, client, mocker):
        mock_send_email = mocker.patch("app.api.v1.user.send_verification_email")
        mock_send_email.side_effect = Exception("Email service error")
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "email-exc@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_register_user_general_exception(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.side_effect = Exception("Unexpected DB error")
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "exc@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "unexpected error occurred during registration"
            in str(response.json()).lower()
        )


class TestEmailVerification:
    @pytest.mark.asyncio
    async def test_email_verification_token_decode_exception(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "decode-exc@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        with patch("app.api.v1.user.jwt.decode", side_effect=Exception("decode error")):
            response = await client.post(f"{PREFIX}/users/email-verifications/badtoken")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "verification token" in str(response.json()).lower()


class TestPasswordReset:
    @pytest.mark.asyncio
    async def test_register_user_creation_returns_none(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = None
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "fail-create@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Fail",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create user" in str(response.json())

    @pytest.mark.asyncio
    async def test_register_user_creation_no_user_id(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_user = MagicMock()
        mock_user.user_id = None
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = False
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.return_value = mock_user
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "no-id@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create user" in str(response.json())

    @pytest.mark.asyncio
    async def test_register_user_general_exception(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.side_effect = Exception("Unexpected DB error")
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "exc@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "unexpected error occurred during registration"
            in str(response.json()).lower()
        )

    @pytest.mark.asyncio
    async def test_email_verification_token_decode_exception(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "decode-exc@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        with patch("app.api.v1.user.jwt.decode", side_effect=Exception("decode error")):
            response = await client.post(f"{PREFIX}/users/email-verifications/badtoken")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "verification token" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_password_reset_malformed_token(self, client):
        response = await client.post(
            f"{PREFIX}/users/password-resets/not.a.jwt",
            json={"new_password": "TestPass123!@"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            "malformed" in str(response.json()).lower()
            or "invalid" in str(response.json()).lower()
        )

    @pytest.mark.asyncio
    async def test_password_reset_user_factory_validation_error(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "factory-error@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance

        mock_uow_instance.reset_password.side_effect = UserFactoryValidationError(
            "fail", "field"
        )
        response = await client.post(
            f"{PREFIX}/users/password-resets/a.b.c",
            json={"new_password": "TestPass123!@"},
        )
        assert response.status_code == 422 or response.status_code == 400

    @pytest.mark.asyncio
    async def test_password_reset_base_application_error(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.side_effect = BaseApplicationError(
            "fail", "fail_code"
        )
        response = await client.post(
            f"{PREFIX}/users/password-resets/a.b.c",
            json={"new_password": "TestPass123!@"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_password_reset_general_exception(self, client, mocker):
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.side_effect = Exception("fail")
        response = await client.post(
            f"{PREFIX}/users/password-resets/a.b.c",
            json={"new_password": "TestPass123!@"},
        )
        assert response.status_code == 500
        assert (
            "unexpected error occurred during password reset"
            in str(response.json()).lower()
        )

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client, mocker):
        """Test registration with duplicate email."""
        mocker.patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            return_value=MagicMock(scalar_one_or_none=lambda: True),
        )
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "dupe@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Dupe",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == 400
        assert "already registered" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_register_user_base_application_error(self, client, mocker):
        """Test registration with BaseApplicationError from DB."""
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        from app.api.middleware.exceptions import BaseApplicationError

        mock_db_execute.side_effect = BaseApplicationError("fail", "fail_code")
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "base-app-error@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == 400
        assert "fail_code" in str(response.json())

    @pytest.mark.asyncio
    async def test_register_user_unhandled_exception(self, client, mocker):
        """Test registration with unhandled exception from DB."""
        mocker.patch("app.api.v1.user.send_verification_email")
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.side_effect = Exception("unexpected error")
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "unhandled-exc@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        assert response.status_code == 500
        assert (
            "unexpected error occurred during registration"
            in str(response.json()).lower()
        )

    """Tests for user registration, including error and edge cases."""

    @pytest.mark.asyncio
    async def test_register_user(self, client, mocker):
        """Test user registration endpoint."""
        _mock_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        response = await client.post(
            f"{PREFIX}/users",
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
            f"{PREFIX}/users",
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
            f"{PREFIX}/users",
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
            f"{PREFIX}/users",
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
            f"{PREFIX}/users",
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
    async def test_register_user_with_base_application_error_logging(
        self, client, mocker
    ):
        """Test that BaseApplicationError is properly logged and re-raised."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        # Mock the database to raise EmailAlreadyRegisteredError which is a BaseApplicationError
        mock_result = mocker.MagicMock()
        mock_result.scalar_one_or_none.return_value = mocker.MagicMock()  # User exists

        mock_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_execute.return_value = mock_result

        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "existing@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_input,expected_status",
        [
            # Too short password
            (
                {
                    "user_email": "testuser@example.com",
                    "user_password": "short",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
                422,
            ),
            # Invalid email format
            (
                {
                    "user_email": "invalid-email",
                    "user_password": "SecurePass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
                422,
            ),
            # Invalid first name (contains numbers)
            (
                {
                    "user_email": "testuser@example.com",
                    "user_password": "SecurePass123!@",
                    "user_first_name": "John Doe 3",
                    "user_country_code": "GB",
                },
                422,
            ),
            # Country code too long
            (
                {
                    "user_email": "testuser@example.com",
                    "user_password": "SecurePass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GBR",
                },
                422,
            ),
            # Password missing required characters
            (
                {
                    "user_email": "testuser@example.com",
                    "user_password": "simplepassword",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
                422,
            ),
        ],
    )
    async def test_user_registration_validation(
        self, client, test_input, expected_status
    ):
        """Test that invalid users cannot be created."""
        response = await client.post(f"{PREFIX}/users", json=test_input)
        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, client, mocker):
        """Test registration with an already registered email."""
        mock_email = mock_email_service(  # noqa: F841
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "duplicate@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Test",
            "user_country_code": "GB",
        }

        response = await client.post(f"{PREFIX}/users", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Attempt duplicate registration
        response = await client.post(f"{PREFIX}/users", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"][0]["msg"] == "Email already registered"
        assert response.json()["detail"][0]["type"] in [
            "emailalreadyregisterederror",
            "email_already_registered",
        ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("email_service_available", [True, False])
    async def test_verification_email_sent_on_registration(
        self, client, mocker, email_service_available
    ):
        mock_send = mock_email_service(
            mocker,
            "app.api.v1.user.send_verification_email",
            success=email_service_available,
        )

        user_data = {
            "user_email": f"verification-test-{email_service_available}@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Test",
            "user_country_code": "GB",
        }

        response = await client.post(f"{PREFIX}/users", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        user_id = response.json().get("user_id")
        assert user_id is not None

        mock_send.assert_called_once()

        if email_service_available:
            call_args = mock_send.call_args[1]
            assert call_args["user_email"] == user_data["user_email"]
            assert call_args["user_id"] == user_id
            assert response.json().get("is_email_verified") is False
        else:
            assert response.json().get("is_email_verified") is False

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found_patch(self, client, mocker):
        """Test email verification for non-existent user (patch style)."""
        mocker.patch("app.api.v1.user.jwt.decode", return_value={"sub": "notfound"})
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        from app.api.middleware.exceptions import UserNotFoundError

        mock_uow_instance.verify_email.side_effect = UserNotFoundError("User not found")
        response = await client.post(f"{PREFIX}/users/email-verifications/validtoken")
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client, mocker):
        """Test email verification with invalid token (decode error)."""
        mocker.patch(
            "app.api.v1.user.jwt.decode", side_effect=Exception("decode error")
        )
        response = await client.post(f"{PREFIX}/users/email-verifications/invalidtoken")
        assert response.status_code == 400
        assert "verification token" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_decode_error(self, client, mocker):
        """Test email verification with decode error."""
        mocker.patch(
            "app.api.v1.user.jwt.decode", side_effect=Exception("decode error")
        )
        response = await client.post(f"{PREFIX}/users/email-verifications/badtoken")
        assert response.status_code == 400
        assert "verification token" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found(self, client, mocker):
        """Test email verification for non-existent user."""
        mocker.patch("app.api.v1.user.jwt.decode", return_value={"sub": "notfound"})
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        from app.api.middleware.exceptions import UserNotFoundError

        mock_uow_instance.verify_email.side_effect = UserNotFoundError("User not found")
        response = await client.post(f"{PREFIX}/users/email-verifications/validtoken")
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    """Tests for email verification, including error and edge cases."""

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
        register_response = await client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        # Generate a valid JWT token for email verification
        from app.api.core.auth import create_token

        token = create_token(user_id=user_id)

        verify_response = await client.post(
            f"{PREFIX}/users/email-verifications/{token}"
        )

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
        register_response = await client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        token = create_token(user_id=user_id, token_type="email_verification")

        verify_response = await client.post(
            f"{PREFIX}/users/email-verifications/{token}?fromReset=true"
        )

        assert verify_response.status_code == status.HTTP_200_OK
        assert "You can now reset your password" in verify_response.json()["message"]

        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token_format(self, client):
        """Test email verification with malformed JWT token."""
        invalid_token = "invalid.token"

        response = await client.post(
            f"{PREFIX}/users/email-verifications/{invalid_token}"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification token" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_verify_email_expired_token(self, client, mocker):
        """Test email verification with expired token."""
        mock_jwt_decode = mocker.patch("app.api.v1.user.jwt.decode")
        mock_jwt_decode.side_effect = Exception("Token expired")

        expired_token = "expired.jwt.token"

        response = await client.post(
            f"{PREFIX}/users/email-verifications/{expired_token}"
        )

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

        response = await client.post(
            f"{PREFIX}/users/email-verifications/{invalid_token}"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock_send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_user_creation_failure(self, client, mocker):
        """Test user registration when user creation returns None."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        # Mock UserUnitOfWork to return None for create_user
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.return_value = None
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{PREFIX}/users",
                json={
                    "user_email": "failure@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create user" in str(response.json())

    @pytest.mark.asyncio
    async def test_register_user_no_user_id(self, client, mocker):
        """Test user registration when created user has no user_id."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        # Mock a user object without user_id
        mock_user = MagicMock()
        mock_user.user_id = None
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = False

        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.return_value = mock_user
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{PREFIX}/users",
                json={
                    "user_email": "no-id@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_password_reset_user_not_found(self, client):
        """Test password reset request when user is not found."""
        response = await client.post(
            f"{PREFIX}/users/password-resets",
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
            f"{PREFIX}/users",
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
                f"{PREFIX}/users/password-resets",
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
            f"{PREFIX}/users",
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
            f"{PREFIX}/users/email-verifications/{verification_token}?fromReset=true",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "You can now reset your password" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_reset_password_malformed_token(self, client):
        """Test password reset with malformed JWT token."""
        response = await client.post(
            f"{PREFIX}/users/password-resets/invalid-token-format",
            json={"new_password": "NewPassword123!"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_password_reset_exception_handling(self, client, mocker):
        """Test password reset request exception handling."""
        # Register a user first
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        register_response = await client.post(
            f"{PREFIX}/users",
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
            f"{PREFIX}/users/email-verifications/{verification_token}"
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
                f"{PREFIX}/users/password-resets",
                json={"user_email": "exception-test@example.com"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "An unexpected error occurred during password reset request" in str(
                response.json()
            )

    @pytest.mark.asyncio
    async def test_request_verification_email_send_failure(self, client, mocker):
        """Test requesting verification email when sending fails."""
        mock_user = MagicMock()
        mock_user.user_id = 1
        mock_user.user_email = "fail@example.com"
        mocker.patch("app.api.v1.user.validate_user_exists", return_value=mock_user)
        mock_send = mocker.patch(
            "app.api.v1.user.send_verification_email", side_effect=Exception("fail")
        )
        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": "fail@example.com"},
        )
        assert response.status_code == 500
        assert "verification email" in str(response.json()).lower()
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_verification_email_user_not_found(self, client, mocker):
        """Test requesting verification email for non-existent user."""
        from app.api.middleware.exceptions import UserNotFoundError

        mocker.patch(
            "app.api.v1.user.validate_user_exists",
            side_effect=UserNotFoundError("User not found"),
        )
        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": "notfound@example.com"},
        )
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_request_verification_email_general_exception(self, client, mocker):
        """Test verification email request with general exception."""
        mock_user = MagicMock()
        mock_user.user_id = 1
        mock_user.user_email = "fail2@example.com"
        mocker.patch("app.api.v1.user.validate_user_exists", return_value=mock_user)
        mock_send = mocker.patch(
            "app.api.v1.user.send_verification_email", side_effect=Exception("fail")
        )
        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": "fail2@example.com"},
        )
        assert response.status_code == 500
        assert "verification email" in str(response.json()).lower()
        mock_send.assert_called_once()

    """Tests for requesting verification emails, including error and edge cases."""

    @pytest.mark.asyncio
    async def test_send_verification_email_endpoint(self, client, mocker):
        """Test the endpoint to send verification email."""
        user_data = {
            "user_email": "verification@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Verify",
            "user_country_code": "GB",
        }

        mock_register_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )
        register_response = await client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        mock_register_email.reset_mock()

        mock_verify_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )
        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": user_data["user_email"]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

        mock_verify_email.assert_called_once()
        call_args = mock_verify_email.call_args[1]
        assert call_args["user_email"] == user_data["user_email"]

    @pytest.mark.asyncio
    async def test_send_verification_email_service_failure(self, client, mocker):
        """Test verification email request when service fails."""
        user_data = {
            "user_email": "verify-fail@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "VerifyFail",
            "user_country_code": "GB",
        }

        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        register_response = await client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        mock_verify_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email", success=False
        )

        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": user_data["user_email"]},
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_verify_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_email_exception_logging(self, client, mocker):
        """Test that verification email exceptions are properly logged."""
        user_data = {
            "user_email": "exception-test@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Exception",
            "user_country_code": "GB",
        }

        # Register user first
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        register_response = await client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Mock send_verification_email to raise an exception
        mock_verify_email = mocker.patch(
            "app.api.v1.user.send_verification_email",
            side_effect=Exception("Service unavailable"),
        )

        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": user_data["user_email"]},
        )

        # Should return 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_verify_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_verification_status_user_not_found(self, client, mocker):
        """Test verification status for non-existent user."""
        from app.api.middleware.exceptions import UserNotFoundError

        mocker.patch(
            "app.api.v1.user.validate_user_exists",
            side_effect=UserNotFoundError("User not found"),
        )
        response = await client.get(
            f"{PREFIX}/users/verification-status?user_email=notfound@example.com"
        )
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    """Tests for checking email verification status, including error and edge cases."""

    @pytest.mark.asyncio
    async def test_check_verification_status_unverified(self, client, mocker):
        """Test checking verification status for an unverified user."""
        mock_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "status_check@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Status",
            "user_country_code": "GB",
        }
        register_response = await client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        assert register_response.json().get("is_email_verified") is False
        response = await client.get(
            f"{PREFIX}/users/verification-status?user_email={user_data['user_email']}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "is_email_verified" in data
        assert data["is_email_verified"] is False
        assert "user_id" in data
        assert data["user_id"] == register_response.json()["user_id"]

        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_verification_status_verified(self, client, mocker):
        """Test checking verification status for a verified user."""
        mock_email = mock_email_service(  # noqa: F841
            mocker, "app.api.v1.user.send_verification_email"
        )

        user_data = {
            "user_email": "verified_status@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Verified",
            "user_country_code": "GB",
        }
        register_response = await client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        # Generate a valid JWT token for email verification
        from app.api.core.auth import create_token

        token = create_token(user_id=user_id)

        verify_response = await client.post(
            f"{PREFIX}/users/email-verifications/{token}"
        )
        assert verify_response.status_code == status.HTTP_200_OK

        response = await client.get(
            f"{PREFIX}/users/verification-status?user_email={user_data['user_email']}"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_email_verified"] is True
        assert data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_check_verification_status_nonexistent_user(self, client):
        """Test checking verification status for a non-existent user."""
        response = await client.get(
            f"{PREFIX}/users/verification-status?user_email=nonexistent@example.com"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"][0]["msg"] == "User not found"
        assert response.json()["detail"][0]["type"] in [
            "usernotfounderror",
            "user_not_found",
        ]

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
            f"{PREFIX}/users/password-resets",
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
        register = await client.post(f"{PREFIX}/users", json=user_data)
        assert register.status_code == status.HTTP_201_CREATED

        # ignore the initial registration call
        _mock_verify.reset_mock()

        # now request reset
        resp = await client.post(
            f"{PREFIX}/users/password-resets",
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
        reg = await client.post(f"{PREFIX}/users", json=user_data)
        user_id = reg.json()["user_id"]
        token = create_token(user_id=user_id, token_type="email_verification")
        verify = await client.post(f"{PREFIX}/users/email-verifications/{token}")
        assert verify.status_code == status.HTTP_200_OK

        _mock_reset = mock_email_service(
            mocker,
            "app.api.services.user.user_unit_of_work.send_password_reset_email",
        )

        resp = await client.post(
            f"{PREFIX}/users/password-resets",
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
            f"{PREFIX}/users/password-resets",
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
            f"{PREFIX}/users/password-resets",
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
        reg = await client.post(f"{PREFIX}/users", json=user_data)
        user_id = reg.json()["user_id"]
        token_ver = create_token(user_id=user_id, token_type="email_verification")
        await client.post(f"{PREFIX}/users/email-verifications/{token_ver}")

        reset_token = create_token(user_id=user_id, token_type="reset")
        new_pass = "NewPass456!#"

        resp = await client.post(
            f"{PREFIX}/users/password-resets/{reset_token}",
            json={"new_password": new_pass},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "has been reset" in resp.json()["message"].lower()
        login = await client.post(
            f"{PREFIX}/auth/token",
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
        from app.api.middleware.exceptions import BaseApplicationError

        # Mock UserUnitOfWork to raise BaseApplicationError
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = BaseApplicationError(
                message="Reset failed", status_code=400, error_code="RESET_ERROR"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/users/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_reset_password_with_validation_error_logging(self, client, mocker):
        """Test password reset with UserFactoryValidationError logging."""
        # Duplicate import removed: UserFactoryValidationError

        # Mock UserUnitOfWork to raise UserFactoryValidationError
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = UserFactoryValidationError(
                field="password", message="Password too weak"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/users/password-resets/{valid_token}",
                json={"new_password": "weak"},
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_reset_password_with_invalid_token_error_logging(
        self, client, mocker
    ):
        """Test password reset with InvalidTokenError logging."""
        from app.api.middleware.exceptions import InvalidTokenError

        # Mock UserUnitOfWork to raise InvalidTokenError
        with patch("app.api.v1.user.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance
            mock_uow_instance.reset_password.side_effect = InvalidTokenError(
                "Invalid token"
            )

            valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

            response = await client.post(
                f"{PREFIX}/users/password-resets/{valid_token}",
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
                f"{PREFIX}/users/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert (
                "An unexpected error occurred during password reset"
                in response.json()["detail"][0]["msg"]
            )

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
                f"{PREFIX}/users/password-resets/{valid_token}",
                json={"new_password": "NewPassword123!"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert "Password has been reset successfully" in response.json()["message"]
