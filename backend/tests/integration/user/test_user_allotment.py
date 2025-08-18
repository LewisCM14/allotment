import pytest
from fastapi import status

from app.api.core.config import settings

PREFIX = settings.API_PREFIX


class TestUserAllotment:
    @pytest.mark.asyncio
    async def test_create_user_allotment(self, client, register_user):
        """Test creating a user allotment."""
        headers = await register_user("allotment_create")

        payload = {
            "allotment_postal_zip_code": "12345",
            "allotment_width_meters": 10.0,
            "allotment_length_meters": 20.0,
        }
        resp = await client.post(
            f"{PREFIX}/users/allotment", json=payload, headers=headers
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["allotment_postal_zip_code"] == payload["allotment_postal_zip_code"]
        assert data["allotment_width_meters"] == payload["allotment_width_meters"]
        assert data["allotment_length_meters"] == payload["allotment_length_meters"]
        assert "user_allotment_id" in data
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_get_and_update_user_allotment(self, client, register_user):
        """Test retrieving and updating a user allotment."""
        headers = await register_user("allotment_get_upd")

        # Create allotment
        payload = {
            "allotment_postal_zip_code": "A1A 1A1",
            "allotment_width_meters": 5.5,
            "allotment_length_meters": 15.5,
        }
        create_resp = await client.post(
            f"{PREFIX}/users/allotment", json=payload, headers=headers
        )
        assert create_resp.status_code == status.HTTP_201_CREATED

        # Get allotment
        get_resp = await client.get(f"{PREFIX}/users/allotment", headers=headers)
        assert get_resp.status_code == status.HTTP_200_OK
        data = get_resp.json()
        assert data["allotment_postal_zip_code"] == payload["allotment_postal_zip_code"]

        # Update allotment
        update_payload = {"allotment_width_meters": 7.0}
        upd_resp = await client.put(
            f"{PREFIX}/users/allotment", json=update_payload, headers=headers
        )
        assert upd_resp.status_code == status.HTTP_200_OK
        upd_data = upd_resp.json()
        assert (
            upd_data["allotment_width_meters"]
            == update_payload["allotment_width_meters"]
        )
        # other fields unchanged
        assert upd_data["allotment_length_meters"] == payload["allotment_length_meters"]
        assert (
            upd_data["allotment_postal_zip_code"]
            == payload["allotment_postal_zip_code"]
        )

    @pytest.mark.parametrize(
        "payload, expected_status",
        [
            (
                {
                    "allotment_postal_zip_code": None,
                    "allotment_width_meters": 10.0,
                    "allotment_length_meters": 20.0,
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            (
                {
                    "allotment_postal_zip_code": "123",
                    "allotment_width_meters": 10.0,
                    "allotment_length_meters": 20.0,
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            (
                {
                    "allotment_postal_zip_code": "12345",
                    "allotment_width_meters": 0.5,
                    "allotment_length_meters": 10.0,
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            (
                {
                    "allotment_postal_zip_code": "12345",
                    "allotment_width_meters": 10.0,
                    "allotment_length_meters": 150.0,
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            (
                {
                    "allotment_postal_zip_code": "12#45",
                    "allotment_width_meters": 10.0,
                    "allotment_length_meters": 20.0,
                },
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_validation_errors_on_create(
        self, client, register_user, payload, expected_status
    ):
        """Test validation errors when creating allotment with invalid data (single attempt)."""
        headers = await register_user("allotment_val")
        resp = await client.post(
            f"{PREFIX}/users/allotment", json=payload, headers=headers
        )
        assert resp.status_code == expected_status

    @pytest.mark.asyncio
    async def test_get_user_allotment_not_found(self, client, register_user):
        headers = await register_user("allotment_not_found")
        # No allotment created yet
        resp = await client.get(f"{PREFIX}/users/allotment", headers=headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in resp.text

    @pytest.mark.asyncio
    async def test_duplicate_user_allotment(self, client, register_user):
        """Test that duplicate allotment creation is rejected."""
        headers = await register_user("allotment_dup")

        payload = {
            "allotment_postal_zip_code": "54321",
            "allotment_width_meters": 12.0,
            "allotment_length_meters": 24.0,
        }
        resp1 = await client.post(
            f"{PREFIX}/users/allotment", json=payload, headers=headers
        )
        assert resp1.status_code == status.HTTP_201_CREATED

        resp2 = await client.post(
            f"{PREFIX}/users/allotment", json=payload, headers=headers
        )
        assert resp2.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_create_user_allotment_unauthorized(self, client):
        payload = {
            "allotment_postal_zip_code": "99999",
            "allotment_width_meters": 5.0,
            "allotment_length_meters": 10.0,
        }
        resp = await client.post(f"{PREFIX}/users/allotment", json=payload)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_update_user_allotment_not_created_yet(self, client, register_user):
        """Updating before creation should 404 (resource missing)."""
        headers = await register_user("allotment_upd_missing")
        update_payload = {"allotment_length_meters": 42.0}
        resp = await client.put(
            f"{PREFIX}/users/allotment", json=update_payload, headers=headers
        )
        assert resp.status_code in {
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
        }
