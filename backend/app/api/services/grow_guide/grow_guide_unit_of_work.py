"""
Grow Guide Unit of Work
- Manages grow guide-related transactions as a single unit of work.
- Coordinates operations across grow guide repositories and ensures atomicity.
"""

from types import TracebackType
from typing import List, Optional, Type

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.exception_handler import DatabaseIntegrityError
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.variety_repository import VarietyRepository

logger = structlog.get_logger()


class GrowGuideUnitOfWork:
    """Unit of Work for managing grow guide-related transactions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.day_repo = DayRepository(db)
        self.variety_repo = VarietyRepository(db)
        self.request_id = request_id_ctx_var.get()

    async def __aenter__(self) -> "GrowGuideUnitOfWork":
        """Enter the runtime context for the Unit of Work."""
        logger.debug(
            "Starting grow guide unit of work",
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
        """Exit the runtime context for the Unit of Work."""
        log_context = {"request_id": self.request_id}

        if exc_type:
            if exc_value:
                sanitized_error = sanitize_error_message(str(exc_value))
                logger.warning(
                    "Rolling back transaction due to error",
                    error=sanitized_error,
                    error_type=exc_type.__name__,
                    **log_context,
                )
            else:
                logger.warning(
                    "Rolling back transaction due to unknown error",
                    error_type=str(exc_type),
                    **log_context,
                )
            await self.db.rollback()
            logger.debug(
                "Transaction rolled back", transaction="rollback", **log_context
            )
        else:
            try:
                with log_timing("db_commit"):
                    await self.db.commit()
                    logger.debug(
                        "Transaction committed successfully",
                        transaction="commit",
                        **log_context,
                    )
            except IntegrityError as ie:
                sanitized_error = sanitize_error_message(str(ie))
                logger.error(
                    "Database integrity error during commit",
                    error=sanitized_error,
                    error_type="IntegrityError",
                    exc_info=True,
                )
                raise DatabaseIntegrityError(
                    message="Database integrity constraint violated"
                )

    @translate_db_exceptions
    async def get_all_feeds(self) -> List[Feed]:
        """Get all available feed types."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_feeds_uow",
        }

        logger.info("Getting all feed types", **log_context)

        with log_timing("uow_get_all_feeds", request_id=self.request_id):
            feeds = await self.variety_repo.get_all_feeds()
            return feeds

    @translate_db_exceptions
    async def get_all_days(self) -> List[Day]:
        """Get all available days."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_days_uow",
        }

        logger.info("Getting all days", **log_context)

        with log_timing("uow_get_all_days", request_id=self.request_id):
            days = await self.day_repo.get_all_days()
            return days
