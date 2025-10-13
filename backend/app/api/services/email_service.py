"""
Email Service
- Handles sending emails through Resend API
- Provides standard email templates
- Centralizes email configuration
"""

from datetime import datetime
from typing import cast

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

# Configure Resend with API key
resend.api_key = settings.RESEND_API_KEY.get_secret_value()

current_year = datetime.now().year


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

            # Resend SDK handles async operations internally
            response = resend.Emails.send(params)

            logger.info(
                "Verification email sent successfully",
                email_id=response.get("id"),
                **log_context,
            )
            return {"message": "Verification email sent successfully"}

    except resend.exceptions.ResendError as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Resend API error",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is temporarily unavailable",
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


async def send_test_email(recipient_email: EmailStr) -> dict[str, str]:
    """
    Send a test email to verify Resend configuration.

    Args:
        recipient_email: The recipient's email address

    Returns:
        dict: Success message

    Raises:
        HTTPException: If email sending fails
    """
    log_context = {
        "recipient": recipient_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "send_test_email",
    }

    try:
        with log_timing("email_test", request_id=log_context["request_id"]):
            email_body = f"""Hello,

This is a test email from your Allotment Service application.
If you received this email, your Resend email configuration is working correctly!

Configuration details:
- Email Provider: Resend
- From Address: {settings.MAIL_FROM}
- Environment: {settings.ENVIRONMENT}

Best regards,
The Allotment Team

------------------------------
© {current_year} Allotment Service. All rights reserved."""

            params: Emails.SendParams = {
                "from": settings.MAIL_FROM,
                "to": recipient_email,
                "subject": "Test Email - Allotment Service",
                "text": email_body,
            }

            response = resend.Emails.send(params)

            logger.info(
                "Test email sent successfully",
                email_id=response.get("id"),
                **log_context,
            )
            email_id = response.get("id")
            return {
                "message": f"Test email sent successfully to {recipient_email}",
                "email_id": email_id if email_id else "unknown",
            }

    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Failed to send test email",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {sanitized_error}",
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

            response = resend.Emails.send(params)

            logger.info(
                "Password reset email sent successfully",
                email_id=response.get("id"),
                **log_context,
            )
            return {"message": "Password reset email sent successfully"}

    except resend.exceptions.ResendError as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Resend API error",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is temporarily unavailable",
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
