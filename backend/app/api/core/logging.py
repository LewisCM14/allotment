"""
Logging Configuration
"""

import logging
import sys
import threading
import time
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from typing import (
    Any,
    Callable,
    Generator,
    List,
    Mapping,
    MutableMapping,
    Tuple,
    Union,
    cast,
)

import structlog

from app.api.core.config import settings
from app.api.middleware.logging_middleware import request_id_ctx_var

ProcessorType = Callable[
    [Any, str, MutableMapping[str, Any]],
    Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]],
]

log_lock = threading.Lock()


def sync_log_to_file(
    event_dict: MutableMapping[str, Any],
) -> Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]]:
    """Sync wrapper to execute logging function safely.

    Note: only the event dictionary is used; logger and method_name
    parameters were unused and removed to avoid lint warnings.
    """
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


def _file_handler_exists_for(root: logging.Logger) -> bool:
    for h in root.handlers:
        try:
            if isinstance(h, RotatingFileHandler) and (
                getattr(h, "baseFilename", None) == settings.LOG_FILE
            ):
                return True
        except Exception:
            continue
    return False


def _build_handlers() -> List[Union[logging.StreamHandler, RotatingFileHandler]]:
    handlers: List[Union[logging.StreamHandler, RotatingFileHandler]] = [
        logging.StreamHandler(sys.stdout)
    ]
    if settings.LOG_TO_FILE is True:
        root_logger = logging.getLogger()
        if not _file_handler_exists_for(root_logger):
            file_handler = RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=getattr(settings, "LOG_MAX_BYTES", 10 * 1024 * 1024),
                backupCount=getattr(settings, "LOG_BACKUP_COUNT", 5),
            )
            handlers.append(file_handler)
    return handlers


def _is_duplicate_handler(h: Any, existing_handler: Any) -> bool:
    try:
        if (
            isinstance(h, RotatingFileHandler)
            and isinstance(existing_handler, RotatingFileHandler)
            and getattr(existing_handler, "baseFilename", None)
            == getattr(h, "baseFilename", None)
        ):
            return True
        if (
            isinstance(h, logging.StreamHandler)
            and isinstance(existing_handler, logging.StreamHandler)
            and getattr(existing_handler, "stream", None) == getattr(h, "stream", None)
        ):
            return True
    except Exception:
        pass
    return False


def _attach_non_duplicate_handlers(root: logging.Logger, handlers: List) -> None:
    if not root.handlers:
        # basicConfig already used the handlers
        root.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        return

    for h in handlers:
        duplicate = any(
            _is_duplicate_handler(h, existing_handler)
            for existing_handler in root.handlers
        )
        if not duplicate:
            root.addHandler(h)


def _build_processors() -> List[ProcessorType]:
    base_processors = [
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]
    if settings.ENVIRONMENT == "production":
        # In production we add container context and return the explicit
        # list. Cast to the declared ProcessorType list for mypy.
        prod_processors = [
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
        return cast(List[ProcessorType], prod_processors)
    return cast(List[ProcessorType], base_processors)


def configure_logging() -> None:
    """Configures structured logging for FastAPI with async file logging."""
    handlers = _build_handlers()
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        handlers=handlers,
    )
    root_logger = logging.getLogger()
    _attach_non_duplicate_handlers(root_logger, handlers)
    processors = _build_processors()
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
