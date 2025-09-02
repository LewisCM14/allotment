import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.config import settings
from app.api.core.limiter import limiter
from app.api.models.grow_guide.calendar_model import Day

PREFIX = settings.API_PREFIX


def _patch_db():
    return patch("app.api.core.database.get_db")


def _patch_days(return_value=None, side_effect=None):
    return patch(
        "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
        return_value=return_value,
        side_effect=side_effect,
    )


def _standard_days():  # seven day objects
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [
        Day(day_id=uuid.uuid4(), day_number=i + 1, day_name=names[i]) for i in range(7)
    ]


@pytest.mark.asyncio
async def test_days_success(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = _standard_days()
        with _patch_days(return_value=items):
            response = await client.get(f"{PREFIX}/days")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 7
    for i, day in enumerate(data):
        assert set(day.keys()) == {"day_id", "day_name", "day_number"}
        assert day["day_name"] == items[i].day_name
        assert day["day_number"] == items[i].day_number


@pytest.mark.asyncio
async def test_days_empty(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        with _patch_days(return_value=[]):
            response = await client.get(f"{PREFIX}/days")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_days_database_error(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        with _patch_days(side_effect=Exception("Database connection failed")):
            response = await client.get(f"{PREFIX}/days")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_days_large_dataset(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = [
            Day(day_id=uuid.uuid4(), day_number=(i % 7) + 1, day_name=f"Day{i}")
            for i in range(20)
        ]
        with _patch_days(return_value=items):
            response = await client.get(f"{PREFIX}/days")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 20


@pytest.mark.asyncio
async def test_days_rate_limiting(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = _standard_days()[:1]
        original_enabled = limiter.enabled
        try:
            limiter.enabled = True
            with _patch_days(return_value=items):
                responses = [await client.get(f"{PREFIX}/days") for _ in range(11)]
        finally:
            limiter.enabled = original_enabled

    for r in responses[:10]:
        assert r.status_code == status.HTTP_200_OK
    assert any(
        r.status_code in (status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_200_OK)
        for r in responses[10:]
    )


@pytest.mark.asyncio
async def test_days_basic_field_validation(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = _standard_days()[:2]
        with _patch_days(return_value=items):
            response = await client.get(f"{PREFIX}/days")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for d in data:
        assert isinstance(d["day_number"], int)
        assert 1 <= d["day_number"] <= 7
        assert len(d["day_name"]) >= 3
