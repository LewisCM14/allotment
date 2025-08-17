from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.main import app, flush_logs


class TestExceptionHandlers:
    """Test custom exception handlers."""

    async def test_business_logic_error_handler(self, client: AsyncClient):
        """Test BusinessLogicError exception handler."""
        error = BusinessLogicError("Test business logic error")

        from fastapi import Request

        from app.api.middleware.exception_handler import application_exception_handler

        mock_request = MagicMock(spec=Request)
        response = await application_exception_handler(mock_request, error)

        assert response.status_code == error.status_code
        content = response.body.decode()
        assert "Test business logic error" in content

    async def test_resource_not_found_error_handler(self, client: AsyncClient):
        """Test ResourceNotFoundError exception handler."""
        error = ResourceNotFoundError("User", "123")

        from fastapi import Request

        from app.api.middleware.exception_handler import application_exception_handler

        mock_request = MagicMock(spec=Request)
        response = await application_exception_handler(mock_request, error)

        assert response.status_code == error.status_code
        content = response.body.decode()
        assert "User with id 123 not found" in content

    async def test_base_application_error_handler(self, client: AsyncClient):
        """Test BaseApplicationError exception handler."""
        error = BaseApplicationError("Test base application error", "TEST_ERROR")

        from fastapi import Request

        from app.api.middleware.exception_handler import application_exception_handler

        mock_request = MagicMock(spec=Request)
        response = await application_exception_handler(mock_request, error)

        assert response.status_code == error.status_code
        content = response.body.decode()
        assert "Test base application error" in content


class TestLifespan:
    """Test application lifespan management."""

    @patch("app.main.flush_logs")
    @patch("app.main.logger")
    async def test_lifespan_normal_flow(self, mock_logger, mock_flush_logs):
        """Test normal lifespan flow without exceptions."""
        from app.main import lifespan

        async with lifespan(app):
            pass

        assert mock_logger.info.call_count >= 2
        mock_flush_logs.assert_called_once()

    @patch("app.main.flush_logs")
    @patch("app.main.logger")
    @patch("app.main.sanitize_error_message")
    @patch("app.main.request_id_ctx_var")
    async def test_lifespan_with_exception(
        self, mock_request_id, mock_sanitize, mock_logger, mock_flush_logs
    ):
        """Test lifespan with exception during yield."""
        from app.main import lifespan

        mock_request_id.get.return_value = "test-request-id"
        mock_sanitize.return_value = "Sanitized error message"

        with pytest.raises(RuntimeError):
            async with lifespan(app):
                raise RuntimeError("Test lifespan error")

        mock_logger.error.assert_called_once()
        mock_sanitize.assert_called_once_with("Test lifespan error")
        mock_flush_logs.assert_called_once()


class TestFlushLogs:
    """Test the flush_logs function."""

    @pytest.fixture
    def mock_handler_open(self):
        """Fixture for an open stream handler."""
        handler = MagicMock()
        handler.flush = MagicMock()
        handler.close = MagicMock()
        handler.stream = MagicMock()
        handler.stream.closed = False
        return handler

    @pytest.fixture
    def mock_handler_closed(self):
        """Fixture for a closed stream handler."""
        handler = MagicMock()
        handler.flush = MagicMock()
        handler.close = MagicMock()
        handler.stream = MagicMock()
        handler.stream.closed = True
        return handler

    @pytest.fixture
    def mock_handler_no_stream(self):
        """Fixture for a handler without stream attribute."""
        handler = MagicMock()
        handler.flush = MagicMock()
        handler.close = MagicMock()
        # Remove stream attribute
        if hasattr(handler, "stream"):
            delattr(handler, "stream")
        return handler

    @patch("app.main.logging.getLogger")
    @patch("app.main.structlog.get_logger")
    def test_flush_logs_success(
        self, mock_structlog, mock_logging_logger, mock_handler_open
    ):
        """Test successful log flushing."""
        mock_logger_instance = MagicMock()
        mock_logger_instance.handlers = [mock_handler_open]
        mock_logging_logger.return_value = mock_logger_instance

        mock_structlog_instance = MagicMock()
        mock_structlog.return_value = mock_structlog_instance

        flush_logs()

        mock_handler_open.flush.assert_called_once()
        mock_handler_open.close.assert_called_once()
        mock_structlog_instance.info.assert_called_once_with(
            "Application shutting down"
        )

    @patch("app.main.logging.getLogger")
    def test_flush_logs_with_closed_stream(
        self, mock_logging_logger, mock_handler_closed
    ):
        """Test flush_logs with closed stream handlers."""
        mock_logger_instance = MagicMock()
        mock_logger_instance.handlers = [mock_handler_closed]
        mock_logging_logger.return_value = mock_logger_instance

        flush_logs()

        mock_handler_closed.flush.assert_called_once()
        # close() should not be called because stream is closed
        assert not mock_handler_closed.close.called

    @patch("app.main.logging.getLogger")
    def test_flush_logs_with_handler_exceptions(
        self, mock_logging_logger, mock_handler_open
    ):
        """Test flush_logs handles handler exceptions gracefully."""
        mock_handler_open.flush.side_effect = ValueError("Flush error")

        mock_logger_instance = MagicMock()
        mock_logger_instance.handlers = [mock_handler_open]
        mock_logging_logger.return_value = mock_logger_instance

        # Should not raise exceptions
        flush_logs()

        mock_handler_open.flush.assert_called_once()

    @patch("app.main.logging.getLogger")
    def test_flush_logs_with_close_exception(
        self, mock_logging_logger, mock_handler_open
    ):
        """Test flush_logs handles close exceptions gracefully."""
        mock_handler_open.close.side_effect = IOError("Close error")

        mock_logger_instance = MagicMock()
        mock_logger_instance.handlers = [mock_handler_open]
        mock_logging_logger.return_value = mock_logger_instance

        # Should not raise exceptions
        flush_logs()

        mock_handler_open.flush.assert_called_once()
        mock_handler_open.close.assert_called_once()

    @patch("app.main.logging.getLogger")
    def test_flush_logs_with_no_stream_handler(
        self, mock_logging_logger, mock_handler_no_stream
    ):
        """Test flush_logs with handlers that don't have streams."""
        mock_logger_instance = MagicMock()
        mock_logger_instance.handlers = [mock_handler_no_stream]
        mock_logging_logger.return_value = mock_logger_instance

        flush_logs()

        mock_handler_no_stream.flush.assert_called_once()
        mock_handler_no_stream.close.assert_called_once()

    @patch("app.main.logging.getLogger")
    def test_flush_logs_general_exception(self, mock_logging_logger):
        """Test flush_logs handles general exceptions gracefully."""
        mock_logging_logger.side_effect = Exception("General error")

        # Should not raise exceptions
        flush_logs()


class TestAppConfiguration:
    """Test application configuration and middleware setup."""

    def test_app_title_and_version(self):
        """Test that app has correct title and version from settings."""
        assert app.title is not None
        assert app.version is not None
        assert app.description == "API for managing allotments"

    def test_middleware_configuration(self):
        """Test that required middleware is configured."""
        assert app.state.limiter is not None

    def test_router_inclusion(self):
        """Test that API router is included."""
        route_paths = [route.path for route in app.routes]
        assert "/" in route_paths
        assert "/test-email" in route_paths
        assert any("/api/v1" in path for path in route_paths)
