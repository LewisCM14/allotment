"""
User Allotment Endpoints
- Provides API endpoints for user allotment operations (create, read, update).
"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth import get_current_user
from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.schemas.user.user_allotment_schema import (
    UserAllotmentCreate,
    UserAllotmentRead,
    UserAllotmentUpdate,
)
from app.api.services.user.user_unit_of_work import UserUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.post(
    "",
    response_model=UserAllotmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create user allotment",
    description="Create an allotment for the authenticated user.",
)
@limiter.limit("3/minute")
async def create_user_allotment(
    request: Request,
    allotment: UserAllotmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> UserAllotmentRead:
    log_context = {
        "user_id": str(current_user.user_id),
        "request_id": request_id_ctx_var.get(),
        "operation": "create_user_allotment",
    }
    logger.info("Attempting to create user allotment", **log_context)
    async with UserUnitOfWork(db) as uow:
        result = await uow.create_user_allotment(current_user.user_id, allotment)
    logger.info("User allotment created", **log_context)
    return UserAllotmentRead.model_validate(result)


@router.get(
    "",
    response_model=UserAllotmentRead,
    status_code=status.HTTP_200_OK,
    summary="Get user allotment",
    description="Get the allotment for the authenticated user.",
)
@limiter.limit("10/minute")
async def get_user_allotment(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> UserAllotmentRead:
    log_context = {
        "user_id": str(current_user.user_id),
        "request_id": request_id_ctx_var.get(),
        "operation": "get_user_allotment",
    }
    logger.info("Fetching user allotment", **log_context)
    async with UserUnitOfWork(db) as uow:
        result = await uow.get_user_allotment(current_user.user_id)
    if not result:
        logger.warning("User allotment not found", **log_context)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User allotment not found.",
        )
    logger.info("User allotment fetched", **log_context)
    return UserAllotmentRead.model_validate(result)


@router.put(
    "",
    response_model=UserAllotmentRead,
    status_code=status.HTTP_200_OK,
    summary="Update user allotment",
    description="Update the allotment for the authenticated user.",
)
@limiter.limit("3/minute")
async def update_user_allotment(
    request: Request,
    allotment: UserAllotmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
) -> UserAllotmentRead:
    log_context = {
        "user_id": str(current_user.user_id),
        "request_id": request_id_ctx_var.get(),
        "operation": "update_user_allotment",
    }
    logger.info("Attempting to update user allotment", **log_context)
    async with UserUnitOfWork(db) as uow:
        result = await uow.update_user_allotment(current_user.user_id, allotment)
    logger.info("User allotment updated", **log_context)
    return UserAllotmentRead.model_validate(result)
