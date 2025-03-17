"""
Authentication Endpoints
- Handles JWT token generation and validation
- User authentication and password verification
- Protected route dependencies
"""

from datetime import UTC, datetime, timedelta
from typing import Optional

import bcrypt
from authlib.jose import JoseError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT using Authlib with RS256 signing.

    Args:
        user_id: The user's ID to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(
        {"alg": settings.JWT_ALGORITHM}, payload, settings.PRIVATE_KEY
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt.

    Args:
        plain_password: The password to verify
        hashed_password: The stored hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by verifying their credentials.

    Args:
        db: Database session
        email: User's email
        password: User's password

    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    user = db.query(User).filter(User.user_email == email).first()
    if user and verify_password(password, user.user_password_hash):
        return user
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
    try:
        payload = jwt.decode(token, settings.PUBLIC_KEY)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    except JoseError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to decode token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
