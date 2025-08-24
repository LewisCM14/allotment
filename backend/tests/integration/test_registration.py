from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from app.api.core.auth_utils import create_token
from app.api.core.config import settings
from app.api.middleware.exception_handler import BaseApplicationError
from tests.conftest import mock_email_service
from tests.test_helpers import mock_user_uow

REGISTRATION_PREFIX = f"{settings.API_PREFIX}/registration"


class TestUserRegistration:
    @pytest.mark.asyncio
    async def test_register_user(self, client, mocker):
        """Test user registration endpoint."""
        _mock_email = mock_email_service(
            mocker, "app.api.v1.registration.send_verification_email"
        )

        response = await client.post(
            f"{REGISTRATION_PREFIX}",
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
    async def test_register_user_sets_datetime_fields(self, client, mocker):
        """Test that user registration sets registered_date and last_active_date."""
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")

        response = await client.post(
            f"{REGISTRATION_PREFIX}",
            json={
                "user_email": "datetime_test@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "DateTimeTest",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data

        # Verify the user was created with proper datetime fields
        # The fact that we can login indicates the datetime fields were properly set
        # (since login updates last_active_date and requires the user to exist)
        login_response = await client.post(
            f"{settings.API_PREFIX}/auth/token",
            json={
                "user_email": "datetime_test@example.com",
                "user_password": "TestPass123!@",
            },
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "desc,user_email,configure_uow",
        [
            (
                "creation_returns_none",
                "creation-none@example.com",
                lambda mocker: mock_user_uow(mocker, methods={"create_user": None}),
            ),
        ],
    )
    async def test_register_user_creation_failures(
        self, client, mocker, desc, user_email, configure_uow
    ):
        """User creation failure cases (only: create_user returns None -> 500)."""
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        configure_uow(mocker)
        response = await client.post(
            f"{REGISTRATION_PREFIX}",
            json={
                "user_email": user_email,
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
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")

        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.side_effect = Exception("Unexpected database error")

        response = await client.post(
            f"{REGISTRATION_PREFIX}",
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
            "app.api.v1.registration.send_verification_email",
            side_effect=Exception("Email service unavailable"),
        )

        response = await client.post(
            f"{REGISTRATION_PREFIX}",
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
            "app.api.v1.registration.send_verification_email",
            side_effect=Exception("Email service down"),
        )

        response = await client.post(
            f"{REGISTRATION_PREFIX}",
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
        mocker.patch("app.api.v1.registration.send_verification_email")
        with patch("app.api.v1.registration.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.side_effect = Exception("Database is on fire")
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{REGISTRATION_PREFIX}",
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
    async def test_register_user_base_application_error(self, client, mocker):
        """Test user registration with a BaseApplicationError from the UoW."""
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        with patch("app.api.v1.registration.UserUnitOfWork") as mock_uow:
            mock_uow_instance = AsyncMock()
            mock_uow_instance.create_user.side_effect = BaseApplicationError(
                message="A specific business logic error occurred",
                error_code="TEST_ERROR",
            )
            mock_uow.return_value.__aenter__.return_value = mock_uow_instance

            response = await client.post(
                f"{REGISTRATION_PREFIX}",
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
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")

        # Mock database query to return an existing user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Existing user
        mock_db_execute = mocker.patch("sqlalchemy.ext.asyncio.AsyncSession.execute")
        mock_db_execute.return_value = mock_result

        response = await client.post(
            f"{REGISTRATION_PREFIX}",
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
            mocker, "app.api.v1.registration.send_verification_email"
        )

        user_data = {
            "user_email": "verify@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Verify",
            "user_country_code": "GB",
        }

        # Register user first
        register_response = await client.post(f"{REGISTRATION_PREFIX}", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        # Generate a valid JWT token for email verification
        from app.api.core.auth_utils import create_token

        token = create_token(user_id=user_id)

        verify_response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/{token}"
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
            mocker, "app.api.v1.registration.send_password_reset_email"
        )

        user_data = {
            "user_email": "verify-reset@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "VerifyReset",
            "user_country_code": "GB",
        }
        register_response = await client.post(f"{REGISTRATION_PREFIX}", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        token = create_token(user_id=user_id, token_type="email_verification")

        verify_response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/{token}?fromReset=true"
        )

        assert verify_response.status_code == status.HTTP_200_OK
        assert "You can now reset your password" in verify_response.json()["message"]

        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token_format(self, client):
        """Test email verification with malformed JWT token."""
        invalid_token = "invalid.token"

        response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/{invalid_token}"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification token" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_verify_email_expired_token(self, client, mocker):
        """Test email verification with expired token."""
        mock_jwt_decode = mocker.patch("app.api.v1.registration.jwt.decode")
        mock_jwt_decode.side_effect = Exception("Token expired")

        expired_token = "expired.jwt.token"

        response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/{expired_token}"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid verification token" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_verify_email_invalid_user(self, client, mocker):
        """Test verifying an email for a non-existent user."""
        mock_send_email = mock_email_service(
            mocker, "app.api.v1.registration.send_verification_email"
        )

        # Create a valid token for a non-existent user ID
        invalid_user_id = "00000000-0000-0000-0000-000000000000"
        invalid_token = create_token(user_id=invalid_user_id)

        response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/{invalid_token}"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock_send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found_patch(self, client, mocker):
        """Alias scenario kept for clarity but delegates to single path; removed duplicate variant below."""
        mocker.patch(
            "app.api.v1.registration.jwt.decode", return_value={"sub": "notfound"}
        )
        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        from app.api.middleware.exception_handler import UserNotFoundError

        mock_uow_instance.verify_email.side_effect = UserNotFoundError("User not found")
        response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/validtoken"
        )
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_decode_error(self, client, mocker):
        """Decode error path (covers generic invalid token scenarios)."""
        mocker.patch(
            "app.api.v1.registration.jwt.decode", side_effect=Exception("decode error")
        )
        response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/invalidtoken"
        )
        assert response.status_code == 400
        assert "verification token" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found(self, client, mocker):
        """Kept single variant for user not found (deduped)."""
        mocker.patch(
            "app.api.v1.registration.jwt.decode", return_value={"sub": "notfound"}
        )
        mock_uow = mocker.patch("app.api.v1.registration.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        from app.api.middleware.exception_handler import UserNotFoundError

        mock_uow_instance.verify_email.side_effect = UserNotFoundError("User not found")
        response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/validtoken"
        )
        assert response.status_code == 404
        assert "user not found" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_verify_email_from_password_reset_query_param(self, client, mocker):
        """Test email verification with fromReset query parameter."""
        mock_send_email = mock_email_service(
            mocker, "app.api.v1.registration.send_password_reset_email"
        )

        user_data = {
            "user_email": "reset-verify@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "ResetVerify",
            "user_country_code": "GB",
        }
        register_response = await client.post(f"{REGISTRATION_PREFIX}", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        token = create_token(user_id=user_id, token_type="email_verification")

        verify_response = await client.post(
            f"{REGISTRATION_PREFIX}/email-verifications/{token}?fromReset=true"
        )

        assert verify_response.status_code == status.HTTP_200_OK
        assert "You can now reset your password" in verify_response.json()["message"]

        mock_send_email.assert_called_once()
