"""
Email Service
- Handles sending emails through SMTP
- Provides standard email templates
- Centralizes email configuration
"""

from datetime import timedelta

import structlog
from fastapi import HTTPException, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.api.core.auth import create_access_token
from app.api.core.config import settings

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
    try:
        # Generate JWT token valid for 1 hour
        token = create_access_token(
            user_id=user_id,
            expires_delta=timedelta(hours=1),
        )

        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        message = MessageSchema(
            subject="Verify Your Email - Allotment Service",
            recipients=[user_email],
            body=f"""
            Hello,
            
            Thank you for registering for a Allotment account!
            
            Please verify your email by clicking the link below:
            
            {verification_link}
            
            This link will expire in 1 hour.
            
            If you did not register for an account, please ignore this email.
            
            Best regards,
            The Allotment Team
            """,
            subtype=MessageType.plain,
        )

        await mail_client.send_message(message)
        logger.info(
            "Verification email sent successfully", email=user_email, user_id=user_id
        )
        return {"message": "Verification email sent successfully"}
    except Exception:
        logger.exception(
            "Failed to send verification email",
            error="REDACTED",
            email=user_email,
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )
