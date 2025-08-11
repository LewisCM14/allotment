import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models.grow_guide.guide_options_model import Day, Feed
from app.api.models.user.user_model import User, UserFeedDay


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

    def test_get_user_preferences_success(
        self,
        client: TestClient,
        sample_user,
        sample_user_feed_day,
        sample_feed,
        sample_day,
    ):
        """Test successful retrieval of user preferences."""
        with patch(
            "app.api.core.auth_utils.get_current_user", return_value=sample_user
        ):
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
                    response = client.get("/v1/user-preferences/")

                assert response.status_code == 200
                data = response.json()
                assert "user_feed_days" in data
                assert "available_feeds" in data
                assert "available_days" in data
                assert len(data["user_feed_days"]) == 1
                assert data["user_feed_days"][0]["feed_name"] == sample_feed.name
                assert data["user_feed_days"][0]["day_name"] == sample_day.name

    def test_get_user_preferences_unauthorized(self, client: TestClient):
        """Test getting user preferences without authentication."""
        response = client.get("/v1/user-preferences/")
        assert response.status_code == 401

    def test_update_user_preferences_success(
        self,
        client: TestClient,
        sample_user,
        sample_user_feed_day,
        sample_feed,
        sample_day,
    ):
        """Test successful update of user preferences."""
        with patch(
            "app.api.core.auth_utils.get_current_user", return_value=sample_user
        ):
            with patch("app.api.core.database.get_db") as mock_get_db:
                mock_db = AsyncMock(spec=AsyncSession)
                mock_get_db.return_value = mock_db

                # Mock the unit of work methods
                mock_preferences_data = {
                    "user_feed_days": [sample_user_feed_day],
                    "available_feeds": [sample_feed],
                    "available_days": [sample_day],
                }

                with (
                    patch(
                        "app.api.services.user.user_unit_of_work.UserUnitOfWork.bulk_update_user_feed_days"
                    ) as mock_bulk_update,
                    patch(
                        "app.api.services.user.user_unit_of_work.UserUnitOfWork.get_user_preferences",
                        return_value=mock_preferences_data,
                    ),
                ):
                    update_data = {
                        "preferences": [
                            {
                                "feed_id": str(sample_feed.id),
                                "day_id": str(sample_day.id),
                            }
                        ]
                    }

                    response = client.put("/v1/user-preferences/", json=update_data)

                assert response.status_code == 200
                data = response.json()
                assert "user_feed_days" in data
                assert "available_feeds" in data
                assert "available_days" in data
                mock_bulk_update.assert_called_once()

    def test_update_user_preferences_invalid_data(
        self, client: TestClient, sample_user
    ):
        """Test updating user preferences with invalid data."""
        with patch(
            "app.api.core.auth_utils.get_current_user", return_value=sample_user
        ):
            # Missing required fields
            invalid_data = {"preferences": [{"feed_id": "invalid"}]}

            response = client.put("/v1/user-preferences/", json=invalid_data)
            assert response.status_code == 422

    def test_update_user_preferences_empty_preferences(
        self, client: TestClient, sample_user
    ):
        """Test updating user preferences with empty preferences list."""
        with patch(
            "app.api.core.auth_utils.get_current_user", return_value=sample_user
        ):
            # Empty preferences list
            invalid_data = {"preferences": []}

            response = client.put("/v1/user-preferences/", json=invalid_data)
            assert response.status_code == 422

    def test_update_user_preferences_unauthorized(self, client: TestClient):
        """Test updating user preferences without authentication."""
        update_data = {
            "preferences": [
                {
                    "feed_id": str(uuid.uuid4()),
                    "day_id": str(uuid.uuid4()),
                }
            ]
        }

        response = client.put("/v1/user-preferences/", json=update_data)
        assert response.status_code == 401
