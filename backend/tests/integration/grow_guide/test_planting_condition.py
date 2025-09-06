"""
Integration tests for Planting Conditions endpoints.
"""

import pytest
from fastapi import status


class TestPlantingConditionsEndpoints:
    """Test suite for planting conditions API endpoints."""

    @pytest.mark.asyncio
    async def test_get_planting_conditions_success(
        self, client, seed_planting_conditions_data
    ):
        """Test successful retrieval of all planting conditions."""
        # Act
        response = await client.get("/api/v1/planting-conditions")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        conditions = response.json()
        assert isinstance(conditions, list)
        assert len(conditions) == 4  # Based on seed data

        # Verify structure of first condition
        condition = conditions[0]
        assert "planting_condition_id" in condition
        assert "planting_condition" in condition

        # Verify data types
        assert isinstance(condition["planting_condition_id"], str)
        assert isinstance(condition["planting_condition"], str)

        # Verify expected condition names are present
        condition_names = [c["planting_condition"] for c in conditions]
        assert "Full Sun" in condition_names
        assert "Partial Shade" in condition_names
        assert "Full Shade" in condition_names
        assert "Sheltered" in condition_names

    @pytest.mark.asyncio
    async def test_get_planting_conditions_empty_database(self, client):
        """Test retrieval when no planting conditions exist in database."""
        # Act
        response = await client.get("/api/v1/planting-conditions")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        conditions = response.json()
        assert isinstance(conditions, list)
        assert len(conditions) == 0

    @pytest.mark.asyncio
    async def test_get_planting_conditions_validates_response_schema(
        self, client, seed_planting_conditions_data
    ):
        """Test that response conforms to expected schema."""
        # Act
        response = await client.get("/api/v1/planting-conditions")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        conditions = response.json()

        for condition in conditions:
            # Verify required fields exist
            required_fields = ["planting_condition_id", "planting_condition"]
            for field in required_fields:
                assert field in condition, f"Missing required field: {field}"

            # Verify planting_condition_id is valid UUID format
            import uuid

            uuid.UUID(
                condition["planting_condition_id"]
            )  # Will raise ValueError if invalid

            # Verify planting_condition is non-empty string
            assert len(condition["planting_condition"].strip()) > 0

    @pytest.mark.asyncio
    async def test_get_planting_conditions_content_verification(
        self, client, seed_planting_conditions_data
    ):
        """Test that planting condition data matches seeded content."""
        # Act
        response = await client.get("/api/v1/planting-conditions")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        conditions = response.json()

        # Create lookup for easier validation
        condition_lookup = {c["planting_condition"]: c for c in conditions}

        # Verify all expected conditions exist
        expected_conditions = ["Full Sun", "Partial Shade", "Full Shade", "Sheltered"]
        for expected_condition in expected_conditions:
            assert expected_condition in condition_lookup, (
                f"Missing condition: {expected_condition}"
            )

    @pytest.mark.asyncio
    async def test_get_planting_conditions_rate_limiting(
        self, client, seed_planting_conditions_data
    ):
        """Test that rate limiting is configured (endpoint should be accessible within limits)."""
        # Act - make multiple requests within rate limit
        responses = []
        for _ in range(5):  # Well under the 10/minute limit
            response = await client.get("/api/v1/planting-conditions")
            responses.append(response)

        # Assert - all requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_planting_conditions_consistent_ordering(
        self, client, seed_planting_conditions_data
    ):
        """Test that planting condition results are returned in consistent order."""
        # Act - make multiple requests
        response1 = await client.get("/api/v1/planting-conditions")
        response2 = await client.get("/api/v1/planting-conditions")

        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        conditions1 = response1.json()
        conditions2 = response2.json()

        # Results should be identical
        assert len(conditions1) == len(conditions2)

        # Compare by planting_condition_id to ensure same items in same order
        condition_ids1 = [c["planting_condition_id"] for c in conditions1]
        condition_ids2 = [c["planting_condition_id"] for c in conditions2]
        assert condition_ids1 == condition_ids2

    @pytest.mark.asyncio
    async def test_get_planting_conditions_logical_grouping(
        self, client, seed_planting_conditions_data
    ):
        """Test that planting conditions represent logical light/environment categories."""
        # Act
        response = await client.get("/api/v1/planting-conditions")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        conditions = response.json()

        condition_names = [c["planting_condition"] for c in conditions]

        # Should include sun/shade spectrum
        sun_shade_conditions = ["Full Sun", "Partial Shade", "Full Shade"]
        for condition in sun_shade_conditions:
            assert condition in condition_names, (
                f"Missing sun/shade condition: {condition}"
            )

        # Should include protection conditions
        protection_conditions = ["Sheltered"]
        for condition in protection_conditions:
            assert condition in condition_names, (
                f"Missing protection condition: {condition}"
            )

    @pytest.mark.asyncio
    async def test_get_planting_conditions_name_format(
        self, client, seed_planting_conditions_data
    ):
        """Test that planting condition names follow expected format."""
        # Act
        response = await client.get("/api/v1/planting-conditions")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        conditions = response.json()

        for condition in conditions:
            condition_name = condition["planting_condition"]

            # Should be properly capitalized (Title Case)
            words = condition_name.split()
            for word in words:
                assert word[0].isupper(), (
                    f"Condition name should be title case: {condition_name}"
                )

            # Should not have extra whitespace
            assert condition_name == condition_name.strip()
            assert "  " not in condition_name  # No double spaces
