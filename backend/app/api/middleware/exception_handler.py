"""
Exception Handling Middleware
"""

import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List

import structlog
from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.middleware.error_codes import (
    AUTH_EXPIRED_TOKEN,
    AUTH_INVALID_CREDENTIALS,
    AUTH_INVALID_TOKEN,
    DB_INTEGRITY_ERROR,
    GENERAL_BUSINESS_RULE_VIOLATION,
    GENERAL_UNEXPECTED_ERROR,
    GENERAL_VALIDATION_ERROR,
    RESOURCE_INVALID_STATE,
    RESOURCE_NOT_FOUND,
    USER_EMAIL_ALREADY_REGISTERED,
    USER_EMAIL_VERIFICATION_FAILED,
    USER_NOT_FOUND,
)
from app.api.middleware.logging_middleware import (
    SENSITIVE_FIELDS,
    sanitize_error_message,
)

logger = structlog.get_logger()


class BaseApplicationError(Exception):
    """Base class for all application exceptions with standardized attributes."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class BusinessLogicError(BaseApplicationError):
    """Base exception for business logic errors."""

    def __init__(
        self,
        message: str = "Business logic error",
        error_code: str = GENERAL_BUSINESS_RULE_VIOLATION,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(message, error_code, status_code)


# User-related exceptions
class UserNotFoundError(BaseApplicationError):
    """Custom exception for user not found errors."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message, USER_NOT_FOUND, status.HTTP_404_NOT_FOUND)


class EmailAlreadyRegisteredError(BaseApplicationError):
    """Custom exception for already registered email."""

    def __init__(self, message: str = "Email already registered"):
        super().__init__(
            message, USER_EMAIL_ALREADY_REGISTERED, status.HTTP_400_BAD_REQUEST
        )


class EmailVerificationError(BaseApplicationError):
    """Custom exception for email verification errors."""

    def __init__(self, message: str = "Email verification failed"):
        super().__init__(
            message, USER_EMAIL_VERIFICATION_FAILED, status.HTTP_400_BAD_REQUEST
        )


# Authentication-related exceptions
class AuthenticationError(BaseApplicationError):
    """Custom exception for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message, AUTH_INVALID_CREDENTIALS, status.HTTP_401_UNAUTHORIZED
        )


class InvalidTokenError(BaseApplicationError):
    """Custom exception for invalid token errors."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, AUTH_INVALID_TOKEN, status.HTTP_401_UNAUTHORIZED)


class ExpiredTokenError(InvalidTokenError):
    """Custom exception for expired token errors."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)
        self.error_code = AUTH_EXPIRED_TOKEN


# Resource-related exceptions
class ResourceNotFoundError(BaseApplicationError):
    """Custom exception for when a resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, RESOURCE_NOT_FOUND, status.HTTP_404_NOT_FOUND)


class InvalidResourceStateError(BaseApplicationError):
    """Custom exception for when a resource is in an invalid state for an operation."""

    def __init__(self, message: str):
        super().__init__(message, RESOURCE_INVALID_STATE, status.HTTP_409_CONFLICT)


# Database-related exceptions
class DatabaseIntegrityError(BaseApplicationError):
    """Custom exception for database integrity errors."""

    def __init__(self, message: str = "Database integrity constraint violation"):
        super().__init__(message, DB_INTEGRITY_ERROR, status.HTTP_409_CONFLICT)


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    def _format_validation_errors(
        self, errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format validation errors with additional context."""
        formatted = []
        for error in errors:
            sanitized_ctx = {
                key: "[REDACTED]" if key.lower() in SENSITIVE_FIELDS else value
                for key, value in error.get("ctx", {}).items()
            }
            formatted.append(
                {
                    "msg": error.get("msg", "Validation error"),
                    "loc": error.get("loc", []),
                    "type": error.get("type", "validation_error"),
                    "code": GENERAL_VALIDATION_ERROR,
                    "ctx": sanitized_ctx,
                }
            )
        return formatted

    def _format_http_exception(self, exc: HTTPException) -> List[Dict[str, Any]]:
        """Format HTTP exceptions for consistent response structure"""
        detail = exc.detail
        status_code = exc.status_code
        code_prefix = f"HTTP_{status_code}"

        if isinstance(detail, str):
            return [{"msg": detail, "type": "http_error", "code": code_prefix}]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Intercepts requests to handle exceptions consistently."""
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        path = request.url.path
        method = request.method

        logger.debug(
            "Request started",
            request_id=request_id,
            method=method,
            path=path,
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                "Request completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(process_time * 1000, 2),
            )
            return response

        except BaseApplicationError as exc:
            logger.warning(
                "Application error",
                request_id=request_id,
                method=method,
                path=path,
                error=str(exc),
                error_code=exc.error_code,
                status_code=exc.status_code,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "detail": [
                        {
                            "msg": exc.message,
                            "type": type(exc).__name__.lower(),
                            "code": exc.error_code,
                        }
                    ]
                },
                headers={"X-Request-ID": request_id},
            )

        except Exception as exc:
            sanitized_error = sanitize_error_message(str(exc))
            logger.error(
                "Unhandled exception",
                request_id=request_id,
                method=method,
                path=path,
                error=sanitized_error,
                error_type=type(exc).__name__,
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": [
                        {
                            "msg": "An unexpected error occurred",
                            "type": "server_error",
                            "code": GENERAL_UNEXPECTED_ERROR,
                            "request_id": request_id,
                        }
                    ]
                },
                headers={"X-Request-ID": request_id},
            )
