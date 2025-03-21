"""
Logging Configuration
"""

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Any, Mapping, MutableMapping, Tuple, Union

import structlog

from app.api.core.config import settings


def sync_log_to_file(
    logger: structlog.BoundLogger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]]:
    """Sync wrapper to execute async logging function."""
    asyncio.create_task(write_log_async(event_dict))
    return event_dict


async def write_log_async(event_dict: MutableMapping[str, Any]) -> None:
    """Writes logs to a file asynchronously, preventing race conditions."""
    log_entry: str = f"{event_dict}\n"
    async with asyncio.Lock():
        await asyncio.to_thread(append_to_file, log_entry)


def append_to_file(log_entry: str) -> None:
    """Blocking file write function."""
    with open(settings.LOG_FILE, "a") as log_file:
        log_file.write(log_entry)


def configure_logging() -> None:
    """Configures structured logging for FastAPI with async file logging."""
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler(sys.stdout), file_handler],
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
