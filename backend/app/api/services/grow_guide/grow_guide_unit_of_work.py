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
from app.api.models.grow_guide.calendar_model import Day, Month, Week
from app.api.models.grow_guide.guide_options_model import (
    Feed,
    Frequency,
    Lifecycle,
    PlantingConditions,
)
from app.api.models.grow_guide.variety_model import Variety
from app.api.repositories.family.family_repository import FamilyRepository
from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.month_repository import MonthRepository
from app.api.repositories.grow_guide.variety_repository import VarietyRepository
from app.api.repositories.grow_guide.week_repository import WeekRepository
from app.api.schemas.grow_guide.variety_schema import VarietyCreate, VarietyUpdate

logger = structlog.get_logger()


class GrowGuideUnitOfWork:
    """Unit of Work for managing grow guide-related transactions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.day_repo = DayRepository(db)
        self.variety_repo = VarietyRepository(db)
        self.week_repo = WeekRepository(db)
        self.month_repo = MonthRepository(db)
        self.family_repo = FamilyRepository(db)
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

    @translate_db_exceptions
    async def get_all_weeks(self) -> List[Week]:
        """Get all available weeks."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_weeks_uow",
        }

        logger.info("Getting all weeks", **log_context)

        with log_timing("uow_get_all_weeks", request_id=self.request_id):
            weeks = await self.week_repo.get_all_weeks()
            return weeks

    @translate_db_exceptions
    async def get_all_months(self) -> List[Month]:
        """Get all available months."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_months_uow",
        }

        logger.info("Getting all months", **log_context)

        with log_timing("uow_get_all_months", request_id=self.request_id):
            months = await self.month_repo.get_all_months()
            return months

    @translate_db_exceptions
    async def get_all_frequencies(self) -> List[Frequency]:
        """Get all available frequencies."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_frequencies_uow",
        }

        logger.info("Getting all frequencies", **log_context)

        with log_timing("uow_get_all_frequencies", request_id=self.request_id):
            frequencies = await self.variety_repo.get_all_frequencies()
            return frequencies

    @translate_db_exceptions
    async def get_all_lifecycles(self) -> List[Lifecycle]:
        """Get all available lifecycles."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_lifecycles_uow",
        }

        logger.info("Getting all lifecycles", **log_context)

        with log_timing("uow_get_all_lifecycles", request_id=self.request_id):
            lifecycles = await self.variety_repo.get_all_lifecycles()
            return lifecycles

    @translate_db_exceptions
    async def get_all_planting_conditions(self) -> List[PlantingConditions]:
        """Get all available planting conditions."""
        log_context = {
            "request_id": self.request_id,
            "operation": "get_all_planting_conditions_uow",
        }

        logger.info("Getting all planting conditions", **log_context)

        with log_timing("uow_get_all_planting_conditions", request_id=self.request_id):
            planting_conditions = await self.variety_repo.get_all_planting_conditions()
            return planting_conditions

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
            weeks = await self.week_repo.get_all_weeks()
            families = await self.family_repo.get_all_families()
            days = await self.day_repo.get_all_days()

            # Feed frequencies are restricted to weekly, fortnightly and yearly
            feed_frequency_names = {"weekly", "fortnightly", "yearly"}
            feed_frequencies = [
                f for f in frequencies if f.frequency_name in feed_frequency_names
            ]

            return {
                "lifecycles": lifecycles,
                "planting_conditions": planting_conditions,
                "frequencies": frequencies,
                "feed_frequencies": feed_frequencies,
                "feeds": feeds,
                "weeks": weeks,
                "families": families,
                "days": days,
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

            # Auto-generate water days from frequency defaults
            default_day_ids = await self.variety_repo.get_default_day_ids_for_frequency(
                created_variety.water_frequency_id
            )
            if not default_day_ids:
                raise BusinessLogicError(
                    message="No default watering days configured for selected water frequency",
                    status_code=422,
                )
            water_days_data = [{"day_id": d} for d in default_day_ids]
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

            # Capture pre-update water frequency to detect changes after mutation
            old_water_frequency_id = variety.water_frequency_id

            # Update variety using factory (mutates instance) then persist
            updated_variety = VarietyFactory.update_variety(variety, variety_data)
            await self.variety_repo.update_variety(updated_variety)

            # Regenerate water days only if water frequency provided AND actually changed
            if (
                variety_data.water_frequency_id is not None
                and variety_data.water_frequency_id != old_water_frequency_id
            ):
                await self.variety_repo.delete_water_days(variety_id)
                # At this point variety_data.water_frequency_id is not None and the factory
                # will have applied it to updated_variety; assert for type narrowing.
                assert updated_variety.water_frequency_id is not None, (
                    "water_frequency_id unexpectedly None after update"
                )
                default_day_ids = (
                    await self.variety_repo.get_default_day_ids_for_frequency(
                        updated_variety.water_frequency_id
                    )
                )
                if not default_day_ids:
                    raise BusinessLogicError(
                        message="No default watering days configured for selected water frequency",
                        status_code=422,
                    )
                water_days_data = [{"day_id": d} for d in default_day_ids]
                water_days = VarietyFactory.create_water_days(
                    variety_id, water_days_data
                )
                await self.variety_repo.create_water_days(water_days)
                # IMPORTANT: After the bulk delete + insert, SQLAlchemy's in-memory relationship
                # collection still contains the previously loaded (now deleted) VarietyWaterDay
                # objects because the bulk DELETE does not synchronize the session state.
                # Assign the freshly created list so that subsequent serialization (before commit)
                # reflects the regenerated set rather than the stale one.
                updated_variety.water_days = water_days

            # Return the mutated instance; API layer does an explicit get_variety for full serialization.
            logger.info("Variety updated successfully", **log_context)
            return updated_variety

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

    @translate_db_exceptions
    async def copy_public_variety_to_user(
        self, public_variety_id: UUID, user_id: UUID
    ) -> Variety:
        """Copy a public variety to belong to the specified user.

        Steps:
        - Load the source public variety
        - Create a VarietyCreate payload mirroring the source (is_public set to False)
        - Ensure the new variety name is unique for the user by auto-suffixing when needed
        - Delegate to create_variety for validation and water-day generation
        """
        log_context = {
            "request_id": self.request_id,
            "operation": "copy_public_variety_to_user_uow",
            "user_id": str(user_id),
            "public_variety_id": str(public_variety_id),
        }

        logger.info("Copying public variety to user", **log_context)

        with log_timing("uow_copy_public_variety_to_user", request_id=self.request_id):
            # Ensure the source variety exists and is public
            source = await self.variety_repo.get_public_variety_by_id(public_variety_id)
            if not source:
                raise ResourceNotFoundError("variety", str(public_variety_id))

            # Determine a unique name for the copied variety for this user using
            # a deterministic single-query approach (no async while loops).
            base_name = source.variety_name
            existing_names = set(
                await self.variety_repo.get_user_variety_names_for_copying(
                    user_id, base_name
                )
            )

            def next_copy_name(base: str, taken: set[str]) -> str:
                # If base isn't taken, use it directly
                if base not in taken:
                    return base

                # Build set of used copy indices: 1 is "(copy)", >=2 is "(copy N)"
                used: set[int] = set()
                copy1 = f"{base} (copy)"
                if copy1 in taken:
                    used.add(1)
                prefix = f"{base} (copy "
                suffix = ")"
                for name in taken:
                    if name.startswith(prefix) and name.endswith(suffix):
                        num_part = name[len(prefix) : -len(suffix)]
                        if num_part.isdigit():
                            used.add(int(num_part))

                # Smallest positive integer not in used
                i = 1
                while i in used:
                    i += 1
                return copy1 if i == 1 else f"{base} (copy {i})"

            candidate_name = next_copy_name(base_name, existing_names)

            # Build creation schema from source fields with the resolved unique name
            create_payload = VarietyCreate(
                variety_name=candidate_name,
                family_id=source.family_id,
                lifecycle_id=source.lifecycle_id,
                sow_week_start_id=source.sow_week_start_id,
                sow_week_end_id=source.sow_week_end_id,
                transplant_week_start_id=source.transplant_week_start_id,
                transplant_week_end_id=source.transplant_week_end_id,
                planting_conditions_id=source.planting_conditions_id,
                soil_ph=source.soil_ph,
                row_width_cm=source.row_width_cm,
                plant_depth_cm=source.plant_depth_cm,
                plant_space_cm=source.plant_space_cm,
                feed_id=source.feed_id,
                feed_week_start_id=source.feed_week_start_id,
                feed_frequency_id=source.feed_frequency_id,
                water_frequency_id=source.water_frequency_id,
                high_temp_degrees=source.high_temp_degrees,
                high_temp_water_frequency_id=source.high_temp_water_frequency_id,
                harvest_week_start_id=source.harvest_week_start_id,
                harvest_week_end_id=source.harvest_week_end_id,
                prune_week_start_id=source.prune_week_start_id,
                prune_week_end_id=source.prune_week_end_id,
                notes=source.notes,
                is_public=False,
            )

            created = await self.create_variety(create_payload, user_id)
            logger.info("Public variety copied successfully", **log_context)
            return created
