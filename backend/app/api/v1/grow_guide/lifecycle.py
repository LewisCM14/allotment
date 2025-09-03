"""
Lifecycle Endpoints
- Provides API endpoints for lifecycle operations (read only).
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
from app.api.schemas.grow_guide.variety_schema import LifecycleRead
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=List[LifecycleRead],
    status_code=status.HTTP_200_OK,
    summary="Get available lifecycles",
    description="Get all available plant lifecycles for variety classification.",
)
@limiter.limit("10/minute")
async def get_lifecycles(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[LifecycleRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_lifecycles",
    }
    logger.info("Fetching available lifecycles", **log_context)

    async with safe_operation("fetching lifecycles", log_context):
        with log_timing("get_lifecycles_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                lifecycles = await uow.get_all_lifecycles()

            logger.info(
                "Lifecycles fetched successfully",
                count=len(lifecycles),
                **log_context,
            )
            return [
                LifecycleRead(
                    lifecycle_id=lifecycle.lifecycle_id,
                    lifecycle_name=lifecycle.lifecycle_name,
                    productivity_years=lifecycle.productivity_years,
                )
                for lifecycle in lifecycles
            ]
