"""
Unit tests for app.api.services.email_service
"""

import pytest
from fastapi import HTTPException

from app.api.services import email_service
from app.api.services.email_service import request_id_ctx_var


class TestEmailService:
    @pytest.mark.asyncio
    async def test_send_verification_email_success(self, mocker):
        mock_send = mocker.patch.object(
            email_service.mail_client, "send_message", autospec=True
        )
        mocker.patch(
            "app.api.services.email_service.create_token", return_value="dummy-token"
        )
        mocker.patch(
            "app.api.services.email_service.settings.FRONTEND_URL", "http://testserver"
        )
        token = request_id_ctx_var.set("req-1")
        try:
            result = await email_service.send_verification_email(
                user_email="user@example.com", user_id="user-1", from_reset=False
            )
            assert "message" in result
            mock_send.assert_awaited_once()
        finally:
            request_id_ctx_var.reset(token)

    @pytest.mark.asyncio
    async def test_send_verification_email_smtp_failure(self, mocker):
        mocker.patch.object(
            email_service.mail_client,
            "send_message",
            side_effect=Exception("SMTP error"),
        )
        mocker.patch(
            "app.api.services.email_service.create_token", return_value="dummy-token"
        )
        mocker.patch(
            "app.api.services.email_service.settings.FRONTEND_URL", "http://testserver"
        )
        token = request_id_ctx_var.set("req-1")
        try:
            with pytest.raises(HTTPException) as exc:
                await email_service.send_verification_email(
                    user_email="user@example.com", user_id="user-1", from_reset=False
                )
            assert exc.value.status_code == 500
        finally:
            request_id_ctx_var.reset(token)

    @pytest.mark.asyncio
    async def test_send_test_email_success(self, mocker):
        mock_send = mocker.patch.object(
            email_service.mail_client, "send_message", autospec=True
        )
        mocker.patch(
            "app.api.services.email_service.settings.MAIL_USERNAME", "testuser"
        )
        token = request_id_ctx_var.set("req-2")
        try:
            result = await email_service.send_test_email("test@example.com")
            assert "message" in result
            mock_send.assert_awaited_once()
        finally:
            request_id_ctx_var.reset(token)

    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(self, mocker):
        mock_send = mocker.patch.object(
            email_service.mail_client, "send_message", autospec=True
        )
        token = request_id_ctx_var.set("req-3")
        try:
            result = await email_service.send_password_reset_email(
                user_email="reset@example.com", reset_url="http://reset-url"
            )
            assert "message" in result
            mock_send.assert_awaited_once()
        finally:
            request_id_ctx_var.reset(token)

    @pytest.mark.asyncio
    async def test_send_password_reset_email_smtp_failure(self, mocker):
        mocker.patch.object(
            email_service.mail_client,
            "send_message",
            side_effect=Exception("SMTP error"),
        )
        token = request_id_ctx_var.set("req-3")
        try:
            with pytest.raises(HTTPException) as exc:
                await email_service.send_password_reset_email(
                    user_email="reset@example.com", reset_url="http://reset-url"
                )
            assert exc.value.status_code == 500
        finally:
            request_id_ctx_var.reset(token)
