"""
Month Endpoints
- Provides API endpoints for month operations (read only).
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
from app.api.schemas.grow_guide.variety_schema import MonthRead
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=List[MonthRead],
    status_code=status.HTTP_200_OK,
    summary="Get available months",
    description="Get all available months for plant scheduling preferences.",
)
@limiter.limit("10/minute")
async def get_months(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[MonthRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_months",
    }
    logger.info("Fetching available months", **log_context)

    async with safe_operation("fetching months", log_context):
        with log_timing("get_months_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                months = await uow.get_all_months()

            logger.info(
                "Months fetched successfully",
                count=len(months),
                **log_context,
            )
            return [MonthRead.model_validate(month) for month in months]
