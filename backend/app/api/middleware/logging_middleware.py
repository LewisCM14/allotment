"""
Logging Middleware
"""

import time
import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger()
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class AsyncLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Logs incoming requests and outgoing responses."""
        clear_contextvars()
        bind_contextvars(
            request_id=str(uuid.uuid4()),
            ip=request.client.host if request.client else "Unknown",
            method=request.method,
            path=request.url.path,
        )
        request_id = str(uuid.uuid4())
        request_id_ctx_var.set(request_id)
        start_time = time.monotonic()

        # Ensure client IP is not None
        client_ip: Optional[str] = request.client.host if request.client else "Unknown"

        logger.info(
            "Incoming request",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            headers=dict(request.headers),
            query_params=dict(request.query_params),
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled Exception",
                request_id=request_id_ctx_var.get(),
                error=str(exc),
                error_type=type(exc).__name__,
                exc_info=True,
                path=request.url.path,
                method=request.method,
            )
            return Response(
                "Internal Server Error",
                status_code=500,
                headers={"X-Request-ID": request_id},
            )

        process_time = time.monotonic() - start_time
        logger.info(
            "Outgoing response",
            request_id=request_id_ctx_var.get(),
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
            response_headers=dict(response.headers),
            content_length=response.headers.get("content-length"),
            rate_limit_remaining=response.headers.get("X-RateLimit-Remaining"),
            rate_limit_limit=response.headers.get("X-RateLimit-Limit"),
        )

        return response
