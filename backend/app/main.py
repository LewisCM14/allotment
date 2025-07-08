"""
Application Entrypoint
"""

import atexit
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr

from app.api.core.config import settings
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.exceptions import register_exception_handlers
from app.api.middleware.logging_middleware import (
    AsyncLoggingMiddleware,
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.schemas.client_error_schema import ClientErrorLog
from app.api.services.email_service import send_test_email
from app.api.v1 import router as api_router

logger = structlog.get_logger()

logger.info(
    "Starting application",
    app_name=settings.APP_NAME,
    version=settings.APP_VERSION,
    environment=settings.ENVIRONMENT,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        logger.info(
            "Application startup complete",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            api_prefix=settings.API_PREFIX,
        )
        yield
    except Exception as exc:
        sanitized_error = sanitize_error_message(str(exc))
        logger.error(
            "Error during application lifespan",
            error=sanitized_error,
            error_type=type(exc).__name__,
            request_id=request_id_ctx_var.get(),
        )
        raise
    finally:
        logger.info(
            "Application shutting down",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
        )
        flush_logs()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for managing allotments",
    lifespan=lifespan,
)


# Register Exception Handlers
# Use FastAPI's built-in exception handling system
logger.debug("Registering exception handlers")
register_exception_handlers(app)


# Request Logging Middleware (replaces the old ExceptionHandlingMiddleware)
logger.debug("Adding request logging middleware")
app.add_middleware(AsyncLoggingMiddleware)

# CORS Middleware
logger.debug("Adding CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Logging Middleware
logger.debug("Adding logging middleware")
app.add_middleware(AsyncLoggingMiddleware)

# Rate Limiter
app.state.limiter = limiter

# Register Routes
logger.debug("Registering API routes")
app.include_router(api_router, prefix="/api/v1")


@app.get(
    "/", tags=["Utility"], summary="API Root", description="Root endpoint for the API"
)
async def root() -> Dict[str, str]:
    """
    Application Root Endpoint

    Returns:
        dict: Metadata about the API, including name, version, and environment.
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "root",
    }

    logger.info(
        "Root endpoint accessed",
        endpoint="/",
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        **log_context,
    )
    return {
        "message": "Welcome to the Allotment Service API!",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.post(
    "/test-email",
    tags=["Utility"],
    status_code=status.HTTP_200_OK,
    summary="Test email configuration",
    description="Send a test email to verify SMTP configuration is working",
    response_model=Dict[str, str],
)
async def test_email_config(email: Optional[EmailStr] = None) -> Dict[str, str]:
    """
    Send a test email to verify SMTP configuration.

    Args:
        email: Optional recipient email (defaults to sender if not provided)

    Returns:
        dict: Success message
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "test_email",
        "recipient": email if email else settings.MAIL_USERNAME,
    }

    logger.info("Test email requested", **log_context)

    try:
        with log_timing("send_email", request_id=log_context["request_id"]):
            recipient = email if email else settings.MAIL_USERNAME
            await send_test_email(recipient)
            logger.info("Test email sent successfully", **log_context)

        return {"message": "Test email sent successfully"}
    except Exception as exc:
        logger.error(
            "Error sending test email",
            error=str(exc),
            error_type=type(exc).__name__,
            **log_context,
        )
        raise


@app.post("/api/v1/log-client-error")
async def handle_log_client_error(
    error_log: ClientErrorLog, request: Request
) -> Dict[str, str]:
    logger.error(
        "Client-side error reported",
        operation="log_client_error",
        client_error_message=error_log.error,
        client_error_details=error_log.details,
    )
    return {"message": "Client error logged successfully"}


def flush_logs() -> None:
    """Flush pending logs during shutdown."""
    try:
        logger = logging.getLogger()

        can_log = all(
            not (
                hasattr(handler, "stream") and handler.stream and handler.stream.closed
            )
            for handler in logger.handlers
            if hasattr(handler, "stream")
        )

        if can_log:
            logger.info("Flushing logs before shutdown")
            structlog.get_logger().info("Application shutting down")

        for handler in logger.handlers:
            try:
                if hasattr(handler, "flush"):
                    handler.flush()
                if hasattr(handler, "close") and not (
                    hasattr(handler, "stream")
                    and handler.stream
                    and handler.stream.closed
                ):
                    handler.close()
            except (ValueError, IOError):
                pass
    except Exception:
        pass


atexit.register(flush_logs)
