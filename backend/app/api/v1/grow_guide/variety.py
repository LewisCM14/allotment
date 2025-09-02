"""
Variety Endpoints
- Provides API endpoints for variety CRUD operations.
- Handles grow guide management for authenticated users.
"""

from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import get_current_user
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.models.grow_guide.variety_model import Variety
from app.api.models.user.user_model import User
from app.api.schemas.grow_guide.variety_schema import (
    VarietyCreate,
    VarietyListRead,
    VarietyOptionsRead,
    VarietyRead,
    VarietyUpdate,
)
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "/options",
    response_model=VarietyOptionsRead,
    status_code=status.HTTP_200_OK,
    summary="Get variety creation options",
    description="Get all available options for variety creation and editing.",
)
@limiter.limit("30/minute")
async def get_variety_options(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VarietyOptionsRead:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_variety_options",
        "user_id": str(current_user.user_id),
    }
    logger.info("Fetching variety options", **log_context)

    async with safe_operation("fetching variety options", log_context):
        with log_timing(
            "get_variety_options_endpoint", request_id=log_context["request_id"]
        ):
            async with GrowGuideUnitOfWork(db) as uow:
                options = await uow.get_variety_options()

            logger.info("Variety options fetched successfully", **log_context)
            return VarietyOptionsRead(**options)


@router.post(
    "",
    response_model=VarietyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new variety",
    description="Create a new grow guide variety for the authenticated user.",
)
@limiter.limit("10/minute")
async def create_variety(
    request: Request,
    variety_data: VarietyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VarietyRead:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "create_variety",
        "user_id": str(current_user.user_id),
        "variety_name": variety_data.variety_name,
    }
    logger.info("Creating variety", **log_context)

    async with safe_operation("creating variety", log_context):
        with log_timing(
            "create_variety_endpoint", request_id=log_context["request_id"]
        ):
            async with GrowGuideUnitOfWork(db) as uow:
                variety = await uow.create_variety(variety_data, current_user.user_id)
                # Fetch the complete variety with all relationships
                complete_variety = await uow.get_variety(
                    variety.variety_id, current_user.user_id
                )

            logger.info("Variety created successfully", **log_context)
            return _convert_variety_to_read_schema(complete_variety)


@router.get(
    "",
    response_model=List[VarietyListRead],
    status_code=status.HTTP_200_OK,
    summary="Get user varieties",
    description="Get all varieties belonging to the authenticated user.",
)
@limiter.limit("30/minute")
async def get_user_varieties(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VarietyListRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_user_varieties",
        "user_id": str(current_user.user_id),
    }
    logger.info("Fetching user varieties", **log_context)

    async with safe_operation("fetching user varieties", log_context):
        with log_timing(
            "get_user_varieties_endpoint", request_id=log_context["request_id"]
        ):
            async with GrowGuideUnitOfWork(db) as uow:
                varieties = await uow.get_user_varieties(current_user.user_id)

            logger.info(
                "User varieties fetched successfully",
                count=len(varieties),
                **log_context,
            )
            return [
                VarietyListRead(
                    variety_id=v.variety_id,
                    variety_name=v.variety_name,
                    lifecycle_name=v.lifecycle.lifecycle_name,
                    is_public=v.is_public,
                    last_updated=v.last_updated.isoformat(),
                )
                for v in varieties
            ]


@router.get(
    "/public",
    response_model=List[VarietyListRead],
    status_code=status.HTTP_200_OK,
    summary="Get public varieties",
    description="Get all public varieties available to all users.",
)
@limiter.limit("30/minute")
async def get_public_varieties(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VarietyListRead]:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_public_varieties",
        "user_id": str(current_user.user_id),
    }
    logger.info("Fetching public varieties", **log_context)

    async with safe_operation("fetching public varieties", log_context):
        with log_timing(
            "get_public_varieties_endpoint", request_id=log_context["request_id"]
        ):
            async with GrowGuideUnitOfWork(db) as uow:
                varieties = await uow.get_public_varieties()

            logger.info(
                "Public varieties fetched successfully",
                count=len(varieties),
                **log_context,
            )
            return [
                VarietyListRead(
                    variety_id=v.variety_id,
                    variety_name=v.variety_name,
                    lifecycle_name=v.lifecycle.lifecycle_name,
                    is_public=v.is_public,
                    last_updated=v.last_updated.isoformat(),
                )
                for v in varieties
            ]


