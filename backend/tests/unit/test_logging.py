import logging
import os
from logging.handlers import RotatingFileHandler

import pytest

from app.api.core import logging as core_logging
from app.api.core.config import settings


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


def _has_rotating_filehandler_for(path: str) -> bool:
    for h in logging.getLogger().handlers:
        if isinstance(h, RotatingFileHandler):
            try:
                if getattr(h, "baseFilename", None) == path:
                    return True
            except Exception:
                continue
    return False


def test_no_file_handler_when_log_to_file_false():
    # Ensure environment default for tests is false
    assert settings.LOG_TO_FILE is False
    # Re-configure logging to reflect current settings
    core_logging.configure_logging()
    assert _has_rotating_filehandler_for(settings.LOG_FILE) is False


def test_logging_middleware_redacts_token_in_password_reset_url() -> None:
    from app.api.middleware.logging_middleware import redact_url_tokens

    url = "http://api.example.com/api/v1/auth/password-resets/eyJhbGciOiJSUzI1NiJ9.payload.sig"
    redacted = redact_url_tokens(url)
    assert "eyJhbGciOiJSUzI1NiJ9" not in redacted
    assert "[REDACTED]" in redacted


def test_logging_middleware_redacts_token_in_email_verification_url() -> None:
    from app.api.middleware.logging_middleware import redact_url_tokens

    url = "http://api.example.com/api/v1/registration/email-verifications/eyJhbGc.payload.sig"
    redacted = redact_url_tokens(url)
    assert "eyJhbGc" not in redacted
    assert "[REDACTED]" in redacted


def test_logging_middleware_redacts_jwt_like_segment_in_any_url_path() -> None:
    from app.api.middleware.logging_middleware import redact_url_tokens

    token = "eyJhbGciOiJSUzI1NiJ9.payload.sig"
    url = f"http://api.example.com/api/v1/audit/{token}/events"
    redacted = redact_url_tokens(url)
    assert token not in redacted
    assert "[REDACTED]" in redacted


def test_logging_middleware_does_not_redact_normal_url() -> None:
    from app.api.middleware.logging_middleware import redact_url_tokens

    url = "http://api.example.com/api/v1/users/profile"
    assert redact_url_tokens(url) == url


def test_logging_middleware_does_not_redact_non_jwt_like_dotted_segment() -> None:
    from app.api.middleware.logging_middleware import redact_url_tokens

    dotted_segment = f"{'a' * 1024}.{'b' * 1024}."
    url = f"http://api.example.com/api/v1/users/{dotted_segment}"
    assert redact_url_tokens(url) == url


def test_configure_logging_idempotent(tmp_path, monkeypatch):
    # Temporarily enable file logging and set a temporary path
    monkeypatch.setattr(settings, "LOG_TO_FILE", True)
    tmp_file = str(tmp_path / "test_app.log")
    monkeypatch.setattr(settings, "LOG_FILE", tmp_file)

    # First call should add a handler
    core_logging.configure_logging()
    assert _has_rotating_filehandler_for(tmp_file) is True

    # Capture number of handlers matching that file
    count_before = sum(
        1
        for h in logging.getLogger().handlers
        if isinstance(h, RotatingFileHandler)
        and getattr(h, "baseFilename", None) == tmp_file
    )

    # Second call should not add a duplicate
    core_logging.configure_logging()
    count_after = sum(
        1
        for h in logging.getLogger().handlers
        if isinstance(h, RotatingFileHandler)
        and getattr(h, "baseFilename", None) == tmp_file
    )

    assert count_after == count_before


def test_configure_logging_reapplies_level_with_existing_handlers(monkeypatch):
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level

    try:
        root_logger.handlers = [logging.StreamHandler()]
        root_logger.setLevel(logging.DEBUG)
        monkeypatch.setattr(settings, "LOG_LEVEL", "INFO")

        core_logging.configure_logging()

        assert root_logger.level == logging.INFO
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
