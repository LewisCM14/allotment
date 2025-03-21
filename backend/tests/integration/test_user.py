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
