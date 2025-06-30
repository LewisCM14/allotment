"""
Health API Tests
"""

import pytest

from app.api.core.config import settings

PREFIX = settings.API_PREFIX


@pytest.mark.asyncio
async def test_health(client):
    """Test the /health endpoint"""
    response = await client.get(f"{PREFIX}/health")

    assert response.status_code == 200

    json_data = response.json()
    assert "status" in json_data
    assert "uptime" in json_data
    assert "version" in json_data
    assert "database" in json_data
    assert "resources" in json_data
    assert "cpu_usage" in json_data["resources"]
    assert "memory_usage" in json_data["resources"]
    assert "disk_usage" in json_data["resources"]
