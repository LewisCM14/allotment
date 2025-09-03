"""
Week Endpoints
- Provides API endpoints for week operations (read only).
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
from app.api.schemas.grow_guide.variety_schema import WeekRead
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=List[WeekRead],
    status_code=status.HTTP_200_OK,
    summary="Get available weeks",
    description="Get all available weeks for plant scheduling preferences.",
)
@limiter.limit("10/minute")
async def get_weeks(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[WeekRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_weeks",
    }
    logger.info("Fetching available weeks", **log_context)

    async with safe_operation("fetching weeks", log_context):
        with log_timing("get_weeks_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                weeks = await uow.get_all_weeks()

            logger.info(
                "Weeks fetched successfully",
                count=len(weeks),
                **log_context,
            )
            return [
                WeekRead(
                    week_id=week.week_id,
                    week_number=week.week_number,
                    week_start_date=week.week_start_date,
                    week_end_date=week.week_end_date,
                )
                for week in weeks
            ]
