"""
Exception Handling Middleware
"""

import traceback
from typing import Awaitable, Callable, Dict, Any, List, Union
import time

import structlog
from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from authlib.jose.errors import JoseError, ExpiredTokenError, InvalidClaimError

from app.api.factories.user_factory import ValidationError
from app.api.middleware.logging_middleware import sanitize_error_message

logger = structlog.get_logger()


class UserNotFoundError(Exception):
    """Custom exception for user not found errors."""
    def __init__(self, message="User not found"):
        self.message = message
        super().__init__(self.message)


class InvalidTokenError(Exception):
    """Custom exception for invalid token errors."""
    def __init__(self, message="Invalid token"):
        self.message = message
        super().__init__(self.message)


class EmailAlreadyRegisteredError(Exception):
    """Custom exception for already registered email."""
    def __init__(self, message="Email already registered"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Custom exception for authentication failures."""
    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Base exception for business logic errors."""
    def __init__(self, message="Business logic error", status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class EmailVerificationError(BusinessLogicError):
    """Custom exception for email verification errors."""
    def __init__(self, message="Email verification failed", status_code=status.HTTP_400_BAD_REQUEST):
        super().__init__(message, status_code)


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Intercepts requests to handle exceptions consistently."""
        start_time = time.time()
        process_time = None  # Initialize process_time to avoid UnboundLocalError
        request_id = request.headers.get("X-Request-ID", "unknown")
        path = request.url.path
        method = request.method
        
        # Basic request logging
        logger.debug(
            f"Request started: {method} {path}",
            request_id=request_id,
            method=method,
            path=path,
        )
        
        try:
            response = await call_next(request)
            
            # Log response time for successful requests
            process_time = time.time() - start_time
            logger.debug(
                f"Request completed: {method} {path}",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(process_time * 1000, 2)
            )
            
            return response
            
        except Exception as exc:
            # Calculate process_time if not already calculated
            if process_time is None:
                process_time = time.time() - start_time

            if isinstance(exc, RequestValidationError):
                logger.warning(
                    "Validation error",
                    request_id=request_id,
                    method=method,
                    path=path,
                    validation_errors=exc.errors(),
                    duration_ms=round(process_time * 1000, 2),
                )
                errors = exc.errors()
                for error in errors:
                    if error.get("ctx"):
                        error["ctx"] = {k: str(v) for k, v in error["ctx"].items()}
                
                # Format errors to be more user-friendly
                formatted_errors = self._format_validation_errors(errors)
                
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={"detail": formatted_errors},
                )
                
            elif isinstance(exc, ValidationError):
                # More specific handling for our custom validation errors
                field = getattr(exc, 'field', None)
                status_code = getattr(exc, 'status_code', status.HTTP_400_BAD_REQUEST)
                
                logger.warning(
                    "Validation error",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=str(exc),
                    field=field,
                    status_code=status_code,
                    duration_ms=round(process_time * 1000, 2),
                )
                
                # Return consistent JSON response
                return JSONResponse(
                    status_code=status_code,
                    content={
                        "detail": [{
                            "msg": str(exc),
                            "loc": [field] if field else ["body"],
                            "type": "validation_error"
                        }]
                    }
                )
                
            elif isinstance(exc, JoseError):
                # Specific handling for JWT errors
                error_detail = "Invalid authentication token"
                status_code = status.HTTP_401_UNAUTHORIZED
                
                if isinstance(exc, ExpiredTokenError):
                    error_detail = "Authentication token has expired"
                elif isinstance(exc, InvalidClaimError):
                    error_detail = f"Invalid token claim: {str(exc)}"
                    
                logger.warning(
                    "JWT authentication error",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=sanitize_error_message(str(exc)),
                    error_type=type(exc).__name__,
                    duration_ms=round(process_time * 1000, 2),
                )
                
                return JSONResponse(
                    status_code=status_code,
                    content={"detail": [{
                        "msg": error_detail,
                        "type": "authentication_error"
                    }]},
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            elif isinstance(exc, HTTPException):
                logger.warning(
                    "HTTP exception",
                    request_id=request_id,
                    method=method,
                    path=path,
                    status_code=exc.status_code,
                    detail=exc.detail,
                    duration_ms=round(process_time * 1000, 2),
                )
                
                # Format the error response consistently
                detail = self._format_http_exception(exc)
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": detail},
                    headers=getattr(exc, "headers", None),
                )
                
            elif isinstance(exc, UserNotFoundError):
                logger.warning(
                    "User not found",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=str(exc),
                    duration_ms=round(process_time * 1000, 2),
                )
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"detail": [{"msg": str(exc), "type": "user_not_found"}]},
                )

            elif isinstance(exc, InvalidTokenError):
                logger.warning(
                    "Invalid token",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=str(exc),
                    duration_ms=round(process_time * 1000, 2),
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": [{"msg": str(exc), "type": "invalid_token"}]},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            elif isinstance(exc, EmailAlreadyRegisteredError):
                logger.warning(
                    "Email already registered",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=str(exc),
                    duration_ms=round(process_time * 1000, 2),
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": [{"msg": str(exc), "type": "email_already_registered"}]},
                )

            elif isinstance(exc, AuthenticationError):
                logger.warning(
                    "Authentication failure",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=str(exc),
                    duration_ms=round(process_time * 1000, 2),
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": [{"msg": str(exc), "type": "authentication_error"}]},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            elif isinstance(exc, BusinessLogicError):
                logger.warning(
                    "Business logic error",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=str(exc),
                    error_type=type(exc).__name__,
                    status_code=exc.status_code,
                    duration_ms=round(process_time * 1000, 2),
                )
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": [{"msg": str(exc), "type": "business_logic_error"}]},
                )

            # Add additional exception handling for repository layer errors
            elif hasattr(exc, 'status_code') and hasattr(exc, 'detail'):
                # Handle exceptions from repository layer that have status_code and detail
                process_time = time.time() - start_time
                status_code = getattr(exc, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
                detail = getattr(exc, 'detail', "An error occurred")
                
                logger.warning(
                    "Repository layer exception",
                    request_id=request_id,
                    method=method,
                    path=path,
                    status_code=status_code,
                    detail=detail,
                    error_type=type(exc).__name__,
                    duration_ms=round(process_time * 1000, 2),
                )
                
                return JSONResponse(
                    status_code=status_code,
                    content={"detail": [{"msg": detail, "type": "domain_error"}]},
                )

            else:
                sanitized_error = sanitize_error_message(str(exc))
                tb = traceback.format_exc()
                if len(tb) > 2000:  # Limit traceback size
                    tb = tb[:1000] + "...\n...\n" + tb[-1000:]
                    
                logger.error(
                    "Unhandled Exception",
                    request_id=request_id,
                    method=method,
                    path=path,
                    error=sanitized_error,
                    error_type=type(exc).__name__,
                    traceback=tb,
                    duration_ms=round(process_time * 1000, 2),
                )
                
                # In production, never expose the real error
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "detail": [
                            {
                                "msg": "An unexpected error occurred",
                                "type": "server_error",
                                "request_id": request_id,  # Include request ID for troubleshooting
                            }
                        ]
                    },
                )
    
    def _format_validation_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format validation errors for consistent response structure"""
        formatted = []
        for error in errors:
            formatted.append({
                "msg": error.get("msg", "Validation error"),
                "loc": error.get("loc", []),
                "type": error.get("type", "validation_error"),
                "ctx": error.get("ctx", {})
            })
        return formatted
    
    def _format_http_exception(self, exc: HTTPException) -> Union[List[Dict[str, Any]], Any]:
        """Format HTTP exceptions for consistent response structure"""
        if isinstance(exc.detail, str):
            return [{
                "msg": exc.detail,
                "type": "http_error"
            }]
        return exc.detail
