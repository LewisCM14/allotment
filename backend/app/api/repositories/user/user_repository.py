"""
User Repository
- Encapsulates database operations for User model
"""

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import (
    translate_db_exceptions,
    validate_user_exists,
)
from app.api.middleware.exception_handler import InvalidTokenError
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
)
from app.api.models import User
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.models.user.user_model import UserAllotment, UserFeedDay
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
    async def update_user_profile(
        self, user_id: str, first_name: str, country_code: str
    ) -> User:
        """Update a user's profile information.

        Args:
            user_id: The user's ID
            first_name: The new first name
            country_code: The new country code

        Returns:
            Updated User object

        Raises:
            UserNotFoundError: If the user is not found
            InvalidTokenError: If the user ID format is invalid
        """
        log_context = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "update_user_profile",
        }

        logger.debug("Updating user profile", **log_context)

        timing_context = {
            k: v for k, v in log_context.items() if k not in ("request_id", "operation")
        }

        with log_timing(
            "db_update_user_profile", request_id=self.request_id, **timing_context
        ):
            user = await validate_user_exists(
                db_session=self.db, user_model=User, user_id=user_id
            )
            assert isinstance(user, User)

            log_context["email"] = user.user_email
            user.user_first_name = first_name
            user.user_country_code = country_code

            logger.info("User profile updated successfully", **log_context)

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

    @translate_db_exceptions
    async def get_user_feed_days(self, user_id: str) -> List[UserFeedDay]:
        """Get all feed day preferences for a user."""
        log_context = {"user_id": str(user_id)}
        with log_timing(
            "db_get_user_feed_days", request_id=self.request_id, **log_context
        ):
            user_uuid = UUID(user_id)
            query = (
                select(UserFeedDay)
                .where(UserFeedDay.user_id == user_uuid)
                .options(selectinload(UserFeedDay.feed), selectinload(UserFeedDay.day))
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())

    @translate_db_exceptions
    async def get_all_feeds(self) -> List[Feed]:
        """Get all available feed types."""
        with log_timing("db_get_all_feeds", request_id=self.request_id):
            query = select(Feed).order_by(Feed.name)
            result = await self.db.execute(query)
            return list(result.scalars().all())

    @translate_db_exceptions
    async def get_all_days(self) -> List[Day]:
        """Get all available days."""
        with log_timing("db_get_all_days", request_id=self.request_id):
            query = select(Day).order_by(Day.day_number)
            result = await self.db.execute(query)
            return list(result.scalars().all())

    @translate_db_exceptions
    async def update_user_feed_day(
        self, user_id: str, feed_id: str, day_id: str
    ) -> UserFeedDay:
        """Update or create a user's feed day preference."""
        log_context = {
            "user_id": str(user_id),
            "feed_id": str(feed_id),
            "day_id": str(day_id),
        }
        with log_timing(
            "db_update_user_feed_day", request_id=self.request_id, **log_context
        ):
            # Convert string IDs to UUIDs
            user_uuid = UUID(user_id)
            feed_uuid = UUID(feed_id)
            day_uuid = UUID(day_id)

            # Check if preference already exists
            query = select(UserFeedDay).where(
                UserFeedDay.user_id == user_uuid, UserFeedDay.feed_id == feed_uuid
            )
            result = await self.db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing preference
                existing.day_id = day_uuid
                self.db.add(existing)
                logger.info(
                    "User feed day preference updated",
                    operation="update_user_feed_day",
                    **log_context,
                )
                return existing
            else:
                # Create new preference
                new_preference = UserFeedDay()
                new_preference.user_id = user_uuid
                new_preference.feed_id = feed_uuid
                new_preference.day_id = day_uuid
                self.db.add(new_preference)
                logger.info(
                    "User feed day preference created",
                    operation="create_user_feed_day",
                    **log_context,
                )
                return new_preference
