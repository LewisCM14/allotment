"""
Email Service
- Outbound transactional & inbound forwarding utilities.
- Resilient send with retry/backoff for transient Resend API failures.
- Centralized subject normalization for forwarded emails.
"""

import asyncio
import re
import time
from collections import deque
from datetime import datetime, timezone
from textwrap import dedent
from typing import Any, Deque, Dict, cast

import httpx
import resend
import structlog
from fastapi import HTTPException, status
from pydantic import EmailStr
from resend.emails._emails import Emails

from app.api.core.auth_utils import create_token
from app.api.core.config import settings
from app.api.core.logging import log_timing
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)

logger = structlog.get_logger()
current_year = datetime.now().year

# Resend config
resend.api_key = settings.RESEND_API_KEY.get_secret_value()
RESEND_API_BASE_URL = "https://api.resend.com"

EMAIL_SERVICE_UNAVAILABLE_MSG = "Email service is temporarily unavailable"

_EMAIL_SEND_TIMESTAMPS: Deque[float] = deque()
_EMAIL_SEND_LOCK = asyncio.Lock()

JSON_MIME = "application/json"


def _compute_delay(attempt: int, base_delay: float) -> float:
    """Compute exponential backoff delay.

    attempt: 1-based attempt counter
    base_delay: initial delay in seconds
    Returns float seconds to sleep
    """
    factor: float = 2.0 ** (attempt - 1)
    delay: float = base_delay * factor
    return delay


def _is_retryable(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


async def _rate_limit_window(max_per_sec: int = 2) -> None:
    async with _EMAIL_SEND_LOCK:
        now = time.monotonic()
        while _EMAIL_SEND_TIMESTAMPS and now - _EMAIL_SEND_TIMESTAMPS[0] > 1.0:
            _EMAIL_SEND_TIMESTAMPS.popleft()
        if len(_EMAIL_SEND_TIMESTAMPS) >= max_per_sec:
            sleep_for = 1.0 - (now - _EMAIL_SEND_TIMESTAMPS[0])
            if sleep_for > 0:
                logger.debug(
                    "Rate limiter sleeping before send",
                    sleep_for=round(sleep_for, 3),
                    operation="send_email_retry",
                )
                await asyncio.sleep(sleep_for)
            now = time.monotonic()
            while _EMAIL_SEND_TIMESTAMPS and now - _EMAIL_SEND_TIMESTAMPS[0] > 1.0:
                _EMAIL_SEND_TIMESTAMPS.popleft()
        _EMAIL_SEND_TIMESTAMPS.append(time.monotonic())


def _parse_success_response(response: httpx.Response) -> Dict[str, Any]:
    try:
        raw_json = response.json()
    except ValueError:
        return {"raw": response.text}
    if isinstance(raw_json, dict):
        return cast(Dict[str, Any], raw_json)
    return {"raw": raw_json}


async def _send_email_with_retry(
    params: Emails.SendParams,
    max_attempts: int = 5,
    base_delay: float = 0.5,
) -> Dict[str, Any]:
    """Send email via Resend with exponential backoff and simple rate limiting."""
    await _rate_limit_window()

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY.get_secret_value()}",
        "Content-Type": JSON_MIME,
        "Accept": JSON_MIME,
    }
    url = f"{RESEND_API_BASE_URL}/emails"

    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=params, headers=headers)
        except httpx.HTTPError as exc:
            if attempt == max_attempts:
                raise RuntimeError(f"Network error sending email: {exc}") from exc
            delay = _compute_delay(attempt, base_delay)
            logger.warning(
                "Transient network error when sending email; backing off",
                error=sanitize_error_message(str(exc)),
                attempt=attempt,
                next_delay=delay,
                operation="send_email_retry",
            )
            await asyncio.sleep(delay)
            continue

        status_code = response.status_code
        if status_code < 400:
            payload = _parse_success_response(response)
            logger.debug(
                "Email send succeeded",
                status_code=status_code,
                attempt=attempt,
                operation="send_email_retry",
            )
            return payload

        body_preview = response.text[:300]
        if not _is_retryable(status_code) or attempt == max_attempts:
            logger.error(
                "Email send failed",
                status_code=status_code,
                attempt=attempt,
                body_preview=body_preview,
                operation="send_email_retry",
            )
            raise RuntimeError(
                f"Failed to send email after {attempt} attempts (status {status_code})"
            )

        delay = _compute_delay(attempt, base_delay)
        logger.warning(
            "Retryable email send failure",
            status_code=status_code,
            attempt=attempt,
            next_delay=delay,
            body_preview=body_preview,
            operation="send_email_retry",
        )
        await asyncio.sleep(delay)

    raise RuntimeError("Failed to send email (exhausted attempts)")


