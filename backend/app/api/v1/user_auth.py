"""
Auth Endpoints
- Provides API endpoints for user-related authentication operations.
"""

import uuid

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
from app.api.middleware.exception_handler import (
    AuthenticationError,
    BaseApplicationError,
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
