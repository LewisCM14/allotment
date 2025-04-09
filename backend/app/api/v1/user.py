"""
User Endpoints
- Provides API endpoints for user-related operations.
"""

import uuid

import structlog
from authlib.jose import JoseError, jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth import create_access_token, create_refresh_token, verify_password
from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
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
        HTTPException:
            - 400: Email already registered
            - 422: Invalid input data
            - 500: Database error or user creation failed
    """
    log_context = {
        "email": user.user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "user_registration",
    }

    try:
        logger.info("Attempting user registration", **log_context)

        with log_timing("check_existing_user", request_id=log_context["request_id"]):
            query = select(User).where(User.user_email == user.user_email)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                logger.warning(
                    "Registration failed - email already exists", **log_context
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        with log_timing("create_user_account", request_id=log_context["request_id"]):
            async with UserUnitOfWork(db) as uow:
                new_user = await uow.create_user(user)

            if not new_user or not new_user.user_id:
                logger.error("User creation failed", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user",
                )
            log_context["user_id"] = str(new_user.user_id)

        try:
            with log_timing("send_verification_email", request_id=log_context["request_id"]):
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

    except HTTPException:
        raise
    except ValueError as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Validation error during user registration",
            error=sanitized_error,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=sanitized_error
        )
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Unexpected error during user registration",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e


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
        HTTPException:
            - 401: Invalid credentials
            - 422: Invalid input format
            - 500: Database error
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "user_login",
    }

    try:
        logger.info("Login attempt", **log_context)
        
        with log_timing("user_authentication", request_id=log_context["request_id"]):
            query = select(User).where(User.user_email == user.user_email)
            result = await db.execute(query)
            db_user = result.scalar_one_or_none()

            if not db_user:
                logger.warning(
                    "Login failed - user not found", email_exists=False, **log_context
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            log_context["email"] = user.user_email
            log_context["user_id"] = str(db_user.user_id)

            # Verify password separately to avoid timing attacks
            if not verify_password(user.user_password, db_user.user_password_hash):
                logger.warning(
                    "Login failed - invalid password", email_exists=True, **log_context
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

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
    except HTTPException:
        raise
    except ValueError as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Validation error during login",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=sanitized_error
        )
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Unexpected error during login",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication",
        ) from e


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
        HTTPException:
            - 401: Invalid or expired refresh token
            - 500: Database error
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "token_refresh",
    }

    try:
        logger.debug("Token refresh requested", **log_context)

        with log_timing("validate_refresh_token", request_id=log_context["request_id"]):
            try:
                payload = jwt.decode(refresh_data.refresh_token, settings.PUBLIC_KEY)
                logger.debug("Token decoded successfully", **log_context)
            except Exception as jwt_error:
                sanitized_error = sanitize_error_message(str(jwt_error))
                logger.warning(
                    "Invalid token format",
                    error=sanitized_error,
                    error_type=type(jwt_error).__name__,
                    **log_context,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Validate token type
            if payload.get("type") != "refresh":
                logger.warning(
                    "Invalid token type for refresh",
                    token_type=payload.get("type"),
                    **log_context,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Missing subject in refresh token", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            log_context["user_id"] = user_id

            try:
                uuid_user_id = uuid.UUID(user_id)
            except ValueError:
                logger.error("Invalid UUID format in token", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user ID format",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        with log_timing("fetch_user", request_id=log_context["request_id"]):
            query = select(User).where(User.user_id == uuid_user_id)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning("User from refresh token not found", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            log_context["email"] = user.user_email

        with log_timing("generate_tokens", request_id=log_context["request_id"]):
            access_token = create_access_token(user_id=str(user.user_id))
            new_refresh_token = create_refresh_token(user_id=str(user.user_id))
            logger.debug("New tokens generated successfully", **log_context)

        logger.info("Tokens refreshed successfully", **log_context)
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user_first_name=user.user_first_name,
            is_email_verified=user.is_email_verified,
            user_id=str(user.user_id),
        )
    except HTTPException:
        raise
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Unexpected error during token refresh",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        ) from e


@router.post(
    "/send-verification-email",
    tags=["User"],
    status_code=status.HTTP_200_OK,
    summary="Send email verification link",
    description="Sends an email verification link to the user",
)
async def request_verification_email(
    user_email: EmailStr, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """
    Send an email verification link to the user.

    Args:
        user_email: The user's email address
        db: Database session

    Returns:
        dict: Success message
    """
    log_context = {
        "email": user_email,
        "request_id": request_id_ctx_var.get(),
        "operation": "request_verification_email",
    }

    try:
        logger.debug("Verification email requested", **log_context)

        with log_timing("find_user", request_id=log_context["request_id"]):
            query = select(User).where(User.user_email == user_email)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning("User not found for verification email", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            log_context["user_id"] = str(user.user_id)

        with log_timing("send_email", request_id=log_context["request_id"]):
            response = await send_verification_email(
                user_email=user_email, user_id=str(user.user_id)
            )
            logger.info("Verification email sent successfully", **log_context)
            return response

    except HTTPException:
        raise
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Error sending verification email",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )


@router.get(
    "/verify-email",
    tags=["User"],
    status_code=status.HTTP_200_OK,
    summary="Verify email using token",
    description="Verifies the user's email using the provided token",
)
async def verify_email_token(
    token: str, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
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

    try:
        logger.debug("Processing email verification", **log_context)

        user_id = None
        with log_timing("decode_token", request_id=log_context["request_id"]):
            try:
                payload = jwt.decode(token, settings.PUBLIC_KEY)
                user_id = payload.get("sub")
                logger.debug("Successfully decoded JWT token", **log_context)
            except JoseError as e:
                sanitized_error = sanitize_error_message(str(e))
                logger.warning(
                    "Failed to decode JWT token, trying as direct user_id",
                    error=sanitized_error,
                    **log_context,
                )
                user_id = token

        if not user_id:
            logger.error("No user_id found in token", **log_context)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token - no user ID found",
            )

        log_context["user_id"] = user_id

        with log_timing("verify_email", request_id=log_context["request_id"]):
            async with UserUnitOfWork(db) as uow:
                user = await uow.verify_email(user_id)
                if user and user.user_email:
                    log_context["email"] = user.user_email

        logger.info("Email verified successfully", **log_context)
        return {"message": "Email verified successfully"}

    except HTTPException:
        raise
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Error verifying email",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email",
        )


@router.get(
    "/verification-status",
    tags=["User"],
    status_code=status.HTTP_200_OK,
    summary="Check email verification status",
    description="Returns the current email verification status for a user",
)
async def check_verification_status(
    user_email: EmailStr, db: AsyncSession = Depends(get_db)
) -> dict:
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

    try:
        logger.debug("Checking email verification status", **log_context)

        with log_timing("fetch_user", request_id=log_context["request_id"]):
            query = select(User).where(User.user_email == user_email)
            result = await db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(
                    "User not found for verification status check", **log_context
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            log_context["user_id"] = str(user.user_id)
            log_context["verification_status"] = str(user.is_email_verified)

            logger.info("Verification status checked", **log_context)

            return {
                "is_email_verified": user.is_email_verified,
                "user_id": str(user.user_id),
            }
    except HTTPException:
        raise
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.exception(
            "Error checking verification status",
            error=sanitized_error,
            error_type=type(e).__name__,
            **log_context,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check verification status",
        )
