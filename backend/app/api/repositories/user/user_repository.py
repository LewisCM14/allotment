"""
User Repository
- Encapsulates database operations for User model
"""

from uuid import UUID

import structlog
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models import User

logger = structlog.get_logger()


class UserRepository:
    """User repository for database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.request_id = request_id_ctx_var.get()

    async def create_user(self, user: User) -> User:
        """Persist a new user."""
        log_context = {
            "user_id": str(user.user_id),
            "email": user.user_email,
            "request_id": self.request_id,
            "operation": "create_user",
        }

        try:
            with log_timing("db_create_user", **log_context):
                self.db.add(user)
                logger.debug("User added to session", **log_context)
                return user
        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.error(
                "Failed to create user",
                error=sanitized_error,
                error_type=type(e).__name__,
                **log_context,
            )
            raise

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

        try:
            with log_timing("db_verify_email", **log_context):
                user_uuid = UUID(user_id)
                user = await self.db.get(User, user_uuid)

                if not user:
                    logger.warning(
                        "User not found for email verification", **log_context
                    )
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

        except ValueError:
            logger.warning(
                "Invalid user_id format for email verification",
                input_value=user_id,
                **log_context,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format",
            )

        except SQLAlchemyError as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.error(
                "Database error during email verification",
                error=sanitized_error,
                error_type=type(e).__name__,
                **log_context,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify email",
            )
