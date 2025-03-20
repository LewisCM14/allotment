"""
Logging Configuration Tests
"""

import asyncio
from unittest.mock import mock_open, patch

import pytest
import structlog

from app.api.core.config import settings
from app.api.core.logging import write_log_async


@pytest.mark.asyncio
async def test_structlog_async_logging(caplog):
    """Tests that structlog properly logs messages in JSON format."""
    logger = structlog.get_logger()

    with caplog.at_level("INFO"):
        logger.info("Test log", key="value")

    log_record = caplog.records[-1]
    assert "Test log" in log_record.message
    assert "key" in log_record.message
    assert "value" in log_record.message


@pytest.mark.asyncio
async def test_write_log_async():
    """Tests that write_log_async correctly writes logs asynchronously."""
    test_event = {"event": "Test Event", "level": "info"}

    with patch("builtins.open", mock_open()) as mocked_file:
        asyncio.create_task(write_log_async(test_event))
        await asyncio.sleep(0.1)

        mocked_file.assert_called_once_with(settings.LOG_FILE, "a")
        mocked_file().write.assert_called_once_with(f"{test_event}\n")
