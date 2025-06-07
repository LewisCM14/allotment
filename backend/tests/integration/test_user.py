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
    def test_register_user(self, client, mocker):
        """Test user registration endpoint."""
        _mock_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        response = client.post(
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
    def test_user_registration_validation(self, client, test_input, expected_status):
        """Test that invalid users cannot be created."""
        response = client.post(f"{PREFIX}/users", json=test_input)
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

        response = client.post(f"{PREFIX}/users", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Attempt duplicate registration
        response = client.post(f"{PREFIX}/users", json=user_data)
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

        response = client.post(f"{PREFIX}/users", json=user_data)
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


class TestUserLogin:
    def test_login_user(self, client, mocker):
        """Test user login with correct credentials."""
        _mock_email = mock_email_service(  # noqa: F841
            mocker, "app.api.v1.user.send_verification_email"
        )

        client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "testuser@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        response = client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "testuser@example.com",
                "user_password": "SecurePass123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "user_first_name" in data
        assert data["user_first_name"] == "Test"

    def test_login_invalid_credentials(self, client):
        """Test login with incorrect password."""
        response = client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "testuser@example.com",
                "user_password": "WrongPassword!",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"][0]["msg"] == "Invalid email or password"
        assert response.json()["detail"][0]["type"] in [
            "authenticationerror",
            "authentication_error",
        ]


class TestTokenRefresh:
    def test_refresh_token(self, client, mocker):
        """Test refreshing access token with valid refresh token."""
        mock_email = mock_email_service(  # noqa: F841
            mocker, "app.api.v1.user.send_verification_email"
        )

        register_response = client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "refresh@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Refresh",
                "user_country_code": "GB",
            },
        )

        assert register_response.status_code == status.HTTP_201_CREATED
        tokens = register_response.json()
        refresh_token = tokens["refresh_token"]

        # 2. Use the refresh token to get a new access token
        refresh_response = client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"

        # 4. Verify tokens are different (token rotation)
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

    def test_refresh_with_invalid_token(self, client):
        """Test refreshing with an invalid refresh token."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        response = client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": invalid_token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json()["detail"][0]["msg"]
        assert response.json()["detail"][0]["type"] in [
            "invalidtokenerror",
            "invalid_token",
        ]

    def test_refresh_with_access_token(self, client, mocker):
        """Test refreshing with an access token instead of refresh token."""
        mock_email = mock_email_service(  # noqa: F841
            mocker, "app.api.v1.user.send_verification_email"
        )

        register_response = client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "wrong_token@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Wrong",
                "user_country_code": "GB",
            },
        )

        tokens = register_response.json()
        access_token = tokens["access_token"]

        response = client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": access_token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.json()["detail"][0]["msg"]
            == "Invalid token type: expected refresh token"
        )
        assert response.json()["detail"][0]["type"] in [
            "invalidtokenerror",
            "invalid_token",
        ]


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
        register_response = client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        # Generate a valid JWT token for email verification
        from app.api.core.auth import create_token

        token = create_token(user_id=user_id)

        verify_response = client.post(f"{PREFIX}/users/email-verifications/{token}")

        assert verify_response.status_code == status.HTTP_200_OK
        assert verify_response.json()["message"] == "Email verified successfully"

        mock_send_email.assert_called_once_with(
            user_email=user_data["user_email"], user_id=user_id
        )

    @pytest.mark.asyncio
    async def test_verify_email_invalid_user(self, client, mocker):
        """Test verifying an email for a non-existent user."""
        mock_send_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )

        # Create a valid token for a non-existent user ID
        invalid_user_id = "00000000-0000-0000-0000-000000000000"
        invalid_token = create_token(user_id=invalid_user_id)

        response = client.post(f"{PREFIX}/users/email-verifications/{invalid_token}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock_send_email.assert_not_called()


class TestRequestVerificationEmail:
    def test_send_verification_email_endpoint(self, client, mocker):
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
        register_response = client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        mock_register_email.reset_mock()

        mock_verify_email = mock_email_service(
            mocker, "app.api.v1.user.send_verification_email"
        )
        response = client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": user_data["user_email"]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.json()

        mock_verify_email.assert_called_once()
        call_args = mock_verify_email.call_args[1]
        assert call_args["user_email"] == user_data["user_email"]


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
        register_response = client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        assert register_response.json().get("is_email_verified") is False
        response = client.get(
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
        register_response = client.post(f"{PREFIX}/users", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        # Generate a valid JWT token for email verification
        from app.api.core.auth import create_token

        token = create_token(user_id=user_id)

        verify_response = client.post(f"{PREFIX}/users/email-verifications/{token}")
        assert verify_response.status_code == status.HTTP_200_OK

        response = client.get(
            f"{PREFIX}/users/verification-status?user_email={user_data['user_email']}"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_email_verified"] is True
        assert data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_check_verification_status_nonexistent_user(self, client):
        """Test checking verification status for a non-existent user."""
        response = client.get(
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
        register = client.post(f"{PREFIX}/users", json=user_data)
        assert register.status_code == status.HTTP_201_CREATED

        # ignore the initial registration call
        _mock_verify.reset_mock()

        # now request reset
        resp = client.post(
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
        reg = client.post(f"{PREFIX}/users", json=user_data)
        user_id = reg.json()["user_id"]
        token = create_token(user_id=user_id, token_type="email_verification")
        verify = client.post(f"{PREFIX}/users/email-verifications/{token}")
        assert verify.status_code == status.HTTP_200_OK

        _mock_reset = mock_email_service(
            mocker,
            "app.api.services.user.user_unit_of_work.send_password_reset_email",
        )

        resp = client.post(
            f"{PREFIX}/users/password-resets",
            json={"user_email": user_data["user_email"]},
        )
        assert resp.status_code == status.HTTP_200_OK
        msg = resp.json()["message"].lower()
        assert "password reset link" in msg
        _mock_reset.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_and_login(self, client, mocker):
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        user_data = {
            "user_email": "do-reset@example.com",
            "user_password": "OldPass123!@",
            "user_first_name": "Reseter",
            "user_country_code": "GB",
        }
        reg = client.post(f"{PREFIX}/users", json=user_data)
        user_id = reg.json()["user_id"]
        token_ver = create_token(user_id=user_id, token_type="email_verification")
        client.post(f"{PREFIX}/users/email-verifications/{token_ver}")

        reset_token = create_token(user_id=user_id, token_type="reset")
        new_pass = "NewPass456!#"

        resp = client.post(
            f"{PREFIX}/users/password-resets/{reset_token}",
            json={"new_password": new_pass},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "has been reset" in resp.json()["message"].lower()
        login = client.post(
            f"{PREFIX}/auth/token",
            json={"user_email": user_data["user_email"], "user_password": new_pass},
        )
        assert login.status_code == status.HTTP_200_OK
        data = login.json()
        assert (
            "access_token" in data
            and data["user_first_name"] == user_data["user_first_name"]
        )

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
    def test_reset_password_errors(self, client, payload, code):
        """Invalid token or weak password yields appropriate error."""
        if code == status.HTTP_401_UNAUTHORIZED:
            bad_token = "bad.token.payload"
            resp = client.post(
                f"{PREFIX}/users/password-resets/{bad_token}", json=payload
            )
        else:
            token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
            resp = client.post(f"{PREFIX}/users/password-resets/{token}", json=payload)

        assert resp.status_code == code
