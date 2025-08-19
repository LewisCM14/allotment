import pytest

from app.api.factories import user_factory
from app.api.schemas.user.user_schema import UserCreate


def build_user_create(
    email: str = "test@example.com",
    password: str = "Passw0rd!",
    first_name: str = "Test",
    country: str = "GB",
):
    return UserCreate(
        user_email=email,
        user_password=password,
        user_first_name=first_name,
        user_country_code=country,
    )


class TestUserFactory:
    def test_create_user_factory(self):
        user = user_factory.create_user(email="test@example.com", password="Passw0rd!")
        assert user.email == "test@example.com"
        assert hasattr(user, "id")

    def test_create_user_has_datetime_fields(self):
        user = user_factory.UserFactory.create_user(
            build_user_create(email="datetime@example.com", first_name="DateTime")
        )
        assert hasattr(user, "registered_date")
        assert hasattr(user, "last_active_date")
        assert user.registered_date is None
        assert user.last_active_date is None

    @pytest.mark.parametrize(
        "value, expected_substr",
        [
            ("A", "at least 2 characters"),
            ("A" * 51, "longer than 50"),
            ("Test123!", "only contain letters"),
        ],
    )
    def test_first_name_validation_errors(self, value, expected_substr):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_first_name(value)
        assert expected_substr in str(exc.value)

    def test_country_code_invalid_length(self):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_country_code("GBR")
        assert "exactly 2 characters" in str(exc.value)

    @pytest.mark.parametrize(
        "password, expected_substr",
        [
            ("Short1!", "at least 8 characters"),
            ("A" * 31 + "a1!", "longer than 30"),
            ("password1!", "uppercase letter"),
            ("PASSWORD1!", "lowercase letter"),
            ("Password!!", "digit"),
            ("Password1", "special character"),
        ],
    )
    def test_password_validation_errors(self, password, expected_substr):
        with pytest.raises(user_factory.UserFactoryValidationError) as exc:
            user_factory.UserFactory.validate_password(password)
        assert expected_substr in str(exc.value)

    def test_create_user_validation_error(self, mocker):
        mocker.patch.object(
            user_factory.UserFactory,
            "validate_first_name",
            side_effect=user_factory.UserFactoryValidationError("fail", "first_name"),
        )
        data = build_user_create(email="fail@example.com", first_name="fail")
        with pytest.raises(user_factory.UserFactoryValidationError):
            user_factory.UserFactory.create_user(data)

    def test_create_user_unexpected_error(self, mocker):
        mocker.patch.object(
            user_factory.UserFactory,
            "validate_first_name",
            side_effect=Exception("boom"),
        )
        data = build_user_create(email="fail2@example.com", first_name="fail")
        with pytest.raises(user_factory.BusinessLogicError):
            user_factory.UserFactory.create_user(data)
