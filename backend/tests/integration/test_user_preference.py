"""
Integration tests for user preference endpoints with new architecture
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.config import settings
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.models.user.user_model import User, UserFeedDay
from tests.conftest import mock_email_service

PREFIX = settings.API_PREFIX


class TestUserPreferenceIntegration:
    """Integration tests for user preference endpoints with new architecture."""

    @pytest.fixture
    def sample_user(self):
        """Create a sample authenticated user."""
        user = User()
        user.user_id = uuid.uuid4()
        user.user_email = "test@example.com"
        user.user_password_hash = "hashed_password"
        user.user_first_name = "Test"
        user.user_country_code = "US"
        user.is_email_verified = True
        return user

    @pytest.fixture
    def sample_feed(self):
        """Create a sample feed."""
        feed = Feed()
        feed.id = uuid.uuid4()
        feed.name = "tomato feed"
        return feed

    @pytest.fixture
    def sample_day(self):
        """Create a sample day."""
        day = Day()
        day.id = uuid.uuid4()
        day.day_number = 1
        day.name = "monday"
        return day

    @pytest.fixture
    def sample_user_feed_day(self, sample_user, sample_feed, sample_day):
        """Create a sample user feed day."""
        ufd = UserFeedDay()
        ufd.user_id = sample_user.user_id
        ufd.feed_id = sample_feed.id
        ufd.day_id = sample_day.id
        ufd.feed = sample_feed
        ufd.day = sample_day
        return ufd

    @pytest.mark.asyncio
    async def test_get_user_preferences_success(
        self,
        client: TestClient,
        mocker,
        sample_user,
        sample_feed,
        sample_day,
        sample_user_feed_day,
    ):
        """Test successful retrieval of user preferences."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"success_test_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "SuccessUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock the new architecture - separate units of work
            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_feed_days",
                    return_value=[sample_user_feed_day],
                ),
                patch(
                    "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_feeds",
                    return_value=[sample_feed],
                ),
                patch(
                    "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                    return_value=[sample_day],
                ),
            ):
                response = await client.get(
                    "/api/v1/users/preferences", headers=headers
                )

            assert response.status_code == 200
            data = response.json()
            assert "user_feed_days" in data
            assert "available_feeds" in data
            assert "available_days" in data
            assert len(data["user_feed_days"]) == 1
            assert data["user_feed_days"][0]["feed_name"] == sample_feed.name
            assert data["user_feed_days"][0]["day_name"] == sample_day.name

    @pytest.mark.asyncio
    async def test_get_user_preferences_unauthorized(self, client: TestClient):
        """Test getting user preferences without authentication."""
        response = await client.get("/api/v1/users/preferences")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_success(
        self, client: TestClient, mocker, sample_feed, sample_day
    ):
        """Test successful update of user feed preference."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"update_success_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "UpdateUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock the new architecture
            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.update_user_feed_day"
                ) as mock_update,
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_feed_days"
                ) as mock_get_user_feeds,
            ):
                # Create mock user feed day for response
                mock_ufd = type("MockUFD", (), {})()
                mock_ufd.feed_id = sample_feed.id
                mock_ufd.day_id = sample_day.id
                mock_ufd.feed = sample_feed
                mock_ufd.day = sample_day

                mock_update.return_value = mock_ufd
                mock_get_user_feeds.return_value = [mock_ufd]

                update_data = {"day_id": str(sample_day.id)}
                response = await client.put(
                    f"/api/v1/users/preferences/{str(sample_feed.id)}",
                    json=update_data,
                    headers=headers,
                )

            assert response.status_code == 200
            data = response.json()
            assert data["feed_id"] == str(sample_feed.id)
            assert data["day_id"] == str(sample_day.id)
            assert data["feed_name"] == sample_feed.name
            assert data["day_name"] == sample_day.name

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_invalid_data(
        self, client: TestClient, mocker, sample_feed
    ):
        """Test updating user feed preference with invalid data."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"invalid_data_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "InvalidUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test with invalid UUID format
        invalid_data = {"day_id": "invalid-uuid"}
        response = await client.put(
            f"/api/v1/users/preferences/{str(sample_feed.id)}",
            json=invalid_data,
            headers=headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_unauthorized(
        self, client: TestClient, sample_feed, sample_day
    ):
        """Test updating user feed preference without authentication."""
        update_data = {"day_id": str(sample_day.id)}
        response = await client.put(
            f"/api/v1/users/preferences/{str(sample_feed.id)}",
            json=update_data,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_not_found_in_results(
        self, client: TestClient, mocker, sample_feed, sample_day
    ):
        """Test update when the updated preference is not found in results (edge case)."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"notfound_pref_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "NotFoundUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock the unit of work methods for the new architecture
            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.update_user_feed_day"
                ) as mock_update,
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_feed_days"
                ) as mock_get_user_feeds,
            ):
                # Mock the update returning a preference that won't be found in get_user_feed_days
                mock_updated_pref = type("MockUpdatedPref", (), {})()
                mock_updated_pref.feed_id = sample_feed.id
                mock_updated_pref.day_id = sample_day.id
                mock_update.return_value = mock_updated_pref

                # Mock get_user_feed_days returning empty list (simulating the not found case)
                mock_get_user_feeds.return_value = []

                update_data = {"day_id": str(sample_day.id)}
                response = await client.put(
                    f"/api/v1/users/preferences/{str(sample_feed.id)}",
                    json=update_data,
                    headers=headers,
                )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_preferences_with_empty_results(
        self, client: TestClient, mocker
    ):
        """Test getting user preferences when no preferences exist."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"empty_pref_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "EmptyUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock empty preferences with new architecture
            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_feed_days",
                    return_value=[],
                ),
                patch(
                    "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_feeds",
                    return_value=[],
                ),
                patch(
                    "app.api.services.grow_guide.grow_guide_unit_of_work.GrowGuideUnitOfWork.get_all_days",
                    return_value=[],
                ),
            ):
                response = await client.get(
                    "/api/v1/users/preferences", headers=headers
                )

            assert response.status_code == 200
            data = response.json()
            assert "user_feed_days" in data
            assert "available_feeds" in data
            assert "available_days" in data
            assert len(data["user_feed_days"]) == 0
            assert len(data["available_feeds"]) == 0
            assert len(data["available_days"]) == 0

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_invalid_feed_id(
        self, client: TestClient, mocker, sample_day
    ):
        """Test updating user feed preference with invalid feed ID format."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"invalid_feed_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "InvalidFeedUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        update_data = {"day_id": str(sample_day.id)}
        response = await client.put(
            "/api/v1/users/preferences/invalid-feed-id",
            json=update_data,
            headers=headers,
        )
        assert response.status_code == 400
