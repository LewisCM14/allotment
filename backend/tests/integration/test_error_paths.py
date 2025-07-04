"""
Tests for error handling and edge cases
"""

from unittest.mock import MagicMock

import pytest
from fastapi import status

from app.api.core.config import settings
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    UserNotFoundError,
)

PREFIX = settings.API_PREFIX


class TestExceptionHandling:
    @pytest.mark.asyncio
    async def test_user_creation_exception_with_error_logging(
        self, client, mocker, caplog
    ):
        """Test exception handling in user creation with log verification."""
        # Mock the safe_operation context manager to raise an exception
        mock_context = MagicMock()
        mock_context.__aenter__.side_effect = Exception("Database connection error")
        mock_safe_op = mocker.patch(
            "app.api.v1.user.safe_operation", return_value=mock_context
        )

        # Also mock email service to avoid actual email sending
        mocker.patch("app.api.v1.user.send_verification_email")

        response = await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "exception-test@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Exception",
                "user_country_code": "GB",
            },
        )

        # Verify response code and error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert (
            "An unexpected error occurred during registration"
            in response.json()["detail"][0]["msg"]
        )

        # Verify the context manager was called
        mock_safe_op.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_verification_request_exception(self, client, mocker, caplog):
        """Test exception handling in email verification request."""
        # First create a user to verify
        mock_email = mocker.patch("app.api.v1.user.send_verification_email")

        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "verify-exception@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Verify",
                "user_country_code": "GB",
            },
        )

        # Clear the mock and make it raise an exception
        mock_email.reset_mock()
        mock_email.side_effect = Exception("Email service unavailable")

        # Test the request verification endpoint
        response = await client.post(
            f"{PREFIX}/users/email-verifications",
            json={"user_email": "verify-exception@example.com"},
        )

        # Should return an error since the email service failed
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "verification email" in response.json()["detail"][0]["msg"].lower()

        # Verify the mock was called
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_password_reset_unverified_email_flow(self, client, mocker):
        """Test password reset request for unverified email."""
        # Create a user with unverified email
        mock_email = mocker.patch("app.api.v1.user.send_verification_email")
        mock_email.return_value = None

        # First register a user but don't verify email
        await client.post(
            f"{PREFIX}/users",
            json={
                "user_email": "unverified-reset@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Unverified",
                "user_country_code": "GB",
            },
        )

        # Reset mock for clarity
        mock_email.reset_mock()

        # Request password reset
        response = await client.post(
            f"{PREFIX}/users/password-resets",
            json={"user_email": "unverified-reset@example.com"},
        )

        # Should succeed but send verification email instead
        assert response.status_code == status.HTTP_200_OK
        assert "verification email" in response.json()["message"].lower()

        # Verify verification email was sent instead
        mock_email.assert_called_once()
        # Check that from_reset=True parameter was passed
        assert mock_email.call_args[1].get("from_reset") is True

    @pytest.mark.asyncio
    async def test_password_reset_with_nonexistent_user(self, client, mocker):
        """Test password reset with non-existent user should not reveal user existence."""
        response = await client.post(
            f"{PREFIX}/users/password-resets",
            json={"user_email": "nonexistent-user@example.com"},
        )

        # Should return success even though user doesn't exist (security feature)
        assert response.status_code == status.HTTP_200_OK
        assert "if your email exists" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_password_reset_with_invalid_token_format(self, client, mocker):
        """Test password reset with invalid token format."""
        response = await client.post(
            f"{PREFIX}/users/password-resets/invalid-token-format",
            json={"new_password": "NewSecurePass123!"},
        )

        # Should return error for invalid token
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_data = response.json()
        # The error message should indicate malformed token
        assert (
            "malformed" in str(response_data).lower()
            or "invalid" in str(response_data).lower()
        )

    @pytest.mark.asyncio
    async def test_login_with_base_application_error(self, client, mocker):
        """Test login when a BaseApplicationError occurs."""
        mock_auth = mocker.patch("app.api.v1.user_auth.authenticate_user")
        mock_error = BaseApplicationError(
            message="Custom error", error_code="TEST_ERROR"
        )
        mock_auth.side_effect = mock_error

        response = await client.post(
            f"{PREFIX}/auth/token",
            json={
                "user_email": "error-test@example.com",
                "user_password": "password",
            },
        )

        # Should return the error from the BaseApplicationError
        assert response.status_code == mock_error.status_code
        assert mock_error.error_code in str(response.json())

    @pytest.mark.asyncio
    async def test_refresh_token_with_nonexistent_user(self, client, mocker):
        """Test refresh token with valid token but nonexistent user."""
        # Mock decode_token to return a valid payload with non-existent user ID
        mock_decode = mocker.patch("app.api.v1.user_auth.decode_token")
        mock_decode.return_value = {"sub": "non-existent-user-id", "type": "refresh"}

        # Mock validate_user_exists to raise UserNotFoundError
        mock_validate = mocker.patch("app.api.v1.user_auth.validate_user_exists")
        mock_validate.side_effect = UserNotFoundError("User not found")

        response = await client.post(
            f"{PREFIX}/auth/token/refresh",
            json={"refresh_token": "valid-looking-token"},
        )

        # Should return user not found error
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "user not found" in str(response.json()).lower()

        # Verify mocks were called
        mock_decode.assert_called_once()
        mock_validate.assert_called_once()
