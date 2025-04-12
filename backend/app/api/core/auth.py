"""
Authentication Utilities
- JWT token generation and validation
- Password verification
- Authentication helpers
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Optional, cast

import bcrypt
import structlog
from authlib.jose import JoseError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.middleware.logging_middleware import sanitize_error_message
from app.api.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
logger = structlog.get_logger()


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token for authenticated user.

    Args:
        user_id: The user's ID to encode in the token
        expires_delta: Optional token expiry override

    Returns:
        str: Encoded JWT access token
    """
    try:
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": str(uuid.uuid4()),  # Add a unique token ID
        }
        token = jwt.encode(
            {"alg": settings.JWT_ALGORITHM}, payload, settings.PRIVATE_KEY
        )
        logger.info(
            "Access token created",
            user_id=user_id,
            expires_at=expire.isoformat(),
            token_type="access",
        )
        return cast(str, token.decode("utf-8"))
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Failed to create access token",
            user_id=user_id,
            error=sanitized_error,
            error_type=type(e).__name__,
        )
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt.

    Args:
        plain_password: The password to verify
        hashed_password: The stored hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        logger.error("Password verification error")
        return False


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by verifying their credentials.

    Args:
        db: Database session
        email: User's email
        password: User's password

    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    try:
        logger.info("User authentication attempt")
        user = db.query(User).filter(User.user_email == email).first()

        if not user:
            # Use generic log message to prevent user enumeration
            logger.warning("Authentication failed")
            return None

        if verify_password(password, user.user_password_hash):
            logger.info("User authenticated successfully", user_id=str(user.user_id))
            return user

        # Use generic log message to prevent user enumeration
        logger.warning("Authentication failed", user_id=str(user.user_id))
        return None

    except Exception as e:
        logger.error("Authentication error", error=str(e))
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Validate JWT and return user.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User: Authenticated user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    logger.debug("Validating JWT token")
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY)
    except JoseError as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Token validation failed",
            error=sanitized_error,
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        logger.warning("Invalid token payload - missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        logger.warning(
            "User from valid token not found in database",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    logger.info("Token validated successfully", user_id=user_id)
    return user


def create_refresh_token(user_id: str) -> str:
    """Generate JWT refresh token with longer expiration.

    Args:
        user_id: The user's ID to encode in the token

    Returns:
        str: Encoded JWT refresh token
    """
    try:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.now(UTC) + expires_delta
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        }
        token = jwt.encode(
            {"alg": settings.JWT_ALGORITHM}, payload, settings.PRIVATE_KEY
        )
        logger.info(
            "Refresh token created",
            user_id=user_id,
            expires_at=expire.isoformat(),
            expires_in_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        return cast(str, token.decode("utf-8"))
    except Exception as e:
        logger.error("Failed to create refresh token", user_id=user_id, error=str(e))
        raise
