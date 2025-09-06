"""
Integration tests for Week endpoints.
"""

import pytest
from fastapi import status


class TestWeekEndpoints:
    """Test suite for week API endpoints."""

    @pytest.mark.asyncio
    async def test_get_weeks_success(self, client, seed_week_data):
        """Test successful retrieval of all weeks."""
        # Act
        response = await client.get("/api/v1/weeks")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        weeks = response.json()
        assert isinstance(weeks, list)
        assert len(weeks) == 3  # Based on seed data

        # Verify structure of first week
        week = weeks[0]
        assert "week_id" in week
        assert "week_number" in week
        assert "week_start_date" in week
        assert "week_end_date" in week

        # Verify data types
        assert isinstance(week["week_id"], str)
        assert isinstance(week["week_number"], int)
        assert isinstance(week["week_start_date"], str)
        assert isinstance(week["week_end_date"], str)

    @pytest.mark.asyncio
    async def test_get_weeks_empty_database(self, client):
        """Test retrieval when no weeks exist in database."""
        # Act
        response = await client.get("/api/v1/weeks")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        weeks = response.json()
        assert isinstance(weeks, list)
        assert len(weeks) == 0

    @pytest.mark.asyncio
    async def test_get_weeks_validates_response_schema(self, client, seed_week_data):
        """Test that response conforms to expected schema."""
        # Act
        response = await client.get("/api/v1/weeks")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        weeks = response.json()

        for week in weeks:
            # Verify required fields exist
            required_fields = [
                "week_id",
                "week_number",
                "week_start_date",
                "week_end_date",
            ]
            for field in required_fields:
                assert field in week, f"Missing required field: {field}"

            # Verify week_id is valid UUID format
            import uuid

            uuid.UUID(week["week_id"])  # Will raise ValueError if invalid

            # Verify week_number is valid (1-53)
            assert 1 <= week["week_number"] <= 53

    @pytest.mark.asyncio
    async def test_get_weeks_content_verification(self, client, seed_week_data):
        """Test that week data matches seeded content."""
        # Act
        response = await client.get("/api/v1/weeks")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        weeks = response.json()

        # Create lookup for easier validation
        week_lookup = {w["week_number"]: w for w in weeks}

        # Verify Week 1
        week1 = week_lookup.get(1)
        assert week1 is not None
        assert week1["week_start_date"] == "01/01"
        assert week1["week_end_date"] == "07/01"

        # Verify Week 2
        week2 = week_lookup.get(2)
        assert week2 is not None
        assert week2["week_start_date"] == "08/01"
        assert week2["week_end_date"] == "14/01"

        # Verify Week 52
        week52 = week_lookup.get(52)
        assert week52 is not None
        assert week52["week_start_date"] == "25/12"
        assert week52["week_end_date"] == "31/12"

    @pytest.mark.asyncio
    async def test_get_weeks_rate_limiting(self, client, seed_week_data):
        """Test that rate limiting is configured (endpoint should be accessible within limits)."""
        # Act - make multiple requests within rate limit
        responses = []
        for _ in range(5):  # Well under the 10/minute limit
            response = await client.get("/api/v1/weeks")
            responses.append(response)

        # Assert - all requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_weeks_consistent_ordering(self, client, seed_week_data):
        """Test that week results are returned in consistent order."""
        # Act - make multiple requests
        response1 = await client.get("/api/v1/weeks")
        response2 = await client.get("/api/v1/weeks")

        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        weeks1 = response1.json()
        weeks2 = response2.json()

        # Results should be identical
        assert len(weeks1) == len(weeks2)

        # Compare by week_id to ensure same items in same order
        week_ids1 = [w["week_id"] for w in weeks1]
        week_ids2 = [w["week_id"] for w in weeks2]
        assert week_ids1 == week_ids2

    @pytest.mark.asyncio
    async def test_get_weeks_date_format_validation(self, client, seed_week_data):
        """Test that week dates are in expected DD/MM format."""
        # Act
        response = await client.get("/api/v1/weeks")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        weeks = response.json()

        for week in weeks:
            start_date = week["week_start_date"]
            end_date = week["week_end_date"]

            # Verify date format (DD/MM)
            assert len(start_date) == 5, (
                f"Start date should be DD/MM format: {start_date}"
            )
            assert start_date[2] == "/", (
                f"Start date should have / separator: {start_date}"
            )

            assert len(end_date) == 5, f"End date should be DD/MM format: {end_date}"
            assert end_date[2] == "/", f"End date should have / separator: {end_date}"

            # Verify day and month parts are numeric
            start_day, start_month = start_date.split("/")
            end_day, end_month = end_date.split("/")

            assert start_day.isdigit() and start_month.isdigit()
            assert end_day.isdigit() and end_month.isdigit()

            # Verify reasonable ranges
            assert 1 <= int(start_day) <= 31
            assert 1 <= int(start_month) <= 12
            assert 1 <= int(end_day) <= 31
            assert 1 <= int(end_month) <= 12

    @pytest.mark.asyncio
    async def test_get_weeks_sorted_by_number(self, client, seed_week_data):
        """Test that weeks are returned in chronological order."""
        # Act
        response = await client.get("/api/v1/weeks")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        weeks = response.json()

        if len(weeks) > 1:
            # Check if weeks are sorted by week_number
            week_numbers = [w["week_number"] for w in weeks]
            assert week_numbers == sorted(week_numbers), (
                "Weeks should be sorted by week_number"
            )
