"""
Variety Endpoints
- Provides API endpoints for variety CRUD operations.
- Handles grow guide management for authenticated users.
"""

from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import get_current_user
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.logging_middleware import request_id_ctx_var
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
    "/metadata",
    response_model=VarietyOptionsRead,
    status_code=status.HTTP_200_OK,
    summary="Get variety metadata",
    description=(
        "Get all reference metadata required for creating or editing a variety, "
        "including lifecycles, planting conditions, frequencies, feeds, weeks, families, and days."
    ),
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
            return VarietyRead.model_validate(complete_variety)


@router.get(
    "",
    response_model=List[VarietyListRead],
    status_code=status.HTTP_200_OK,
    summary="List varieties",
    description=(
        "List varieties. Use the 'visibility' query parameter to choose between"
        " a user's own varieties (visibility=user, default) or public varieties"
        " (visibility=public)."
    ),
)
@limiter.limit("30/minute")
async def list_varieties(
    request: Request,
    visibility: str = Query("user", pattern="^(user|public)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VarietyListRead]:
    operation = (
        "get_public_varieties" if visibility == "public" else "get_user_varieties"
    )
    timing_key = (
        "get_public_varieties_endpoint"
        if visibility == "public"
        else "get_user_varieties_endpoint"
    )
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": operation,
        "user_id": str(current_user.user_id),
        "visibility": visibility,
    }
    logger.info("Fetching varieties", **log_context)

    async with safe_operation("fetching varieties", log_context):
        with log_timing(timing_key, request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                if visibility == "public":
                    varieties = await uow.get_public_varieties()
                else:
                    varieties = await uow.get_user_varieties(current_user.user_id)

            logger.info(
                "Varieties fetched successfully",
                count=len(varieties),
                **log_context,
            )
            return [VarietyListRead.model_validate(v) for v in varieties]


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
            return VarietyRead.model_validate(variety)


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
            return VarietyRead.model_validate(complete_variety)


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


@router.post(
    "/{variety_id}/copy",
    response_model=VarietyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Copy public variety",
    description=("Copy a public variety to your account."),
)
@limiter.limit("10/minute")
async def copy_variety(
    request: Request,
    variety_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VarietyRead:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "copy_public_variety",
        "user_id": str(current_user.user_id),
        "variety_id": str(variety_id),
    }
    logger.info("Copying public variety", **log_context)

    async with safe_operation("copying public variety", log_context):
        with log_timing("copy_variety_endpoint", request_id=log_context["request_id"]):
            async with GrowGuideUnitOfWork(db) as uow:
                created = await uow.copy_public_variety_to_user(
                    variety_id, current_user.user_id
                )

            logger.info("Variety copied successfully", **log_context)
            async with GrowGuideUnitOfWork(db) as uow2:
                complete = await uow2.get_variety(
                    created.variety_id, current_user.user_id
                )
            return VarietyRead.model_validate(complete)
