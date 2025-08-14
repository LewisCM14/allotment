"""
User Preferences Unit of Work
- Manages user preference-related transactions as a single unit of work.
- Coordinates operations across UserRepository and GrowGuide repositories.
- Handles cross-domain coordination for user preferences functionality.
"""

import uuid
from types import TracebackType
from typing import Optional, Type

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.variety_repository import VarietyRepository
from app.api.repositories.user.user_repository import UserRepository
from app.api.schemas.user.user_preference_schema import (
    DayRead,
    FeedDayRead,
    FeedRead,
    UserPreferencesRead,
)

logger = structlog.get_logger()


class UserPreferencesUnitOfWork:
    """Unit of Work for managing user preference-related transactions and cross-domain coordination."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.variety_repo = VarietyRepository(db)
        self.day_repo = DayRepository(db)
        self.request_id = request_id_ctx_var.get()

    async def __aenter__(self) -> "UserPreferencesUnitOfWork":
        """Enter the runtime context for the Unit of Work."""
        logger.debug(
            "Starting user preferences unit of work",
            request_id=self.request_id,
            transaction="begin",
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context for the Unit of Work."""
        log_context = {"request_id": self.request_id}

        if exc_type:
            if exc_value:
                logger.error(
                    "Transaction failed, rolling back",
                    error=str(exc_value),
                    error_type=exc_type.__name__,
                    transaction="rollback",
                    **log_context,
                )
            else:
                logger.warning(
                    "Transaction exception without value, rolling back",
                    transaction="rollback",
                    **log_context,
                )
            await self.db.rollback()
            logger.debug(
                "Transaction rolled back", transaction="rollback", **log_context
            )
        else:
            try:
                await self.db.commit()
                logger.debug(
                    "Transaction committed successfully",
                    transaction="commit",
                    **log_context,
                )
            except IntegrityError as ie:
                await self.db.rollback()
                logger.error(
                    "Integrity constraint violation, rolled back",
                    error=str(ie),
                    transaction="rollback_after_integrity_error",
                    **log_context,
                )
                raise

    @translate_db_exceptions
    async def get_user_preferences(self, user_id: str) -> UserPreferencesRead:
        """Get all user preferences with available options."""
        log_context = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "get_user_preferences_uow",
        }

        logger.info("Getting user preferences via UOW", **log_context)

        with log_timing("uow_get_user_preferences", request_id=self.request_id):
            # Get user's current feed day preferences
            user_feed_days = await self.user_repo.get_user_feed_days(user_id)

            # Get available options from grow guide domain
            available_feeds = await self.variety_repo.get_all_feeds()
            available_days = await self.day_repo.get_all_days()

            logger.info("User preferences retrieved successfully", **log_context)

            return UserPreferencesRead(
                user_feed_days=[
                    FeedDayRead(
                        feed_id=ufd.feed_id,
                        feed_name=ufd.feed.name,
                        day_id=ufd.day_id,
                        day_name=ufd.day.name,
                    )
                    for ufd in user_feed_days
                ],
                available_feeds=[
                    FeedRead(id=feed.id, name=feed.name) for feed in available_feeds
                ],
                available_days=[
                    DayRead(id=day.id, day_number=day.day_number, name=day.name)
                    for day in available_days
                ],
            )

    @translate_db_exceptions
    async def update_user_feed_preference(
        self, user_id: str, feed_id: str, day_id: str
    ) -> FeedDayRead:
        """Update a user's feed day preference and return the updated preference."""
        log_context = {
            "user_id": user_id,
            "feed_id": feed_id,
            "day_id": day_id,
            "request_id": self.request_id,
            "operation": "update_user_feed_preference_uow",
        }

        logger.info("Updating user feed preference via UOW", **log_context)

        with log_timing("uow_update_user_feed_preference", request_id=self.request_id):
            # Validate feed_id format
            try:
                uuid.UUID(feed_id)
            except ValueError:
                logger.warning("Invalid feed_id format", **log_context)
                raise BusinessLogicError(
                    f"Invalid feed_id format: {feed_id}",
                    status_code=400,
                )

            # Update the preference
            await self.user_repo.update_user_feed_day(user_id, feed_id, day_id)

            # Get the updated preference with feed and day names for response
            user_feed_days = await self.user_repo.get_user_feed_days(user_id)

            # Find the updated preference in the results
            updated_feed_day = None
            for ufd in user_feed_days:
                if str(ufd.feed_id) == feed_id and str(ufd.day_id) == day_id:
                    updated_feed_day = ufd
                    break

            if not updated_feed_day:
                logger.warning("Updated preference not found in results", **log_context)
                raise ResourceNotFoundError("Feed preference", feed_id)

            logger.info("User feed preference updated successfully", **log_context)

            return FeedDayRead(
                feed_id=updated_feed_day.feed_id,
                feed_name=updated_feed_day.feed.name,
                day_id=updated_feed_day.day_id,
                day_name=updated_feed_day.day.name,
            )
