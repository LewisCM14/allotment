"""
Feed Endpoints
- Provides API endpoints for feed operations (read only).
"""

from typing import List

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.schemas.user.user_preference_schema import FeedRead
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=List[FeedRead],
    status_code=status.HTTP_200_OK,
    summary="Get available feed types",
    description="Get all available feed types for plant feeding preferences.",
)
@limiter.limit("10/minute")
async def get_feeds(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[FeedRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_feeds",
    }
    logger.info("Fetching available feed types", **log_context)

    async with safe_operation("fetching feed types", log_context):
        with log_timing("get_feeds_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                feeds = await uow.get_all_feeds()

            logger.info(
                "Feed types fetched successfully",
                count=len(feeds),
                **log_context,
            )
            return [FeedRead(id=feed.id, name=feed.name) for feed in feeds]
