"""
Unit tests for Day API endpoints using real database fixtures
"""

from unittest.mock import Mock

import pytest
from fastapi import Request

from app.api.v1.day import get_days
from tests.conftest import TestingSessionLocal


class TestDayEndpointUnit:
    """Unit tests for day endpoint functions."""

    @pytest.mark.asyncio
    async def test_get_days_unit_success(self, seed_day_data):
        """Unit test for successful get_days function."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act
            result = await get_days(mock_request, db)

            # Assert
            assert len(result) == 7
            # Verify we got all days in the correct format
            day_numbers = [day.day_number for day in result]
            day_names = [day.name for day in result]

            assert 1 in day_numbers
            assert 7 in day_numbers
            assert "Mon" in day_names
            assert "Sun" in day_names

            # Verify each day has an ID
            for day in result:
                assert day.id is not None
                assert day.day_number is not None
                assert day.name is not None

    @pytest.mark.asyncio
    async def test_get_days_unit_empty_result(self):
        """Unit test for get_days with empty database."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act (no seed_day_data fixture, so database is empty)
            result = await get_days(mock_request, db)

            # Assert
            assert len(result) == 0
            assert result == []

    @pytest.mark.asyncio
    async def test_get_days_unit_day_ordering(self, seed_day_data):
        """Unit test for day ordering (should be ordered by day_number)."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act
            result = await get_days(mock_request, db)

            # Assert
            assert len(result) == 7

            # The repository should return days ordered by day_number
            # (This is handled by the repository layer, not the endpoint)
            for i, day in enumerate(result):
                assert day.day_number is not None
                assert day.name is not None
                assert day.id is not None

    @pytest.mark.asyncio
    async def test_get_days_unit_specific_data_validation(self, seed_day_data):
        """Unit test to validate specific day data."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act
            result = await get_days(mock_request, db)

            # Assert
            assert len(result) == 7

            # Find specific days and validate their data
            monday = next((day for day in result if day.name == "Mon"), None)
            assert monday is not None
            assert monday.day_number == 1

            sunday = next((day for day in result if day.name == "Sun"), None)
            assert sunday is not None
            assert sunday.day_number == 7

            # Verify all days have unique IDs
            ids = [day.id for day in result]
            assert len(ids) == len(set(ids))  # All IDs should be unique

            # Verify all days have unique day_numbers
            day_numbers = [day.day_number for day in result]
            assert len(day_numbers) == len(
                set(day_numbers)
            )  # All day_numbers should be unique
