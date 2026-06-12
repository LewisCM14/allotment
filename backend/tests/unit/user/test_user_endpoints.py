"""
HIGH-3 tests: account enumeration + user_id disclosure fixes.

These tests pin the expected security-hardened behaviour:
  1. POST /users/email-verifications with an unknown email must return 200 (no enumeration).
  2. GET /users/verification-status without auth must return 401.
  3. GET /users/verification-status with valid auth must NOT include user_id in the response.
"""

import pytest

from app.api.core.auth_utils import create_token
from app.api.core.config import settings

USER_PREFIX = f"{settings.API_PREFIX}/users"


@pytest.mark.asyncio
async def test_request_verification_email_unknown_email_returns_200(client):
    """Endpoint must return 200 with a generic message for unknown emails
    to prevent account enumeration."""
    response = await client.post(
        f"{USER_PREFIX}/email-verifications",
        json={"user_email": "nobody@test-nonexistent-domain.com"},
    )
    assert response.status_code == 200
    assert "sent" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_check_verification_status_requires_auth(client):
    """Endpoint must return 401 without a valid Bearer token."""
    response = await client.get(f"{USER_PREFIX}/verification-status")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_check_verification_status_does_not_expose_user_id(client, mocker):
    """Response body must not contain a user_id field."""
    import uuid
    from unittest.mock import MagicMock

    mock_user = MagicMock()
    mock_user.is_email_verified = True
    mock_user.user_id = uuid.uuid4()

    mocker.patch(
        "app.api.core.auth_utils.validate_user_exists",
        return_value=mock_user,
    )

    token = create_token(user_id=str(mock_user.user_id), token_type="access")
    response = await client.get(
        f"{USER_PREFIX}/verification-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "user_id" not in response.json()