async def send_verification_email(
    user_email: EmailStr, user_id: str, from_reset: bool = False
) -> dict[str, str]:
    """
    Send an email verification link to the user.

    Args:
        user_email: The user's email address
        user_id: The user's ID
        from_reset: Whether this verification is part of password reset flow

    Returns:
        dict: Success message

    Raises:
        HTTPException: If email sending fails
    """
    log_context = {
        "user_id": user_id,
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "send_verification_email",
        "is_from_reset": from_reset,
    }

    try:
        with log_timing("email_verification", request_id=log_context["request_id"]):
            token = create_token(
                user_id=user_id,
                expiry_seconds=3600,  # 1 hour
                token_type="email_verification",
            )

            verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}&fromReset={str(from_reset).lower()}"

            logger.debug(
                "Generated verification link",
                frontend_url=settings.FRONTEND_URL,
                token_expiry="1 hour",
                **log_context,
            )

            email_body = f"""Dear Allotment Member,

Thank you for creating an account. We're excited to have you join our community of gardening enthusiasts.

To complete your registration and access all features, please verify your email address by clicking the link below:

{verification_link}

This verification link will expire in 1 hour for security purposes. If you don't complete the verification within this timeframe, you'll need to request a new verification email.

If you did not create an account with Allotment, please disregard this email or contact our support team.

Best regards,
The Allotment Team

------------------------------
This is an automated message. Please do not reply directly to this email.
© {current_year} Allotment Service. All rights reserved."""

            params: Emails.SendParams = {
                "from": settings.MAIL_FROM,
                "to": user_email,
                "subject": "Email Verification Required - Allotment Service",
                "text": email_body,
            }

            response = await _send_email_with_retry(params)

            logger.info(
                "Verification email sent successfully",
                email_id=response.get("id"),
                **log_context,
            )
            return {"message": "Verification email sent successfully"}

    except (httpx.HTTPError, RuntimeError) as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Resend API error",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=EMAIL_SERVICE_UNAVAILABLE_MSG,
        )
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Unhandled exception during email sending",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )


async def send_password_reset_email(
    user_email: EmailStr, reset_url: str
) -> dict[str, str]:
    """
    Send a password reset link to the user.

    Args:
        user_email: The user's email address
        reset_url: The password reset URL with token

    Returns:
        dict: Success message

    Raises:
        HTTPException: If email sending fails
    """
    log_context = {
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "send_password_reset_email",
    }

    try:
        with log_timing("email_password_reset", request_id=log_context["request_id"]):
            email_body = f"""Dear Allotment Member,

You recently requested to reset your password. Click the link below to set a new password:

{reset_url}

This password reset link will expire in 1 hour for security purposes. 
If you did not request a password reset, please ignore this email or contact support if you have concerns.

Best regards,
The Allotment Team

------------------------------
This is an automated message. Please do not reply directly to this email.
© {current_year} Allotment Service. All rights reserved."""

            params: Emails.SendParams = {
                "from": settings.MAIL_FROM,
                "to": user_email,
                "subject": "Password Reset - Allotment Service",
                "text": email_body,
            }

            response = await _send_email_with_retry(params)

            logger.info(
                "Password reset email sent successfully",
                email_id=response.get("id"),
                **log_context,
            )
            return {"message": "Password reset email sent successfully"}

    except (httpx.HTTPError, RuntimeError) as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Resend API error",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=EMAIL_SERVICE_UNAVAILABLE_MSG,
        )
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Unhandled exception during email sending",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email",
        )


