"""
Email Service
- Handles sending emails through SMTP
- Provides standard email templates
- Centralizes email configuration
"""

from datetime import datetime, timedelta

import structlog
from fastapi import HTTPException, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.api.core.auth import create_access_token
from app.api.core.config import settings
from app.api.core.logging import log_timing
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)

logger = structlog.get_logger()

email_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_USERNAME,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

mail_client = FastMail(email_conf)

current_year = datetime.now().year


async def send_verification_email(user_email: EmailStr, user_id: str) -> dict[str, str]:
    """
    Send an email verification link to the user.

    Args:
        user_email: The user's email address
        user_id: The user's ID

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
    }

    try:
        with log_timing("email_verification", request_id=log_context["request_id"]):
            # Generate JWT token valid for 1 hour
            token = create_access_token(
                user_id=user_id,
                expires_delta=timedelta(hours=1),
            )

            verification_link = f"{settings.FRONTEND_URL}/verify-email?token=[REDACTED]"

            # Log without including the actual token
            logger.debug(
                "Generated verification link",
                frontend_url=settings.FRONTEND_URL,
                token_expiry="1 hour",
                **log_context,
            )

            message = MessageSchema(
                subject="Email Verification Required - Allotment Service",
                recipients=[user_email],
                body=f"""Dear Allotment Member,

                Thank you for creating an account. We're excited to have you join our community of gardening enthusiasts.

                To complete your registration and access all features, please verify your email address by clicking the link below:

                {verification_link.replace("[REDACTED]", token)}

                This verification link will expire in 1 hour for security purposes. If you don't complete the verification within this timeframe, you'll need to request a new verification email.

                If you did not create an account with Allotment, please disregard this email or contact our support team.

                Best regards,
                The Allotment Team

                ------------------------------
                This is an automated message. Please do not reply directly to this email.
                """,
                subtype=MessageType.plain,
            )

            await mail_client.send_message(message)
            logger.info("Verification email sent successfully", **log_context)
            return {"message": "Verification email sent successfully"}

    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Failed to send verification email",
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
    Send a test email to verify SMTP configuration.

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
            message = MessageSchema(
                subject="Test Email - Allotment Service",
                recipients=[recipient_email],
                body=f"""
                Hello,

                This is a test email from your Allotment Service application.
                If you received this email, your email configuration is working correctly!

                Configuration details:
                - SMTP Server: smtp.gmail.com
                - Port: 587
                - Username: {settings.MAIL_USERNAME}
                - TLS: Enabled

                Best regards,
                The Allotment Team
                """,
                subtype=MessageType.plain,
            )

            await mail_client.send_message(message)
            logger.info("Test email sent successfully", **log_context)
            return {"message": f"Test email sent successfully to {recipient_email}"}

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
