"""
Logging Middleware
"""

import time
from typing import Awaitable, Callable, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class AsyncLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Logs incoming requests and outgoing responses."""
        start_time = time.monotonic()

        # Ensure client IP is not None
        client_ip: Optional[str] = request.client.host if request.client else "Unknown"

        logger.info(
            "Incoming request",
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.error("Unhandled Exception", error=str(exc), exc_info=True)
            return Response("Internal Server Error", status_code=500)

        process_time = time.monotonic() - start_time
        logger.info(
            "Outgoing response",
            status_code=response.status_code,
            process_time=f"{process_time:.3f}s",
        )

        return response
