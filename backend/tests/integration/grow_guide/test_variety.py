"""
Integration tests for variety endpoints.
"""

from uuid import uuid4

import pytest
from fastapi import status

from app.api.core.config import settings


class TestVarietyEndpointsIntegration:
    """Integration tests for variety API endpoints."""

    @pytest.mark.asyncio
    async def test_get_variety_options_requires_auth(self, client):
        """Test that variety options endpoint requires authentication."""
        response = await client.get(f"{settings.API_PREFIX}/grow-guide/options")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_variety_options_success(
        self,
        client,
        integration_auth_headers,
        seed_lifecycle_data,
        seed_planting_conditions_data,
        seed_frequency_data,
        seed_feed_data,
        seed_week_data,
        complete_family_seed_data,
    ):
        """Test successful retrieval of variety options."""
        response = await client.get(
            f"{settings.API_PREFIX}/grow-guide/options",
            headers=integration_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check all required option types are present
        assert "lifecycles" in data
        assert "planting_conditions" in data
        assert "frequencies" in data
        assert "feeds" in data
        assert "weeks" in data
        assert "families" in data

        # Check data structure
        assert len(data["lifecycles"]) == 3
        assert len(data["planting_conditions"]) == 4
        assert len(data["frequencies"]) == 3
        assert len(data["feeds"]) == 5
        assert len(data["weeks"]) == 3
        assert len(data["families"]) >= 1

    @pytest.mark.asyncio
    async def test_create_variety_success(
        self,
        client,
        integration_auth_headers,
        seed_lifecycle_data,
        seed_planting_conditions_data,
    ):
        """Test successful variety creation."""
        variety_data = {
            "variety_name": "Test Tomato",
            "lifecycle_id": str(seed_lifecycle_data[0]["id"]),
            "planting_conditions_id": str(seed_planting_conditions_data[0]["id"]),
            "is_public": False,
            "water_days": [],
        }

        response = await client.post(
            f"{settings.API_PREFIX}/grow-guide",
            headers=integration_auth_headers,
            json=variety_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["variety_name"] == "Test Tomato"
        assert data["is_public"] is False
        assert data["lifecycle"]["lifecycle_name"] == "Annual"
        assert data["planting_conditions"]["planting_condition"] == "Full Sun"
        assert data["water_days"] == []

    @pytest.mark.asyncio
    async def test_create_variety_with_water_days(
        self,
        client,
        integration_auth_headers,
        seed_lifecycle_data,
        seed_planting_conditions_data,
        seed_day_data,
    ):
        """Test variety creation with water days."""
        variety_data = {
            "variety_name": "Watered Tomato",
            "lifecycle_id": str(seed_lifecycle_data[0]["id"]),
            "planting_conditions_id": str(seed_planting_conditions_data[0]["id"]),
            "is_public": False,
            "water_days": [
                {"day_id": str(seed_day_data[0]["id"])},  # Monday
                {"day_id": str(seed_day_data[2]["id"])},  # Wednesday
            ],
        }

        response = await client.post(
            f"{settings.API_PREFIX}/grow-guide",
            headers=integration_auth_headers,
            json=variety_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["variety_name"] == "Watered Tomato"
        assert len(data["water_days"]) == 2

        # Check water days are correct
        water_day_names = {wd["day_name"] for wd in data["water_days"]}
        assert "Mon" in water_day_names
        assert "Wed" in water_day_names

    @pytest.mark.asyncio
    async def test_create_variety_validation_error(
        self,
        client,
        integration_auth_headers,
        seed_lifecycle_data,
        seed_planting_conditions_data,
    ):
        """Test variety creation with validation error."""
        variety_data = {
            "variety_name": "Test Tomato",
            "lifecycle_id": str(seed_lifecycle_data[0]["id"]),
            "planting_conditions_id": str(seed_planting_conditions_data[0]["id"]),
            "transplant_week_start_id": str(uuid4()),  # Only start provided
            # transplant_week_end_id missing - should cause validation error
        }

        response = await client.post(
            f"{settings.API_PREFIX}/grow-guide",
            headers=integration_auth_headers,
            json=variety_data,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            "transplant week start and end must be provided together"
            in response.text.lower()
        )

    @pytest.mark.asyncio
    async def test_get_user_varieties(
        self,
        client,
        integration_auth_headers,
        seed_variety_data,
    ):
        """Test getting user varieties."""
        response = await client.get(
            f"{settings.API_PREFIX}/grow-guide",
            headers=integration_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) >= 1
        assert any(v["variety_name"] == "Test Tomato" for v in data)

        # Check structure of list items
        for variety in data:
            assert "variety_id" in variety
            assert "variety_name" in variety
            assert "lifecycle_name" in variety
            assert "is_public" in variety
            assert "last_updated" in variety

    @pytest.mark.asyncio
    async def test_get_public_varieties(
        self,
        client,
        integration_auth_headers,
        seed_public_variety_data,
    ):
        """Test getting public varieties."""
        response = await client.get(
            f"{settings.API_PREFIX}/grow-guide/public",
            headers=integration_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) >= 1
        assert any(v["variety_name"] == "Public Tomato" for v in data)
        assert all(v["is_public"] for v in data)

    @pytest.mark.asyncio
    async def test_get_variety_by_id(
        self,
        client,
        integration_auth_headers,
        seed_variety_data,
    ):
        """Test getting a specific variety by ID."""
        variety_id = seed_variety_data["variety_id"]

        response = await client.get(
            f"{settings.API_PREFIX}/grow-guide/{variety_id}",
            headers=integration_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["variety_id"] == str(variety_id)
        assert data["variety_name"] == "Test Tomato"
        assert "lifecycle" in data
        assert "planting_conditions" in data

    @pytest.mark.asyncio
    async def test_get_variety_not_found(
        self,
        client,
        integration_auth_headers,
    ):
        """Test getting a non-existent variety."""
        fake_id = uuid4()

        response = await client.get(
            f"{settings.API_PREFIX}/grow-guide/{fake_id}",
            headers=integration_auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_variety(
        self,
        client,
        integration_auth_headers,
        seed_variety_data,
    ):
        """Test updating a variety."""
        variety_id = seed_variety_data["variety_id"]

        update_data = {
            "variety_name": "Updated Tomato",
            "notes": "This is an updated variety",
        }

        response = await client.put(
            f"{settings.API_PREFIX}/grow-guide/{variety_id}",
            headers=integration_auth_headers,
            json=update_data,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["variety_name"] == "Updated Tomato"
        assert data["notes"] == "This is an updated variety"

    @pytest.mark.asyncio
    async def test_update_variety_not_found(
        self,
        client,
        integration_auth_headers,
    ):
        """Test updating a non-existent variety."""
        fake_id = uuid4()

        update_data = {
            "variety_name": "Updated Tomato",
        }

        response = await client.put(
            f"{settings.API_PREFIX}/grow-guide/{fake_id}",
            headers=integration_auth_headers,
            json=update_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_variety(
        self,
        client,
        integration_auth_headers,
        seed_variety_data,
    ):
        """Test deleting a variety."""
        variety_id = seed_variety_data["variety_id"]

        response = await client.delete(
            f"{settings.API_PREFIX}/grow-guide/{variety_id}",
            headers=integration_auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify variety is deleted
        get_response = await client.get(
            f"{settings.API_PREFIX}/grow-guide/{variety_id}",
            headers=integration_auth_headers,
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_variety_not_found(
        self,
        client,
        integration_auth_headers,
    ):
        """Test deleting a non-existent variety."""
        fake_id = uuid4()

        response = await client.delete(
            f"{settings.API_PREFIX}/grow-guide/{fake_id}",
            headers=integration_auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_variety_name_uniqueness_per_user(
        self,
        client,
        integration_auth_headers,
        seed_lifecycle_data,
        seed_planting_conditions_data,
    ):
        """Test that variety names must be unique per user."""
        variety_data = {
            "variety_name": "Duplicate Tomato",
            "lifecycle_id": str(seed_lifecycle_data[0]["id"]),
            "planting_conditions_id": str(seed_planting_conditions_data[0]["id"]),
            "is_public": False,
        }

        # Create first variety
        response1 = await client.post(
            f"{settings.API_PREFIX}/grow-guide",
            headers=integration_auth_headers,
            json=variety_data,
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create second variety with same name
        response2 = await client.post(
            f"{settings.API_PREFIX}/grow-guide",
            headers=integration_auth_headers,
            json=variety_data,
        )
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response2.text.lower()
