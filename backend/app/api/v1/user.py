"""
User Profile Endpoints
- Provides API endpoints for user profile management and email verification status.
"""

import structlog
from fastapi import APIRouter, Depends, Query, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database import get_db
from app.api.core.logging import log_timing
from app.api.middleware.exception_handler import (
    validate_user_exists,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
)
from app.api.models import User
from app.api.schemas.user.user_schema import (
    EmailRequest,
    MessageResponse,
    VerificationStatusResponse,
)
from app.api.services.email_service import (
    send_verification_email,
)

router = APIRouter()
logger = structlog.get_logger()

INTERNAL_SERVER_ERROR_MSG = "Internal server error"


@router.post(
    "/email-verifications",
    tags=["User"],
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send email verification link",
    description="Sends an email verification link to the user's email address provided in the request body",
)
async def request_verification_email(
    request_data: EmailRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    """
    Send an email verification link to the user.

    Args:
        request_data: Contains the user's email address
        db: Database session

    Returns:
        MessageResponse: Success message

    Raises:
        UserNotFoundError: If the user is not found
    """
    user_email = request_data.user_email
    log_context = {
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "request_verification_email",
    }
    logger.debug("Verification email requested", **log_context)
    user = await validate_user_exists(
        db_session=db, user_model=User, user_email=user_email
    )
    log_context["user_id"] = str(user.user_id)
    try:
        logger.debug("About to call send_verification_email", **log_context)
        with log_timing("send_email", request_id=log_context["request_id"]):
            await send_verification_email(
                user_email=user_email, user_id=str(user.user_id)
            )
        logger.debug("send_verification_email call completed", **log_context)
        logger.info("Verification email sent successfully", **log_context)
        return MessageResponse(message="Verification email sent successfully")
    except Exception as e:
        logger.error(
            "Failed to send verification email during operation",
            error=str(e),
            error_code="EMAIL_VERIFICATION_ERROR",
            **log_context,
        )
        return MessageResponse(message=INTERNAL_SERVER_ERROR_MSG)


@router.get(
    "/verification-status",
    tags=["User"],
    response_model=VerificationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Check email verification status",
    description="Returns the current email verification status for a user",
)
async def check_verification_status(
    user_email: EmailStr = Query(...),
    db: AsyncSession = Depends(get_db),
) -> VerificationStatusResponse:
    """
    Check if a user's email is verified.

    Args:
        user_email: The user's email address
        db: Database session

    Returns:
        VerificationStatusResponse: Contains verification status
    """
    log_context = {
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "check_verification_status",
    }
    logger.debug("Checking email verification status", **log_context)
    user = await validate_user_exists(
        db_session=db, user_model=User, user_email=user_email
    )
    log_context["user_id"] = str(user.user_id)
    log_context["verification_status"] = str(user.is_email_verified)
    logger.info("Verification status checked", **log_context)
    return VerificationStatusResponse(
        is_email_verified=user.is_email_verified,
        user_id=str(user.user_id),
    )
