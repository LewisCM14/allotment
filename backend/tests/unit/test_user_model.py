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
