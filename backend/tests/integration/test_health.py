"""
Health API Tests
"""

from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

import app.api.v1.health
from app.api.core.config import settings

PREFIX = settings.API_PREFIX


@pytest.mark.asyncio
async def test_health_healthy_database(client):
    """Test the /health endpoint with healthy database"""
    response = await client.get(f"{PREFIX}/health")

    assert response.status_code == 200

    json_data = response.json()
    assert "status" in json_data
    assert json_data["status"] == "ok"
    assert "uptime" in json_data
    assert "version" in json_data
    assert json_data["database"] == "healthy"
    assert "resources" in json_data
    assert "cpu_usage" in json_data["resources"]
    assert "memory_usage" in json_data["resources"]
    assert "disk_usage" in json_data["resources"]


@pytest.mark.asyncio
async def test_health_database_connection_failure(client):
    """Test the /health endpoint when database connection fails"""
    with patch(
        "sqlalchemy.ext.asyncio.AsyncSession.scalar",
        side_effect=SQLAlchemyError("Connection failed"),
    ):
        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "degraded"
        assert json_data["database"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_database_query_returns_unexpected_result(client):
    """Test the /health endpoint when database query returns unexpected result"""
    with patch("sqlalchemy.ext.asyncio.AsyncSession.scalar", return_value=0):
        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "degraded"
        assert json_data["database"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_high_cpu_usage(client):
    """Test the /health endpoint with high CPU usage"""
    with patch("app.api.v1.health.psutil.cpu_percent", return_value=90.0):
        app.api.v1.health._previous_resources_state = {
            "cpu_critical": False,
            "memory_critical": False,
            "disk_critical": False,
            "any_critical": False,
        }

        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["resources"]["cpu_usage"] == 90.0


@pytest.mark.asyncio
async def test_health_high_memory_usage(client):
    """Test the /health endpoint with high memory usage"""
    with patch("app.api.v1.health.psutil.virtual_memory") as mock_memory:
        mock_memory.return_value.percent = 90.0
        app.api.v1.health._previous_resources_state = {
            "cpu_critical": False,
            "memory_critical": False,
            "disk_critical": False,
            "any_critical": False,
        }

        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["resources"]["memory_usage"] == 90.0


@pytest.mark.asyncio
async def test_health_high_disk_usage(client):
    """Test the /health endpoint with high disk usage"""
    with patch("app.api.v1.health.psutil.disk_usage") as mock_disk:
        mock_disk.return_value.percent = 90.0
        app.api.v1.health._previous_resources_state = {
            "cpu_critical": False,
            "memory_critical": False,
            "disk_critical": False,
            "any_critical": False,
        }

        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["resources"]["disk_usage"] == 90.0


@pytest.mark.asyncio
async def test_health_all_resources_critical(client):
    """Test the /health endpoint with all resources critical"""
    with (
        patch("app.api.v1.health.psutil.cpu_percent", return_value=90.0),
        patch("app.api.v1.health.psutil.virtual_memory") as mock_memory,
        patch("app.api.v1.health.psutil.disk_usage") as mock_disk,
    ):
        mock_memory.return_value.percent = 90.0
        mock_disk.return_value.percent = 90.0

        app.api.v1.health._previous_resources_state = {
            "cpu_critical": False,
            "memory_critical": False,
            "disk_critical": False,
            "any_critical": False,
        }

        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["resources"]["cpu_usage"] == 90.0
        assert json_data["resources"]["memory_usage"] == 90.0
        assert json_data["resources"]["disk_usage"] == 90.0


@pytest.mark.asyncio
async def test_health_resources_return_to_normal(client):
    """Test the /health endpoint when resources return to normal levels"""
    app.api.v1.health._previous_resources_state = {
        "cpu_critical": True,
        "memory_critical": True,
        "disk_critical": True,
        "any_critical": True,
    }

    with (
        patch("app.api.v1.health.psutil.cpu_percent", return_value=50.0),
        patch("app.api.v1.health.psutil.virtual_memory") as mock_memory,
        patch("app.api.v1.health.psutil.disk_usage") as mock_disk,
    ):
        mock_memory.return_value.percent = 50.0
        mock_disk.return_value.percent = 50.0

        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["resources"]["cpu_usage"] == 50.0
        assert json_data["resources"]["memory_usage"] == 50.0
        assert json_data["resources"]["disk_usage"] == 50.0


@pytest.mark.asyncio
async def test_health_no_state_change_when_already_critical(client):
    """Test the /health endpoint when resources are already critical"""
    app.api.v1.health._previous_resources_state = {
        "cpu_critical": True,
        "memory_critical": True,
        "disk_critical": True,
        "any_critical": True,
    }

    with (
        patch("app.api.v1.health.psutil.cpu_percent", return_value=90.0),
        patch("app.api.v1.health.psutil.virtual_memory") as mock_memory,
        patch("app.api.v1.health.psutil.disk_usage") as mock_disk,
    ):
        mock_memory.return_value.percent = 90.0
        mock_disk.return_value.percent = 90.0

        response = await client.get(f"{PREFIX}/health")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["resources"]["cpu_usage"] == 90.0
        assert json_data["resources"]["memory_usage"] == 90.0
        assert json_data["resources"]["disk_usage"] == 90.0
