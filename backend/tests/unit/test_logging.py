"""
Tests for logging functionality - refactored to use conftest.py fixtures
"""

import logging
import os
from logging.handlers import RotatingFileHandler

import pytest


class TestLoggingRotation:
    """Test log rotation functionality."""

    @pytest.fixture
    def log_config(self):
        """Configuration for test logging."""
        return {
            "file": "test_app.log",
            "max_bytes": 1024,  # 1 KB for testing
            "backup_count": 2,
        }

    @pytest.fixture
    def test_logger(self, log_config):
        """Set up a RotatingFileHandler for testing."""
        log_file = log_config["file"]
        max_bytes = log_config["max_bytes"]
        backup_count = log_config["backup_count"]

        # Remove any existing test log files
        for i in range(backup_count + 1):
            try:
                os.remove(f"{log_file}.{i}")
            except FileNotFoundError:
                pass

        handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
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

        # Ensure all log files are removed after the test
        try:
            os.remove(log_file)
        except FileNotFoundError:
            pass

        for i in range(backup_count + 1):
            try:
                os.remove(f"{log_file}.{i}")
            except FileNotFoundError:
                pass

    @pytest.fixture
    def log_entries_generator(self):
        """Generate test log entries."""

        def generate_entries(count=100):
            return [f"Test log entry {i}" for i in range(count)]

        return generate_entries

    def test_log_rotation(self, test_logger, log_config, log_entries_generator):
        """Test that log rotation works as expected."""
        log_file = log_config["file"]
        backup_count = log_config["backup_count"]

        # Write logs to exceed the maxBytes limit
        entries = log_entries_generator()
        for entry in entries:
            test_logger.info(entry)

        # Check that the main log file and backups exist
        assert os.path.exists(log_file)
        assert os.path.exists(f"{log_file}.1")

        # Check that the number of backup files does not exceed the limit
        backup_files = [f for f in os.listdir(".") if f.startswith(log_file)]
        assert len(backup_files) <= backup_count + 1

        # Verify content in the rotated files
        with open(f"{log_file}.1", "r") as f:
            content = f.read()
            assert "Test log entry" in content
