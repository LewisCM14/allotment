"""
Authentication Utilities
- JWT token generation and validation
- Password verification
- Authentication helpers
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal, Optional, cast

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

TokenType = Literal["access", "refresh", "reset"]


def create_token(
    user_id: str,
    expiry_seconds: Optional[int] = None,
    token_type: TokenType = "access",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a JWT token.

    Args:
        user_id: The user's ID to encode in the token
        expiry_seconds: Token expiration time in seconds (takes precedence over expires_delta)
        token_type: Type of the token ("access", "refresh", "reset")
        expires_delta: Optional token expiry as timedelta (used if expiry_seconds not provided)

    Returns:
        str: Encoded JWT token
    """
    try:
        if expiry_seconds is not None:
            expire_seconds = expiry_seconds
        elif expires_delta:
            expire_seconds = int(expires_delta.total_seconds())
        else:
            if token_type == "access":
                expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            elif token_type == "refresh":
                expire_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
            elif token_type == "reset":
                expire_seconds = settings.RESET_TOKEN_EXPIRE_MINUTES * 60

        expire = datetime.now(UTC) + timedelta(seconds=expire_seconds)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": str(uuid.uuid4()),
            "type": token_type,
        }

        token = jwt.encode(
            {"alg": settings.JWT_ALGORITHM}, payload, settings.PRIVATE_KEY
        )

        logger.info(
            "Token created",
            user_id=user_id,
            token_type=token_type,
            expires_at=expire.isoformat(),
            expires_in_seconds=expire_seconds,
        )

        return cast(str, token.decode("utf-8"))
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            f"Failed to create {token_type} token",
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
