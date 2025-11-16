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
async def test_log_client_error(client: AsyncClient):
    error_data = {
        "error": "Client side error occurred",
        "details": {"component": "LoginForm", "stack": "Error stack trace"},
    }
    response = await client.post("/api/v1/log-client-error", json=error_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Client error logged successfully"
