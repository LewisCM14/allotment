"""
Authentication Utilities
- JWT token generation and validation
- Password verification
- Authentication helpers
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Optional, cast

import bcrypt
import structlog
from authlib.jose import JoseError, jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.middleware.error_handler import validate_user_exists
from app.api.middleware.exception_handler import InvalidTokenError
from app.api.middleware.logging_middleware import sanitize_error_message
from app.api.models import User

logger = structlog.get_logger()

TokenType = Literal["access", "refresh", "reset", "email_verification", "verification"]


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
            elif token_type == "email_verification" or token_type == "verification":
                expire_seconds = settings.RESET_TOKEN_EXPIRE_MINUTES * 60
            else:
                raise ValueError(f"Unknown token type: {token_type}")

        expire = datetime.now(UTC) + timedelta(seconds=expire_seconds)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(UTC),
            "jti": str(uuid.uuid4()),
            "type": token_type,
        }

        if not settings.PRIVATE_KEY:
            raise ValueError("Private key is not loaded. Ensure the key file exists.")

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


def decode_token(token: str) -> dict[str, Any]:
    """Decode JWT token and return payload."""
    logger.debug("Validating JWT token")
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY)
        return cast(dict[str, Any], payload)
    except (JoseError, ValueError) as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(
            "Token validation failed",
            error=sanitized_error,
            error_type=type(e).__name__,
        )
        raise InvalidTokenError("Invalid token") from e


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Authenticate user by verifying their credentials."""
    try:
        logger.info("User authentication attempt")
        result = await db.execute(select(User).filter(User.user_email == email))
        user = result.scalar_one_or_none()

        if not user:
            # Use generic log message to prevent user enumeration
            logger.warning("Authentication failed")
            return None

        if verify_password(password, user.user_password_hash):
            # Update last_active_date on successful login
            user.last_active_date = datetime.now(UTC)
            await db.commit()
            await db.refresh(user)

            logger.info("User authenticated successfully", user_id=str(user.user_id))
            return user

        # Use generic log message to prevent user enumeration
        logger.warning("Authentication failed", user_id=str(user.user_id))
        return None

    except Exception as e:
        logger.error("Authentication error", error=str(e))
        return None


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current user from the authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    token_type, _, token = authorization.partition(" ")
    if token_type.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token type, "Bearer" expected.',
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing"
        )

    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        logger.warning("Invalid token payload - missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await validate_user_exists(db_session=db, user_model=User, user_id=user_id)
    return cast(User, user)
