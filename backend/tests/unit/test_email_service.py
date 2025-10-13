import pytest
from fastapi import HTTPException
from resend.exceptions import ResendError

from app.api.services import email_service
from app.api.services.email_service import request_id_ctx_var


class TestEmailService:
    @pytest.fixture
    def mock_resend_send(self, mocker):
        """Mock the Resend send method for all tests in this class."""
        return mocker.patch(
            "app.api.services.email_service.resend.Emails.send",
            return_value={"id": "test-email-id"},
        )

    @pytest.fixture
    def mock_settings(self, mocker):
        """Mock email service settings."""
        mocker.patch(
            "app.api.services.email_service.settings.FRONTEND_URL", "http://testserver"
        )
        mocker.patch(
            "app.api.services.email_service.settings.MAIL_FROM",
            "test@resend.dev",
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
        mock_resend_send,
        mock_settings,
        mock_token_creation,
        set_request_context,
    ):
        """Test successful verification email sending."""
        result = await email_service.send_verification_email(
            user_email=mock_user.user_email,
            user_id=str(mock_user.user_id),
            from_reset=False,
        )

        assert "message" in result
        mock_resend_send.assert_called_once()
        mock_token_creation.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_verification_email_api_failure(
        self,
        mock_user,
        mock_resend_send,
        mock_settings,
        mock_token_creation,
        set_request_context,
    ):
        """Test verification email with Resend API failure."""
        mock_resend_send.side_effect = ResendError(
            code=400,
            error_type="validation_error",
            message="API error",
            suggested_action="Check your API key",
        )

        with pytest.raises(HTTPException) as exc:
            await email_service.send_verification_email(
                user_email=mock_user.user_email,
                user_id=str(mock_user.user_id),
                from_reset=False,
            )

        assert exc.value.status_code == 503

    @pytest.mark.asyncio
    async def test_send_test_email_success(
        self, mock_resend_send, mock_settings, set_request_context
    ):
        """Test successful test email sending."""
        result = await email_service.send_test_email("test@example.com")

        assert "message" in result
        assert "email_id" in result
        mock_resend_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(
        self, mock_resend_send, set_request_context
    ):
        """Test successful password reset email sending."""
        result = await email_service.send_password_reset_email(
            user_email="reset@example.com", reset_url="http://reset-url"
        )

        assert "message" in result
        mock_resend_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_password_reset_email_api_failure(
        self, mock_resend_send, set_request_context
    ):
        """Test password reset email with Resend API failure."""
        mock_resend_send.side_effect = ResendError(
            code=400,
            error_type="validation_error",
            message="API error",
            suggested_action="Check your API key",
        )

        with pytest.raises(HTTPException) as exc:
            await email_service.send_password_reset_email(
                user_email="reset@example.com", reset_url="http://reset-url"
            )

        assert exc.value.status_code == 503
