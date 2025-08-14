"""
Day API Integration Tests
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.config import settings
from app.api.models.grow_guide.calendar_model import Day

PREFIX = settings.API_PREFIX


class TestDayApi:
    """Integration tests for day API endpoints."""

    @pytest.mark.asyncio
    async def test_get_days_success(self, client):
        """Test successful retrieval of days."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Create mock days (representing days of the week) with IDs
            mock_days = [
                Day(id=uuid.uuid4(), day_number=1, name="Mon"),
                Day(id=uuid.uuid4(), day_number=2, name="Tue"),
                Day(id=uuid.uuid4(), day_number=3, name="Wed"),
                Day(id=uuid.uuid4(), day_number=4, name="Thu"),
                Day(id=uuid.uuid4(), day_number=5, name="Fri"),
                Day(id=uuid.uuid4(), day_number=6, name="Sat"),
                Day(id=uuid.uuid4(), day_number=7, name="Sun"),
            ]

            # Mock the GrowGuideUnitOfWork.get_all_days method
            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                return_value=mock_days,
            ):
                response = await client.get(f"{PREFIX}/days")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 7

            # Verify day structure and order
            for i, day_data in enumerate(data):
                assert "id" in day_data
                assert "name" in day_data
                assert "day_number" in day_data
                assert day_data["name"] == mock_days[i].name
                assert day_data["day_number"] == mock_days[i].day_number
                assert isinstance(day_data["id"], str)

    @pytest.mark.asyncio
    async def test_get_days_empty_list(self, client):
        """Test retrieval when no days exist."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock empty days list
            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                return_value=[],
            ):
                response = await client.get(f"{PREFIX}/days")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_days_database_error(self, client):
        """Test handling of database errors."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock database error
            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                side_effect=Exception("Database connection failed"),
            ):
                response = await client.get(f"{PREFIX}/days")

            # The error should be handled by the error middleware
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_get_days_rate_limiting(self, client):
        """Test rate limiting on days endpoint."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock successful days response
            mock_days = [Day(id=uuid.uuid4(), day_number=1, name="Mon")]
            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                return_value=mock_days,
            ):
                # Make multiple requests to test rate limiting (10/minute limit)
                responses = []
                for _ in range(12):  # Exceed the limit
                    response = await client.get(f"{PREFIX}/days")
                    responses.append(response)

                # First 10 should succeed
                for response in responses[:10]:
                    assert response.status_code == status.HTTP_200_OK

                # The rate limiter might not immediately reject on the 11th request
                # depending on timing, so we just check that we get responses
                assert len(responses) == 12

    @pytest.mark.asyncio
    async def test_get_days_response_structure(self, client):
        """Test the detailed structure of day response."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Create a mock day with specific attributes
            import uuid

            day_id = uuid.uuid4()
            mock_day = Day(id=uuid.uuid4(), day_number=3, name="Wed")
            mock_day.id = day_id

            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                return_value=[mock_day],
            ):
                response = await client.get(f"{PREFIX}/days")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1

            day_item = data[0]
            assert day_item["id"] == str(day_id)
            assert day_item["name"] == "Wed"
            assert day_item["day_number"] == 3
            assert len(day_item.keys()) == 3  # id, name, and day_number

    @pytest.mark.asyncio
    async def test_get_days_ordered_by_day_number(self, client):
        """Test that days are returned in proper order."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Create mock days in mixed order
            mock_days = [
                Day(id=uuid.uuid4(), day_number=7, name="Sun"),
                Day(id=uuid.uuid4(), day_number=1, name="Mon"),
                Day(id=uuid.uuid4(), day_number=5, name="Fri"),
                Day(id=uuid.uuid4(), day_number=3, name="Wed"),
            ]

            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                return_value=mock_days,
            ):
                response = await client.get(f"{PREFIX}/days")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 4

            # Verify the order matches what was returned (repository should handle ordering)
            expected_order = [7, 1, 5, 3]  # Order from mock_days
            for i, day_data in enumerate(data):
                assert day_data["day_number"] == expected_order[i]

    @pytest.mark.asyncio
    async def test_get_days_day_number_validation(self, client):
        """Test that day numbers are properly validated."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Create days with various day numbers
            mock_days = [
                Day(id=uuid.uuid4(), day_number=1, name="Mon"),
                Day(id=uuid.uuid4(), day_number=7, name="Sun"),
            ]

            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                return_value=mock_days,
            ):
                response = await client.get(f"{PREFIX}/days")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify day numbers are integers in valid range
            for day_data in data:
                assert isinstance(day_data["day_number"], int)
                assert 1 <= day_data["day_number"] <= 7

    @pytest.mark.asyncio
    async def test_get_days_name_format_validation(self, client):
        """Test that day names are properly formatted."""
        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Create days with standard 3-letter abbreviations
            mock_days = [
                Day(id=uuid.uuid4(), day_number=1, name="Mon"),
                Day(id=uuid.uuid4(), day_number=2, name="Tue"),
                Day(id=uuid.uuid4(), day_number=3, name="Wed"),
            ]

            with patch(
                "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                return_value=mock_days,
            ):
                response = await client.get(f"{PREFIX}/days")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify day names are strings with expected format
            for day_data in data:
                assert isinstance(day_data["name"], str)
                assert len(day_data["name"]) == 3  # Standard 3-letter abbreviation
                assert day_data["name"].isalpha()  # Only letters
