"""
Family Endpoints
"""

from typing import List

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.schemas.family.family_schema import BotanicalGroupSchema
from app.api.services.family.family_unit_of_work import FamilyUnitOfWork

router = APIRouter(prefix="/families", tags=["Families"])
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
) -> List[BotanicalGroup]:
    """
    Retrieve all botanical groups along with their families and recommended rotation years.
    This data is used to populate the dropdown menu in the families tab.
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "list_botanical_groups",
    }
    logger.info("Attempting to list botanical groups", **log_context)

    try:
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
        return botanical_groups
    except BaseApplicationError as exc:
        logger.warning(
            f"Failed to list botanical groups: {type(exc).__name__}",
            error=str(exc),
            error_code=exc.error_code,
            status_code=exc.status_code,
            **log_context,
        )
        raise
    except Exception as exc:
        sanitized_error = sanitize_error_message(str(exc))
        logger.error(
            "Unhandled exception during listing botanical groups",
            error=sanitized_error,
            error_type=type(exc).__name__,
            **log_context,
        )
        raise BusinessLogicError(
            message="An unexpected error occurred while retrieving botanical groups.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
