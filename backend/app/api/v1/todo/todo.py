"""
ToDo Endpoints
- Provides API endpoints for weekly and daily task retrieval.
"""

from typing import Optional

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
from app.api.schemas.todo.weekly_todo_schema import WeeklyTodoRead
from app.api.services.todo.weekly_todo import WeeklyTodoUnitOfWork

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "/weekly",
    response_model=WeeklyTodoRead,
    status_code=status.HTTP_200_OK,
    summary="Get weekly todo list",
    description=(
        "Get weekly and daily tasks for the authenticated user's active varieties. "
        "Optionally specify a week number (1-52), otherwise returns tasks for the current week."
    ),
)
@limiter.limit("30/minute")
async def get_weekly_todo(
    request: Request,
    week_number: Optional[int] = Query(
        None,
        ge=1,
        le=52,
        description="Week number (1-52). If not provided, uses current week.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyTodoRead:
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_weekly_todo",
        "user_id": str(current_user.user_id),
        "week_number": week_number,
    }
    logger.info("Fetching weekly todo", **log_context)

    async with safe_operation("fetching weekly todo", log_context):
        with log_timing(
            "get_weekly_todo_endpoint", request_id=log_context["request_id"]
        ):
            async with WeeklyTodoUnitOfWork(db) as uow:
                todo_data = await uow.get_weekly_todo(
                    str(current_user.user_id), week_number
                )

            logger.info("Weekly todo fetched successfully", **log_context)
            return WeeklyTodoRead(**todo_data)
