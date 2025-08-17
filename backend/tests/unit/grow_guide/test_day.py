from unittest.mock import Mock

import pytest
from fastapi import Request

from app.api.v1.day import get_days
from tests.conftest import TestingSessionLocal


def _assert_day_objects(days):
    """Common structural & uniqueness assertions for day objects."""
    assert days, "Expected non-empty days list"
    ids = set()
    numbers = []
    for d in days:
        assert d.id is not None
        assert d.name and isinstance(d.name, str)
        assert isinstance(d.day_number, int)
        ids.add(d.id)
        numbers.append(d.day_number)
    assert len(ids) == len(days), "Duplicate day IDs detected"
    assert len(set(numbers)) == len(days), "Duplicate day numbers detected"
    # Ordering (repository applies ORDER BY day_number asc)
    assert numbers == sorted(numbers), "Days not ordered by day_number ascending"


class TestDayEndpointUnit:
    """Day endpoint function tests (bypassing HTTP layer)."""

    @pytest.mark.asyncio
    async def test_get_days_unit_happy_path(self, seed_day_data):
        mock_request = Mock(spec=Request)
        async with TestingSessionLocal() as db:
            result = await get_days(mock_request, db)

        assert len(result) == 7
        _assert_day_objects(result)
        # Spot check boundary days
        names = {d.name for d in result}
        assert {"Mon", "Sun"}.issubset(names)
        day_map = {d.name: d.day_number for d in result}
        assert day_map["Mon"] == 1
        assert day_map["Sun"] == 7

    @pytest.mark.asyncio
    async def test_get_days_unit_empty(self):
        mock_request = Mock(spec=Request)
        async with TestingSessionLocal() as db:
            result = await get_days(mock_request, db)
        assert result == []
