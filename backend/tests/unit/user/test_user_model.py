from datetime import datetime, timezone

from app.api.models.user import user_model


class TestUserModel:
    def test_user_model_fields(self):
        user = user_model.User(
            user_email="test@example.com",
            user_password_hash="dummyhash",
            user_first_name="John",
            user_country_code="GB",
        )
        assert user.user_email == "test@example.com"
        assert hasattr(user, "user_id")
        assert user.user_first_name == "John"
        assert user.user_country_code == "GB"

    def test_set_and_check_password(self):
        user = user_model.User(
            user_email="pwtest@example.com",
            user_password_hash="",
            user_first_name="Jane",
            user_country_code="GB",
        )
        user.set_password("mysecret")
        assert user.check_password("mysecret") is True
        assert user.check_password("wrong") is False

    def test_user_datetime_fields(self):
        """Test that datetime fields are properly set."""
        user = user_model.User(
            user_email="datetime@example.com",
            user_password_hash="dummyhash",
            user_first_name="DateTime",
            user_country_code="GB",
        )

        # Check that datetime fields exist
        assert hasattr(user, "registered_date")
        assert hasattr(user, "last_active_date")

        # When creating a user without explicitly setting dates,
        # they should be None (will be set by database defaults)
        assert user.registered_date is None
        assert user.last_active_date is None

        # Test setting datetime fields explicitly
        now = datetime.now(timezone.utc)
        user.registered_date = now
        user.last_active_date = now

        assert user.registered_date == now
        assert user.last_active_date == now

    def test_user_model_with_all_fields(self):
        """Test user model with all fields including datetime fields."""
        now = datetime.now(timezone.utc)

        user = user_model.User(
            user_email="complete@example.com",
            user_password_hash="dummyhash",
            user_first_name="Complete",
            user_country_code="GB",
            is_email_verified=True,
            registered_date=now,
            last_active_date=now,
        )

        assert user.user_email == "complete@example.com"
        assert user.user_first_name == "Complete"
        assert user.user_country_code == "GB"
        assert user.is_email_verified is True
        assert user.registered_date == now
        assert user.last_active_date == now
