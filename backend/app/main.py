"""
Application Entrypoint
"""

import structlog
from fastapi import FastAPI

from app.api.core.config import settings
from app.api.middleware.exception_handler import setup_exception_handler
from app.api.middleware.logging_middleware import AsyncLoggingMiddleware
from app.api.v1 import router as api_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

logger = structlog.get_logger()

# Logging Middleware
app.add_middleware(AsyncLoggingMiddleware)

# Register Exception Handler
setup_exception_handler(app)


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Application Root"""
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Allotment Service API!"}
