"""
Integration tests for Month endpoints.
"""

import pytest
from fastapi import status


class TestMonthEndpoints:
    """Test suite for month API endpoints."""

    @pytest.mark.asyncio
    async def test_get_months_success(self, client, seed_week_data):
        """Test successful retrieval of all months."""
        # Act
        response = await client.get("/api/v1/months")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        months = response.json()
        assert isinstance(months, list)
        assert len(months) == 3  # Based on seed data

        # Verify structure of first month
        month = months[0]
        assert "month_id" in month
        assert "month_number" in month
        assert "month_name" in month

        # Verify data types
        assert isinstance(month["month_id"], str)
        assert isinstance(month["month_number"], int)
        assert isinstance(month["month_name"], str)

        # Verify expected month names are present
        month_names = [m["month_name"] for m in months]
        assert "January" in month_names
        assert "February" in month_names
        assert "December" in month_names

    @pytest.mark.asyncio
    async def test_get_months_empty_database(self, client):
        """Test retrieval when no months exist in database."""
        # Act
        response = await client.get("/api/v1/months")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        months = response.json()
        assert isinstance(months, list)
        assert len(months) == 0

    @pytest.mark.asyncio
    async def test_get_months_validates_response_schema(self, client, seed_week_data):
        """Test that response conforms to expected schema."""
        # Act
        response = await client.get("/api/v1/months")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        months = response.json()

        for month in months:
            # Verify required fields exist
            required_fields = ["month_id", "month_number", "month_name"]
            for field in required_fields:
                assert field in month, f"Missing required field: {field}"

            # Verify month_id is valid UUID format
            import uuid

            uuid.UUID(month["month_id"])  # Will raise ValueError if invalid

            # Verify month_number is valid (1-12)
            assert 1 <= month["month_number"] <= 12

    @pytest.mark.asyncio
    async def test_get_months_content_verification(self, client, seed_week_data):
        """Test that month data matches seeded content."""
        # Act
        response = await client.get("/api/v1/months")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        months = response.json()

        # Create lookup for easier validation
        month_lookup = {m["month_name"]: m for m in months}

        # Verify January
        january = month_lookup.get("January")
        assert january is not None
        assert january["month_number"] == 1

        # Verify February
        february = month_lookup.get("February")
        assert february is not None
        assert february["month_number"] == 2

        # Verify December
        december = month_lookup.get("December")
        assert december is not None
        assert december["month_number"] == 12

    @pytest.mark.asyncio
    async def test_get_months_rate_limiting(self, client, seed_week_data):
        """Test that rate limiting is configured (endpoint should be accessible within limits)."""
        # Act - make multiple requests within rate limit
        responses = []
        for _ in range(5):  # Well under the 10/minute limit
            response = await client.get("/api/v1/months")
            responses.append(response)

        # Assert - all requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_months_consistent_ordering(self, client, seed_week_data):
        """Test that month results are returned in consistent order."""
        # Act - make multiple requests
        response1 = await client.get("/api/v1/months")
        response2 = await client.get("/api/v1/months")

        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        months1 = response1.json()
        months2 = response2.json()

        # Results should be identical
        assert len(months1) == len(months2)

        # Compare by month_id to ensure same items in same order
        month_ids1 = [m["month_id"] for m in months1]
        month_ids2 = [m["month_id"] for m in months2]
        assert month_ids1 == month_ids2

    @pytest.mark.asyncio
    async def test_get_months_number_name_consistency(self, client, seed_week_data):
        """Test that month numbers and names are consistent."""
        # Act
        response = await client.get("/api/v1/months")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        months = response.json()

        # Expected mappings based on seed data
        expected_mappings = {1: "January", 2: "February", 12: "December"}

        for month in months:
            month_number = month["month_number"]
            month_name = month["month_name"]

            # Verify the number-name mapping is correct
            if month_number in expected_mappings:
                assert month_name == expected_mappings[month_number]

    @pytest.mark.asyncio
    async def test_get_months_sorted_by_number(self, client, seed_week_data):
        """Test that months are returned in chronological order."""
        # Act
        response = await client.get("/api/v1/months")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        months = response.json()

        if len(months) > 1:
            # Check if months are sorted by month_number
            month_numbers = [m["month_number"] for m in months]
            assert month_numbers == sorted(month_numbers), (
                "Months should be sorted by month_number"
            )
