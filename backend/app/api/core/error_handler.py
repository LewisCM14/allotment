"""
Exception Translation Layer

Provides utilities to translate low-level exceptions to domain-specific exceptions.
"""

import contextlib
from functools import wraps
from typing import Any, Callable, Dict, TypeVar, Awaitable

import structlog
from authlib.jose.errors import JoseError, ExpiredTokenError, InvalidClaimError
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.api.middleware.exception_handler import (
    InvalidTokenError,
    BusinessLogicError,
    UserNotFoundError,
)
from app.api.middleware.logging_middleware import sanitize_error_message

logger = structlog.get_logger()

T = TypeVar('T')

def translate_token_exceptions(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator to translate JWT exceptions into application-specific exceptions"""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except ExpiredTokenError:
            raise InvalidTokenError("Token has expired")
        except InvalidClaimError as e:
            raise InvalidTokenError(f"Invalid token claim: {str(e)}")
        except JoseError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except ValueError as e:
            # Handle specific ValueError from token validation
            error_msg = str(e)
            if "key may not be safe" in error_msg or "Invalid key" in error_msg:
                raise InvalidTokenError("Invalid token signature")
            # Re-raise other ValueErrors
            raise
        except Exception:
            # Re-raise any other exceptions
            raise
    return wrapper

def translate_db_exceptions(db_func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to translate database exceptions to domain-specific exceptions.
    
    Handles:
    - IntegrityError (uniqueness violations, etc.)
    - Other SQLAlchemy errors
    """
    async def wrapper(*args, **kwargs):
        try:
            return await db_func(*args, **kwargs) if callable(db_func) else db_func
        except IntegrityError as ie:
            error_msg = str(ie).lower()
            # Translate specific integrity errors based on error message
            if "unique constraint" in error_msg and "email" in error_msg:
                from app.api.middleware.exception_handler import EmailAlreadyRegisteredError
                raise EmailAlreadyRegisteredError()
                
            # Generic database integrity error
            logger.error(
                "Database integrity error",
                error=sanitize_error_message(str(ie)),
                error_type="IntegrityError",
            )
            raise BusinessLogicError(
                "Data integrity violation", 
                status_code=status.HTTP_409_CONFLICT
            )
        except SQLAlchemyError as se:
            # Generic database error
            logger.error(
                "Database error",
                error=sanitize_error_message(str(se)),
                error_type=type(se).__name__,
            )
            raise BusinessLogicError(
                "Database operation failed", 
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper

@contextlib.asynccontextmanager
async def safe_operation(operation_name: str, log_context: Dict[str, Any], error_code: int = status.HTTP_400_BAD_REQUEST):
    """Context manager for safely executing operations with standardized error handling"""
    try:
        yield
    except BusinessLogicError:
        # Let middleware handle BusinessLogicError as is
        raise
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            f"Error during {operation_name}",
            error_type=error_type,
            error_details=str(e),
            **log_context
        )
        # Convert to BusinessLogicError for consistent handling
        raise BusinessLogicError(
            f"Failed to perform {operation_name}: {str(e)}",
            status_code=error_code
        )

async def validate_user_exists(db_session, user_model, user_email=None, user_id=None, log_context=None):
    """Utility to validate user existence by email or ID"""
    from sqlalchemy import select
    
    if not log_context:
        log_context = {}
        
    if user_email:
        query = select(user_model).where(user_model.user_email == user_email)
        identifier = user_email
        field = "email"
    elif user_id:
        query = select(user_model).where(user_model.user_id == user_id)
        identifier = str(user_id)
        field = "ID"
    else:
        raise ValueError("Either user_email or user_id must be provided")
        
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(
            f"User with {field} {identifier} not found",
            **log_context
        )
        # Use consistent error message to match tests
        raise UserNotFoundError("User not found")
        
    return user
