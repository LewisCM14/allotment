"""
User API Tests
"""

import pytest
from fastapi import status

from app.api.core.config import settings

PREFIX = settings.API_PREFIX


class TestRegisterUser:
    def test_register_user(self, client):
        """Test user registration endpoint."""
        response = client.post(
            f"{PREFIX}/user",
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
                    "user_password": "SecurePass123!",
                    "user_first_name": "Test",
                    "user_country_code": "GB",
                },
                422,
            ),
            # Invalid first name (contains numbers)
            (
                {
                    "user_email": "testuser@example.com",
                    "user_password": "SecurePass123!",
                    "user_first_name": "John Doe 3",
                    "user_country_code": "GB",
                },
                422,
            ),
            # Country code too long
            (
                {
                    "user_email": "testuser@example.com",
                    "user_password": "SecurePass123!",
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
        response = client.post(f"{PREFIX}/user", json=test_input)

        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, client):
        """Test registration with an already registered email."""
        # First registration
        user_data = {
            "user_email": "duplicate@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Test",
            "user_country_code": "GB",
        }

        response = client.post(f"{PREFIX}/user", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        # Attempt duplicate registration
        response = client.post(f"{PREFIX}/user", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Email already registered"


class TestUserLogin:
    def test_login_user(self, client):
        """Test user login with correct credentials."""
        client.post(
            f"{PREFIX}/user",
            json={
                "user_email": "testuser@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        response = client.post(
            f"{PREFIX}/user/auth/login",
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
            f"{PREFIX}/user/auth/login",
            json={
                "user_email": "testuser@example.com",
                "user_password": "WrongPassword!",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"


class TestTokenRefresh:
    def test_refresh_token(self, client):
        """Test refreshing access token with valid refresh token."""
        register_response = client.post(
            f"{PREFIX}/user",
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
            f"{PREFIX}/user/auth/refresh",
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
            f"{PREFIX}/user/auth/refresh",
            json={"refresh_token": invalid_token},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_refresh_with_access_token(self, client):
        """Test refreshing with an access token instead of refresh token."""
        register_response = client.post(
            f"{PREFIX}/user",
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
            f"{PREFIX}/user/auth/refresh",
            json={"refresh_token": access_token},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token type" in response.json()["detail"]


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_verify_email(self, client):
        """Test verifying a user's email."""
        user_data = {
            "user_email": "verify@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Verify",
            "user_country_code": "GB",
        }
        register_response = client.post(f"{PREFIX}/user", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["user_id"]

        verify_response = client.post(f"{PREFIX}/user/verify-email?user_id={user_id}")
        assert verify_response.status_code == status.HTTP_200_OK
        assert verify_response.json()["message"] == "Email verified successfully"

    @pytest.mark.asyncio
    async def test_verify_email_invalid_user(self, client):
        """Test verifying an email for a non-existent user."""
        invalid_user_id = "00000000-0000-0000-0000-000000000000"
        verify_response = client.post(
            f"{PREFIX}/user/verify-email?user_id={invalid_user_id}"
        )
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
        assert verify_response.json()["detail"] == "User not found"
