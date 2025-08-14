"""
Day Endpoints
- Provides API endpoints for day operations (read only).
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
from app.api.schemas.user.user_preference_schema import DayRead
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=List[DayRead],
    status_code=status.HTTP_200_OK,
    summary="Get available days",
    description="Get all available days for plant feeding preferences.",
)
@limiter.limit("10/minute")
async def get_days(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[DayRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_days",
    }
    logger.info("Fetching available days", **log_context)

    async with safe_operation("fetching days", log_context):
        with log_timing("get_days_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                days = await uow.get_all_days()

            logger.info(
                "Days fetched successfully",
                count=len(days),
                **log_context,
            )
            return [
                DayRead(id=day.id, day_number=day.day_number, name=day.name)
                for day in days
            ]
