"""
Logging Middleware
"""

import time

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = structlog.get_logger()


class AsyncLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.monotonic()

        logger.info(
            "Incoming request",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host,
        )

        try:
            response = await call_next(request)
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
