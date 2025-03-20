"""
Exception Handling
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


async def async_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Logs async exceptions and returns a structured error response."""
    logger.error(
        "Unhandled Exception",
        url=str(request.url),
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred."},
    )


def setup_exception_handler(app: FastAPI) -> None:
    """Registers the custom async exception handler."""
    app.add_exception_handler(Exception, async_exception_handler)
