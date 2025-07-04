from app.api.factories import user_factory


class TestUserFactory:
    def test_create_user_factory(self):
        user = user_factory.create_user(email="test@example.com", password="Passw0rd!")
        assert user.email == "test@example.com"
        assert hasattr(user, "id")
