"""
Logging Configuration
"""

import asyncio
import logging
import sys

import structlog

from app.api.core.config import settings


def sync_log_to_file(logger, method_name, event_dict):
    """Sync wrapper to execute async logging function."""
    asyncio.create_task(write_log_async(event_dict))
    return event_dict


async def write_log_async(event_dict):
    """Writes logs to a file asynchronously, preventing race conditions."""
    log_entry = f"{event_dict}\n"
    async with asyncio.Lock():
        await asyncio.to_thread(append_to_file, log_entry)


def append_to_file(log_entry):
    """Blocking file write function."""
    with open(settings.LOG_FILE, "a") as log_file:
        log_file.write(log_entry)


def configure_logging():
    """Configures structured logging for FastAPI with async file logging."""
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            sync_log_to_file,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


configure_logging()
logger = structlog.get_logger()
