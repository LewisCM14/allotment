"""
User Preference Endpoints
- Provides API endpoints for user preference operations (read, update).
"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import get_current_user
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.schemas.user.user_preference_schema import (
    FeedDayRead,
    UserFeedDayUpdate,
    UserPreferencesRead,
)
from app.api.services.user.user_preferences_unit_of_work import (
    UserPreferencesUnitOfWork,
)

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
            async with UserPreferencesUnitOfWork(db) as uow:
                preferences = await uow.get_user_preferences(str(current_user.user_id))

            logger.info("User preferences fetched successfully", **log_context)
            return preferences


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
        with log_timing(
            "update_user_feed_preference_endpoint", request_id=log_context["request_id"]
        ):
            async with UserPreferencesUnitOfWork(db) as uow:
                updated_preference = await uow.update_user_feed_preference(
                    str(current_user.user_id), feed_id, str(preference_update.day_id)
                )

            logger.info("User feed preference updated successfully", **log_context)
            return updated_preference
