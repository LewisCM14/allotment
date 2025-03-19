"""
User API Tests
"""

import pytest
from fastapi import status

API_VERSION = "api/v1"


class TestRegisterUser:
    def test_register_user(self, client):
        """Test user registration endpoint."""
        response = client.post(
            f"{API_VERSION}/user",
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
        "test_input,expected_status,expected_detail",
        [
            (
                {
                    "user_email": "test@example.com",
                    "user_password": "invalid",
                    "user_first_name": "John Smith",
                    "user_country_code": "GB",
                },
                422,
                "String should have at least 8 characters",
            ),
            (
                {
                    "user_email": "invalid",
                    "user_password": "TestPass123!@",
                    "user_first_name": "John Smith",
                    "user_country_code": "GB",
                },
                422,
                "value is not a valid email address: An email address must have an @-sign.",
            ),
            (
                {
                    "user_email": "test@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "John Smith 3rd",
                    "user_country_code": "GB",
                },
                422,
                "Value error, First name can only contain letters, spaces, and hyphens",
            ),
            (
                {
                    "user_email": "test@example.com",
                    "user_password": "TestPass123!@",
                    "user_first_name": "John Smith",
                    "user_country_code": "USA",
                },
                422,
                "String should have at most 2 characters",
            ),
        ],
    )
    def test_create_user_validation_errors(
        self, client, test_input, expected_status, expected_detail
    ):
        """Test validation errors in user creation."""
        response = client.post(f"{API_VERSION}/user", json=test_input)
        assert response.status_code == expected_status
        assert expected_detail in response.json()["detail"][0]["msg"]


class TestUserLogin:
    def test_login_user(self, client):
        """Test user login with correct credentials."""
        client.post(
            f"{API_VERSION}/user",
            json={
                "user_email": "testuser@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Test",
                "user_country_code": "GB",
            },
        )

        response = client.post(
            f"{API_VERSION}/user/auth/login",
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
            f"{API_VERSION}/user/auth/login",
            json={
                "user_email": "testuser@example.com",
                "user_password": "WrongPassword!",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"
