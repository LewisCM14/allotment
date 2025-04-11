"""
Application Entrypoint
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

import structlog
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr

from app.api.core.config import settings
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.exception_handler import ExceptionHandlingMiddleware
from app.api.middleware.logging_middleware import (
    AsyncLoggingMiddleware,
    request_id_ctx_var,
)
from app.api.services.email_service import send_test_email
from app.api.v1 import router as api_router

logger = structlog.get_logger()

logger.info(
    "Starting application",
    app_name=settings.APP_NAME,
    version=settings.APP_VERSION,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "Application startup complete",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        api_prefix=settings.API_PREFIX,
    )
    yield
    logger.info(
        "Application shutting down",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for managing allotments",
    lifespan=lifespan,
)

# Exception Handling Middleware
logger.debug("Adding exception handling middleware")
app.add_middleware(ExceptionHandlingMiddleware)

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
def root() -> Dict[str, str]:
    """
    Application Root Endpoint

    Returns:
        dict: Metadata about the API, including name, version, and environment.
    """
    logger.info(
        "Root endpoint accessed",
        endpoint="/",
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
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

    async with safe_operation(
        "sending test email", log_context, status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        with log_timing("send_email", request_id=log_context["request_id"]):
            recipient = email if email else settings.MAIL_USERNAME
            await send_test_email(recipient)
            logger.info("Test email sent successfully", **log_context)

    return {"message": "Test email sent successfully"}
