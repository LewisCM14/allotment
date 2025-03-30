"""
User Endpoints
- Handles user registration and authentication
- Provides login functionality
- Returns JWT tokens for authenticated users
"""

import uuid

import structlog
from authlib.jose import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth import create_access_token, create_refresh_token, verify_password
from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.models import User
from app.api.repositories import UserRepository
from app.api.schemas import RefreshRequest, TokenResponse, UserCreate, UserLogin

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
    try:
        logger.info("Attempting user registration", email=user.user_email)

        query = select(User).where(User.user_email == user.user_email)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            logger.warning(
                "Registration failed - email already exists", email=user.user_email
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user
        user_repo = UserRepository(db)
        new_user, access_token = await user_repo.create_user(user)

        # Validate creation
        if not new_user or not new_user.user_id:
            logger.error("User creation failed", email=user.user_email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

        logger.info(
            "User successfully registered",
            user_id=str(new_user.user_id),
            email=user.user_email,
        )
        refresh_token = create_refresh_token(user_id=str(new_user.user_id))
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            "Validation error during user registration",
            error=str(e),
            email=user.user_email,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        logger.exception(
            "Unexpected error during user registration",
            error=str(e),
            email=user.user_email,
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
        TokenResponse: JWT access token

    Raises:
        HTTPException:
            - 401: Invalid credentials
            - 422: Invalid input format
            - 500: Database error
    """
    try:
        logger.info("Login attempt", email=user.user_email)

        # Query user by email & check if exists
        query = select(User).where(User.user_email == user.user_email)
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()
        if not db_user:
            logger.warning("Login failed - user not found", email=user.user_email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password separately to avoid timing attacks
        if not verify_password(user.user_password, db_user.user_password_hash):
            logger.warning(
                "Login failed - invalid password",
                email=user.user_email,
                user_id=str(db_user.user_id),
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(user_id=str(db_user.user_id))
        refresh_token = create_refresh_token(user_id=str(db_user.user_id))

        logger.info(
            "Login successful", email=user.user_email, user_id=str(db_user.user_id)
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            "Validation error during login", error=str(e), email=user.user_email
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        logger.exception(
            "Unexpected error during login", error=str(e), email=user.user_email
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
    try:
        try:
            payload = jwt.decode(refresh_data.refresh_token, settings.PUBLIC_KEY)
        except Exception as jwt_error:
            logger.error("Invalid token format", error=str(jwt_error))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "refresh":
            logger.warning("Invalid token type for refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Missing subject in refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            uuid_user_id = uuid.UUID(user_id)
        except ValueError:
            logger.error("Invalid UUID format in token", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        query = select(User).where(User.user_id == uuid_user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("User from refresh token not found", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(user_id=str(user.user_id))
        new_refresh_token = create_refresh_token(user_id=str(user.user_id))

        logger.info("Tokens refreshed successfully", user_id=user_id)
        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during token refresh", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        ) from e
