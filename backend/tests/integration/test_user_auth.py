"""
User Authentication API Tests
"""

from fastapi import status

from app.api.core.config import settings
from tests.conftest import mock_email_service

PREFIX = settings.API_PREFIX


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
