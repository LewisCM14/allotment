"""
Auth Endpoints
- Provides API endpoints for user authentication and password reset operations.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import (
    authenticate_user,
    create_token,
    decode_token,
)
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.factories.user_factory import UserFactoryValidationError
from app.api.middleware.exception_handler import (
    AuthenticationError,
    BaseApplicationError,
    BusinessLogicError,
    InvalidTokenError,
    validate_user_exists,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models import User
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import (
    MessageResponse,
    PasswordResetRequest,
    PasswordUpdate,
    RefreshRequest,
    UserLogin,
)
from app.api.services.email_service import (
    send_verification_email,
)
from app.api.services.user.user_unit_of_work import UserUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/token",
    tags=["Auth"],
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

    from app.api.middleware.error_handler import safe_operation

    async with safe_operation("authenticating user", log_context):
        db_user = await authenticate_user(db, user.user_email, user.user_password)
        if not db_user:
            raise AuthenticationError("Invalid email or password")

        log_context["user_id"] = str(db_user.user_id)

        with log_timing("generate_tokens", request_id=log_context["request_id"]):
            access_token = create_token(
                user_id=str(db_user.user_id), token_type="access"
            )
            refresh_token = create_token(
                user_id=str(db_user.user_id), token_type="refresh"
            )

        logger.info("Login successful", **log_context)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user_first_name=db_user.user_first_name,
            is_email_verified=db_user.is_email_verified,
            user_id=str(db_user.user_id),
        )


@router.post(
    "/token/refresh",
    tags=["Auth"],
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generate new access and refresh tokens using an existing refresh token",
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request, refresh_data: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    log_context = {
        "request_id": request.headers.get("X-Request-ID", str(uuid.uuid4())),
        "operation": "refresh_token",
    }
    logger.debug("Entering refresh_token endpoint", **log_context)

    try:
        try:
            payload = decode_token(refresh_data.refresh_token)
        except BaseApplicationError as e:
            logger.warning(
                "Invalid token error in refresh_token", error=str(e), **log_context
            )
            raise
        except Exception as e:
            logger.warning(
                "Exception in decode_token in refresh_token",
                error=str(e),
                **log_context,
            )
            raise InvalidTokenError(str(e)) from e

        logger.debug("Token decoded successfully", payload=payload, **log_context)

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
        user = await validate_user_exists(
            db_session=db,
            user_model=User,
            user_id=user_id,
        )
        log_context["email"] = user.user_email

        access_token = create_token(user_id=str(user.user_id), token_type="access")
        new_refresh_token = create_token(
            user_id=str(user.user_id), token_type="refresh"
        )
        logger.info("Tokens refreshed successfully", **log_context)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user_first_name=user.user_first_name,
            is_email_verified=user.is_email_verified,
            user_id=str(user.user_id),
        )

    except InvalidTokenError as e:
        logger.warning(
            "Invalid token error in refresh_token", error=str(e), **log_context
        )
        raise
    except Exception as e:
        logger.error(
            "Unexpected exception in refresh_token",
            error_type=type(e).__name__,
            error_message=str(e),
            **log_context,
        )
        raise
    finally:
        logger.debug("Exiting refresh_token endpoint", **log_context)


@router.post(
    "/password-resets",
    tags=["Auth"],
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
    tags=["Auth"],
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token from path",
    description="Resets a user's password using a valid reset token from the URL path and new password from the request body.",
)
@limiter.limit("5/minute")
async def reset_password(
    token: str,
    password_data: PasswordUpdate,
    request: Request,
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
    INTERNAL_SERVER_ERROR_MSG = "Internal server error"
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "reset_password",
    }
    logger.debug("Password reset attempt with token", **log_context)

    try:
        try:
            decode_token(token)
        except Exception as exc:
            logger.error(
                "General exception during token decode",
                error=str(exc),
                **log_context,
            )
            raise BusinessLogicError(
                message=INTERNAL_SERVER_ERROR_MSG,
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

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
        # Return both a message and the error code for consistency
        raise HTTPException(
            status_code=e.status_code, detail=[{"msg": str(e), "type": e.error_code}]
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
            "Unhandled exception during password reset",
            error=sanitized_error,
            error_type=type(exc).__name__,
            **log_context,
        )
        raise BusinessLogicError(
            message=INTERNAL_SERVER_ERROR_MSG,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
