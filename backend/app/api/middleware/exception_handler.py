"""
Provides standardized exception classes and handlers that work with FastAPI's
built-in exception handling system.
"""

import json
import time
import uuid
from typing import Any, Dict, Optional

import anyio
import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.api.core.config import settings
from app.api.middleware.error_codes import (
    AUTH_EXPIRED_TOKEN,
    AUTH_INVALID_CREDENTIALS,
    AUTH_INVALID_TOKEN,
    DB_INTEGRITY_ERROR,
    DB_QUERY_ERROR,
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

# Constants
VALIDATION_ERROR_MSG = "Validation error"


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


def create_error_response(
    status_code: int,
    message: str,
    error_type: str,
    error_code: str,
    request_id: str,
    extra_data: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response."""
    logger.info(
        "Creating error response",
        status_code=status_code,
        message=message,
        error_type=error_type,
        error_code=error_code,
        request_id=request_id,
    )

    error_detail = {
        "msg": message,
        "type": error_type,
        "code": error_code,
    }

    if extra_data:
        error_detail.update(extra_data)

    # Add metadata for server errors
    if status_code >= 500:
        error_detail.update(
            {
                "request_id": request_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "environment": settings.ENVIRONMENT,
            }
        )

    return JSONResponse(
        status_code=status_code,
        content={"detail": [error_detail]},
        headers={"X-Request-ID": request_id},
    )


def _sanitize_validation_context(error_ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize validation error context to avoid exposing sensitive data."""
    sanitized_ctx = {}
    for key, value in error_ctx.items():
        if key.lower() in SENSITIVE_FIELDS:
            sanitized_ctx[key] = "[REDACTED]"
        else:
            try:
                # Test if value is JSON serializable
                json.dumps(value)
                sanitized_ctx[key] = value
            except TypeError:
                # Convert non-serializable values to string
                sanitized_ctx[key] = str(value)
    return sanitized_ctx


def _format_validation_error(error: Dict[str, Any]) -> Dict[str, Any]:
    """Format a single validation error with proper sanitization."""
    sanitized_ctx = {}
    if "ctx" in error and error["ctx"]:
        sanitized_ctx = _sanitize_validation_context(error["ctx"])

    return {
        "msg": error.get("msg", VALIDATION_ERROR_MSG),
        "loc": error.get("loc", []),
        "type": "validation_error",
        "code": GENERAL_VALIDATION_ERROR,
        "ctx": sanitized_ctx,
    }


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle FastAPI validation errors with proper formatting and logging."""
    if not isinstance(exc, RequestValidationError):
        raise exc  # safety check, should not occur with proper registration
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.warning(
        VALIDATION_ERROR_MSG,
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        errors=exc.errors(),
    )

    # Format validation errors with security sanitization
    formatted_errors = [_format_validation_error(error) for error in exc.errors()]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": formatted_errors},
        headers={"X-Request-ID": request_id},
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle direct Pydantic validation errors."""
    if not isinstance(exc, ValidationError):
        raise exc
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.warning(
        "Pydantic validation error",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        errors=exc.errors(),
    )

    formatted_errors: list[Dict[str, Any]] = []
    for error in exc.errors():
        sanitized_ctx = {}
        if "ctx" in error:
            sanitized_ctx = {
                key: "[REDACTED]" if key.lower() in SENSITIVE_FIELDS else value
                for key, value in error["ctx"].items()
            }
        formatted_errors.append(
            {
                "msg": error.get("msg", VALIDATION_ERROR_MSG),
                "loc": error.get("loc", []),
                "type": error.get("type", "validation_error"),
                "code": GENERAL_VALIDATION_ERROR,
                "ctx": sanitized_ctx,
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": formatted_errors},
        headers={"X-Request-ID": request_id},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI HTTP exceptions with consistent formatting."""
    if not isinstance(exc, HTTPException):
        raise exc
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.warning(
        "HTTP exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    detail_msg = str(exc.detail)
    error_detail = [
        {
            "msg": detail_msg,
            "type": "http_error",
            "code": f"HTTP_{exc.status_code}",
        }
    ]

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": error_detail},
        headers={"X-Request-ID": request_id},
    )


async def application_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle custom application exceptions."""
    if not isinstance(exc, BaseApplicationError):
        raise exc
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.warning(
        "Application error",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        error=str(exc),
        error_code=exc.error_code,
        status_code=exc.status_code,
        error_type=type(exc).__name__,
    )

    return create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_type=type(exc).__name__.lower(),
        error_code=exc.error_code,
        request_id=request_id,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    sanitized_error = sanitize_error_message(str(exc))
    logger.error(
        "Unhandled exception in general_exception_handler",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        error=sanitized_error,
        error_type=type(exc).__name__,
        exc_info=settings.LOG_LEVEL.upper() == "DEBUG",
    )
    logger.debug(
        "General exception handler invoked",
        request_id=request_id,
        error_type=type(exc).__name__,
        error_message=str(exc),
    )

    response = create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred",
        error_type="server_error",
        error_code=GENERAL_UNEXPECTED_ERROR,
        request_id=request_id,
    )

    # Safely decode response.body for both bytes and memoryview
    body_bytes = response.body
    if isinstance(body_bytes, memoryview):
        body_bytes = body_bytes.tobytes()
    response_content = body_bytes.decode("utf-8")
    logger.debug(
        "Exiting general_exception_handler",
        response_status_code=response.status_code,
        response_content=response_content,
    )

    return response


def handle_db_exceptions(error: Exception) -> None:
    """Convert database exceptions to application exceptions."""
    if isinstance(error, IntegrityError):
        error_msg = str(error).lower()
        if "unique constraint" in error_msg and "email" in error_msg:
            raise EmailAlreadyRegisteredError()
        if "unique constraint" in error_msg and "user_allotment.user_id" in error_msg:
            raise DatabaseIntegrityError(message="User already has an allotment")

        logger.error(
            "Database integrity error",
            error=sanitize_error_message(str(error)),
            error_type="IntegrityError",
            exc_info=True,
        )
        raise DatabaseIntegrityError(message="Data integrity violation")

    elif isinstance(error, SQLAlchemyError):
        logger.error(
            "Database error",
            error=sanitize_error_message(str(error)),
            error_type=type(error).__name__,
            exc_info=True,
        )
        raise BusinessLogicError(
            message="Database operation failed",
            error_code=DB_QUERY_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def handle_auth_exceptions(error: Exception) -> None:
    """Convert authentication library exceptions to application exceptions."""
    from authlib.jose.errors import (
        ExpiredTokenError as AuthlibExpiredTokenError,
    )
    from authlib.jose.errors import (
        InvalidClaimError,
        JoseError,
    )

    if isinstance(error, AuthlibExpiredTokenError):
        raise ExpiredTokenError()
    elif isinstance(error, InvalidClaimError):
        raise InvalidTokenError(f"Invalid token claim: {str(error)}")
    elif isinstance(error, JoseError):
        raise InvalidTokenError(f"Invalid token: {str(error)}")
    elif isinstance(error, ValueError):
        error_msg = str(error)
        if "key may not be safe" in error_msg or "Invalid key" in error_msg:
            raise InvalidTokenError("Invalid token signature")


async def validate_user_exists(
    db_session: AsyncSession,
    user_model: Any,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Any:
    """Validate that a user exists in the database."""
    import uuid

    try:
        if user_email:
            query = select(user_model).where(user_model.user_email == user_email)
        elif user_id:
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                raise InvalidTokenError("Invalid user ID format")
            query = select(user_model).where(user_model.user_id == user_uuid)
        else:
            raise ValueError("Either user_email or user_id must be provided")

        result = await db_session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundError()

        return user

    except ValueError as e:
        if "invalid literal for uuid" in str(e):
            raise InvalidTokenError("Invalid user ID format")
        raise


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers for the FastAPI application."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(BaseApplicationError, application_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    # Custom application exceptions
    app.add_exception_handler(BaseApplicationError, application_exception_handler)

    # Fallback for any other unhandled exceptions (must be last)
    app.add_exception_handler(Exception, general_exception_handler)
    # HTTP exceptions (4xx/5xx from route handlers)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Custom application exceptions
    app.add_exception_handler(BaseApplicationError, application_exception_handler)

    # Fallback for any other unhandled exceptions (must be last)
    app.add_exception_handler(Exception, general_exception_handler)


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        logger.debug(
            "Entering ExceptionHandlingMiddleware.dispatch",
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
        )
        try:
            try:
                response = await call_next(request)
                logger.debug(
                    "Exiting ExceptionHandlingMiddleware.dispatch",
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            except anyio.EndOfStream as e:
                logger.error(
                    "EndOfStream error intercepted in ExceptionHandlingMiddleware.dispatch",
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                )
                response = await general_exception_handler(request, e)
            except Exception as e:
                logger.error(
                    "Exception intercepted in ExceptionHandlingMiddleware.dispatch",
                    exception_type=type(e).__name__,
                    exception_message=str(e),
                )
                if isinstance(e, BaseApplicationError):
                    response = await application_exception_handler(request, e)
                else:
                    response = await general_exception_handler(request, e)
        except Exception as e:
            # Catch any exception not caught above (e.g., in route handler before response)
            logger.error(
                "Exception intercepted at outermost ExceptionHandlingMiddleware level",
                exception_type=type(e).__name__,
                exception_message=str(e),
            )
            response = await general_exception_handler(request, e)

        logger.debug(
            "Response created by ExceptionHandlingMiddleware.dispatch",
            status_code=response.status_code,
            headers=dict(response.headers),
        )
        return response
