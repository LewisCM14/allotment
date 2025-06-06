"""
Logging Middleware
"""

import re
import time
import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable, Dict, Optional

import structlog
from fastapi import Request, Response
from opentelemetry import trace
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger()
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Headers that should be redacted for security reasons
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "api-key",
    "x-auth-token",
    "secret",
    "password",
}

# Query parameters that should be redacted
SENSITIVE_PARAMS = {"token", "password", "secret", "key", "api_key", "auth"}

# List of fields that should never be logged in any context
SENSITIVE_FIELDS = {
    "password",
    "token",
    "secret",
    "key",
    "auth",
    "credit_card",
    "ssn",
    "pin",
    "oauth",
    "jwt",
    "authorization",
    "credential",
}

limiter = Limiter(key_func=get_remote_address)


def sanitize_headers(headers: Dict) -> Dict:
    """Redact sensitive header values."""
    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_HEADERS):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


def sanitize_params(params: Dict) -> Dict:
    """Redact sensitive query parameter values."""
    sanitized = {}
    for key, value in params.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_PARAMS):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


def sanitize_error_message(error_msg: str) -> str:
    """Sanitize potential sensitive data from error messages.

    Args:
        error_msg: The error message to sanitize

    Returns:
        A sanitized version of the error message with sensitive data redacted
    """
    for field in SENSITIVE_FIELDS:
        if field in error_msg.lower():
            # Replace any content that might contain the actual value
            pattern = rf"{field}[^\s]*\s*[=:]\s*[^\s]+"
            error_msg = re.sub(
                pattern, f"{field}=[REDACTED]", error_msg, flags=re.IGNORECASE
            )
    return error_msg


tracer = trace.get_tracer(__name__)


class AsyncLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Logs incoming requests, outgoing responses, and rate-limiting events."""
        clear_contextvars()
        request_id = str(uuid.uuid4())
        bind_contextvars(
            request_id=request_id,
            ip=request.client.host if request.client else "Unknown",
            method=request.method,
            path=request.url.path,
        )
        request_id_ctx_var.set(request_id)
        start_time = time.monotonic()

        client_ip: Optional[str] = request.client.host if request.client else "Unknown"

        with tracer.start_as_current_span("http_request") as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute(
                "http.client_ip", client_ip if client_ip is not None else ""
            )

            logger.info(
                "Incoming request",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                client_ip=client_ip,
                headers=sanitize_headers(dict(request.headers)),
                query_params=sanitize_params(dict(request.query_params)),
            )

            try:
                response: Response = await call_next(request)
            except Exception as exc:
                error_category = (
                    "OperationalError"
                    if isinstance(exc, (OSError, ConnectionError))
                    else "ProgrammerError"
                )
                logger.error(
                    "Unhandled Exception",
                    request_id=request_id_ctx_var.get(),
                    error=sanitize_error_message(str(exc)),
                    error_type=type(exc).__name__,
                    error_category=error_category,
                    exc_info=True,
                    path=request.url.path,
                    method=request.method,
                )
                return Response(
                    "Internal Server Error",
                    status_code=500,
                    headers={"X-Request-ID": request_id},
                )

            rate_limit_remaining = response.headers.get("X-RateLimit-Remaining", None)
            if rate_limit_remaining == "0":
                logger.warning(
                    "Rate limit exceeded",
                    request_id=request_id,
                    client_ip=client_ip,
                    method=request.method,
                    path=request.url.path,
                )

            process_time = time.monotonic() - start_time
            logger.info(
                "Outgoing response",
                request_id=request_id_ctx_var.get(),
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
                response_headers=sanitize_headers(dict(response.headers)),
                content_length=response.headers.get("content-length"),
                rate_limit_remaining=rate_limit_remaining,
                rate_limit_limit=response.headers.get("X-RateLimit-Limit", "N/A"),
            )
            response.headers["X-Request-ID"] = request_id
            return response
