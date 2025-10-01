"""
User Active Varieties Endpoints
- Provides endpoints to manage the varieties a user has marked as active.
"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import get_current_user
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.error_handler import safe_operation
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.schemas.user.user_active_varieties_schema import (
    UserActiveVarietyCreate,
    UserActiveVarietyListRead,
    UserActiveVarietyRead,
)
from app.api.services.user.user_active_varieties_unit_of_work import (
    UserActiveVarietiesUnitOfWork,
)

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=UserActiveVarietyListRead,
    status_code=status.HTTP_200_OK,
    summary="List active varieties",
    description="Return the varieties the authenticated user has marked as active.",
)
@limiter.limit("20/minute")
async def list_active_varieties(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> UserActiveVarietyListRead:
    log_context = {
        "user_id": str(current_user.user_id),
        "request_id": request_id_ctx_var.get(),
        "operation": "list_active_varieties",
    }
    logger.info("Listing user active varieties", **log_context)

    async with safe_operation("retrieving user active varieties", log_context):
        with log_timing(
            "list_active_varieties_endpoint",
            request_id=log_context["request_id"],
            user_id=log_context["user_id"],
        ):
            async with UserActiveVarietiesUnitOfWork(db) as uow:
                active_varieties = await uow.get_active_varieties(
                    str(current_user.user_id)
                )

        active_variety_reads = [
            UserActiveVarietyRead.model_validate(av) for av in active_varieties
        ]

        logger.info("User active varieties retrieved", **log_context)
        return UserActiveVarietyListRead(active_varieties=active_variety_reads)


@router.post(
    "",
    response_model=UserActiveVarietyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Activate a variety",
    description="Mark a variety as active for the authenticated user.",
)
@limiter.limit("15/minute")
async def activate_variety(
    payload: UserActiveVarietyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> UserActiveVarietyRead:
    log_context = {
        "user_id": str(current_user.user_id),
        "variety_id": str(payload.variety_id),
        "request_id": request_id_ctx_var.get(),
        "operation": "activate_variety",
    }
    logger.info("Activating user variety", **log_context)

    async with safe_operation("activating user active variety", log_context):
        with log_timing(
            "activate_variety_endpoint",
            request_id=log_context["request_id"],
            user_id=log_context["user_id"],
            variety_id=log_context["variety_id"],
        ):
            async with UserActiveVarietiesUnitOfWork(db) as uow:
                active_variety = await uow.activate_variety(
                    str(current_user.user_id), str(payload.variety_id)
                )

        logger.info("User variety activated", **log_context)
        return UserActiveVarietyRead.model_validate(active_variety)


@router.delete(
    "/{variety_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a variety",
    description="Remove a variety from the authenticated user's active list.",
)
@limiter.limit("15/minute")
async def deactivate_variety(
    variety_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> Response:
    log_context = {
        "user_id": str(current_user.user_id),
        "variety_id": variety_id,
        "request_id": request_id_ctx_var.get(),
        "operation": "deactivate_variety",
    }
    logger.info("Deactivating user variety", **log_context)

    async with safe_operation("deactivating user active variety", log_context):
        with log_timing(
            "deactivate_variety_endpoint",
            request_id=log_context["request_id"],
            user_id=log_context["user_id"],
            variety_id=log_context["variety_id"],
        ):
            async with UserActiveVarietiesUnitOfWork(db) as uow:
                await uow.deactivate_variety(str(current_user.user_id), variety_id)

        logger.info("User variety deactivated", **log_context)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
