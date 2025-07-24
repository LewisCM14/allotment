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
from app.api.models.user.user_model import UserAllotment
from app.api.schemas.user.user_allotment_schema import (
    UserAllotmentCreate,
    UserAllotmentUpdate,
)

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

        timing_context = {
            k: v for k, v in log_context.items() if k not in ("request_id", "operation")
        }

        with log_timing("db_create_user", request_id=self.request_id, **timing_context):
            self.db.add(user)
            logger.info("User added to session", **log_context)
        return user

    @translate_db_exceptions
    async def verify_email(self, user_id: str) -> User:
        """Mark a user's email as verified."""
        log_context = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "verify_email",
        }

        logger.debug("Attempting to verify email", **log_context)

        timing_context = {
            k: v for k, v in log_context.items() if k not in ("request_id", "operation")
        }

        with log_timing(
            "db_verify_email", request_id=self.request_id, **timing_context
        ):
            try:
                user_uuid = UUID(user_id)
            except ValueError as e:
                logger.error("Invalid UUID format", error=str(e), **log_context)
                raise InvalidTokenError("Invalid user ID format")

            user = await self.db.get(User, user_uuid)

            if not user:
                logger.warning("User not found for email verification", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if not user.is_email_verified:
                user.is_email_verified = True
                await self.db.flush()
                logger.info(
                    "Email verification successful",
                    previous_status=False,
                    new_status=True,
                    **log_context,
                )

            return user

    @translate_db_exceptions
    async def get_user_by_email(self, user_email: str) -> Optional[User]:
        """
        Get a user by their email address.

        Args:
            user_email: Email address to look up

        Returns:
            User object if found, None otherwise
        """
        log_context = {"email": user_email}

        with log_timing(
            "db_get_user_by_email", request_id=self.request_id, **log_context
        ):
            query = select(User).where(User.user_email == user_email)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

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

        timing_context = {
            k: v for k, v in log_context.items() if k not in ("request_id", "operation")
        }

        with log_timing(
            "db_update_password", request_id=self.request_id, **timing_context
        ):
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

    @translate_db_exceptions
    async def create_user_allotment(
        self, user_id: str, allotment_data: UserAllotmentCreate
    ) -> UserAllotment:
        """Create a new allotment for a user."""
        log_context = {
            "user_id": str(user_id),
        }
        with log_timing(
            "db_create_user_allotment", request_id=self.request_id, **log_context
        ):
            new_allotment = UserAllotment(
                user_id=user_id, **allotment_data.model_dump()
            )
            self.db.add(new_allotment)
            logger.info(
                "User allotment added to session",
                operation="create_user_allotment",
                **log_context,
            )
            return new_allotment

    @translate_db_exceptions
    async def get_user_allotment(self, user_id: str) -> Optional[UserAllotment]:
        """Fetch a user's allotment by user_id."""
        log_context = {"user_id": str(user_id)}
        with log_timing(
            "db_get_user_allotment", request_id=self.request_id, **log_context
        ):
            query = select(UserAllotment).where(UserAllotment.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

    @translate_db_exceptions
    async def update_user_allotment(
        self, user_id: str, allotment_data: UserAllotmentUpdate
    ) -> UserAllotment:
        """Update a user's allotment."""
        log_context = {"user_id": str(user_id), "request_id": self.request_id}
        timing_context = {k: v for k, v in log_context.items() if k != "request_id"}
        with log_timing(
            "db_update_user_allotment", request_id=self.request_id, **timing_context
        ):
            query = select(UserAllotment).where(UserAllotment.user_id == user_id)
            result = await self.db.execute(query)
            allotment = result.scalar_one_or_none()

            if not allotment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Allotment not found",
                )

            update_data = allotment_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(allotment, key, value)

            self.db.add(allotment)
            logger.info(
                "User allotment updated in session",
                operation="update_user_allotment",
                **log_context,
            )
            return allotment
