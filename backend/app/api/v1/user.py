"""
User Endpoints
- Provides API endpoints for user-related operations.
"""

import uuid
from typing import Any, Dict

import structlog
from authlib.jose import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth import (
    create_token,
    verify_password,
)
from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.factories.user_factory import UserFactoryValidationError
from app.api.middleware.error_handler import (
    safe_operation,
    translate_token_exceptions,
    validate_user_exists,
)
from app.api.middleware.exception_handler import (
    AuthenticationError,
    BaseApplicationError,
    BusinessLogicError,
    EmailAlreadyRegisteredError,
    EmailVerificationError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models import User
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import (
    EmailRequest,
    MessageResponse,
    PasswordResetRequest,
    PasswordUpdate,
    RefreshRequest,
    UserCreate,
    UserLogin,
    VerificationStatusResponse,
)
from app.api.services.email_service import (
    send_verification_email,
)
from app.api.services.user.user_unit_of_work import UserUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "",
    tags=["User"],
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
        with log_timing("check_existing_user", request_id=log_context["request_id"]):
            query = select(User).where(User.user_email == user.user_email)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                logger.warning(
                    "Registration failed - email already exists", **log_context
                )
                raise EmailAlreadyRegisteredError()
        new_user = None
        async with safe_operation(
            "user_creation", log_context, status.HTTP_500_INTERNAL_SERVER_ERROR
        ):
            with log_timing(
                "create_user_account", request_id=log_context["request_id"]
            ):
                async with UserUnitOfWork(db) as uow:
                    new_user = await uow.create_user(user)
            if not new_user or not new_user.user_id:
                logger.error("User creation failed", **log_context)
                raise BusinessLogicError(
                    message="Failed to create user",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            log_context["user_id"] = str(new_user.user_id)
        try:
            with log_timing(
                "send_verification_email", request_id=log_context["request_id"]
            ):
                await send_verification_email(
                    user_email=user.user_email, user_id=str(new_user.user_id)
                )
                logger.info(
                    "Verification email sent during registration", **log_context
                )
        except Exception as email_error:
            sanitized_error = sanitize_error_message(str(email_error))
            logger.error(
                "Failed to send verification email during registration",
                error=sanitized_error,
                error_type=type(email_error).__name__,
                **log_context,
            )
        with log_timing("generate_tokens", request_id=log_context["request_id"]):
            access_token = create_token(
                user_id=str(new_user.user_id), token_type="access"
            )
            refresh_token = create_token(
                user_id=str(new_user.user_id), token_type="refresh"
            )
            logger.debug("Tokens generated successfully", **log_context)
        logger.info("User successfully registered", **log_context)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user_first_name=new_user.user_first_name,
            is_email_verified=new_user.is_email_verified,
            user_id=str(new_user.user_id),
        )
    except BaseApplicationError as exc:
        logger.warning(
            f"User registration failed: {type(exc).__name__}",
            error=str(exc),
            error_code=exc.error_code,
            status_code=exc.status_code,
            **log_context,
        )
        raise
    except Exception as exc:
        sanitized_error = sanitize_error_message(str(exc))
        logger.error(
            "Unhandled exception during user registration",
            error=sanitized_error,
            error_type=type(exc).__name__,
            **log_context,
        )
        raise BusinessLogicError(
            message="An unexpected error occurred during registration",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


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
        async with safe_operation(
            "sending verification email",
            log_context,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ):
            with log_timing("send_email", request_id=log_context["request_id"]):
                await send_verification_email(
                    user_email=user_email, user_id=str(user.user_id)
                )
                logger.info("Verification email sent successfully", **log_context)
                return MessageResponse(message="Verification email sent successfully")
    except Exception as e:
        logger.error(
            "Failed to send verification email during operation",
            error=str(e),
            error_code="EMAIL_VERIFICATION_ERROR",
            **log_context,
        )
        raise


@router.post(
    "/email-verifications/{token}",
    tags=["User"],
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
        return MessageResponse(
            message="Email verified successfully. You can now reset your password."
        )
    return MessageResponse(message="Email verified successfully")


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
    db: AsyncSession = Depends(get_db),  # Changed to Query parameter
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


@router.post(
    "/password-resets",
    tags=["User"],
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Sends a password reset link to the user's email",
)
@limiter.limit("5/minute")
async def request_password_reset(
    request: Request,
    user_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Request a password reset link.

    Args:
        request: The incoming request
        user_data: Request containing user's email
        db: Database session

    Returns:
        MessageResponse: Success message

    Raises:
        UserNotFoundError: If the email is not found
    """
    user_email = user_data.user_email
    log_context = {
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "request_password_reset",
    }
    logger.debug("Password reset requested", **log_context)

    try:
        query = select(User).where(User.user_email == user_email)
        db_result = await db.execute(query)
        user = db_result.scalar_one_or_none()

        if not user:
            logger.warning("User not found for password reset", **log_context)
            return MessageResponse(
                message="If your email exists in our system and is verified, you will receive a password reset link shortly."
            )

        if not user.is_email_verified:
            logger.info(
                "User email not verified, sending verification email", **log_context
            )
            await send_verification_email(
                user_email=user.user_email, user_id=str(user.user_id), from_reset=True
            )
            return MessageResponse(
                message="Your email is not verified. A verification email has been sent to your address."
            )

        async with UserUnitOfWork(db) as uow:
            reset_result = await uow.request_password_reset(user_email)
            logger.info(
                "Password reset operation completed",
                status=reset_result["status"],
                **log_context,
            )
            return MessageResponse(message=reset_result["message"])
    except BaseApplicationError as exc:
        logger.warning(
            f"{type(exc).__name__}",
            error=str(exc),
            error_code=exc.error_code,
            status_code=exc.status_code,
            **log_context,
        )
        raise
    except Exception as exc:
        sanitized_error = sanitize_error_message(str(exc))
        logger.error(
            "Unhandled exception during password reset request",
            error=sanitized_error,
            error_type=type(exc).__name__,
            **log_context,
        )
        raise BusinessLogicError(
            message="An unexpected error occurred during password reset request",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/password-resets/{token}",
    tags=["User"],
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token from path",
    description="Resets a user's password using a valid reset token from the URL path and new password from the request body.",
)
@limiter.limit("5/minute")
async def reset_password(
    token: str,
    password_data: PasswordUpdate,
    request: Request,  # Keep request for logging if needed, or remove if not used
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Reset user's password using a reset token.

    Args:
        token: The reset token from the URL path
        password_data: Contains the new password
        request: The incoming request
        db: Database session

    Returns:
        MessageResponse: Success message

    Raises:
        InvalidTokenError: If the token is invalid or expired
        ValidationError: If the new password doesn't meet requirements
        BusinessLogicError: Other unexpected errors
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "reset_password",
    }
    logger.debug("Password reset attempt with token", **log_context)

    try:
        token_parts = token.split(".")
        if len(token_parts) != 3:
            logger.warning("Malformed JWT token format", **log_context)
            raise InvalidTokenError("Malformed JWT token")

        async with UserUnitOfWork(db) as uow:
            await uow.reset_password(token, password_data.new_password)

        logger.info("Password reset successful", **log_context)
        return MessageResponse(message="Password has been reset successfully")
    except UserFactoryValidationError as e:
        logger.warning(
            "Password validation failed during reset",
            error=str(e),
            field=e.field,
            **log_context,
        )
        raise e
    except InvalidTokenError as e:
        logger.warning("Invalid reset token", error=str(e), **log_context)
        raise HTTPException(status_code=e.status_code, detail=e.error_code)
    except BaseApplicationError as exc:
        logger.warning(
            f"{type(exc).__name__}",
            error=str(exc),
            error_code=exc.error_code,
            status_code=exc.status_code,
            **log_context,
        )
        raise
    except Exception as exc:
        sanitized_error = sanitize_error_message(str(exc))
        logger.error(
            "Unhandled exception during password reset",
            error=sanitized_error,
            error_type=type(exc).__name__,
            **log_context,
        )
        raise BusinessLogicError(
            message="An unexpected error occurred during password reset",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
