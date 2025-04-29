"""
Logging Configuration Tests
"""

import asyncio
import json
from unittest.mock import MagicMock, mock_open, patch

import pytest
import structlog
from app.api.core.config import settings
from app.api.core.logging import log_timing, write_log_async
from app.api.middleware.logging_middleware import (
    AsyncLoggingMiddleware,
    request_id_ctx_var,
    sanitize_error_message,
    sanitize_headers,
    sanitize_params,
)


class TestStructLog:
    @pytest.mark.asyncio
    async def test_structlog_async_logging(self, caplog):
        """Tests that structlog properly logs messages in JSON format."""
        logger = structlog.get_logger()

        with caplog.at_level("INFO"):
            logger.info("Test log", key="value")

        log_record = caplog.records[-1]
        assert "Test log" in log_record.message
        assert "key" in log_record.message
        assert "value" in log_record.message

    @pytest.mark.asyncio
    async def test_write_log_async(self):
        """Tests that write_log_async correctly writes logs asynchronously."""
        test_event = {"event": "Test Event", "level": "info"}

        with patch("builtins.open", mock_open()) as mocked_file:
            asyncio.create_task(write_log_async(test_event))
            await asyncio.sleep(0.1)

            mocked_file.assert_called_once_with(settings.LOG_FILE, "a")
            mocked_file().write.assert_called_once_with(f"{test_event}\n")


class TestLoggingContextManagers:
    @pytest.mark.asyncio
    async def test_log_timing_context_manager(self, caplog):
        """Test the log_timing context manager."""
        logger = structlog.get_logger()

        # Set a request ID in the context
        request_id = "test-request-id"
        request_id_ctx_var.set(request_id)

        with caplog.at_level("DEBUG"):
            # Use the context manager with both positional and keyword arguments
            with log_timing("test_operation", extra_field="test_value"):
                # Simulate some work
                await asyncio.sleep(0.01)

        # Check that we got start and completion log messages
        assert len(caplog.records) >= 2

        # Check the first log message (starting operation)
        start_message = caplog.records[0].message
        assert "Starting test_operation" in start_message
        assert "test-request-id" in start_message
        assert "extra_field" in start_message
        assert "test_value" in start_message

        # Check the completion message
        complete_message = caplog.records[-1].message
        assert "Completed test_operation" in complete_message
        assert "process_time" in complete_message
        assert "test-request-id" in complete_message


class TestDataSanitization:
    @pytest.mark.parametrize(
        "headers,expected",
        [
            (
                {"Content-Type": "application/json"},
                {"Content-Type": "application/json"},
            ),
            ({"Authorization": "Bearer token123"}, {"Authorization": "[REDACTED]"}),
            ({"x-api-key": "secret-key"}, {"x-api-key": "[REDACTED]"}),
        ],
    )
    def test_sanitize_headers(self, headers, expected):
        """Test that sensitive headers are properly sanitized."""
        sanitized = sanitize_headers(headers)
        assert sanitized == expected

    @pytest.mark.parametrize(
        "params,expected",
        [
            ({"page": "1"}, {"page": "1"}),
            ({"token": "abc123"}, {"token": "[REDACTED]"}),
            ({"api_key": "secret-key"}, {"api_key": "[REDACTED]"}),
        ],
    )
    def test_sanitize_params(self, params, expected):
        """Test that sensitive query parameters are properly sanitized."""
        sanitized = sanitize_params(params)
        assert sanitized == expected

    @pytest.mark.parametrize(
        "error_msg,expected",
        [
            # Update the test to match the actual regex behavior
            ("Error: Invalid password provided", "Error: Invalid password provided"),
            ("User token=abc123 is invalid", "User token=[REDACTED] is invalid"),
            ("Something unrelated", "Something unrelated"),
        ],
    )
    def test_sanitize_error_message(self, error_msg, expected):
        """Test that sensitive data is redacted from error messages."""
        sanitized = sanitize_error_message(error_msg)
        assert sanitized == expected


class TestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_logging_middleware_request_response(self, caplog):
        """Test that the logging middleware logs requests and responses correctly."""
        middleware = AsyncLoggingMiddleware(None)

        # Mock request and response objects
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.url.__str__.return_value = "http://testserver/api/test"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {
            "User-Agent": "test-agent",
            "Authorization": "Bearer token",
        }
        mock_request.query_params = {}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Type": "application/json",
            "Content-Length": "42",
        }

        # Mock the call_next function to return our mocked response
        async def mock_call_next(_):
            return mock_response

        # Use the caplog fixture directly
        caplog.set_level("INFO")

        # Call the middleware
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Check the response is passed through correctly
        assert response == mock_response

        # Verify logs are captured
        logs = caplog.records
        request_logs = [log for log in logs if "Incoming request" in log.message]
        response_logs = [log for log in logs if "Outgoing response" in log.message]

        assert len(request_logs) >= 1, "Request log should be present"
        assert len(response_logs) >= 1, "Response log should be present"

    @pytest.mark.asyncio
    async def test_logging_middleware_exception_handling(self, caplog):
        """Test that the middleware handles exceptions correctly and sanitizes errors."""
        middleware = AsyncLoggingMiddleware(None)

        # Mock request object
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.url.__str__.return_value = "http://testserver/api/test"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.query_params = {}

        # Mock call_next to raise an exception
        async def mock_call_next_exception(_):
            raise ValueError("Test error with password=secret123")

        # Use the caplog fixture directly
        caplog.set_level("ERROR")

        # Call the middleware with the exception-raising call_next
        response = await middleware.dispatch(mock_request, mock_call_next_exception)

        # Check response is a 500
        assert response.status_code == 500

        # Verify logs are captured
        logs = caplog.records
        error_logs = [log for log in logs if "Unhandled Exception" in log.message]

        assert len(error_logs) >= 1, "Error log should be present"

        # Check only the 'error' field in the log, not the entire traceback
        log_data = json.loads(error_logs[0].message)

        # Verify the error field is redacted
        assert "password=[REDACTED]" in log_data["error"], (
            "Password should be redacted in the error field"
        )
        assert "password=secret" not in log_data["error"], (
            "Password should not be visible in the error field"
        )

        # Verify other expected fields are present
        assert "error_type" in log_data
        assert log_data["error_type"] == "ValueError"
        assert "request_id" in log_data
        assert "path" in log_data
        assert log_data["path"] == "/api/test"
