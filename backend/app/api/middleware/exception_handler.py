"""
Exception Handling Middleware
"""

import traceback
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.middleware.logging_middleware import sanitize_error_message

logger = structlog.get_logger()


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Intercepts requests to handle exceptions consistently."""
        try:
            return await call_next(request)
        except RequestValidationError as exc:
            logger.warning(
                "Validation error",
                method=request.method,
                url=str(request.url),
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
        except Exception as exc:
            sanitized_error = sanitize_error_message(str(exc))
            logger.error(
                "Unhandled Exception",
                method=request.method,
                url=str(request.url),
                error=sanitized_error,
                error_type=type(exc).__name__,
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
