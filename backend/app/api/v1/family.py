"""
Family Endpoints
- Defines API endpoints for family and botanical group operations.
"""

from typing import Any, List
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.database import get_db
from app.api.core.limiter import limiter
from app.api.core.logging import log_timing
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
    ResourceNotFoundError,  # Add ResourceNotFoundError
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.family.botanical_group_model import BotanicalGroup
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
                botanical_groups: List[
                    BotanicalGroup
                ] = await uow.get_all_botanical_groups_with_families()
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
) -> Any:
    """
    Retrieve all information for a specific family, including pests, diseases, interventions, and symptoms.
    """
    log_context = {
        "request_id": request_id_ctx_var.get(),
        "operation": "get_family_info",
        "family_id": family_id,
    }
    logger.info("Attempting to retrieve family info", **log_context)
    from app.api.middleware.error_handler import safe_operation

    async with safe_operation(
        "get_family_info", log_context, status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        with log_timing(
            "get_family_info_from_uow", request_id=log_context["request_id"]
        ):
            async with FamilyUnitOfWork(db) as uow:
                result = await uow.get_family_info(family_id)
        logger.info("Successfully retrieved family info", **log_context)
        if result is None:
            # If result is None, it means either the family_id format was invalid
            # or a validly formatted family_id was not found in the database.
            # Attempt to parse the family_id string to determine which case it is.
            try:
                family_uuid_for_response = UUID(family_id)
            except ValueError:
                # family_id string is not a valid UUID format.
                # Raise ResourceNotFoundError, which will be handled by ExceptionHandlingMiddleware
                # and result in an HTTP 404 response.
                raise ResourceNotFoundError(
                    message=f"Family with ID '{family_id}' not found or ID is invalid."
                )

            # family_id string was a valid UUID format, but the family was not found in the DB.
            # Return an empty FamilyInfoSchema with the valid ID.
            return FamilyInfoSchema(
                id=family_uuid_for_response,
                name="",
                pests=[],
                diseases=[],
                interventions=[],
                symptoms=[],
            )
        return result


# Add this method to FamilyUnitOfWork if missing:
# async def get_all_botanical_groups_with_families(self) -> List[BotanicalGroup]:
#     return await self.family_repo.get_all_botanical_groups_with_families()
