"""
User Endpoints
- Provides API endpoints for user-related operations.
"""

import uuid
from typing import Any, Dict

import structlog
from authlib.jose import jwt
from fastapi import APIRouter, Depends, Request, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth import create_access_token, create_refresh_token, verify_password
from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
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
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models import User
from app.api.schemas import TokenResponse, UserLogin
from app.api.schemas.user.user_schema import RefreshRequest, UserCreate
from app.api.services.email_service import send_verification_email
from app.api.services.user.user_unit_of_work import UserUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/",
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
            refresh_token = create_refresh_token(user_id=str(new_user.user_id))
            access_token = create_access_token(user_id=str(new_user.user_id))
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
    "/auth/login",
    tags=["User"],
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and return access token",
)
@limiter.limit("5/minute")
async def login(
    request: Request, user: UserLogin, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and generate access token.

    Args:
        user: Login credentials
        db: Database session

    Returns:
        TokenResponse: JWT access token with user_first_name

    Raises:
        AuthenticationError: Invalid credentials
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "user_login",
        "email": user.user_email,
    }

    logger.info("Login attempt", **log_context)

    try:
        db_user = await validate_user_exists(
            db_session=db,
            user_model=User,
            user_email=user.user_email,
            log_context=log_context,
        )

        log_context["user_id"] = str(db_user.user_id)

        async with safe_operation("user_authentication", log_context):
            with log_timing(
                "password_verification", request_id=log_context["request_id"]
            ):
                if not verify_password(user.user_password, db_user.user_password_hash):
                    logger.warning(
                        "Login failed - invalid password",
                        email_exists=True,
                        **log_context,
                    )
                    raise AuthenticationError("Invalid email or password")

        with log_timing("generate_tokens", request_id=log_context["request_id"]):
            access_token = create_access_token(user_id=str(db_user.user_id))
            refresh_token = create_refresh_token(user_id=str(db_user.user_id))
            logger.debug("Tokens generated successfully", **log_context)

        logger.info("Login successful", **log_context)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_first_name=db_user.user_first_name,
            is_email_verified=db_user.is_email_verified,
            user_id=str(db_user.user_id),
        )

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
            "Unhandled exception during login",
            error=sanitized_error,
            error_type=type(exc).__name__,
            **log_context,
        )
        raise BusinessLogicError(
            message="An unexpected error occurred during login",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/auth/refresh",
    tags=["User"],
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generate new access and refresh tokens using an existing refresh token",
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request, refresh_data: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access and refresh tokens.

    Args:
        request: The incoming HTTP request
        refresh_data: The refresh token data
        db: Database session

    Returns:
        TokenResponse: New access and refresh tokens

    Raises:
        InvalidTokenError: Invalid or expired refresh token
        UserNotFoundError: User not found
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "token_refresh",
    }

    logger.debug("Token refresh requested", **log_context)

    # First validate token format before decoding to catch malformed tokens
    token_parts = refresh_data.refresh_token.split(".")
    if len(token_parts) != 3:
        raise InvalidTokenError("Malformed JWT token format")

    @translate_token_exceptions
    async def decode_token() -> Dict[str, Any]:
        decoded = jwt.decode(
            refresh_data.refresh_token,
            settings.PUBLIC_KEY,
            claims_options={"exp": {"essential": True}},
        )
        return dict(decoded)  # Convert to dict explicitly

    payload = await decode_token()

    if payload.get("type") != "refresh":
        logger.warning(
            "Invalid token type for refresh",
            expected="refresh",
            received=payload.get("type"),
            **log_context,
        )
        raise InvalidTokenError("Invalid token type: expected refresh token")

    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Missing subject in refresh token", **log_context)
        raise InvalidTokenError("Invalid token - no user ID found")

    log_context["user_id"] = user_id

    try:
        uuid_user_id = uuid.UUID(user_id)
    except ValueError:
        logger.error("Invalid UUID format in token", **log_context)
        raise InvalidTokenError("Invalid user ID format")

    user = await validate_user_exists(
        db_session=db,
        user_model=User,
        user_id=str(uuid_user_id),
        log_context=log_context,
    )
    log_context["email"] = user.user_email

    access_token = create_access_token(user_id=str(user.user_id))
    new_refresh_token = create_refresh_token(user_id=str(user.user_id))

    logger.info("Tokens refreshed successfully", **log_context)
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user_first_name=user.user_first_name,
        is_email_verified=user.is_email_verified,
        user_id=str(user.user_id),
    )


@router.post(
    "/send-verification-email",
    tags=["User"],
    status_code=status.HTTP_200_OK,
    summary="Send email verification link",
    description="Sends an email verification link to the user",
)
async def request_verification_email(
    user_email: EmailStr, db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Send an email verification link to the user.

    Args:
        user_email: The user's email address
        db: Database session

    Returns:
        dict: Success message

    Raises:
        UserNotFoundError: If the user is not found
    """
    log_context = {
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "request_verification_email",
    }

    logger.debug("Verification email requested", **log_context)

    user = await validate_user_exists(
        db_session=db, user_model=User, user_email=user_email, log_context=log_context
    )
    log_context["user_id"] = str(user.user_id)

    async with safe_operation(
        "sending verification email", log_context, status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        with log_timing("send_email", request_id=log_context["request_id"]):
            response = await send_verification_email(
                user_email=user_email, user_id=str(user.user_id)
            )
            logger.info("Verification email sent successfully", **log_context)
            return response


@router.get(
    "/verify-email",
    tags=["User"],
    status_code=status.HTTP_200_OK,
    summary="Verify email using token",
    description="Verifies the user's email using the provided token",
)
async def verify_email_token(
    token: str, db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Verify the user's email using the token.

    Args:
        token: The JWT token from the verification link
        db: Database session

    Returns:
        dict: Success message
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "verify_email",
        "token_provided": bool(token),
    }

    logger.debug("Processing email verification", **log_context)

    @translate_token_exceptions
    async def attempt_decode() -> str:
        payload = jwt.decode(token, settings.PUBLIC_KEY)
        return str(payload.get("sub", ""))  # Explicitly cast to string

    try:
        user_id = await attempt_decode()
        logger.debug("Successfully decoded JWT token", **log_context)
    except InvalidTokenError:
        logger.warning("Not a valid JWT, trying as direct user_id", **log_context)
        user_id = token

    if not user_id:
        logger.error("No user_id found in token", **log_context)
        raise EmailVerificationError(
            message="Invalid verification token - no user ID found"
        )

    log_context["user_id"] = user_id

    async with safe_operation("email verification", log_context):
        async with UserUnitOfWork(db) as uow:
            user = await uow.verify_email(user_id)
            if user and user.user_email:
                log_context["email"] = user.user_email

    logger.info("Email verified successfully", **log_context)
    return {"message": "Email verified successfully"}


@router.get(
    "/verification-status",
    tags=["User"],
    status_code=status.HTTP_200_OK,
    summary="Check email verification status",
    description="Returns the current email verification status for a user",
)
async def check_verification_status(
    user_email: EmailStr, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if a user's email is verified.

    Args:
        user_email: The user's email address
        db: Database session

    Returns:
        dict: Contains verification status
    """
    log_context = {
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "check_verification_status",
    }

    logger.debug("Checking email verification status", **log_context)

    user = await validate_user_exists(
        db_session=db, user_model=User, user_email=user_email, log_context=log_context
    )

    log_context["user_id"] = str(user.user_id)
    log_context["verification_status"] = str(user.is_email_verified)

    logger.info("Verification status checked", **log_context)

    return {
        "is_email_verified": user.is_email_verified,
        "user_id": str(user.user_id),
    }
