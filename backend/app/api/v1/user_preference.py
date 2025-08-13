"""
User Preference Endpoints
- Provides API endpoints for user preference operations (read, update).
"""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import get_current_user
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.schemas.user.user_preference_schema import (
    DayRead,
    FeedDayRead,
    FeedRead,
    UserFeedDayUpdate,
    UserPreferencesRead,
)
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork
from app.api.services.user.user_unit_of_work import UserUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=UserPreferencesRead,
    status_code=status.HTTP_200_OK,
    summary="Get user preferences",
    description="Get all user preferences including feed days and available options.",
)
@limiter.limit("10/minute")
async def get_user_preferences(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> UserPreferencesRead:
    log_context = {
        "user_id": str(current_user.user_id),
        "request_id": request_id_ctx_var.get(),
        "operation": "get_user_preferences",
    }
    logger.info("Fetching user preferences", **log_context)

    async with safe_operation("fetching user preferences", log_context):
        with log_timing(
            "get_user_preferences_endpoint", request_id=log_context["request_id"]
        ):
            # Coordinate between both units of work at API layer
            async with UserUnitOfWork(db) as user_uow:
                user_feed_days = await user_uow.get_user_feed_days(
                    str(current_user.user_id)
                )

            async with GrowGuideUnitOfWork(db) as grow_guide_uow:
                available_feeds = await grow_guide_uow.get_all_feeds()
                available_days = await grow_guide_uow.get_all_days()

            logger.info("User preferences fetched successfully", **log_context)
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


@router.put(
    "/{feed_id}",
    response_model=FeedDayRead,
    status_code=status.HTTP_200_OK,
    summary="Update user feed preference",
    description="Update the day preference for a specific feed type.",
)
@limiter.limit("10/minute")
async def update_user_feed_preference(
    feed_id: str,
    preference_update: UserFeedDayUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> FeedDayRead:
    log_context = {
        "user_id": str(current_user.user_id),
        "feed_id": feed_id,
        "day_id": str(preference_update.day_id),
        "request_id": request_id_ctx_var.get(),
        "operation": "update_user_feed_preference",
    }
    logger.info("Updating user feed preference", **log_context)

    async with safe_operation("updating user feed preference", log_context):
        # Validate feed_id is a valid UUID
        try:
            uuid.UUID(feed_id)
        except ValueError:
            logger.warning("Invalid feed_id format", **log_context)
            raise BusinessLogicError(
                f"Invalid feed_id format: {feed_id}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        with log_timing(
            "update_user_feed_preference_endpoint", request_id=log_context["request_id"]
        ):
            async with UserUnitOfWork(db) as uow:
                # Update the preference
                await uow.update_user_feed_day(
                    str(current_user.user_id), feed_id, str(preference_update.day_id)
                )

                # Get the updated preference with feed and day names for response
                user_feed_days = await uow.get_user_feed_days(str(current_user.user_id))

                # Find the updated preference in the results
                updated_feed_day = None
                for ufd in user_feed_days:
                    if str(ufd.feed_id) == feed_id and str(ufd.day_id) == str(
                        preference_update.day_id
                    ):
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
