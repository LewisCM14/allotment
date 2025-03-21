"""
Exception Handling
"""

import traceback
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = structlog.get_logger()


async def async_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Logs async exceptions and returns a structured error response."""
    request_info: Dict[str, Any] = {
        "method": request.method,
        "url": str(request.url),
        "client_host": request.client.host if request.client else "Unknown",
        "headers": dict(request.headers),
        "path_params": request.path_params,
        "error_type": exc.__class__.__name__,
    }

    # Handle Pydantic validation errors separately
    if isinstance(exc, RequestValidationError):
        logger.warning(
            "Validation error",
            **request_info,
            validation_errors=exc.errors(),
        )
        errors = exc.errors()
        for error in errors:
            if error.get("ctx"):
                error["ctx"] = {k: str(v) for k, v in error["ctx"].items()}
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": errors},
        )

    if isinstance(exc, ValueError):
        logger.warning(
            "Value validation error",
            **request_info,
            error=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": [
                    {
                        "loc": ["body"],
                        "msg": str(exc),
                        "type": "value_error",
                    }
                ]
            },
        )

    logger.error(
        "Unexpected error",
        **request_info,
        error=str(exc),
        traceback=traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": [
                {
                    "msg": "An unexpected error occurred",
                    "type": "server_error",
                }
            ]
        },
    )


def setup_exception_handler(app: FastAPI) -> None:
    """Registers the custom async exception handler."""
    logger.info("Setting up exception handlers")

    try:
        app.add_exception_handler(Exception, async_exception_handler)
        app.add_exception_handler(RequestValidationError, async_exception_handler)
        logger.info("Exception handlers registered successfully")
    except Exception as e:
        logger.error(
            "Failed to setup exception handlers",
            error=str(e),
            traceback=traceback.format_exc(),
        )
        raise
