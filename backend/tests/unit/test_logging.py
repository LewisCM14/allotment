import logging
import os
from logging.handlers import RotatingFileHandler

import pytest

LOG_FILE = "test_app.log"
LOG_MAX_BYTES = 1024  # 1 KB for testing
LOG_BACKUP_COUNT = 2


class TestLoggingRotation:
    @pytest.fixture(scope="function")
    def setup_logging(self):
        """Set up a RotatingFileHandler for testing."""
        # Remove any existing test log files
        for i in range(LOG_BACKUP_COUNT + 1):
            try:
                os.remove(f"{LOG_FILE}.{i}")
            except FileNotFoundError:
                pass

        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        yield logger

        # Cleanup
        logger.removeHandler(handler)
        handler.close()

        # Ensure all log files, including the main log file, are removed after the test
        try:
            os.remove(LOG_FILE)
        except FileNotFoundError:
            pass

        for i in range(LOG_BACKUP_COUNT + 1):
            try:
                os.remove(f"{LOG_FILE}.{i}")
            except FileNotFoundError:
                pass

    def test_log_rotation(self, setup_logging):
        """Test that log rotation works as expected."""
        logger = setup_logging

        # Write logs to exceed the maxBytes limit
        for i in range(100):
            logger.info(f"Test log entry {i}")

        # Check that the main log file and backups exist
        assert os.path.exists(LOG_FILE)
        assert os.path.exists(f"{LOG_FILE}.1")

        # Check that the number of backup files does not exceed the limit
        backup_files = [f for f in os.listdir(".") if f.startswith(LOG_FILE)]
        assert len(backup_files) <= LOG_BACKUP_COUNT + 1

        # Verify content in the rotated files
        with open(f"{LOG_FILE}.1", "r") as f:
            content = f.read()
            assert "Test log entry" in content