@router.get(
    "/{variety_id}",
    response_model=VarietyRead,
    status_code=status.HTTP_200_OK,
    summary="Get variety by ID",
    description="Get a specific variety by ID. Must be owned by user or be public.",
)
@limiter.limit("60/minute")
async def get_variety(
    request: Request,
    variety_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VarietyRead:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_variety",
        "user_id": str(current_user.user_id),
        "variety_id": str(variety_id),
    }
    logger.info("Fetching variety", **log_context)

    async with safe_operation("fetching variety", log_context):
        with log_timing("get_variety_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                variety = await uow.get_variety(variety_id, current_user.user_id)

            logger.info("Variety fetched successfully", **log_context)
            return _convert_variety_to_read_schema(variety)


@router.put(
    "/{variety_id}",
    response_model=VarietyRead,
    status_code=status.HTTP_200_OK,
    summary="Update variety",
    description="Update an existing variety. Only the owner can update.",
)
@limiter.limit("10/minute")
async def update_variety(
    request: Request,
    variety_id: UUID,
    variety_data: VarietyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VarietyRead:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "update_variety",
        "user_id": str(current_user.user_id),
        "variety_id": str(variety_id),
    }
    logger.info("Updating variety", **log_context)

    async with safe_operation("updating variety", log_context):
        with log_timing(
            "update_variety_endpoint", request_id=log_context["request_id"]
        ):
            async with GrowGuideUnitOfWork(db) as uow:
                variety = await uow.update_variety(
                    variety_id, variety_data, current_user.user_id
                )
                # Fetch the complete updated variety with all relationships
                complete_variety = await uow.get_variety(
                    variety.variety_id, current_user.user_id
                )

            logger.info("Variety updated successfully", **log_context)
            return _convert_variety_to_read_schema(complete_variety)


@router.delete(
    "/{variety_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete variety",
    description="Delete a variety. Only the owner can delete.",
)
@limiter.limit("10/minute")
async def delete_variety(
    request: Request,
    variety_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "delete_variety",
        "user_id": str(current_user.user_id),
        "variety_id": str(variety_id),
    }
    logger.info("Deleting variety", **log_context)

    async with safe_operation("deleting variety", log_context):
        with log_timing(
            "delete_variety_endpoint", request_id=log_context["request_id"]
        ):
            async with GrowGuideUnitOfWork(db) as uow:
                await uow.delete_variety(variety_id, current_user.user_id)

            logger.info("Variety deleted successfully", **log_context)


def _convert_variety_to_read_schema(variety: Variety) -> VarietyRead:
    """Convert a Variety model to VarietyRead schema."""
    from app.api.schemas.grow_guide.variety_schema import (
        FamilyRead,
        FeedRead,
        FrequencyRead,
        LifecycleRead,
        PlantingConditionsRead,
        VarietyWaterDayRead,
    )

    return VarietyRead(
        variety_id=variety.variety_id,
        variety_name=variety.variety_name,
        owner_user_id=variety.owner_user_id,
        family=FamilyRead(
            family_id=variety.family.family_id,
            family_name=variety.family.family_name,
        )
        if variety.family
        else None,
        lifecycle=LifecycleRead(
            lifecycle_id=variety.lifecycle.lifecycle_id,
            lifecycle_name=variety.lifecycle.lifecycle_name,
            productivity_years=variety.lifecycle.productivity_years,
        ),
        planting_conditions=PlantingConditionsRead(
            planting_condition_id=variety.planting_conditions.planting_condition_id,
            planting_condition=variety.planting_conditions.planting_condition,
        ),
        sow_week_start_id=variety.sow_week_start_id,
        sow_week_end_id=variety.sow_week_end_id,
        transplant_week_start_id=variety.transplant_week_start_id,
        transplant_week_end_id=variety.transplant_week_end_id,
        soil_ph=variety.soil_ph,
        row_width_cm=variety.row_width_cm,
        plant_depth_cm=variety.plant_depth_cm,
        plant_space_cm=variety.plant_space_cm,
        feed=FeedRead(
            feed_id=variety.feed.feed_id,
            feed_name=variety.feed.feed_name,
        )
        if variety.feed
        else None,
        feed_week_start_id=variety.feed_week_start_id,
        feed_frequency=FrequencyRead(
            frequency_id=variety.feed_frequency.frequency_id,
            frequency_name=variety.feed_frequency.frequency_name,
            frequency_days_per_year=variety.feed_frequency.frequency_days_per_year,
        )
        if variety.feed_frequency
        else None,
        water_frequency=FrequencyRead(
            frequency_id=variety.water_frequency.frequency_id,
            frequency_name=variety.water_frequency.frequency_name,
            frequency_days_per_year=variety.water_frequency.frequency_days_per_year,
        )
        if variety.water_frequency
        else None,
        high_temp_degrees=variety.high_temp_degrees,
        high_temp_water_frequency=FrequencyRead(
            frequency_id=variety.high_temp_water_frequency.frequency_id,
            frequency_name=variety.high_temp_water_frequency.frequency_name,
            frequency_days_per_year=variety.high_temp_water_frequency.frequency_days_per_year,
        )
        if variety.high_temp_water_frequency
        else None,
        harvest_week_start_id=variety.harvest_week_start_id,
        harvest_week_end_id=variety.harvest_week_end_id,
        prune_week_start_id=variety.prune_week_start_id,
        prune_week_end_id=variety.prune_week_end_id,
        notes=variety.notes,
        is_public=variety.is_public,
        last_updated=variety.last_updated.isoformat(),
        water_days=[
            VarietyWaterDayRead(
                day_id=wd.day_id,
                day_name=wd.day.day_name,
            )
            for wd in variety.water_days
        ],
    )
