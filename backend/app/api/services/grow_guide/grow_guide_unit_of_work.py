"""
Grow Guide Unit of Work
- Manages grow guide-related transactions as a single unit of work.
- Coordinates operations across grow guide repositories and ensures atomicity.
"""

from types import TracebackType
from typing import List, Optional, Type
from uuid import UUID

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.factories.variety_factory import VarietyFactory
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    DatabaseIntegrityError,
    ResourceNotFoundError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.models.grow_guide.variety_model import Variety
from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.variety_repository import VarietyRepository
from app.api.schemas.grow_guide.variety_schema import VarietyCreate, VarietyUpdate

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

    # Feed operations
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

    # Variety option operations
    @translate_db_exceptions
    async def get_variety_options(self) -> dict:
        """Get all options needed for variety creation/editing."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_variety_options_uow",
        }

        logger.info("Getting variety options", **log_context)

        with log_timing("uow_get_variety_options", request_id=self.request_id):
            lifecycles = await self.variety_repo.get_all_lifecycles()
            planting_conditions = await self.variety_repo.get_all_planting_conditions()
            frequencies = await self.variety_repo.get_all_frequencies()
            feeds = await self.variety_repo.get_all_feeds()
            weeks = await self.variety_repo.get_all_weeks()
            families = await self.variety_repo.get_all_families()

            return {
                "lifecycles": lifecycles,
                "planting_conditions": planting_conditions,
                "frequencies": frequencies,
                "feeds": feeds,
                "weeks": weeks,
                "families": families,
            }

    # Variety CRUD operations
    @translate_db_exceptions
    async def create_variety(
        self, variety_data: VarietyCreate, user_id: UUID
    ) -> Variety:
        """Create a new variety."""
        log_context = {
            "request_id": self.request_id,
            "operation": "create_variety_uow",
            "user_id": str(user_id),
            "variety_name": variety_data.variety_name,
        }

        logger.info("Creating variety", **log_context)

        with log_timing("uow_create_variety", request_id=self.request_id):
            # Check if variety name already exists for user
            name_exists = await self.variety_repo.variety_name_exists_for_user(
                user_id, variety_data.variety_name
            )
            if name_exists:
                raise BusinessLogicError(
                    message=f"Variety '{variety_data.variety_name}' already exists for this user",
                    status_code=409,
                )

            # Create variety using factory
            variety = VarietyFactory.create_variety(variety_data, user_id)
            created_variety = await self.variety_repo.create_variety(variety)

            # Create water days if provided
            if variety_data.water_days:
                water_days_data = [
                    {"day_id": wd.day_id} for wd in variety_data.water_days
                ]
                water_days = VarietyFactory.create_water_days(
                    created_variety.variety_id, water_days_data
                )
                await self.variety_repo.create_water_days(water_days)

            logger.info("Variety created successfully", **log_context)
            return created_variety

    @translate_db_exceptions
    async def get_variety(self, variety_id: UUID, user_id: UUID) -> Variety:
        """Get a variety by ID."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_variety_uow",
            "user_id": str(user_id),
            "variety_id": str(variety_id),
        }

        logger.info("Getting variety", **log_context)

        with log_timing("uow_get_variety", request_id=self.request_id):
            variety = await self.variety_repo.get_variety_by_id(variety_id, user_id)
            if not variety:
                raise ResourceNotFoundError("variety", str(variety_id))

            logger.info("Variety retrieved successfully", **log_context)
            return variety

    @translate_db_exceptions
    async def get_user_varieties(self, user_id: UUID) -> List[Variety]:
        """Get all varieties belonging to a user."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_user_varieties_uow",
            "user_id": str(user_id),
        }

        logger.info("Getting user varieties", **log_context)

        with log_timing("uow_get_user_varieties", request_id=self.request_id):
            varieties = await self.variety_repo.get_user_varieties(user_id)
            logger.info(
                "User varieties retrieved successfully",
                count=len(varieties),
                **log_context,
            )
            return varieties

    @translate_db_exceptions
    async def get_public_varieties(self) -> List[Variety]:
        """Get all public varieties."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_public_varieties_uow",
        }

        logger.info("Getting public varieties", **log_context)

        with log_timing("uow_get_public_varieties", request_id=self.request_id):
            varieties = await self.variety_repo.get_public_varieties()
            logger.info(
                "Public varieties retrieved successfully",
                count=len(varieties),
                **log_context,
            )
            return varieties

    @translate_db_exceptions
    async def update_variety(
        self, variety_id: UUID, variety_data: VarietyUpdate, user_id: UUID
    ) -> Variety:
        """Update an existing variety."""
        log_context = {
            "request_id": self.request_id,
            "operation": "update_variety_uow",
            "user_id": str(user_id),
            "variety_id": str(variety_id),
        }

        logger.info("Updating variety", **log_context)

        with log_timing("uow_update_variety", request_id=self.request_id):
            # Get existing variety
            variety = await self.variety_repo.get_variety_by_id(variety_id, user_id)
            if not variety:
                raise ResourceNotFoundError("variety", str(variety_id))

            # Check ownership
            if variety.owner_user_id != user_id:
                raise BusinessLogicError(
                    message="You can only update your own varieties",
                    status_code=403,
                )

            # Check if new name conflicts with existing varieties
            if (
                variety_data.variety_name
                and variety_data.variety_name != variety.variety_name
            ):
                name_exists = await self.variety_repo.variety_name_exists_for_user(
                    user_id, variety_data.variety_name, exclude_variety_id=variety_id
                )
                if name_exists:
                    raise BusinessLogicError(
                        message=f"Variety '{variety_data.variety_name}' already exists for this user",
                        status_code=409,
                    )

            # Update variety using factory
            updated_variety = VarietyFactory.update_variety(variety, variety_data)
            result = await self.variety_repo.update_variety(updated_variety)

            # Update water days if provided
            if variety_data.water_days is not None:
                # Delete existing water days
                await self.variety_repo.delete_water_days(variety_id)

                # Create new water days
                if variety_data.water_days:
                    water_days_data = [
                        {"day_id": wd.day_id} for wd in variety_data.water_days
                    ]
                    water_days = VarietyFactory.create_water_days(
                        variety_id, water_days_data
                    )
                    await self.variety_repo.create_water_days(water_days)

            logger.info("Variety updated successfully", **log_context)
            return result

    @translate_db_exceptions
    async def delete_variety(self, variety_id: UUID, user_id: UUID) -> bool:
        """Delete a variety."""
        log_context = {
            "request_id": self.request_id,
            "operation": "delete_variety_uow",
            "user_id": str(user_id),
            "variety_id": str(variety_id),
        }

        logger.info("Deleting variety", **log_context)

        with log_timing("uow_delete_variety", request_id=self.request_id):
            success = await self.variety_repo.delete_variety(variety_id, user_id)
            if not success:
                raise ResourceNotFoundError("variety", str(variety_id))

            logger.info("Variety deleted successfully", **log_context)
            return success
