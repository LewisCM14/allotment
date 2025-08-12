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
    """Integration tests for user preference endpoints."""

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
        sample_user_feed_day,
        sample_feed,
        sample_day,
    ):
        """Test successful retrieval of user preferences."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"pref_user_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "PrefUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock the unit of work methods
            mock_preferences_data = {
                "user_feed_days": [sample_user_feed_day],
                "available_feeds": [sample_feed],
                "available_days": [sample_day],
            }

            with patch(
                "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences",
                return_value=mock_preferences_data,
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
        assert response.status_code == 422  # Missing authorization header

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_success(
        self, client: TestClient, mocker, sample_user, sample_feed, sample_day
    ):
        """Test successful update of a user feed preference."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"update_pref_{uuid.uuid4().hex}@example.com",
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

            # Mock the unit of work methods
            with patch(
                "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences"
            ) as mock_get_prefs:
                # Create mock user feed day for response
                mock_ufd = (
                    sample_user.copy()
                    if hasattr(sample_user, "copy")
                    else type("MockUFD", (), {})()
                )
                mock_ufd.feed_id = sample_feed.id
                mock_ufd.day_id = sample_day.id
                mock_ufd.feed = sample_feed
                mock_ufd.day = sample_day

                mock_get_prefs.return_value = {
                    "user_feed_days": [mock_ufd],
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                }

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
        self, client: TestClient, mocker, sample_user, sample_feed
    ):
        """Test updating user feed preference with invalid data."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"invalid_pref_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "InvalidUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Invalid day_id format
        invalid_data = {"day_id": "invalid-uuid"}

        response = await client.put(
            f"/api/v1/users/preferences/{str(sample_feed.id)}",
            json=invalid_data,
            headers=headers,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_unauthorized(
        self, client: TestClient, sample_feed
    ):
        """Test updating user feed preference without authentication."""
        update_data = {"day_id": str(uuid.uuid4())}

        response = await client.put(
            f"/api/v1/users/preferences/{str(sample_feed.id)}", json=update_data
        )
        assert response.status_code == 422  # Missing authorization header

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_not_found_in_results(
        self, client: TestClient, mocker, sample_user, sample_feed, sample_day
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

            # Mock the unit of work to return an empty result after update
            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.update_user_feed_day"
                ) as mock_update,
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences"
                ) as mock_get_prefs,
            ):
                # Mock the update returning a preference that won't be found in get_preferences
                mock_updated_pref = type("MockUpdatedPref", (), {})()
                mock_updated_pref.feed_id = sample_feed.id
                mock_updated_pref.day_id = sample_day.id
                mock_update.return_value = mock_updated_pref

                # Mock get_user_preferences returning empty user_feed_days (simulating the not found case)
                mock_get_prefs.return_value = {
                    "user_feed_days": [],  # Empty - no matching preference found
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                }

                update_data = {"day_id": str(sample_day.id)}
                response = await client.put(
                    f"/api/v1/users/preferences/{str(sample_feed.id)}",
                    json=update_data,
                    headers=headers,
                )

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert len(data["detail"]) > 0
            assert data["detail"][0]["code"] == "RES_001"
            assert "Feed preference" in data["detail"][0]["msg"]

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

            # Mock empty preferences
            with patch(
                "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences",
                return_value={
                    "user_feed_days": [],
                    "available_feeds": [],
                    "available_days": [],
                },
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
    async def test_update_user_feed_preference_service_layer_handling(
        self, client: TestClient, mocker, sample_feed, sample_day
    ):
        """Test updating user feed preference and handling service layer responses."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"service_test_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "ServiceUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        update_data = {"day_id": str(sample_day.id)}

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock successful service layer operations
            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.update_user_feed_day"
                ) as mock_update,
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences"
                ) as mock_get_prefs,
            ):
                # Mock update returning a valid preference
                mock_updated_pref = type("MockUpdatedPref", (), {})()
                mock_updated_pref.feed_id = sample_feed.id
                mock_updated_pref.day_id = sample_day.id
                mock_update.return_value = mock_updated_pref

                # Mock successful get_user_preferences
                ufd = UserFeedDay()
                ufd.feed_id = sample_feed.id
                ufd.day_id = sample_day.id
                ufd.feed = sample_feed
                ufd.day = sample_day

                mock_get_prefs.return_value = {
                    "user_feed_days": [ufd],
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                }

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
    async def test_get_user_preferences_with_multiple_feed_days(
        self, client: TestClient, mocker, sample_user, sample_feed, sample_day
    ):
        """Test getting user preferences with multiple feed days."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"multi_pref_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "MultiUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create multiple feed days
        feed2 = Feed()
        feed2.id = uuid.uuid4()
        feed2.name = "potato feed"

        day2 = Day()
        day2.id = uuid.uuid4()
        day2.day_number = 2
        day2.name = "tuesday"

        ufd1 = UserFeedDay()
        ufd1.user_id = sample_user.user_id
        ufd1.feed_id = sample_feed.id
        ufd1.day_id = sample_day.id
        ufd1.feed = sample_feed
        ufd1.day = sample_day

        ufd2 = UserFeedDay()
        ufd2.user_id = sample_user.user_id
        ufd2.feed_id = feed2.id
        ufd2.day_id = day2.id
        ufd2.feed = feed2
        ufd2.day = day2

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Mock multiple preferences
            mock_preferences_data = {
                "user_feed_days": [ufd1, ufd2],
                "available_feeds": [sample_feed, feed2],
                "available_days": [sample_day, day2],
            }

            with patch(
                "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences",
                return_value=mock_preferences_data,
            ):
                response = await client.get(
                    "/api/v1/users/preferences", headers=headers
                )

            assert response.status_code == 200
            data = response.json()
            assert len(data["user_feed_days"]) == 2
            assert len(data["available_feeds"]) == 2
            assert len(data["available_days"]) == 2

            # Verify the data is correctly mapped
            feed_names = [ufd["feed_name"] for ufd in data["user_feed_days"]]
            assert sample_feed.name in feed_names
            assert feed2.name in feed_names

    @pytest.mark.asyncio
    async def test_endpoints_with_logging_coverage(
        self, client: TestClient, mocker, sample_feed, sample_day
    ):
        """Test endpoints to ensure logging statements are covered."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"logging_test_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "LoggingUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Test get_user_preferences with logging
            with patch(
                "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences",
                return_value={
                    "user_feed_days": [],
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                },
            ):
                # This should hit the logging statements in get_user_preferences
                response = await client.get(
                    "/api/v1/users/preferences", headers=headers
                )
                assert response.status_code == 200

            # Test successful update_user_feed_preference with full path coverage
            ufd = UserFeedDay()
            ufd.feed_id = sample_feed.id
            ufd.day_id = sample_day.id
            ufd.feed = sample_feed
            ufd.day = sample_day

            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.update_user_feed_day"
                ) as mock_update,
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences"
                ) as mock_get_prefs,
            ):
                mock_updated_pref = type("MockUpdatedPref", (), {})()
                mock_updated_pref.feed_id = sample_feed.id
                mock_updated_pref.day_id = sample_day.id
                mock_update.return_value = mock_updated_pref

                mock_get_prefs.return_value = {
                    "user_feed_days": [ufd],
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                }

                update_data = {"day_id": str(sample_day.id)}
                # This should hit all the logging and success paths
                response = await client.put(
                    f"/api/v1/users/preferences/{str(sample_feed.id)}",
                    json=update_data,
                    headers=headers,
                )
                assert response.status_code == 200
                data = response.json()
                assert data["feed_name"] == sample_feed.name
                assert data["day_name"] == sample_day.name

    @pytest.mark.asyncio
    async def test_complete_flow_coverage(
        self, client: TestClient, mocker, sample_feed, sample_day
    ):
        """Test complete flow to ensure all code paths and logging are covered."""
        # Create a user and get a real token
        mock_email_service(mocker, "app.api.v1.registration.send_verification_email")
        reg_resp = await client.post(
            f"{PREFIX}/registration",
            json={
                "user_email": f"complete_flow_{uuid.uuid4().hex}@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "CompleteUser",
                "user_country_code": "US",
            },
        )
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create test data
        ufd = UserFeedDay()
        ufd.feed_id = sample_feed.id
        ufd.day_id = sample_day.id
        ufd.feed = sample_feed
        ufd.day = sample_day

        with patch("app.api.core.database.get_db") as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db

            # Test 1: get_user_preferences with data to trigger final return and logging
            with patch(
                "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences",
                return_value={
                    "user_feed_days": [ufd],
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                },
            ):
                # This should hit the final logging and return in get_user_preferences
                response = await client.get(
                    "/api/v1/users/preferences", headers=headers
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data["user_feed_days"]) == 1
                assert data["user_feed_days"][0]["feed_name"] == sample_feed.name

            # Test 2: successful update that finds the preference in results
            with (
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.update_user_feed_day"
                ) as mock_update,
                patch(
                    "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences"
                ) as mock_get_prefs,
            ):
                # Mock update operation
                mock_updated_pref = type("MockUpdatedPref", (), {})()
                mock_updated_pref.feed_id = sample_feed.id
                mock_updated_pref.day_id = sample_day.id
                mock_update.return_value = mock_updated_pref

                # Mock get_user_preferences to return the updated preference
                # This ensures the preference is found and we hit the success path
                mock_get_prefs.return_value = {
                    "user_feed_days": [ufd],
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                }

                update_data = {"day_id": str(sample_day.id)}
                # This should hit the final success logging and return statement
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
