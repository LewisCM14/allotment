"""
Frequency Endpoints
- Provides API endpoints for frequency operations (read only).
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
from app.api.schemas.grow_guide.variety_schema import FrequencyRead
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=List[FrequencyRead],
    status_code=status.HTTP_200_OK,
    summary="Get available frequencies",
    description="Get all available frequencies for plant watering and feeding preferences.",
)
@limiter.limit("10/minute")
async def get_frequencies(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[FrequencyRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_frequencies",
    }
    logger.info("Fetching available frequencies", **log_context)

    async with safe_operation("fetching frequencies", log_context):
        with log_timing(
            "get_frequencies_endpoint", request_id=log_context["request_id"]
        ):
            async with GrowGuideUnitOfWork(db) as uow:
                frequencies = await uow.get_all_frequencies()

            logger.info(
                "Frequencies fetched successfully",
                count=len(frequencies),
                **log_context,
            )
            return [
                FrequencyRead.model_validate(frequency) for frequency in frequencies
            ]
