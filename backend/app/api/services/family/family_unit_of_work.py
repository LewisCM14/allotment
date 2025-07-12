"""
Family Unit of Work
- Manages family-related transactions as a single unit of work.
- Coordinates operations across the FamilyRepository and ensures atomicity.
- Handles transaction management (commit/rollback) for family-related operations.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, List, Optional, Type

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.repositories.family.family_repository import FamilyRepository
from app.api.schemas.family.family_schema import FamilyInfoSchema

logger = structlog.get_logger()


class FamilyUnitOfWork:
    """Unit of Work for managing family-related transactions."""

    def __init__(self, db: AsyncSession):
        """Initialize the unit of work with a database session."""
        self.db = db
        self.family_repo = FamilyRepository(db)
        self.request_id = request_id_ctx_var.get()

    async def __aenter__(self) -> "FamilyUnitOfWork":
        """Enter the runtime context for the Unit of Work."""
        logger.debug(
            "Starting family unit of work",
            request_id=self.request_id,
            transaction="begin",
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context for the Unit of Work, handling commit/rollback."""
        log_context = {"request_id": self.request_id}

        if exc_type:
            if exc_value:
                sanitized_error = sanitize_error_message(str(exc_value))
                logger.warning(
                    "Rolling back family transaction due to error",
                    error=sanitized_error,
                    error_type=exc_type.__name__,
                    **log_context,
                )
            else:
                logger.warning(
                    "Rolling back family transaction due to unknown error",
                    error_type=str(exc_type),
                    **log_context,
                )
            await self.db.rollback()
            logger.debug(
                "Family transaction rolled back", transaction="rollback", **log_context
            )
        else:
            await self.db.commit()
            logger.debug(
                "Family transaction committed successfully (or no changes to commit for read)",
                transaction="commit",
                **log_context,
            )

    async def get_all_botanical_groups_with_families(self) -> List[BotanicalGroup]:
        """
        Retrieves all botanical groups with their families via the repository.
        """
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_botanical_groups_with_families",
        }
        logger.info("Starting operation to fetch botanical groups", **log_context)

        try:
            botanical_groups = (
                await self.family_repo.get_all_botanical_groups_with_families()
            )
            logger.info(
                "Successfully retrieved botanical groups",
                count=len(botanical_groups),
                **log_context,
            )
            return botanical_groups
        except Exception as e:
            logger.error(
                "Error retrieving botanical groups",
                error=str(e),
                **log_context,
            )
            raise

    async def get_family_details(self, family_id: Any) -> Optional[FamilyInfoSchema]:
        """
        Retrieves detailed information for a specific family.

        Args:
            family_id: The ID of the family to retrieve.

        Returns:
            A Pydantic schema containing detailed family information, or None if not found.
        """
        return await self.family_repo.get_family_info(family_id)
