"""
Application Entrypoint
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

import structlog
from fastapi import FastAPI

from app.api.core.config import settings
from app.api.middleware.exception_handler import setup_exception_handler
from app.api.middleware.logging_middleware import AsyncLoggingMiddleware
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

# Logging Middleware
logger.debug("Adding logging middleware")
app.add_middleware(AsyncLoggingMiddleware)

# Register Exception Handler
logger.debug("Setting up exception handlers")
setup_exception_handler(app)

# Register Routes
logger.debug("Registering API routes")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root() -> Dict[str, str]:
    """Application Root"""
    logger.info(
        "Root endpoint accessed", endpoint="/", app_version=settings.APP_VERSION
    )
    return {
        "message": "Welcome to the Allotment Service API!",
        "version": settings.APP_VERSION,
    }
