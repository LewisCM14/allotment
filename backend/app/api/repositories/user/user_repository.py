"""
User Repository
- Encapsulates database operations for User model
"""

from typing import Optional
from uuid import UUID

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.exception_handler import InvalidTokenError
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
)
from app.api.models import User

logger = structlog.get_logger()


class UserRepository:
    """User repository for database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.request_id = request_id_ctx_var.get()

    @translate_db_exceptions
    async def create_user(self, user: User) -> User:
        """Persist a new user."""
        log_context = {
            "user_id": str(user.user_id),
            "email": user.user_email,
            "request_id": self.request_id,
            "operation": "create_user",
        }

        with log_timing("db_create_user", request_id=log_context["request_id"]):
            self.db.add(user)
            logger.info("User added to session", **log_context)
        return user

    @translate_db_exceptions
    async def verify_email(self, user_id: str) -> User:
        """Mark a user's email as verified.

        Args:
            user_id: The ID of the user to update

        Returns:
            User: Updated user

        Raises:
            HTTPException: If the user is not found or the update fails
        """
        log_context = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "verify_email",
        }

        logger.debug("Attempting to verify email", **log_context)

        with log_timing("db_verify_email", request_id=log_context["request_id"]):
            try:
                user_uuid = UUID(user_id)
            except ValueError as e:
                logger.warning(
                    "Invalid user_id format",
                    error=str(e),
                    **log_context,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID format",
                )

            user = await self.db.get(User, user_uuid)

            if not user:
                logger.warning("User not found for email verification", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            log_context["email"] = user.user_email

            user.is_email_verified = True
            logger.info(
                "Email verification successful",
                previous_status=False,
                new_status=True,
                **log_context,
            )
        return user

    @translate_db_exceptions
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address.

        Args:
            email: The user's email address

        Returns:
            User object or None if not found
        """
        log_context = {
            "email": email,
            "request_id": self.request_id,
            "operation": "get_user_by_email",
        }

        logger.debug("Fetching user by email", **log_context)

        with log_timing(
            "db_get_user_by_email", request_id=self.request_id, **log_context
        ):
            query = select(User).where(User.user_email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if user:
                log_context["user_id"] = str(user.user_id)
                logger.debug("User found", user_found=True, **log_context)
            else:
                logger.debug("User not found", user_found=False, **log_context)

        return user

    @translate_db_exceptions
    async def update_user_password(self, user_id: str, new_password: str) -> User:
        """Update a user's password.

        Args:
            user_id: The user's ID
            new_password: The new password

        Returns:
            Updated User object

        Raises:
            HTTPException: If the user is not found
        """
        log_context = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "update_user_password",
        }

        logger.debug("Updating user password", **log_context)

        with log_timing("db_update_password", **log_context):
            try:
                user_uuid = UUID(user_id)
            except ValueError as e:
                logger.error("Invalid UUID format", error=str(e), **log_context)
                raise InvalidTokenError("Invalid user ID format")

            user = await self.db.get(User, user_uuid)
            if not user:
                logger.warning("User not found for password reset", **log_context)
                raise InvalidTokenError("User not found")

            log_context["email"] = user.user_email
            user.set_password(new_password)

            logger.info("User password updated", **log_context)

        return user
