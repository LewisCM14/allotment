"""
Logging Configuration
"""

import asyncio
import logging
import sys
import threading
import time
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from typing import Any, Generator, List, Mapping, MutableMapping, Tuple, Union

import structlog

from app.api.core.config import settings
from app.api.middleware.logging_middleware import request_id_ctx_var

log_lock = threading.Lock()


def sync_log_to_file(
    logger: structlog.BoundLogger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]]:
    """Sync wrapper to execute async logging function."""
    if settings.LOG_TO_FILE:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(write_log_async(event_dict))
        else:
            asyncio.run(write_log_async(event_dict))
    return event_dict


async def write_log_async(event_dict: MutableMapping[str, Any]) -> None:
    """Writes logs to a file asynchronously, preventing race conditions."""
    log_entry: str = f"{event_dict}\n"
    with log_lock:
        await asyncio.to_thread(append_to_file, log_entry)


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

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            sync_log_to_file,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


configure_logging()
logger = structlog.get_logger()
