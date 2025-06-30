from app.api.factories import user_factory


def test_create_user_factory():
    user = user_factory.create_user(email="test@example.com", password="Passw0rd!")
    assert user.email == "test@example.com"
    assert hasattr(user, "id")
