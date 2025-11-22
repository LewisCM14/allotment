from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.services.email_service import _fetch_inbound_email_content


@pytest.mark.asyncio
async def test_fetch_inbound_email_content_standard_structure():
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


@pytest.mark.asyncio
async def test_fetch_inbound_email_content_nested_data():
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


@pytest.mark.asyncio
async def test_fetch_inbound_email_content_body_fallback():
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


@pytest.mark.asyncio
async def test_fetch_inbound_email_content_raw_fallback():
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


@pytest.mark.asyncio
async def test_fetch_inbound_email_content_nested_body_dict():
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
