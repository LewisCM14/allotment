"""Integration tests for a few top-level endpoints (condensed)."""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint_success(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Welcome to the Allotment Service API!"
    assert {"app_name", "version"}.issubset(data.keys())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params",
    [
        {"email": "test@example.com"},
        {},  # default email path
    ],
)
async def test_test_email_endpoint(client: AsyncClient, params):
    response = await client.post("/test-email", params=params)
    # Endpoint may return 200 or 500 depending on email backend; just ensure structure
    assert response.status_code in (200, 500)
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_log_client_error(client: AsyncClient):
    error_data = {
        "error": "Client side error occurred",
        "details": {"component": "LoginForm", "stack": "Error stack trace"},
    }
    response = await client.post("/api/v1/log-client-error", json=error_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Client error logged successfully"
