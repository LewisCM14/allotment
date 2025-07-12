from unittest.mock import patch

import pytest
from fastapi import status

from app.api.core.config import settings
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
)
from tests.conftest import mock_email_service

PREFIX = settings.API_PREFIX


class TestUserLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client, mocker):
        """Test user login with correct credentials."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "testuser@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )
        response = await client.post(
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

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login with incorrect password."""
        response = await client.post(
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

    @pytest.mark.asyncio
    async def test_login_with_token_generation_exception(self, client, mocker):
        """Test handling of exceptions during token generation."""
        mocker.patch("app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "token-error@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Token",
                "user_country_code": "GB",
            },
        )
        with patch(
            "app.api.v1.user_auth.create_token",
            side_effect=Exception("Token generation failed"),
        ):
            response = await client.post(
                f"{PREFIX}/auth/token",
                json={
                    "user_email": "token-error@example.com",
                    "user_password": "SecurePass123!",
                },
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "unexpected error" in response.json()["detail"][0]["msg"].lower()

    @pytest.mark.asyncio
    async def test_login_with_specific_business_logic_error(self, client, mocker):
        """Test handling of specific BusinessLogicError during login."""
        mock_authenticate = mocker.patch("app.api.v1.user_auth.authenticate_user")

        mock_authenticate.side_effect = BusinessLogicError(
            message="Account locked",
            error_code="ACCOUNT_LOCKED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
        response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "locked@example.com",
                "user_password": "password",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "account locked" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_login_base_application_error(self, client, mocker):
        """Test login with BaseApplicationError from authenticate_user."""
        mock_auth = mocker.patch("app.api.v1.user_auth.authenticate_user")
        mock_auth.side_effect = BaseApplicationError("fail", "fail_code")
        response = await client.post(
            f"{PREFIX}/auth/token",
            json={"user_email": "fail@example.com", "user_password": "failfail"},
        )
        assert response.status_code in (400, 422)
        assert "fail_code" in str(response.json())

    @pytest.mark.asyncio
    async def test_login_general_exception(self, client, mocker):
        """Test login with general exception from authenticate_user."""
        mock_auth = mocker.patch("app.api.v1.user_auth.authenticate_user")
        mock_auth.side_effect = Exception("fail")
        response = await client.post(
            f"{PREFIX}/auth/token",
            json={"user_email": "fail2@example.com", "user_password": "failfail"},
        )
        assert response.status_code in (500, 422)
        if response.status_code != 422:
            assert (
                "unexpected error occurred while authenticating user"
                in str(response.json()).lower()
            )


class TestTokenRefresh:
    @pytest.mark.asyncio
    async def test_refresh_token_decode_token_missing_type(self, client, mocker):
        """Test refresh token decode returns missing type."""
        mock_decode = mocker.patch("app.api.v1.user_auth.decode_token")
        mock_decode.return_value = {"sub": "user-id"}
        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": "token"},
        )
        assert response.status_code == 401
        assert "expected refresh token" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_refresh_token_decode_token_missing_sub(self, client, mocker):
        """Test refresh token decode returns missing sub."""
        mock_decode = mocker.patch("app.api.v1.user_auth.decode_token")
        mock_decode.return_value = {"type": "refresh"}
        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": "token"},
        )
        assert response.status_code == 401
        assert "no user id found" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_refresh_token_validate_user_exists_raises(self, client, mocker):
        """Test refresh token when validate_user_exists raises BaseApplicationError."""
        mock_decode = mocker.patch("app.api.v1.user_auth.decode_token")
        mock_decode.return_value = {"type": "refresh", "sub": "user-id"}
        mock_validate = mocker.patch("app.api.v1.user_auth.validate_user_exists")

        mock_validate.side_effect = BaseApplicationError("fail", "fail_code")
        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": "token"},
        )
        assert response.status_code == 400
        assert "fail_code" in str(response.json())

    @pytest.mark.asyncio
    async def test_token_refresh_with_invalid_token_payload(self, client, mocker):
        """Test refresh token when decode works but payload is invalid."""
        mock_decode = mocker.patch("app.api.v1.user_auth.decode_token")
        mock_decode.return_value = {"sub": "user-id"}
        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": "invalid-payload-token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid token type" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_login_with_exception_during_login(self, client, mocker):
        """Test login when an unexpected exception occurs."""
        # Mock authenticate_user to raise an exception
        with patch(
            "app.api.v1.user_auth.authenticate_user",
            side_effect=Exception("Database error"),
        ):
            response = await client.post(
                f"{PREFIX}/auth/token",
                json={
                    "user_email": "test@example.com",
                    "user_password": "testpass",
                },
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "An unexpected error occurred while authenticating user" in str(
                response.json()
            )

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login with incorrect password."""
        response = await client.post(
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

    @pytest.mark.asyncio
    async def test_refresh_token_generates_unique_tokens(self, client, mocker):
        """Test that refresh token endpoint generates unique tokens."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "unique-tokens@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Unique",
                "user_country_code": "GB",
            },
        )
        login_response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "unique-tokens@example.com",
                "user_password": "SecurePass123!",
            },
        )
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        old_access_token = login_data["access_token"]
        refresh_response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )
        refresh_data = refresh_response.json()
        assert refresh_data["access_token"] != old_access_token
        assert refresh_data["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token(self, client, mocker):
        """Test refreshing access token with valid refresh token."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        register_response = await client.post(
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
        refresh_response = await client.post(
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

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client):
        """Test refreshing with an invalid refresh token."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": invalid_token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, client, mocker):
        """Test refreshing with an access token instead of refresh token."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        register_response = await client.post(
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

        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_with_authentication_error(self, client, mocker):
        """Test login when authentication fails."""
        # Mock authenticate_user to return None (authentication failure)
        with patch("app.api.v1.user_auth.authenticate_user", return_value=None):
            response = await client.post(
                f"{PREFIX}/auth/token",
                json={
                    "user_email": "test@example.com",
                    "user_password": "wrongpassword",
                },
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid email or password" in str(response.json())

    @pytest.mark.asyncio
    async def test_refresh_token_missing_user_id(self, client, mocker):
        """Test refresh token when token is missing user ID."""
        # Mock decode_token to return payload without 'sub'
        with patch(
            "app.api.v1.user_auth.decode_token", return_value={"type": "refresh"}
        ):
            response = await client.post(
                f"{PREFIX}/auth/token/refresh",
                json={"refresh_token": "fake_token"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token - no user ID found" in str(response.json())

    @pytest.mark.asyncio
    async def test_refresh_token_wrong_type(self, client, mocker):
        """Test refresh token when token type is not 'refresh'."""
        # Mock decode_token to return access token type
        with patch(
            "app.api.v1.user_auth.decode_token",
            return_value={"type": "access", "sub": "user123"},
        ):
            response = await client.post(
                f"{PREFIX}/auth/token/refresh",
                json={"refresh_token": "fake_token"},
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid token type: expected refresh token" in str(response.json())


class TestUserAuthErrorHandling:
    @pytest.mark.asyncio
    async def test_login_general_exception(self, client, mocker):
        """Test login handles general exceptions."""
        # Mock authenticate_user to raise a general exception
        mock_auth = mocker.patch("app.api.v1.user_auth.authenticate_user")
        mock_auth.side_effect = Exception("Database connection error")

        response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "test@example.com",
                "user_password": "TestPass123!",
            },
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "unexpected error occurred" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_login_authentication_error(self, client, mocker):
        """Test login with authentication error."""
        # Mock authenticate_user to return None (invalid credentials)
        mock_auth = mocker.patch("app.api.v1.user_auth.authenticate_user")
        mock_auth.return_value = None

        response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "invalid@example.com",
                "user_password": "WrongPass123!",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalid_token_exception(self, client, mocker):
        """Test refresh token handles invalid token exceptions."""
        # Mock decode_token to raise InvalidTokenError
        mock_decode = mocker.patch("app.api.v1.user_auth.decode_token")
        mock_decode.side_effect = Exception("Token decode error")

        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": "invalid_token"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token decode error" in str(response.json())


class TestUserAuthSuccessFlows:
    @pytest.mark.asyncio
    async def test_login_success_with_token_generation(self, client, mocker):
        """Test successful login with proper token generation."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        # Create a user first
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "login-success@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "LoginSuccess",
                "user_country_code": "GB",
            },
        )

        # Now login
        response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "login-success@example.com",
                "user_password": "TestPass123!@",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_first_name"] == "LoginSuccess"
        assert "is_email_verified" in data
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_refresh_token_success_flow(self, client, mocker):
        """Test successful refresh token flow with proper response."""
        mock_email_service(mocker, "app.api.v1.user.send_verification_email")

        # Create and login user to get tokens
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "refresh-success@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "RefreshSuccess",
                "user_country_code": "GB",
            },
        )

        login_response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "refresh-success@example.com",
                "user_password": "TestPass123!@",
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Test refresh
        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_first_name"] == "RefreshSuccess"
        assert "is_email_verified" in data
        assert "user_id" in data
