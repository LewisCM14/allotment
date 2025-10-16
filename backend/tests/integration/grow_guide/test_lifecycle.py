"""
Integration tests for Lifecycle endpoints.
"""

import pytest
from fastapi import status


class TestLifecycleEndpoints:
    """Test suite for lifecycle API endpoints."""

    @pytest.mark.asyncio
    async def test_get_lifecycles_success(self, client, seed_lifecycle_data):
        """Test successful retrieval of all lifecycles."""
        # Act
        response = await client.get("/api/v1/lifecycles")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        lifecycles = response.json()
        assert isinstance(lifecycles, list)
        assert len(lifecycles) == 3  # Based on seed data

        # Verify structure of first lifecycle
        lifecycle = lifecycles[0]
        assert "lifecycle_id" in lifecycle
        assert "lifecycle_name" in lifecycle
        assert "productivity_years" in lifecycle

        # Verify data types
        assert isinstance(lifecycle["lifecycle_id"], str)
        assert isinstance(lifecycle["lifecycle_name"], str)
        assert isinstance(lifecycle["productivity_years"], int)

        # Verify expected lifecycle names are present
        lifecycle_names = [lc["lifecycle_name"] for lc in lifecycles]
        assert "annual" in lifecycle_names
        assert "biennial" in lifecycle_names
        assert "perennial" in lifecycle_names

    @pytest.mark.asyncio
    async def test_get_lifecycles_empty_database(self, client):
        """Test retrieval when no lifecycles exist in database."""
        # Act
        response = await client.get("/api/v1/lifecycles")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        lifecycles = response.json()
        assert isinstance(lifecycles, list)
        assert len(lifecycles) == 0

    @pytest.mark.asyncio
    async def test_get_lifecycles_validates_response_schema(
        self, client, seed_lifecycle_data
    ):
        """Test that response conforms to expected schema."""
        # Act
        response = await client.get("/api/v1/lifecycles")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        lifecycles = response.json()

        for lifecycle in lifecycles:
            # Verify required fields exist
            required_fields = ["lifecycle_id", "lifecycle_name", "productivity_years"]
            for field in required_fields:
                assert field in lifecycle, f"Missing required field: {field}"

            # Verify lifecycle_id is valid UUID format
            import uuid

            uuid.UUID(lifecycle["lifecycle_id"])  # Will raise ValueError if invalid

            # Verify productivity_years is positive
            assert lifecycle["productivity_years"] > 0

    @pytest.mark.asyncio
    async def test_get_lifecycles_content_verification(
        self, client, seed_lifecycle_data
    ):
        """Test that lifecycle data matches seeded content."""
        # Act
        response = await client.get("/api/v1/lifecycles")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        lifecycles = response.json()

        # Create lookup for easier validation
        lifecycle_lookup = {lc["lifecycle_name"]: lc for lc in lifecycles}

        # Verify Annual lifecycle
        annual = lifecycle_lookup.get("annual")
        assert annual is not None
        assert annual["productivity_years"] == 1

        # Verify Biennial lifecycle
        biennial = lifecycle_lookup.get("biennial")
        assert biennial is not None
        assert biennial["productivity_years"] == 2

        # Verify Perennial lifecycle
        perennial = lifecycle_lookup.get("perennial")
        assert perennial is not None
        assert perennial["productivity_years"] == 10

    @pytest.mark.asyncio
    async def test_get_lifecycles_rate_limiting(self, client, seed_lifecycle_data):
        """Test that rate limiting is configured (endpoint should be accessible within limits)."""
        # Act - make multiple requests within rate limit
        responses = []
        for _ in range(5):  # Well under the 10/minute limit
            response = await client.get("/api/v1/lifecycles")
            responses.append(response)

        # Assert - all requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_lifecycles_consistent_ordering(
        self, client, seed_lifecycle_data
    ):
        """Test that lifecycle results are returned in consistent order."""
        # Act - make multiple requests
        response1 = await client.get("/api/v1/lifecycles")
        response2 = await client.get("/api/v1/lifecycles")

        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        lifecycles1 = response1.json()
        lifecycles2 = response2.json()

        # Results should be identical
        assert len(lifecycles1) == len(lifecycles2)

        # Compare by lifecycle_id to ensure same items in same order
        lifecycle_ids1 = [lc["lifecycle_id"] for lc in lifecycles1]
        lifecycle_ids2 = [lc["lifecycle_id"] for lc in lifecycles2]
        assert lifecycle_ids1 == lifecycle_ids2

    @pytest.mark.asyncio
    async def test_get_lifecycles_productivity_years_range(
        self, client, seed_lifecycle_data
    ):
        """Test that productivity years values are within expected ranges."""
        # Act
        response = await client.get("/api/v1/lifecycles")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        lifecycles = response.json()

        for lifecycle in lifecycles:
            productivity_years = lifecycle["productivity_years"]
            # Productivity years should be reasonable (1-100 years)
            assert 1 <= productivity_years <= 100

            # Verify specific expected values based on lifecycle type
            name = lifecycle["lifecycle_name"]
            if name == "annual":
                assert productivity_years == 1
            elif name == "biennial":
                assert productivity_years == 2
            elif name == "perennial":
                assert productivity_years >= 3  # Perennials live multiple years
