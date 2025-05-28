"""
Family Repository
- Encapsulate the logic required to access the: Family, Botanical Group, Family Antagonist & Family Companion tables.
"""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.models.family.family_model import Family


class FamilyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_botanical_groups_with_families(self) -> List[BotanicalGroup]:
        """
        Retrieves all botanical groups, with their associated families preloaded.
        """
        query = (
            select(BotanicalGroup)
            .options(joinedload(BotanicalGroup.families))
            .order_by(BotanicalGroup.name)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_family_by_id(self, family_id: int) -> Family | None:
        """
        Retrieves a single family by its ID, with antagonists and companions.
        (Example for future use, not directly for the botanical group list)
        """
        query = (
            select(Family)
            .options(
                joinedload(Family.botanical_group),
                joinedload(Family.antagonises),
                joinedload(Family.companion_to),
            )
            .filter(Family.id == family_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
