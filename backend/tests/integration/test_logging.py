import asyncio
from unittest.mock import MagicMock, mock_open, patch

import pytest
import structlog

from app.api.core.config import settings
from app.api.core.logging import log_timing
from app.api.middleware.logging_middleware import (
    AsyncLoggingMiddleware,
    request_id_ctx_var,
    sanitize_error_message,
    sanitize_headers,
    sanitize_params,
)


@pytest.mark.asyncio
async def test_structlog_basic(caplog):
    logger = structlog.get_logger()
    with caplog.at_level("INFO"):
        logger.info("Test log", key="value")
    assert any("Test log" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_file_logging():
    from app.api.core.logging import sync_log_to_file

    event = {"event": "Test Event", "level": "info"}
    with patch("builtins.open", mock_open()) as mocked_file:
        with patch("app.api.core.logging.settings.LOG_TO_FILE", True):
            sync_log_to_file(structlog.get_logger(), "info", event)
            mocked_file.assert_called_once_with(settings.LOG_FILE, "a")


@pytest.mark.asyncio
async def test_log_timing_context_manager(caplog):
    request_id_ctx_var.set("req-id")
    with caplog.at_level("DEBUG"):
        with log_timing("op", extra="x"):
            await asyncio.sleep(0.001)
    messages = [r.message for r in caplog.records]
    assert any("Starting op" in m for m in messages)
    assert any("Completed op" in m for m in messages)


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({"Content-Type": "application/json"}, {"Content-Type": "application/json"}),
        ({"Authorization": "Bearer token123"}, {"Authorization": "[REDACTED]"}),
    ],
)
def test_sanitize_headers(headers, expected):
    assert sanitize_headers(headers) == expected


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"page": "1"}, {"page": "1"}),
        ({"token": "abc"}, {"token": "[REDACTED]"}),
    ],
)
def test_sanitize_params(params, expected):
    assert sanitize_params(params) == expected


@pytest.mark.parametrize(
    "msg,expected",
    [
        ("Error: Invalid password", "Error: Invalid password"),
        ("User token=abc123", "User token=[REDACTED]"),
    ],
)
def test_sanitize_error_message(msg, expected):
    assert sanitize_error_message(msg) == expected


@pytest.mark.asyncio
async def test_logging_middleware_request_response(caplog):
    middleware = AsyncLoggingMiddleware(None)
    req = MagicMock()
    req.method = "GET"
    req.url.path = "/api/test"
    req.url.__str__.return_value = "http://testserver/api/test"
    req.client.host = "127.0.0.1"
    req.headers = {"User-Agent": "test-agent"}
    req.query_params = {}
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json", "Content-Length": "10"}

    async def call_next(_):
        return resp

    caplog.set_level("INFO")
    result = await middleware.dispatch(req, call_next)
    assert result == resp
    msgs = [r.message for r in caplog.records]
    assert any("Incoming request" in m for m in msgs)
    assert any("Outgoing response" in m for m in msgs)


@pytest.mark.asyncio
async def test_logging_middleware_exception_handling(caplog):
    middleware = AsyncLoggingMiddleware(None)
    req = MagicMock()
    req.method = "GET"
    req.url.path = "/api/test"
    req.url.__str__.return_value = "http://testserver/api/test"
    req.client.host = "127.0.0.1"
    req.headers = {"User-Agent": "test-agent"}
    req.query_params = {}

    async def call_next(_):
        raise ValueError("Test error with password=secret123")

    caplog.set_level("ERROR")
    result = await middleware.dispatch(req, call_next)
    assert result.status_code == 500
    msgs = [r.message for r in caplog.records]
    assert any("password=[REDACTED]" in m for m in msgs)
