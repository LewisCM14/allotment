"""
Auth Endpoints
- Provides API endpoints for user-related authentication operations.
"""

import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth import (
    authenticate_user,
    create_token,
    decode_token,
)
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    validate_user_exists,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
)
from app.api.models import User
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import (
    RefreshRequest,
    UserLogin,
)

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "/token",
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

    payload = decode_token(refresh_data.refresh_token)

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
    new_refresh_token = create_token(user_id=str(user.user_id), token_type="refresh")
    logger.info("Tokens refreshed successfully", **log_context)
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user_first_name=user.user_first_name,
        is_email_verified=user.is_email_verified,
        user_id=str(user.user_id),
    )
