"""
Integration tests for Frequency endpoints.
"""

import pytest
from fastapi import status


class TestFrequencyEndpoints:
    """Test suite for frequency API endpoints."""

    @pytest.mark.asyncio
    async def test_get_frequencies_success(self, client, seed_frequency_data):
        """Test successful retrieval of all frequencies."""
        # Act
        response = await client.get("/api/v1/frequencies")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        frequencies = response.json()
        assert isinstance(frequencies, list)
        assert len(frequencies) == 3  # Based on seed data

        # Verify structure of first frequency
        frequency = frequencies[0]
        assert "frequency_id" in frequency
        assert "frequency_name" in frequency
        assert "frequency_days_per_year" in frequency

        # Verify data types
        assert isinstance(frequency["frequency_id"], str)
        assert isinstance(frequency["frequency_name"], str)
        assert isinstance(frequency["frequency_days_per_year"], int)

        # Verify expected frequency names are present
        frequency_names = [freq["frequency_name"] for freq in frequencies]
        assert "Daily" in frequency_names
        assert "Weekly" in frequency_names
        assert "Monthly" in frequency_names

    @pytest.mark.asyncio
    async def test_get_frequencies_empty_database(self, client):
        """Test retrieval when no frequencies exist in database."""
        # Act
        response = await client.get("/api/v1/frequencies")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        frequencies = response.json()
        assert isinstance(frequencies, list)
        assert len(frequencies) == 0

    @pytest.mark.asyncio
    async def test_get_frequencies_validates_response_schema(
        self, client, seed_frequency_data
    ):
        """Test that response conforms to expected schema."""
        # Act
        response = await client.get("/api/v1/frequencies")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        frequencies = response.json()

        for frequency in frequencies:
            # Verify required fields exist
            required_fields = [
                "frequency_id",
                "frequency_name",
                "frequency_days_per_year",
            ]
            for field in required_fields:
                assert field in frequency, f"Missing required field: {field}"

            # Verify frequency_id is valid UUID format
            import uuid

            uuid.UUID(frequency["frequency_id"])  # Will raise ValueError if invalid

            # Verify frequency_days_per_year is positive
            assert frequency["frequency_days_per_year"] > 0

    @pytest.mark.asyncio
    async def test_get_frequencies_content_verification(
        self, client, seed_frequency_data
    ):
        """Test that frequency data matches seeded content."""
        # Act
        response = await client.get("/api/v1/frequencies")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        frequencies = response.json()

        # Create lookup for easier validation
        freq_lookup = {freq["frequency_name"]: freq for freq in frequencies}

        # Verify Daily frequency
        daily = freq_lookup.get("Daily")
        assert daily is not None
        assert daily["frequency_days_per_year"] == 365

        # Verify Weekly frequency
        weekly = freq_lookup.get("Weekly")
        assert weekly is not None
        assert weekly["frequency_days_per_year"] == 52

        # Verify Monthly frequency
        monthly = freq_lookup.get("Monthly")
        assert monthly is not None
        assert monthly["frequency_days_per_year"] == 12

    @pytest.mark.asyncio
    async def test_get_frequencies_rate_limiting(self, client, seed_frequency_data):
        """Test that rate limiting is configured (endpoint should be accessible within limits)."""
        # Act - make multiple requests within rate limit
        responses = []
        for _ in range(5):  # Well under the 10/minute limit
            response = await client.get("/api/v1/frequencies")
            responses.append(response)

        # Assert - all requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_frequencies_consistent_ordering(
        self, client, seed_frequency_data
    ):
        """Test that frequency results are returned in consistent order."""
        # Act - make multiple requests
        response1 = await client.get("/api/v1/frequencies")
        response2 = await client.get("/api/v1/frequencies")

        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        frequencies1 = response1.json()
        frequencies2 = response2.json()

        # Results should be identical
        assert len(frequencies1) == len(frequencies2)

        # Compare by frequency_id to ensure same items in same order
        freq_ids1 = [freq["frequency_id"] for freq in frequencies1]
        freq_ids2 = [freq["frequency_id"] for freq in frequencies2]
        assert freq_ids1 == freq_ids2
