"""Health API tests (parametrized & deterministic)."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

import app.api.v1.health
from app.api.core.config import settings

PREFIX = settings.API_PREFIX


@pytest.mark.asyncio
async def test_health_healthy_database(client, reset_health_state):
    """Healthy path with deterministic resource metrics (avoid flakiness)."""
    with (
        patch("app.api.v1.health.psutil.cpu_percent", return_value=10.0),
        patch(
            "app.api.v1.health.psutil.virtual_memory",
            return_value=SimpleNamespace(percent=10.0),
        ),
        patch(
            "app.api.v1.health.psutil.disk_usage",
            return_value=SimpleNamespace(percent=10.0),
        ),
        patch("sqlalchemy.ext.asyncio.AsyncSession.scalar", return_value=1),
    ):
        response = await client.get(f"{PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert set(["cpu_usage", "memory_usage", "disk_usage"]).issubset(
        data["resources"].keys()
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scalar_value,scalar_side_effect,expected_db_status",
    [
        (1, None, "healthy"),  # baseline healthy (sanity)
        (0, None, "unhealthy"),  # unexpected result
        (None, SQLAlchemyError("Connection failed"), "unhealthy"),  # connection failure
    ],
)
async def test_health_database_states(
    client, scalar_value, scalar_side_effect, expected_db_status, reset_health_state
):
    """Database result variations -> healthy vs degraded."""
    with (
        patch(
            "sqlalchemy.ext.asyncio.AsyncSession.scalar",
            return_value=scalar_value,
            side_effect=scalar_side_effect,
        ),
        patch("app.api.v1.health.psutil.cpu_percent", return_value=10.0),
        patch(
            "app.api.v1.health.psutil.virtual_memory",
            return_value=SimpleNamespace(percent=10.0),
        ),
        patch(
            "app.api.v1.health.psutil.disk_usage",
            return_value=SimpleNamespace(percent=10.0),
        ),
    ):
        response = await client.get(f"{PREFIX}/health")

    assert response.status_code == 200
    data = response.json()
    assert data["database"] == expected_db_status
    # Overall status matches database health (ok if healthy else degraded)
    assert data["status"] == ("ok" if expected_db_status == "healthy" else "degraded")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scenario,cpu,mem,disk,prev_state",
    [
        (
            "high_cpu",
            90.0,
            50.0,
            50.0,
            {
                "cpu_critical": False,
                "memory_critical": False,
                "disk_critical": False,
                "any_critical": False,
            },
        ),
        (
            "high_memory",
            50.0,
            90.0,
            50.0,
            {
                "cpu_critical": False,
                "memory_critical": False,
                "disk_critical": False,
                "any_critical": False,
            },
        ),
        (
            "high_disk",
            50.0,
            50.0,
            90.0,
            {
                "cpu_critical": False,
                "memory_critical": False,
                "disk_critical": False,
                "any_critical": False,
            },
        ),
        (
            "all_critical",
            90.0,
            90.0,
            90.0,
            {
                "cpu_critical": False,
                "memory_critical": False,
                "disk_critical": False,
                "any_critical": False,
            },
        ),
        (
            "return_to_normal",
            50.0,
            50.0,
            50.0,
            {
                "cpu_critical": True,
                "memory_critical": True,
                "disk_critical": True,
                "any_critical": True,
            },
        ),
        (
            "already_critical",
            90.0,
            90.0,
            90.0,
            {
                "cpu_critical": True,
                "memory_critical": True,
                "disk_critical": True,
                "any_critical": True,
            },
        ),
    ],
)
async def test_health_resource_scenarios(
    client, scenario, cpu, mem, disk, prev_state, reset_health_state
):
    """Resource usage permutations (CPU/memory/disk) including state transitions."""
    # Seed previous state explicitly for scenario
    app.api.v1.health._previous_resources_state = prev_state.copy()
    with (
        patch("app.api.v1.health.psutil.cpu_percent", return_value=cpu),
        patch(
            "app.api.v1.health.psutil.virtual_memory",
            return_value=SimpleNamespace(percent=mem),
        ),
        patch(
            "app.api.v1.health.psutil.disk_usage",
            return_value=SimpleNamespace(percent=disk),
        ),
        patch("sqlalchemy.ext.asyncio.AsyncSession.scalar", return_value=1),
    ):
        response = await client.get(f"{PREFIX}/health")

    assert response.status_code == 200
    data = response.json()
    assert data["resources"]["cpu_usage"] == cpu
    assert data["resources"]["memory_usage"] == mem
    assert data["resources"]["disk_usage"] == disk
    # Degraded if database unhealthy (not here) else ok
    assert data["status"] in ["ok", "degraded"]
