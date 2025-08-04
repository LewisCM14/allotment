"""
Registration Endpoints
- Provides API endpoints for user registration and email verification operations.
"""

import structlog
from authlib.jose import jwt
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import (
    create_token,
)
from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import (
    translate_token_exceptions,
)
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
    EmailAlreadyRegisteredError,
    EmailVerificationError,
    InvalidTokenError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models import User
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import (
    MessageResponse,
    UserCreate,
)
from app.api.services.email_service import (
    send_password_reset_email,
    send_verification_email,
)
from app.api.services.user.user_unit_of_work import UserUnitOfWork

router = APIRouter()
logger = structlog.get_logger()

INTERNAL_SERVER_ERROR_MSG = "Internal server error"


@router.post(
    "",
    tags=["Registration"],
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and returns an access token",
)
@limiter.limit("5/minute")
async def create_user(
    request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Create a new user account.

    Args:
        user: User registration details
        db: Database session

    Returns:
        TokenResponse: JWT access token

    Raises:
        EmailAlreadyRegisteredError: Email is already registered
        BusinessLogicError: Other business logic errors
    """
    log_context = {
        "email": user.user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "user_registration",
    }
    logger.info("Attempting user registration", **log_context)

    try:
        # Check if email already exists
        with log_timing("check_existing_user", request_id=log_context["request_id"]):
            query = select(User).where(User.user_email == user.user_email)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                raise EmailAlreadyRegisteredError()

        # Create user
        with log_timing("create_user_account", request_id=log_context["request_id"]):
            async with UserUnitOfWork(db) as uow:
                new_user = await uow.create_user(user)
    except BaseApplicationError:
        raise
    except Exception as e:
        error_type = type(e).__name__
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Error during registration",
            error_type=error_type,
            error_details=sanitized_error,
            exc_info=True,
            **log_context,
        )
        raise BusinessLogicError(
            message="An unexpected error occurred during registration.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not new_user or not new_user.user_id:
        raise BusinessLogicError(
            message="Failed to create user",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    log_context["user_id"] = str(new_user.user_id)

    # Send verification email (non-blocking)
    try:
        with log_timing(
            "send_verification_email", request_id=log_context["request_id"]
        ):
            await send_verification_email(
                user_email=user.user_email, user_id=str(new_user.user_id)
            )
    except Exception as email_error:
        # Log but don't fail registration for email issues
        sanitized_error = sanitize_error_message(str(email_error))
        logger.error(
            "Failed to send verification email during registration",
            error=sanitized_error,
            error_type=type(email_error).__name__,
            **log_context,
        )

    # Generate tokens
    with log_timing("generate_tokens", request_id=log_context["request_id"]):
        access_token = create_token(user_id=str(new_user.user_id), token_type="access")
        refresh_token = create_token(
            user_id=str(new_user.user_id), token_type="refresh"
        )

    logger.info("User successfully registered", **log_context)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_first_name=new_user.user_first_name,
        is_email_verified=new_user.is_email_verified,
        user_id=str(new_user.user_id),
    )


@router.post(
    "/email-verifications/{token}",
    tags=["Registration"],
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email using token from path",
    description="Verifies the user's email using the provided token in the URL path. This is a POST request as it changes server state.",
)
async def verify_email_token(
    token: str,
    from_reset: bool = Query(False, alias="fromReset"),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Verify the user's email using the token.

    Args:
        token: The JWT token from the verification link
        from_reset: Whether this verification is part of password reset flow
        db: Database session

    Returns:
        MessageResponse: Success message
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "verify_email",
        "token_provided": bool(token),
    }
    logger.debug("Processing email verification", **log_context)

    @translate_token_exceptions
    async def attempt_decode() -> str:
        try:
            payload = jwt.decode(
                token,
                settings.PUBLIC_KEY,
                claims_options={"exp": {"essential": True}},
            )
            return str(payload.get("sub", ""))
        except Exception as exc:
            logger.error(
                "Failed to decode token",
                error=str(exc),
                token_provided=bool(token),
                **{k: v for k, v in log_context.items() if k != "token_provided"},
            )
            raise InvalidTokenError("Invalid or expired token")

    try:
        user_id = await attempt_decode()
    except InvalidTokenError:
        logger.warning("Invalid JWT token provided", **log_context)
        raise EmailVerificationError("Invalid verification token")
    log_context["user_id"] = user_id
    log_context["is_from_reset"] = from_reset

    async with UserUnitOfWork(db) as uow:
        user = await uow.verify_email(user_id)
    logger.info(
        "Email verification processed",
        is_verified=user.is_email_verified,
        **log_context,
    )

    if from_reset:
        # When verifying email from password reset flow, automatically send password reset email
        with log_timing(
            "send_password_reset_email", request_id=log_context["request_id"]
        ):
            reset_token = create_token(user_id=user_id, token_type="reset")
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            await send_password_reset_email(
                user_email=user.user_email, reset_url=reset_url
            )

        return MessageResponse(
            message="Email verified successfully. You can now reset your password."
        )
    return MessageResponse(message="Email verified successfully")
