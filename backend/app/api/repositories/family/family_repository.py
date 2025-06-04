"""
Family Repository
- Encapsulates the logic required to access the: Family, Botanical Group, Family Antagonist & Family Companion tables.
- Also provides methods to retrieve related disease and pest information for a family.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.models.disease_and_pest.association_tables import (
    disease_prevention,
    disease_symptom,
    disease_treatment,
    family_disease,
    family_pest,
    pest_prevention,
    pest_treatment,
)
from app.api.models.disease_and_pest.disease_model import Disease
from app.api.models.disease_and_pest.intervention_model import Intervention
from app.api.models.disease_and_pest.pest_model import Pest
from app.api.models.disease_and_pest.symptom_model import Symptom
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.models.family.family_model import Family


class FamilyRepository:
    """Repository for Family and related tables."""

    def __init__(self, db: AsyncSession):
        """Initializes the repository with a database session."""
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
        return list(result.unique().scalars().all())

    async def get_family_by_id(self, family_id: int) -> Family | None:
        """
        Retrieves a single family by its ID, with antagonists and companions.
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

    async def get_family_info(self, family_id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information for a specific family, including pests, diseases,
        their symptoms, treatments, preventions, and all interventions and symptoms.
        """
        # Ensure family_id is a UUID object
        if isinstance(family_id, str):
            try:
                family_id = uuid.UUID(family_id)
            except ValueError:
                return None

        # Fetch family
        family = await self.db.get(Family, family_id)
        if family is None:
            return None

        # Fetch pests for this family
        pests = (
            (
                await self.db.execute(
                    select(Pest)
                    .join(family_pest, Pest.id == family_pest.c.pest_id)
                    .where(family_pest.c.family_id == family_id)
                )
            )
            .scalars()
            .all()
        )

        # For each pest, fetch treatments and preventions
        pest_info = []
        for pest in pests:
            treatments = (
                (
                    await self.db.execute(
                        select(Intervention)
                        .join(
                            pest_treatment,
                            Intervention.id == pest_treatment.c.intervention_id,
                        )
                        .where(pest_treatment.c.pest_id == pest.id)
                    )
                )
                .scalars()
                .all()
            )
            preventions = (
                (
                    await self.db.execute(
                        select(Intervention)
                        .join(
                            pest_prevention,
                            Intervention.id == pest_prevention.c.intervention_id,
                        )
                        .where(pest_prevention.c.pest_id == pest.id)
                    )
                )
                .scalars()
                .all()
            )
            pest_info.append(
                {
                    "id": pest.id,
                    "name": pest.name,
                    "treatments": treatments,
                    "preventions": preventions,
                }
            )

        # Fetch diseases for this family
        diseases = (
            (
                await self.db.execute(
                    select(Disease)
                    .join(family_disease, Disease.id == family_disease.c.disease_id)
                    .where(family_disease.c.family_id == family_id)
                )
            )
            .scalars()
            .all()
        )

        # For each disease, fetch symptoms, treatments, preventions
        disease_info = []
        for disease in diseases:
            symptoms = (
                (
                    await self.db.execute(
                        select(Symptom)
                        .join(
                            disease_symptom, Symptom.id == disease_symptom.c.symptom_id
                        )
                        .where(disease_symptom.c.disease_id == disease.id)
                    )
                )
                .scalars()
                .all()
            )
            treatments = (
                (
                    await self.db.execute(
                        select(Intervention)
                        .join(
                            disease_treatment,
                            Intervention.id == disease_treatment.c.intervention_id,
                        )
                        .where(disease_treatment.c.disease_id == disease.id)
                    )
                )
                .scalars()
                .all()
            )
            preventions = (
                (
                    await self.db.execute(
                        select(Intervention)
                        .join(
                            disease_prevention,
                            Intervention.id == disease_prevention.c.intervention_id,
                        )
                        .where(disease_prevention.c.disease_id == disease.id)
                    )
                )
                .scalars()
                .all()
            )
            disease_info.append(
                {
                    "id": disease.id,
                    "name": disease.name,
                    "symptoms": symptoms,
                    "treatments": treatments,
                    "preventions": preventions,
                }
            )

        # Fetch all interventions and symptoms for reference
        interventions = (await self.db.execute(select(Intervention))).scalars().all()
        symptoms = (await self.db.execute(select(Symptom))).scalars().all()

        return {
            "id": family.id,
            "name": family.name,
            "pests": pest_info,
            "diseases": disease_info,
            "interventions": interventions,
            "symptoms": symptoms,
        }
