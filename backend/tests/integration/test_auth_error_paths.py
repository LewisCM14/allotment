"""
Additional tests for auth login and token refresh
"""

from unittest.mock import patch

import pytest
from fastapi import status

from app.api.core.config import settings

PREFIX = settings.API_PREFIX


class TestAuthExceptionHandling:
    @pytest.mark.asyncio
    async def test_login_with_token_generation_exception(self, client, mocker):
        """Test handling of exceptions during token generation."""
        # First create a user
        mocker.patch("app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "token-error@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Token",
                "user_country_code": "GB",
            },
        )

        # Mock create_token to throw an exception during login
        with patch(
            "app.api.v1.user_auth.create_token",
            side_effect=Exception("Token generation failed"),
        ):
            response = await client.post(
                f"{PREFIX}/auth/token",
                json={
                    "user_email": "token-error@example.com",
                    "user_password": "SecurePass123!",
                },
            )

            # Verify error response
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "unexpected error" in response.json()["detail"][0]["msg"].lower()

    @pytest.mark.asyncio
    async def test_login_with_specific_business_logic_error(self, client, mocker):
        """Test handling of specific BusinessLogicError during login."""
        # Mock authenticate_user to raise a specific business logic error
        mock_authenticate = mocker.patch("app.api.v1.user_auth.authenticate_user")
        from app.api.middleware.exception_handler import BusinessLogicError

        mock_authenticate.side_effect = BusinessLogicError(
            message="Account locked",
            error_code="ACCOUNT_LOCKED",
            status_code=status.HTTP_403_FORBIDDEN,
        )

        response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "locked@example.com",
                "user_password": "password",
            },
        )

        # Verify error response
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "account locked" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_token_refresh_with_invalid_token_payload(self, client, mocker):
        """Test refresh token when decode works but payload is invalid."""
        # Mock decode_token to return incomplete payload
        mock_decode = mocker.patch("app.api.v1.user_auth.decode_token")
        # Missing 'type' field in payload
        mock_decode.return_value = {"sub": "user-id"}

        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": "invalid-payload-token"},
        )

        # Verify error response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid token type" in str(response.json()).lower()

    @pytest.mark.asyncio
    async def test_refresh_token_generates_unique_tokens(self, client, mocker):
        """Test that refresh token endpoint generates unique tokens."""
        # Create and login a user first
        mocker.patch("app.api.v1.user.send_verification_email")
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "unique-tokens@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Unique",
                "user_country_code": "GB",
            },
        )

        login_response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "unique-tokens@example.com",
                "user_password": "SecurePass123!",
            },
        )

        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]
        old_access_token = login_data["access_token"]

        # Now use the refresh token
        refresh_response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": refresh_token},
        )

        refresh_data = refresh_response.json()

        # Verify tokens are different
        assert refresh_data["access_token"] != old_access_token
        assert refresh_data["refresh_token"] != refresh_token