async def _fetch_inbound_email_content(email_id: str) -> tuple[str | None, str | None]:
    """Retrieve inbound email content from Resend when webhook payload lacks body."""

    if not email_id:
        return None, None

    url = f"{RESEND_API_BASE_URL}/emails/{email_id}"
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY.get_secret_value()}",
        "Accept": "application/json",
    }

    logger.info(
        "Attempting to fetch inbound email content",
        email_id=email_id,
        url=url,
        operation="fetch_inbound_email_content",
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Failed to fetch inbound email content",
            email_id=email_id,
            status_code=exc.response.status_code,
            reason=exc.response.text,
            operation="fetch_inbound_email_content",
        )
        return None, None
    except httpx.HTTPError as exc:
        logger.warning(
            "HTTP error while fetching inbound email content",
            email_id=email_id,
            error=sanitize_error_message(str(exc)),
            operation="fetch_inbound_email_content",
        )
        return None, None

    payload = response.json()

    logger.info(
        "Fetched inbound email content from API",
        email_id=email_id,
        payload=payload,
        operation="fetch_inbound_email_content",
    )

    # Resend API returns text/html directly at top level or nested
    text_body = payload.get("text")
    html_body = payload.get("html")

    # Check if nested under "data"
    if not text_body and not html_body and "data" in payload:
        data = payload["data"]
        if isinstance(data, dict):
            text_body = data.get("text")
            html_body = data.get("html")

    # Some providers nest bodies under "text" -> {"body": "..."}
    if isinstance(text_body, dict):
        text_body = text_body.get("body")
    if isinstance(html_body, dict):
        html_body = html_body.get("body")

    if not text_body and not html_body:
        # Fallback: check for 'body' or 'raw' fields
        text_body = payload.get("body") or payload.get("raw")

    logger.debug(
        "Parsed email body content",
        email_id=email_id,
        has_text=bool(text_body),
        has_html=bool(html_body),
        text_preview=text_body[:100] if text_body else None,
        operation="fetch_inbound_email_content",
    )

    return text_body, html_body


async def forward_inbound_email(
    from_email: str,
    subject: str,
    body: str,
    reply_to: str | None = None,
    email_id: str | None = None,
) -> dict[str, str]:
    """
    Forward an inbound email received via Resend webhook to CONTACT_TO.

    Args:
        from_email: Original sender's email address.
        subject: Email subject line.
        body: Email body (text or HTML).
        reply_to: Optional reply-to address.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If forwarding fails.
    """
    log_context = {
        "from_email": from_email,
        "subject": subject,
        "operation": "forward_inbound_email",
        "request_id": request_id_ctx_var.get(),
        "email_id": email_id,
    }

    try:
        with log_timing("email_forward_inbound", request_id=log_context["request_id"]):
            base_subject = subject or "(No subject)"
            cleaned_subject = re.sub(r"^(?:\[Fwd\]\s*)+", "", base_subject).strip()
            final_subject = (
                f"[Fwd] {cleaned_subject}" if cleaned_subject else "[Fwd] (No subject)"
            )

            resolved_body = (
                body.strip()
                if body and body.strip()
                else "(Email body not included in webhook - please check original message)"
            )

            forwarded_body = dedent(
                f"""
                Forwarded message from: {from_email}
                Subject: {cleaned_subject or "(No subject)"}
                Received: {datetime.now(timezone.utc).isoformat()}

                --- Original Message ---

                {resolved_body}
                """
            ).strip()

            params: Emails.SendParams = {
                "from": settings.CONTACT_FROM,
                "to": settings.CONTACT_TO,
                "reply_to": reply_to or from_email,
                "subject": final_subject,
                "text": forwarded_body,
            }

            response = await _send_email_with_retry(params)
            logger.info(
                "Inbound email forwarded successfully",
                forwarded_email_id=response.get("id"),
                **log_context,
            )
            return {"message": "Inbound email forwarded successfully"}

    except (httpx.HTTPError, RuntimeError) as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Resend API error (forward inbound)",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=EMAIL_SERVICE_UNAVAILABLE_MSG,
        )
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Unhandled exception during inbound email forwarding",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to forward inbound email",
        )
