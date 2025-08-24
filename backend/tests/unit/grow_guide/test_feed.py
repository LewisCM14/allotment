from unittest.mock import Mock

import pytest
from fastapi import Request

from app.api.v1.grow_guide.feed import get_feeds
from tests.conftest import TestingSessionLocal


def _assert_feed_objects(feeds):
    assert feeds, "Expected non-empty feed list"
    ids = set()
    names = set()
    for f in feeds:
        assert f.id is not None
        assert f.name and isinstance(f.name, str)
        ids.add(f.id)
        names.add(f.name)
    assert len(ids) == len(feeds), "Duplicate feed IDs detected"
    assert len(names) == len(feeds), "Duplicate feed names detected"


class TestFeedEndpointUnit:
    @pytest.mark.asyncio
    async def test_get_feeds_unit_happy_path(self, seed_feed_data):
        mock_request = Mock(spec=Request)
        async with TestingSessionLocal() as db:
            result = await get_feeds(mock_request, db)
        assert len(result) == 5
        _assert_feed_objects(result)
        names = {f.name for f in result}
        # Spot check a few seeded feeds (allow flexible set membership)
        expected_any = {"Tomato Feed", "General Purpose Feed"}
        assert expected_any.issubset(names)

    @pytest.mark.asyncio
    async def test_get_feeds_unit_empty(self):
        mock_request = Mock(spec=Request)
        async with TestingSessionLocal() as db:
            result = await get_feeds(mock_request, db)
        assert result == []
