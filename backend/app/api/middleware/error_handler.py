"""
Exception Translation Layer

Provides utilities to translate low-level exceptions to domain-specific exceptions.
"""

import contextlib
import uuid
from functools import wraps
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    Optional,
    TypeVar,
)

import structlog
from authlib.jose.errors import (
    ExpiredTokenError as AuthlibExpiredTokenError,
)
from authlib.jose.errors import (
    InvalidClaimError,
    JoseError,
)
from fastapi import status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.error_codes import DB_QUERY_ERROR
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
    DatabaseIntegrityError,
    EmailAlreadyRegisteredError,
    ExpiredTokenError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.api.middleware.logging_middleware import sanitize_error_message

logger = structlog.get_logger()

T = TypeVar("T")
R = TypeVar("R")


def translate_token_exceptions(
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """Decorator to translate JWT exceptions into application-specific exceptions"""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except AuthlibExpiredTokenError:
            raise ExpiredTokenError()
        except InvalidClaimError as e:
            raise InvalidTokenError(f"Invalid token claim: {str(e)}")
        except JoseError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except ValueError as e:
            error_msg = str(e)
            if "key may not be safe" in error_msg or "Invalid key" in error_msg:
                raise InvalidTokenError("Invalid token signature")
            raise
        except Exception:
            raise

    return wrapper


def translate_db_exceptions(
    db_func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    """
    Decorator to translate database exceptions to domain-specific exceptions.

    Handles:
    - IntegrityError (uniqueness violations, etc.)
    - Other SQLAlchemy errors
    """

    @wraps(db_func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await db_func(*args, **kwargs)
        except IntegrityError as ie:
            error_msg = str(ie).lower()
            if "unique constraint" in error_msg and "email" in error_msg:
                raise EmailAlreadyRegisteredError()

            logger.error(
                "Database integrity error",
                error=sanitize_error_message(str(ie)),
                error_type="IntegrityError",
                exc_info=True,
            )
            raise DatabaseIntegrityError(message="Data integrity violation")
        except SQLAlchemyError as se:
            logger.error(
                "Database error",
                error=sanitize_error_message(str(se)),
                error_type=type(se).__name__,
                exc_info=True,
            )
            raise BusinessLogicError(
                message="Database operation failed",
                error_code=DB_QUERY_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return wrapper


@contextlib.asynccontextmanager
async def safe_operation(
    operation_name: str,
    log_context: Dict[str, Any],
    error_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> AsyncGenerator[None, None]:
    """Context manager for safely executing operations with standardized error handling"""
    try:
        yield
    except (RequestValidationError, ValidationError):
        raise
    except BaseApplicationError:
        raise
    except Exception as e:
        error_type = type(e).__name__
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            f"Error during {operation_name}",
            error_type=error_type,
            error_details=sanitized_error,
            exc_info=True,
            **log_context,
        )
        raise BusinessLogicError(
            message=f"An unexpected error occurred while {operation_name.replace('_', ' ')}.",
            status_code=error_code,
        )


def handle_route_exceptions(
    operation: str,
    log_context: Dict[str, Any],
    error: Exception,
    default_message: str = "An unexpected error occurred",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> None:
    """
    Standardized exception handler for API routes

    Args:
        operation: Name of the operation being performed
        log_context: Logging context dictionary
        error: The exception that was raised
        default_message: Default message for BusinessLogicError
        status_code: Status code to use for BusinessLogicError

    Raises:
        BaseApplicationError: Re-raises if error is a BaseApplicationError
        BusinessLogicError: For all other errors
    """
    if isinstance(error, BaseApplicationError):
        logger.warning(
            f"{operation} failed: {type(error).__name__}",
            error=str(error),
            error_code=error.error_code,
            status_code=error.status_code,
            **log_context,
        )
    else:
        sanitized_error = sanitize_error_message(str(error))
        logger.error(
            f"Unhandled exception during {operation}",
            error=sanitized_error,
            error_type=type(error).__name__,
            **log_context,
        )
        raise BusinessLogicError(
            message=default_message,
            status_code=status_code,
        )


async def validate_user_exists(
    db_session: AsyncSession,
    user_model: Any,
    user_email: Optional[str] = None,
    user_id: Optional[str] = None,
    log_context: Optional[Dict[str, Any]] = None,
) -> Any:
    """Validate that a user exists."""
    try:
        if user_email:
            query = select(user_model).where(user_model.user_email == user_email)
        elif user_id:
            user_uuid = uuid.UUID(user_id)
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
        raise
