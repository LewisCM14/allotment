"""
User Allotment API Tests
"""

import uuid

import pytest
from fastapi import status

from app.api.core.config import settings
from tests.conftest import mock_email_service

PREFIX = settings.API_PREFIX


class TestUserAllotment:
    @pytest.mark.asyncio
    async def test_create_user_allotment(self, client, mocker):
        """Test creating a user allotment."""
        _ = mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        # Register a new user and obtain an access token
        reg_resp = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": f"allotment_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Allot",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == status.HTTP_201_CREATED
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

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
    async def test_get_and_update_user_allotment(self, client, mocker):
        """Test retrieving and updating a user allotment."""
        _ = mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": f"allotment2_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Allot",
                "user_country_code": "CA",
            },
        )
        assert reg_resp.status_code == status.HTTP_201_CREATED
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

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
        self, client, mocker, payload, expected_status
    ):
        """Test validation errors when creating allotment with invalid data."""
        _ = mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        # Register user
        reg_resp = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": f"val_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Val",
                "user_country_code": "UK",
            },
        )
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            f"{PREFIX}/users/allotment", json=payload, headers=headers
        )
        assert resp.status_code == expected_status

    @pytest.mark.asyncio
    async def test_duplicate_user_allotment(self, client, mocker):
        """Test that duplicate allotment creation is rejected."""
        _ = mock_email_service(mocker, "app.api.v1.user.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": f"dup_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Dup",
                "user_country_code": "DE",
            },
        )
        assert reg_resp.status_code == status.HTTP_201_CREATED
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

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
