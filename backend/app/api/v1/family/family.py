"""
Family Endpoints
- Defines API endpoints for family and botanical group operations.
"""

from typing import List

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_codes import RESOURCE_NOT_FOUND
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.exception_handler import (
    ResourceNotFoundError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
)
from app.api.schemas.family.family_schema import BotanicalGroupSchema, FamilyInfoSchema
from app.api.services.family.family_unit_of_work import FamilyUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "/botanical-groups/",
    response_model=List[BotanicalGroupSchema],
    status_code=status.HTTP_200_OK,
    summary="List all botanical groups with their families",
)
@limiter.limit("20/minute")
async def list_botanical_groups_with_families(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> List[BotanicalGroupSchema]:
    """
    Retrieve all botanical groups along with their families and recommended rotation years.
    This data is used to populate the dropdown menu in the families tab.
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "list_botanical_groups",
    }
    logger.info("Attempting to list botanical groups", **log_context)

    async with safe_operation("retrieving botanical groups", log_context):
        async with FamilyUnitOfWork(db) as uow:
            with log_timing(
                "get_all_botanical_groups_from_uow",
                request_id=log_context["request_id"],
            ):
                botanical_groups = await uow.get_all_botanical_groups_with_families()

    logger.info(
        "Successfully retrieved botanical groups",
        count=len(botanical_groups),
        **log_context,
    )
    return [BotanicalGroupSchema.model_validate(bg) for bg in botanical_groups]


@router.get(
    "/{family_id}/info",
    response_model=FamilyInfoSchema,
    status_code=status.HTTP_200_OK,
    summary="Get all information for a family (pests, diseases, etc)",
)
@limiter.limit("20/minute")
async def get_family_info(
    request: Request,
    family_id: str,
    db: AsyncSession = Depends(get_db),
) -> FamilyInfoSchema:
    """
    Retrieve all information for a specific family, including pests, diseases, interventions, symptoms, and botanical group.
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_family_info",
        "family_id": family_id,
    }
    logger.info("Attempting to retrieve family info", **log_context)

    async with safe_operation("retrieving family information", log_context):
        async with FamilyUnitOfWork(db) as uow:
            with log_timing(
                "get_family_info_from_uow", request_id=log_context["request_id"]
            ):
                result = await uow.get_family_details(family_id)

        if result is None:
            logger.error(
                "Family not found",
                error_code=RESOURCE_NOT_FOUND,
                **log_context,
            )
            raise ResourceNotFoundError(resource_id=family_id, resource_type="Family")

        logger.info("Successfully retrieved family info", **log_context)
        return result
