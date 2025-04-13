"""
Auth module unit tests.
"""

import bcrypt
import pytest

from app.api.core.auth import (
    verify_password
)


@pytest.mark.asyncio
async def test_password_hashing():
    """Test that passwords are properly hashed and verified."""
    plain_password = "SecurePass123!"
    hashed_password = bcrypt.hashpw(
        plain_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    assert isinstance(hashed_password, str)
    assert verify_password(plain_password, hashed_password) is True
    assert verify_password("WrongPassword", hashed_password) is False


# def test_protected_route(client):
#     """Test accessing a protected route with a valid token."""
#     register_response = client.post("/users", json={
#         "user_email": "secureuser@example.com",
#         "user_password": "SecurePass123!",
#         "user_first_name": "Test",
#         "user_country_code": "US"
#     })

#     access_token = register_response.json()["access_token"]

#     response = client.get("/protected-route", headers={"Authorization": f"Bearer {access_token}"})

#     assert response.status_code == 200
#     assert response.json()["user_email"] == "secureuser@example.com"


# def test_protected_route_invalid_token(client):
#     """Test accessing a protected route with an invalid token."""
#     response = client.get("/protected-route", headers={"Authorization": "Bearer invalidtoken123"})

#     assert response.status_code == 401
#     assert response.json()["detail"] == "Invalid authentication credentials"


# def test_expired_token(client):
#     """Test that an expired JWT token is rejected."""
#     expired_token = create_token(user_id="1234", expires_delta=timedelta(seconds=1))

#     time.sleep(2)

#     response = client.get("/api/v1/grow-guide/protected-route", headers={"Authorization": f"Bearer {expired_token}"})

#     assert response.status_code == 401
#     assert "detail" in response.json()
