from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.api.services.email_service import (
    _EMAIL_SEND_TIMESTAMPS,
    _fetch_inbound_email_content,
    _rate_limit_window,
    _send_email_with_retry,
    forward_inbound_email,
    send_password_reset_email,
    send_verification_email,
)


@pytest.mark.asyncio
class TestEmailServiceInternals:
    async def test_rate_limit_window(self):
        # Clear existing timestamps
        _EMAIL_SEND_TIMESTAMPS.clear()

        # Mock time.monotonic to simulate rapid requests
        with patch("time.monotonic") as mock_time:
            # Provide enough values for multiple calls
            # Each call to _rate_limit_window calls monotonic() at least twice (start and end of loop check)
            # plus potentially more if it sleeps.
            # Let's use a side_effect function to just increment time
            mock_time.side_effect = [100.0 + i * 0.1 for i in range(20)]

            # First call - should pass
            await _rate_limit_window(max_per_sec=2)
            assert len(_EMAIL_SEND_TIMESTAMPS) == 1

            # Second call - should pass
            await _rate_limit_window(max_per_sec=2)
            assert len(_EMAIL_SEND_TIMESTAMPS) == 2

            # Third call - should trigger sleep
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await _rate_limit_window(max_per_sec=2)
                mock_sleep.assert_called_once()

    async def test_send_email_with_retry_success(self):
        params = {"to": "test@example.com", "subject": "test"}
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post = AsyncMock()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "123"}
            mock_client.post.return_value = mock_response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            result = await _send_email_with_retry(params)
            assert result == {"id": "123"}

    async def test_send_email_with_retry_retryable_failure_then_success(self):
        params = {"to": "test@example.com", "subject": "test"}
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post = AsyncMock()

            # First attempt 500, second 200
            response1 = MagicMock()
            response1.status_code = 500
            response1.text = "Server Error"

            response2 = MagicMock()
            response2.status_code = 200
            response2.json.return_value = {"id": "123"}

            mock_client.post.side_effect = [response1, response2]

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await _send_email_with_retry(params)
                assert result == {"id": "123"}
                assert mock_client.post.call_count == 2

    async def test_send_email_with_retry_exhausted(self):
        params = {"to": "test@example.com", "subject": "test"}
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post = AsyncMock()

            response = MagicMock()
            response.status_code = 500
            response.text = "Server Error"
            mock_client.post.return_value = response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="Failed to send email after"):
                    await _send_email_with_retry(params, max_attempts=2)

    async def test_send_email_with_retry_non_retryable(self):
        params = {"to": "test@example.com", "subject": "test"}
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post = AsyncMock()

            response = MagicMock()
            response.status_code = 400
            response.text = "Bad Request"
            mock_client.post.return_value = response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(RuntimeError, match="status 400"):
                await _send_email_with_retry(params)


@pytest.mark.asyncio
class TestPublicEmailFunctions:
    async def test_send_verification_email_success(self):
        with patch(
            "app.api.services.email_service._send_email_with_retry",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = {"id": "123"}
            result = await send_verification_email("test@example.com", "user123")
            assert result == {"message": "Verification email sent successfully"}
            mock_send.assert_called_once()

    async def test_send_verification_email_failure(self):
        with patch(
            "app.api.services.email_service._send_email_with_retry",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.side_effect = RuntimeError("Failed")
            with pytest.raises(HTTPException) as exc:
                await send_verification_email("test@example.com", "user123")
            assert exc.value.status_code == 503

    async def test_send_password_reset_email_success(self):
        with patch(
            "app.api.services.email_service._send_email_with_retry",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = {"id": "123"}
            result = await send_password_reset_email(
                "test@example.com", "http://reset.url"
            )
            assert result == {"message": "Password reset email sent successfully"}
            mock_send.assert_called_once()

    async def test_send_password_reset_email_failure(self):
        with patch(
            "app.api.services.email_service._send_email_with_retry",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.side_effect = Exception("Unexpected")
            with pytest.raises(HTTPException) as exc:
                await send_password_reset_email("test@example.com", "http://reset.url")
            assert exc.value.status_code == 500

    async def test_forward_inbound_email_success(self):
        with patch(
            "app.api.services.email_service._send_email_with_retry",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = {"id": "123"}
            result = await forward_inbound_email(
                "sender@example.com", "Subject", "Body"
            )
            assert result == {"message": "Inbound email forwarded successfully"}
            mock_send.assert_called_once()

    async def test_forward_inbound_email_failure(self):
        with patch(
            "app.api.services.email_service._send_email_with_retry",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.side_effect = RuntimeError("Failed")
            with pytest.raises(HTTPException) as exc:
                await forward_inbound_email("sender@example.com", "Subject", "Body")
            assert exc.value.status_code == 503

    async def test_fetch_inbound_email_content_http_error(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Network error")

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            text, html = await _fetch_inbound_email_content("email_id")
            assert text is None
            assert html is None


@pytest.mark.asyncio
class TestFetchInboundEmailContent:
    async def test_fetch_inbound_email_content_standard_structure(self):
        """Test fetching email content with standard text/html structure."""
        email_id = "test-email-id"
        mock_response_data = {"text": "Hello text", "html": "<p>Hello html</p>"}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            text, html = await _fetch_inbound_email_content(email_id)

            assert text == "Hello text"
            assert html == "<p>Hello html</p>"

    async def test_fetch_inbound_email_content_nested_data(self):
        """Test fetching email content nested under 'data'."""
        email_id = "test-email-id"
        mock_response_data = {
            "data": {"text": "Hello text nested", "html": "<p>Hello html nested</p>"}
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            text, html = await _fetch_inbound_email_content(email_id)

            assert text == "Hello text nested"
            assert html == "<p>Hello html nested</p>"

    async def test_fetch_inbound_email_content_body_fallback(self):
        """Test fetching email content using 'body' fallback."""
        email_id = "test-email-id"
        mock_response_data = {"body": "Hello body fallback"}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            text, html = await _fetch_inbound_email_content(email_id)

            assert text == "Hello body fallback"
            assert html is None

    async def test_fetch_inbound_email_content_raw_fallback(self):
        """Test fetching email content using 'raw' fallback."""
        email_id = "test-email-id"
        mock_response_data = {"raw": "Hello raw fallback"}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            text, html = await _fetch_inbound_email_content(email_id)

            assert text == "Hello raw fallback"
            assert html is None

    async def test_fetch_inbound_email_content_nested_body_dict(self):
        """Test fetching email content where text/html are dicts with 'body'."""
        email_id = "test-email-id"
        mock_response_data = {
            "text": {"body": "Hello text dict"},
            "html": {"body": "<p>Hello html dict</p>"},
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get = AsyncMock()

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get.return_value = mock_response

            mock_instance = mock_client_cls.return_value
            mock_instance.__aenter__ = AsyncMock(return_value=mock_client)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            text, html = await _fetch_inbound_email_content(email_id)

            assert text == "Hello text dict"
            assert html == "<p>Hello html dict</p>"
