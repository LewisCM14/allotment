"""
Variety Repository
- Encapsulate the logic required to access the: Variety, Variety Water Day, Planting Conditions, Feed, Lifecycle and Frequency tables.
"""

from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.models.family.family_model import Family
from app.api.models.grow_guide.calendar_model import Week
from app.api.models.grow_guide.guide_options_model import (
    Feed,
    Frequency,
    Lifecycle,
    PlantingConditions,
)
from app.api.models.grow_guide.variety_model import Variety, VarietyWaterDay

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
    async def get_all_weeks(self) -> List[Week]:
        """Get all weeks of the year."""
        with log_timing("db_get_all_weeks", request_id=self.request_id):
            result = await self.db.execute(select(Week).order_by(Week.week_number))
            return list(result.scalars().all())

    @translate_db_exceptions
    async def get_all_families(self) -> List[Family]:
        """Get all available plant families."""
        with log_timing("db_get_all_families", request_id=self.request_id):
            result = await self.db.execute(select(Family).order_by(Family.family_name))
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
            return result.scalar_one_or_none()

    @translate_db_exceptions
    async def get_user_varieties(self, user_id: UUID) -> List[Variety]:
        """Get all varieties belonging to a user."""
        with log_timing("db_get_user_varieties", request_id=self.request_id):
            stmt = (
                select(Variety)
                .options(selectinload(Variety.lifecycle))
                .where(Variety.owner_user_id == user_id)
                .order_by(Variety.variety_name)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())

    @translate_db_exceptions
    async def get_public_varieties(self) -> List[Variety]:
        """Get all public varieties."""
        with log_timing("db_get_public_varieties", request_id=self.request_id):
            stmt = (
                select(Variety)
                .options(selectinload(Variety.lifecycle))
                .where(Variety.is_public)
                .order_by(Variety.variety_name)
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())

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
