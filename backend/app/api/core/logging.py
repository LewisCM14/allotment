"""
Logging Configuration
"""

import logging
import sys
import threading
import time
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from typing import Any, Callable, Generator, List, Mapping, MutableMapping, Tuple, Union

import structlog

from app.api.core.config import settings
from app.api.middleware.logging_middleware import request_id_ctx_var

ProcessorType = Callable[
    [Any, str, MutableMapping[str, Any]],
    Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]],
]

log_lock = threading.Lock()


def sync_log_to_file(
    logger: structlog.BoundLogger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]]:
    """Sync wrapper to execute logging function safely."""
    if settings.LOG_TO_FILE:
        log_entry: str = f"{event_dict}\n"
        try:
            with log_lock:
                append_to_file(log_entry)
        except Exception as e:
            print(f"Failed to log to file: {e}", file=sys.stderr)
    return event_dict


def append_to_file(log_entry: str) -> None:
    """Blocking file write function."""
    try:
        with open(settings.LOG_FILE, "a") as log_file:
            log_file.write(log_entry)
    except Exception as e:
        print(f"Failed to write log entry: {e}", file=sys.stderr)


@contextmanager
def log_timing(operation: str, **context: Any) -> Generator[None, None, None]:
    """Context manager to log timing information for operations."""
    start_time = time.monotonic()
    request_id = request_id_ctx_var.get()

    log_context = {"request_id": request_id, "operation": operation, **context}
    logger = structlog.get_logger()
    logger.debug(f"Starting {operation}", **log_context)

    try:
        yield
    finally:
        process_time = time.monotonic() - start_time
        if process_time > settings.SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"Slow operation detected: {operation}",
                process_time=f"{process_time:.3f}s",
                **log_context,
            )
        else:
            logger.debug(
                f"Completed {operation}",
                process_time=f"{process_time:.3f}s",
                **log_context,
            )


def configure_logging() -> None:
    """Configures structured logging for FastAPI with async file logging."""
    handlers: List[Union[logging.StreamHandler, RotatingFileHandler]] = [
        logging.StreamHandler(sys.stdout)
    ]

    if settings.LOG_TO_FILE is True:
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        handlers.append(file_handler)

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        handlers=handlers,
    )

    processors: List[ProcessorType]

    if settings.ENVIRONMENT == "production":
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            add_container_context,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            sync_log_to_file,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def add_container_context(
    logger: structlog.BoundLogger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Add container-specific context to log entries."""
    import os

    hostname = os.environ.get("HOSTNAME", "unknown")
    event_dict["container_id"] = hostname
    return event_dict


configure_logging()
logger = structlog.get_logger()
