"""
User API Tests
"""

import uuid

import pytest
from fastapi import status

from app.api.core.auth import create_token
from app.api.core.config import settings
from tests.conftest import mock_email_service

PREFIX = settings.API_PREFIX


class TestRegisterUser:
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
        assert "An unexpected error occurred during registration" in response.json()["detail"][0]["msg"]

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


class TestVerifyEmail:
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


class TestRequestVerificationEmail:
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

        mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )
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


class TestEmailVerificationStatus:
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


class TestPasswordResetFlow:
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
        assert "An unexpected error occurred during password reset request" in resp.json()["detail"][0]["msg"]

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
    async def test_reset_password_malformed_token(self, client):
        """Test password reset with malformed JWT token."""
        malformed_token = "bad.token"

        resp = await client.post(
            f"{PREFIX}/users/password-resets/{malformed_token}",
            json={"new_password": "NewPass123!"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_reset_password_handles_validation_error(self, client, mocker):
        """Test password reset handles UserFactoryValidationError."""
        from app.api.factories.user_factory import UserFactoryValidationError

        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.side_effect = UserFactoryValidationError(
            "Password too weak", "password"
        )

        valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

        resp = await client.post(
            f"{PREFIX}/users/password-resets/{valid_token}",
            json={"new_password": "weak"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_reset_password_handles_general_exception(self, client, mocker):
        """Test password reset handles unexpected exceptions."""
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.side_effect = Exception("Unexpected error")

        valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")

        resp = await client.post(
            f"{PREFIX}/users/password-resets/{valid_token}",
            json={"new_password": "ValidPass123!"},
        )
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "An unexpected error occurred during password reset" in resp.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "payload,code",
        [
            (
                {"new_password": "Whatever1!"},
                status.HTTP_401_UNAUTHORIZED,
            ),
            (
                {
                    "new_password": "short",
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
        ],
    )
    async def test_reset_password_errors(self, client, payload, code):
        """Invalid token or weak password yields appropriate error."""
        if code == status.HTTP_401_UNAUTHORIZED:
            bad_token = "bad.token.payload"
            resp = await client.post(
                f"{PREFIX}/users/password-resets/{bad_token}", json=payload
            )
        else:
            token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
            resp = await client.post(
                f"{PREFIX}/users/password-resets/{token}", json=payload
            )

        assert resp.status_code == code


class TestAdditionalCoverageScenarios:
    """Additional test cases to improve coverage of edge cases and error paths."""

    @pytest.mark.asyncio
    async def test_verify_email_with_invalid_user_id_in_token(self, client, mocker):
        """Test email verification with invalid user ID format in token."""

        invalid_token = create_token(user_id="invalid-uuid-format")

        response = await client.post(
            f"{PREFIX}/users/email-verifications/{invalid_token}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_request_verification_email_for_nonexistent_user(self, client):
        """Test requesting verification email for non-existent user."""
        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": "nonexistent@example.com"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"][0]["msg"]


class TestCoverageEnhancement:
    """Additional tests to reach 80%+ coverage."""
    
    @pytest.mark.asyncio
    async def test_register_user_with_base_application_error(self, client, mocker):
        """Test user registration handles BaseApplicationError from UnitOfWork."""
        from app.api.middleware.exception_handler import BusinessLogicError
        
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.create_user.side_effect = BusinessLogicError(
            "Database constraint violation"
        )
        
        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "base-error@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Database constraint violation" in response.json()["detail"][0]["msg"]
    
    @pytest.mark.asyncio
    async def test_request_password_reset_with_base_application_error(self, client, mocker):
        """Test password reset request handles BaseApplicationError."""
        from app.api.middleware.exception_handler import BusinessLogicError
        
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        
        user_data = {
            "user_email": "reset-error@example.com",
            "user_password": "TestPass123!@",
            "user_first_name": "ResetError",
            "user_country_code": "GB",
        }
        reg = await client.post(f"{PREFIX}/users", json=user_data)
        user_id = reg.json()["user_id"]
        token = create_token(user_id=user_id, token_type="email_verification")
        await client.post(f"{PREFIX}/users/email-verifications/{token}")
        
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.request_password_reset.side_effect = BusinessLogicError(
            "Password reset service unavailable"
        )
        
        resp = await client.post(
            f"{PREFIX}/users/password-resets",
            json={"user_email": user_data["user_email"]},
        )
        
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Password reset service unavailable" in resp.json()["detail"][0]["msg"]
    
    @pytest.mark.asyncio
    async def test_reset_password_with_base_application_error(self, client, mocker):
        """Test password reset handles BaseApplicationError."""
        from app.api.middleware.exception_handler import BusinessLogicError
        
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.side_effect = BusinessLogicError(
            "Password reset failed due to business rule"
        )
        
        valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
        
        resp = await client.post(
            f"{PREFIX}/users/password-resets/{valid_token}",
            json={"new_password": "ValidPass123!"},
        )
        
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "Password reset failed due to business rule" in resp.json()["detail"][0]["msg"]
    
    @pytest.mark.asyncio
    async def test_reset_password_with_invalid_token_error(self, client, mocker):
        """Test password reset handles InvalidTokenError."""
        from app.api.middleware.exception_handler import InvalidTokenError
        
        mock_uow = mocker.patch("app.api.v1.user.UserUnitOfWork")
        mock_uow_instance = mocker.AsyncMock()
        mock_uow.return_value.__aenter__.return_value = mock_uow_instance
        mock_uow_instance.reset_password.side_effect = InvalidTokenError(
            "Token has expired"
        )
        
        valid_token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
        
        resp = await client.post(
            f"{PREFIX}/users/password-resets/{valid_token}",
            json={"new_password": "ValidPass123!"},
        )
        
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
