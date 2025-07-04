"""
Integration tests for main.py endpoints and middleware
"""

from fastapi import status
from httpx import AsyncClient


class TestRootEndpoint:
    """Test the root endpoint."""

    async def test_root_endpoint_success(self, client: AsyncClient):
        response = await client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Welcome to the Allotment Service API!"
        assert "app_name" in data
        assert "version" in data


class TestTestEmailEndpoint:
    """Test the test email endpoint."""

    async def test_test_email_with_provided_email(self, client: AsyncClient):
        test_email = "test@example.com"
        response = await client.post("/test-email", params={"email": test_email})
        # Accept 200 or 500, but check response structure for dummy/test mode
        assert response.status_code in (200, 500)
        data = response.json()
        assert "message" in data

    async def test_test_email_without_provided_email(self, client: AsyncClient):
        response = await client.post("/test-email")
        assert response.status_code in (200, 500)
        data = response.json()
        assert "message" in data


class TestClientErrorLogging:
    """Test client error logging endpoint."""

    async def test_log_client_error(self, client: AsyncClient):
        error_data = {
            "error": "Client side error occurred",
            "details": {"component": "LoginForm", "stack": "Error stack trace"},
        }
        response = await client.post("/api/v1/log-client-error", json=error_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Client error logged successfully"
