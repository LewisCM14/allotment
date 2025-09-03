"""
Planting Conditions Endpoints
- Provides API endpoints for planting conditions operations (read only).
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
from app.api.schemas.grow_guide.variety_schema import PlantingConditionsRead
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=List[PlantingConditionsRead],
    status_code=status.HTTP_200_OK,
    summary="Get available planting conditions",
    description="Get all available planting conditions for variety configuration.",
)
@limiter.limit("10/minute")
async def get_planting_conditions(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[PlantingConditionsRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_planting_conditions",
    }
    logger.info("Fetching available planting conditions", **log_context)

    async with safe_operation("fetching planting conditions", log_context):
        with log_timing("get_planting_conditions_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                planting_conditions = await uow.get_all_planting_conditions()

            logger.info(
                "Planting conditions fetched successfully",
                count=len(planting_conditions),
                **log_context,
            )
            return [
                PlantingConditionsRead(
                    planting_condition_id=condition.planting_condition_id,
                    planting_condition=condition.planting_condition,
                )
                for condition in planting_conditions
            ]
