from datetime import datetime, timezone

import pytest

from tests.test_helpers import make_user_model


class TestUserModel:
    def test_user_model_fields_minimal(self):
        user = make_user_model(
            email="test@example.com", first_name="John", country_code="GB"
        )
        assert user.user_email == "test@example.com"
        assert hasattr(user, "user_id")
        assert user.user_first_name == "John"
        assert user.user_country_code == "GB"
        # default flags
        assert user.is_email_verified is False

    def test_set_and_check_password(self):
        user = make_user_model(
            email="pwtest@example.com", first_name="Jane", password_hash=""
        )
        user.set_password("mysecret")
        assert user.check_password("mysecret") is True
        assert user.check_password("wrong") is False

    @pytest.mark.parametrize("explicit", [False, True])
    def test_datetime_fields(self, explicit: bool):
        if explicit:
            now = datetime.now(timezone.utc)
            user = make_user_model(
                email="complete@example.com",
                first_name="Complete",
                verified=True,
                registered_date=now,
                last_active_date=now,
            )
            assert user.registered_date == now
            assert user.last_active_date == now
            assert user.is_email_verified is True
        else:
            user = make_user_model(email="datetime@example.com", first_name="DateTime")
            assert user.registered_date is None
            assert user.last_active_date is None
            assert user.is_email_verified is False

        # common invariants
        assert hasattr(user, "registered_date")
        assert hasattr(user, "last_active_date")
