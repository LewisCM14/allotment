"""
Variety Repository
- Encapsulate the logic required to access the: Variety, Variety Water Day, Planting Conditions, Feed, Lifecycle and Frequency tables.
"""

from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import (
    Feed,
    Frequency,
    FrequencyDefaultDay,
    Lifecycle,
    PlantingConditions,
)
from app.api.models.grow_guide.variety_model import Variety, VarietyWaterDay
from app.api.models.user.user_model import UserActiveVariety

logger = structlog.get_logger()


class VarietyRepository:
    """Variety repository for database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.request_id = request_id_ctx_var.get()

    @translate_db_exceptions
    async def get_all_feeds(self) -> List[Feed]:
        """Get all available feed types."""
        with log_timing("db_get_all_feeds", request_id=self.request_id):
            result = await self.db.execute(select(Feed).order_by(Feed.feed_name))
            return list(result.scalars().all())

    @translate_db_exceptions
    async def get_all_lifecycles(self) -> List[Lifecycle]:
        """Get all available lifecycle types."""
        with log_timing("db_get_all_lifecycles", request_id=self.request_id):
            result = await self.db.execute(
                select(Lifecycle).order_by(Lifecycle.lifecycle_name)
            )
            return list(result.scalars().all())

    @translate_db_exceptions
    async def get_all_planting_conditions(self) -> List[PlantingConditions]:
        """Get all available planting conditions."""
        with log_timing("db_get_all_planting_conditions", request_id=self.request_id):
            result = await self.db.execute(
                select(PlantingConditions).order_by(
                    PlantingConditions.planting_condition
                )
            )
            return list(result.scalars().all())

    @translate_db_exceptions
    async def get_all_frequencies(self) -> List[Frequency]:
        """Get all available frequency types."""
        with log_timing("db_get_all_frequencies", request_id=self.request_id):
            result = await self.db.execute(
                select(Frequency).order_by(Frequency.frequency_name)
            )
            return list(result.scalars().all())

    @translate_db_exceptions
    async def create_variety(self, variety: Variety) -> Variety:
        """Create a new variety."""
        with log_timing("db_create_variety", request_id=self.request_id):
            self.db.add(variety)
            await self.db.flush()
            await self.db.refresh(variety)
            return variety

    @translate_db_exceptions
    async def get_variety_by_id(
        self, variety_id: UUID, user_id: UUID
    ) -> Optional[Variety]:
        """Get a variety by ID, ensuring it belongs to the user or is public."""
        with log_timing("db_get_variety_by_id", request_id=self.request_id):
            stmt = (
                select(Variety)
                .options(
                    selectinload(Variety.family),
                    selectinload(Variety.lifecycle),
                    selectinload(Variety.planting_conditions),
                    selectinload(Variety.feed),
                    selectinload(Variety.feed_frequency),
                    selectinload(Variety.water_frequency),
                    selectinload(Variety.high_temp_water_frequency),
                    selectinload(Variety.water_days).selectinload(VarietyWaterDay.day),
                )
                .where(
                    Variety.variety_id == variety_id,
                    (Variety.owner_user_id == user_id) | (Variety.is_public),
                )
            )
            result = await self.db.execute(stmt)
            variety = result.scalar_one_or_none()

            if variety is None:
                return None

            is_active = False
            if variety.owner_user_id == user_id:
                active_stmt = (
                    select(func.count(UserActiveVariety.variety_id))
                    .where(
                        UserActiveVariety.user_id == user_id,
                        UserActiveVariety.variety_id == variety.variety_id,
                    )
                    .limit(1)
                )
                active_result = await self.db.execute(active_stmt)
                is_active = (active_result.scalar_one_or_none() or 0) > 0

            setattr(variety, "is_active", is_active)
            return variety

    @translate_db_exceptions
    async def get_variety_owned_by_user(
        self, variety_id: UUID, user_id: UUID
    ) -> Optional[Variety]:
        """Return a variety only if it is owned by the specified user."""
        with log_timing("db_get_variety_owned_by_user", request_id=self.request_id):
            stmt = select(Variety).where(
                Variety.variety_id == variety_id,
                Variety.owner_user_id == user_id,
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

    @translate_db_exceptions
    async def get_user_varieties(self, user_id: UUID) -> List[Variety]:
        """Get all varieties belonging to a user."""
        with log_timing("db_get_user_varieties", request_id=self.request_id):
            active_count_subquery = (
                select(func.count(UserActiveVariety.variety_id))
                .where(
                    UserActiveVariety.user_id == user_id,
                    UserActiveVariety.variety_id == Variety.variety_id,
                )
                .correlate(Variety)
                .scalar_subquery()
            )

            stmt = (
                select(Variety, active_count_subquery.label("active_variety_count"))
                .options(
                    selectinload(Variety.lifecycle),
                    selectinload(Variety.family),  # eager load family for list view
                )
                .where(Variety.owner_user_id == user_id)
                .order_by(Variety.variety_name)
            )
            result = await self.db.execute(stmt)
            rows = result.unique().all()

            varieties: List[Variety] = []
            for variety, active_variety_count in rows:
                setattr(variety, "is_active", (active_variety_count or 0) > 0)
                varieties.append(variety)
            return varieties

    @translate_db_exceptions
    async def get_public_varieties(self) -> List[Variety]:
        """Get all public varieties."""
        with log_timing("db_get_public_varieties", request_id=self.request_id):
            stmt = (
                select(Variety)
                .options(
                    selectinload(Variety.lifecycle),
                    selectinload(Variety.family),  # eager load family for list view
                )
                .where(Variety.is_public)
                .order_by(Variety.variety_name)
            )
            result = await self.db.execute(stmt)
            varieties = list(result.scalars().unique().all())
            for variety in varieties:
                setattr(variety, "is_active", False)
            return varieties

    @translate_db_exceptions
    async def get_public_variety_by_id(self, variety_id: UUID) -> Optional[Variety]:
        """Get a single public variety by ID."""
        with log_timing("db_get_public_variety_by_id", request_id=self.request_id):
            stmt = select(Variety).where(
                Variety.variety_id == variety_id, Variety.is_public
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

    @translate_db_exceptions
    async def update_variety(self, variety: Variety) -> Variety:
        """Update an existing variety."""
        with log_timing("db_update_variety", request_id=self.request_id):
            await self.db.flush()
            await self.db.refresh(variety)
            return variety

    @translate_db_exceptions
    async def delete_variety(self, variety_id: UUID, user_id: UUID) -> bool:
        """Delete a variety if it belongs to the user."""
        with log_timing("db_delete_variety", request_id=self.request_id):
            # First check if the variety exists and belongs to the user
            stmt = select(Variety).where(
                Variety.variety_id == variety_id, Variety.owner_user_id == user_id
            )
            result = await self.db.execute(stmt)
            variety = result.scalar_one_or_none()

            if variety is None:
                return False

            # Delete the variety (cascade will handle water days)
            await self.db.delete(variety)
            await self.db.flush()
            return True

    @translate_db_exceptions
    async def create_water_days(
        self, water_days: List[VarietyWaterDay]
    ) -> List[VarietyWaterDay]:
        """Create water day associations for a variety."""
        with log_timing("db_create_water_days", request_id=self.request_id):
            for water_day in water_days:
                self.db.add(water_day)
            await self.db.flush()
            return water_days

    @translate_db_exceptions
    async def get_default_day_ids_for_frequency(self, frequency_id: UUID) -> List[UUID]:
        """Return the default day IDs configured for a frequency."""
        with log_timing(
            "db_get_default_day_ids_for_frequency", request_id=self.request_id
        ):
            stmt = (
                select(FrequencyDefaultDay.day_id)
                .join(Day, Day.day_id == FrequencyDefaultDay.day_id)
                .where(FrequencyDefaultDay.frequency_id == frequency_id)
                .order_by(Day.day_number)
            )
            result = await self.db.execute(stmt)
            return [row[0] for row in result.fetchall()]

    @translate_db_exceptions
    async def delete_water_days(self, variety_id: UUID) -> None:
        """Delete all water day associations for a variety."""
        with log_timing("db_delete_water_days", request_id=self.request_id):
            stmt = delete(VarietyWaterDay).where(
                VarietyWaterDay.variety_id == variety_id
            )
            await self.db.execute(stmt)
            await self.db.flush()

    @translate_db_exceptions
    async def variety_name_exists_for_user(
        self,
        user_id: UUID,
        variety_name: str,
        exclude_variety_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a variety name already exists for a user."""
        with log_timing("db_variety_name_exists", request_id=self.request_id):
            stmt = select(Variety).where(
                Variety.owner_user_id == user_id, Variety.variety_name == variety_name
            )

            if exclude_variety_id:
                stmt = stmt.where(Variety.variety_id != exclude_variety_id)

            result = await self.db.execute(stmt)
            return result.scalar_one_or_none() is not None

    @translate_db_exceptions
    async def get_user_variety_names_for_copying(
        self, user_id: UUID, base_name: str
    ) -> List[str]:
        """Return all existing variety names for a user that would conflict with a copy of base_name.

        This includes exact base_name and any names following the pattern:
        - "{base_name} (copy)"
        - "{base_name} (copy N)" where N is a positive integer
        """
        with log_timing(
            "db_get_user_variety_names_for_copying", request_id=self.request_id
        ):
            like_pattern = f"{base_name} (copy%"
            stmt = (
                select(Variety.variety_name)
                .where(
                    Variety.owner_user_id == user_id,
                    or_(
                        Variety.variety_name == base_name,
                        Variety.variety_name.like(like_pattern),
                    ),
                )
                .order_by(Variety.variety_name)
            )
            result = await self.db.execute(stmt)
            return [row[0] for row in result.fetchall()]
