"""
Unit tests for app.api.services.email_service

REFACTORED to use improved conftest.py fixtures and test helpers.
"""

import pytest
from fastapi import HTTPException

from app.api.services import email_service
from app.api.services.email_service import request_id_ctx_var


class TestEmailService:
    @pytest.fixture
    def mock_email_client(self, mocker):
        """Mock the email client for all tests in this class."""
        return mocker.patch.object(
            email_service.mail_client, "send_message", autospec=True
        )

    @pytest.fixture
    def mock_settings(self, mocker):
        """Mock email service settings."""
        mocker.patch(
            "app.api.services.email_service.settings.FRONTEND_URL", "http://testserver"
        )
        mocker.patch(
            "app.api.services.email_service.settings.MAIL_USERNAME", "testuser"
        )

    @pytest.fixture
    def mock_token_creation(self, mocker):
        """Mock token creation for email services."""
        return mocker.patch(
            "app.api.services.email_service.create_token", return_value="dummy-token"
        )

    @pytest.fixture
    def set_request_context(self):
        """Set request context for email service tests."""
        token = request_id_ctx_var.set("test-req-id")
        yield
        request_id_ctx_var.reset(token)

    @pytest.mark.asyncio
    async def test_send_verification_email_success(
        self,
        mock_user,
        mock_email_client,
        mock_settings,
        mock_token_creation,
        set_request_context,
    ):
        """Test successful verification email sending using standardized fixtures."""
        result = await email_service.send_verification_email(
            user_email=mock_user.user_email,
            user_id=str(mock_user.user_id),
            from_reset=False,
        )

        assert "message" in result
        mock_email_client.assert_awaited_once()
        mock_token_creation.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_email_smtp_failure(
        self,
        mock_user,
        mock_email_client,
        mock_settings,
        mock_token_creation,
        set_request_context,
    ):
        """Test verification email with SMTP failure."""
        # Make email client raise an exception
        mock_email_client.side_effect = Exception("SMTP error")

        with pytest.raises(HTTPException) as exc:
            await email_service.send_verification_email(
                user_email=mock_user.user_email,
                user_id=str(mock_user.user_id),
                from_reset=False,
            )

        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_send_test_email_success(
        self, mock_email_client, mock_settings, set_request_context
    ):
        """Test successful test email sending."""
        result = await email_service.send_test_email("test@example.com")

        assert "message" in result
        mock_email_client.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(
        self, mock_email_client, set_request_context
    ):
        """Test successful password reset email sending."""
        result = await email_service.send_password_reset_email(
            user_email="reset@example.com", reset_url="http://reset-url"
        )

        assert "message" in result
        mock_email_client.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_password_reset_email_smtp_failure(
        self, mock_email_client, set_request_context
    ):
        """Test password reset email with SMTP failure."""
        mock_email_client.side_effect = Exception("SMTP error")

        with pytest.raises(HTTPException) as exc:
            await email_service.send_password_reset_email(
                user_email="reset@example.com", reset_url="http://reset-url"
            )

        assert exc.value.status_code == 500
