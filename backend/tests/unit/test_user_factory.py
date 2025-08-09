import pytest

from app.api.factories import user_factory


class TestUserFactory:
    def test_create_user_factory(self):
        user = user_factory.create_user(email="test@example.com", password="Passw0rd!")
        assert user.email == "test@example.com"
        assert hasattr(user, "id")

    def test_create_user_has_datetime_fields(self):
        """Test that created users have datetime fields."""
        from app.api.schemas.user.user_schema import UserCreate

        user_data = UserCreate(
            user_email="datetime@example.com",
            user_password="Passw0rd!",
            user_first_name="DateTime",
            user_country_code="GB",
        )

        user = user_factory.UserFactory.create_user(user_data)

        # Verify the user model has datetime fields
        assert hasattr(user, "registered_date")
        assert hasattr(user, "last_active_date")

        # These fields should be None initially (set by database defaults)
        assert user.registered_date is None
        assert user.last_active_date is None

    def test_first_name_too_short(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_first_name("A")
        assert "at least 2 characters" in str(exc.value)

    def test_first_name_too_long(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_first_name("A" * 51)
        assert "longer than 50" in str(exc.value)

    def test_first_name_invalid_chars(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_first_name("Test123!")
        assert "only contain letters" in str(exc.value)

    def test_country_code_invalid_length(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_country_code("GBR")
        assert "exactly 2 characters" in str(exc.value)

    def test_password_too_short(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_password("Short1!")
        assert "at least 8 characters" in str(exc.value)

    def test_password_too_long(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_password("A" * 31 + "a1!")
        assert "longer than 30" in str(exc.value)

    def test_password_missing_uppercase(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_password("password1!")
        assert "uppercase letter" in str(exc.value)

    def test_password_missing_lowercase(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_password("PASSWORD1!")
        assert "lowercase letter" in str(exc.value)

    def test_password_missing_digit(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_password("Password!!")
        assert "digit" in str(exc.value)

    def test_password_missing_special(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_password("Password1")
        assert "special character" in str(exc.value)

    def test_create_user_validation_error(self, mocker):
        # Patch validate_first_name to raise
        mocker.patch.object(
            user_factory.UserFactory,
            "validate_first_name",
            side_effect=user_factory.UserFactoryValidationError("fail", "first_name"),
        )
        from app.api.schemas.user.user_schema import UserCreate

        data = UserCreate(
            user_email="fail@example.com",
            user_password="Passw0rd!",
            user_first_name="fail",
            user_country_code="GB",
        )
        with pytest.raises(user_factory.UserFactoryValidationError):
            user_factory.UserFactory.create_user(data)

    def test_create_user_unexpected_error(self, mocker):
        # Patch validate_first_name to raise generic Exception
        mocker.patch.object(
            user_factory.UserFactory,
            "validate_first_name",
            side_effect=Exception("boom"),
        )
        from app.api.schemas.user.user_schema import UserCreate

        data = UserCreate(
            user_email="fail2@example.com",
            user_password="Passw0rd!",
            user_first_name="fail",
            user_country_code="GB",
        )
        with pytest.raises(user_factory.BusinessLogicError):
            user_factory.UserFactory.create_user(data)
