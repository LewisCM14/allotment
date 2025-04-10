"""
Application Entrypoint
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

import structlog
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import EmailStr

from app.api.core.config import settings
from app.api.core.limiter import limiter
from app.api.middleware.exception_handler import ExceptionHandlingMiddleware
from app.api.middleware.logging_middleware import AsyncLoggingMiddleware
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

# Exception Handling Middleware
logger.debug("Adding exception handling middleware")
app.add_middleware(ExceptionHandlingMiddleware)

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
)
async def test_email_config(
    email: Optional[EmailStr] = None,
) -> dict[str, str]:
    """
    Send a test email to verify SMTP configuration.

    Args:
        email: Optional recipient email (defaults to sender if not provided)

    Returns:
        dict: Success message
    """
    try:
        recipient = email if email else settings.MAIL_USERNAME

        await send_test_email(recipient)
        return {"message": "Test email sent successfully"}
    except Exception as e:
        logger.exception("Error sending test email", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}",
        )
