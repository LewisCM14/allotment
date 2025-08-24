"""
Logging Middleware
"""

import json
import re
import time
import uuid
from contextvars import ContextVar
from typing import Any, Awaitable, Callable, Dict, Optional

import structlog
from fastapi import Request, Response
from opentelemetry import trace
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger()
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Standard redaction text used across sanitizers
REDACTED = "[REDACTED]"

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
            sanitized[key] = REDACTED
        else:
            sanitized[key] = value
    return sanitized


def sanitize_params(params: Dict) -> Dict:
    """Redact sensitive query parameter values."""
    sanitized = {}
    for key, value in params.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_PARAMS):
            sanitized[key] = REDACTED
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
    # Try to parse free-form JSON and scrub known sensitive keys.
    try:
        parsed = json.loads(error_msg)
        if isinstance(parsed, (dict, list)):
            try:
                return json.dumps(_scrub_obj(parsed))
            except Exception:
                # Fall back to textual redaction if JSON re-dump fails
                pass
    except Exception:
        # Not JSON or failed to parse — fall back to regex scrubbing below
        pass

    # Textual regex-based redaction for known sensitive fields
    lower_msg = error_msg.lower()
    for field in SENSITIVE_FIELDS:
        if field in lower_msg:
            pattern = rf"{field}[^\s]*\s*[=:]\s*[^\s]+"
            error_msg = re.sub(
                pattern, f"{field}={REDACTED}", error_msg, flags=re.IGNORECASE
            )
    return error_msg


def _scrub_obj(obj: Any) -> Any:
    """Recursively scrub sensitive keys from parsed JSON-like objects.

    Extracted to module scope to simplify `sanitize_error_message` and lower its
    cognitive complexity.
    """
    if isinstance(obj, dict):
        return {
            k: (REDACTED if k.lower() in SENSITIVE_FIELDS else _scrub_obj(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_scrub_obj(v) for v in obj]
    return obj


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

            # Add trace/span ids into the context for log correlation
            span_ctx = span.get_span_context()
            trace_id = None
            span_id = None
            try:
                trace_id = (
                    format(span_ctx.trace_id, "032x")
                    if getattr(span_ctx, "trace_id", None)
                    else None
                )
                span_id = (
                    format(span_ctx.span_id, "016x")
                    if getattr(span_ctx, "span_id", None)
                    else None
                )
            except Exception:
                trace_id = None
                span_id = None

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
                # Log the exception with sanitized message and exc_info, then re-raise
                logger.error(
                    "Unhandled Exception",
                    request_id=request_id_ctx_var.get(),
                    error=sanitize_error_message(str(exc)),
                    error_type=type(exc).__name__,
                    error_category=error_category,
                    exc_info=True,
                    path=request.url.path,
                    method=request.method,
                    trace_id=trace_id,
                    span_id=span_id,
                )
                raise

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
