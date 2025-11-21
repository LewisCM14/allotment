"""
Application Entrypoint
"""

import atexit
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from svix.webhooks import Webhook, WebhookVerificationError

from app.api.core.config import settings
from app.api.core.limiter import limiter
from app.api.core.logging import configure_logging
from app.api.middleware.exception_handler import register_exception_handlers
from app.api.middleware.logging_middleware import (
    AsyncLoggingMiddleware,
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.schemas.client_error_schema import ClientErrorLog
from app.api.schemas.inbound_email_schema import InboundEmailPayload
from app.api.services.email_service import (
    forward_inbound_email,
)
from app.api.v1 import router as api_router

configure_logging()

logger = structlog.get_logger()

logger.info(
    "Starting application",
    app_name=settings.APP_NAME,
    version=settings.APP_VERSION,
    environment=settings.ENVIRONMENT,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        logger.info(
            "Application startup complete",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            api_prefix=settings.API_PREFIX,
        )
        yield
    except Exception as exc:
        sanitized_error = sanitize_error_message(str(exc))
        logger.error(
            "Error during application lifespan",
            error=sanitized_error,
            error_type=type(exc).__name__,
            request_id=request_id_ctx_var.get(),
        )
        raise
    finally:
        logger.info(
            "Application shutting down",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
        )
        flush_logs()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for managing allotments",
    lifespan=lifespan,
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
)


logger.debug("Registering exception handlers")
register_exception_handlers(app)


# Logging Middleware
logger.debug("Adding logging middleware")
app.add_middleware(AsyncLoggingMiddleware)


# CORS Middleware
logger.debug("Adding CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Rate Limiter
app.state.limiter = limiter


# Register Routes
logger.debug("Registering API routes")
app.include_router(api_router, prefix="/api/v1")


@app.get(
    "/", tags=["Utility"], summary="API Root", description="Root endpoint for the API"
)
async def root() -> Dict[str, str]:
    """
    Application Root Endpoint

    Returns:
        dict: Metadata about the API, including name, version, and environment.
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "root",
    }

    logger.info(
        "Root endpoint accessed",
        endpoint="/",
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        **log_context,
    )
    return {
        "message": "Welcome to the Allotment Service API!",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.post("/api/v1/log-client-error", tags=["Utility"])
async def handle_log_client_error(
    error_log: ClientErrorLog, request: Request
) -> Dict[str, str]:
    logger.error(
        "Client-side error reported",
        operation="log_client_error",
        client_error_message=error_log.error,
        client_error_details=error_log.details,
    )
    return {"message": "Client error logged successfully"}


async def verify_resend_signature(request: Request) -> InboundEmailPayload:
    """Verify Resend (Svix-backed) webhook signature.

    Always requires `RESEND_WEBHOOK_SECRET` to be configured. Raises 500 if missing,
    401 if signature absent/invalid, 400 if payload invalid.
    """
    raw_body = await request.body()

    if not settings.RESEND_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured; cannot verify inbound email",
        )
    secret_value = settings.RESEND_WEBHOOK_SECRET.get_secret_value()

    svix_headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }

    if not svix_headers["svix-signature"]:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    try:
        wh = Webhook(secret_value)
        wh.verify(raw_body, svix_headers)
        logger.debug(
            "Svix webhook signature verified",
            operation="inbound_email_webhook",
            svix_id=svix_headers.get("svix-id"),
        )
    except WebhookVerificationError:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = InboundEmailPayload.model_validate_json(raw_body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc
    return payload


@app.post(
    "/webhooks/inbound-email",
    tags=["Webhooks"],
    status_code=status.HTTP_200_OK,
    summary="Resend inbound email webhook",
    description="Receives inbound emails from Resend and forwards them to CONTACT_TO",
)
async def handle_inbound_email(
    payload: InboundEmailPayload = Depends(verify_resend_signature),
) -> Dict[str, str]:
    """
    Webhook endpoint for Resend inbound emails.

    Receives emails sent to contact@mail.allotment.wiki and forwards them
    to the configured CONTACT_TO inbox.
    """
    data = payload.data
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "inbound_email_webhook",
        "event_type": payload.type,
        "from": data.from_,
        "to": ",".join([str(addr) for addr in data.to])
        if isinstance(data.to, list)
        else str(data.to),
        "subject": data.subject,
    }

    if payload.type != "email.received":
        logger.info(
            "Ignoring non-inbound email event",
            **log_context,
        )
        return {"message": "Event ignored"}

    logger.info("Inbound email received", **log_context)

    try:
        body = data.text or data.html or ""
        logger.debug(
            "Webhook body content",
            has_text=bool(data.text),
            has_html=bool(data.html),
            text_length=len(data.text) if data.text else 0,
            html_length=len(data.html) if data.html else 0,
            **log_context,
        )
        subject = data.subject or "(No subject)"
        await forward_inbound_email(
            from_email=str(data.from_),
            subject=subject,
            body=body,
            reply_to=data.reply_to,
            email_id=data.email_id,
        )
        logger.info("Inbound email processed successfully", **log_context)
        return {"message": "Email forwarded"}
    except Exception as exc:
        logger.error(
            "Failed to process inbound email",
            error=sanitize_error_message(str(exc)),
            error_type=type(exc).__name__,
            **log_context,
        )
        raise


def flush_logs() -> None:
    """Flush pending logs during shutdown."""
    try:
        logger = logging.getLogger()

        can_log = all(
            not (
                hasattr(handler, "stream") and handler.stream and handler.stream.closed
            )
            for handler in logger.handlers
            if hasattr(handler, "stream")
        )

        if can_log:
            logger.info("Flushing logs before shutdown")
            structlog.get_logger().info("Application shutting down")

        for handler in logger.handlers:
            try:
                if hasattr(handler, "flush"):
                    handler.flush()
                if hasattr(handler, "close") and not (
                    hasattr(handler, "stream")
                    and handler.stream
                    and handler.stream.closed
                ):
                    handler.close()
            except (ValueError, IOError):
                pass
    except Exception:
        pass


atexit.register(flush_logs)
