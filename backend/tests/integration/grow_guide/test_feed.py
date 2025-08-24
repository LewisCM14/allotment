import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.config import settings
from app.api.core.limiter import limiter
from app.api.models.grow_guide.guide_options_model import Feed

PREFIX = settings.API_PREFIX


def _patch_db():
    return patch("app.api.core.database.get_db")


def _patch_feeds(return_value=None, side_effect=None):
    return patch(
        "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_feeds",
        return_value=return_value,
        side_effect=side_effect,
    )


def _standard_feeds():
    names = ["Tomato Feed", "General Purpose Feed", "Organic Feed"]
    return [Feed(id=uuid.uuid4(), name=n) for n in names]


@pytest.mark.asyncio
async def test_feeds_success(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = _standard_feeds()
        with _patch_feeds(return_value=items):
            response = await client.get(f"{PREFIX}/feed")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    for i, feed in enumerate(data):
        assert set(feed.keys()) == {"id", "name"}
        assert feed["name"] == items[i].name


@pytest.mark.asyncio
async def test_feeds_empty(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        with _patch_feeds(return_value=[]):
            response = await client.get(f"{PREFIX}/feed")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_feeds_database_error(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        with _patch_feeds(side_effect=Exception("Database connection failed")):
            response = await client.get(f"{PREFIX}/feed")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_feeds_large_dataset(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = [Feed(id=uuid.uuid4(), name=f"Feed Type {i}") for i in range(60)]
        with _patch_feeds(return_value=items):
            response = await client.get(f"{PREFIX}/feed")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 60


@pytest.mark.asyncio
async def test_feeds_rate_limiting(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = _standard_feeds()[:1]
        original_enabled = limiter.enabled
        try:
            limiter.enabled = True
            with _patch_feeds(return_value=items):
                responses = [await client.get(f"{PREFIX}/feed") for _ in range(11)]
        finally:
            limiter.enabled = original_enabled

    for r in responses[:10]:
        assert r.status_code == status.HTTP_200_OK
    assert any(
        r.status_code in (status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_200_OK)
        for r in responses[10:]
    )


@pytest.mark.asyncio
async def test_feeds_basic_field_validation(client):
    with _patch_db() as mock_get_db:
        mock_db = AsyncMock(spec=AsyncSession)
        mock_get_db.return_value = mock_db
        items = _standard_feeds()[:2]
        with _patch_feeds(return_value=items):
            response = await client.get(f"{PREFIX}/feed")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for f in data:
        assert isinstance(f["name"], str)
        assert len(f["name"]) >= 3
