"""
Family Repository
- Encapsulates the logic required to access the: Family, Botanical Group, Family Antagonist & Family Companion tables.
- Also provides methods to retrieve related disease and pest information for a family.
"""

import uuid
from collections import defaultdict
from typing import Any, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.models.disease_and_pest.disease_model import (
    Disease,
    disease_prevention,
    disease_symptom,
    disease_treatment,
    family_disease,
)
from app.api.models.disease_and_pest.intervention_model import Intervention
from app.api.models.disease_and_pest.pest_model import (
    Pest,
    family_pest,
    pest_prevention,
    pest_treatment,
)
from app.api.models.disease_and_pest.symptom_model import Symptom
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.models.family.family_model import Family
from app.api.models.family.family_model import (
    family_antagonists_assoc as family_antagonist,
)
from app.api.models.family.family_model import (
    family_companions_assoc as family_companion,
)
from app.api.schemas.family.family_schema import (
    BotanicalGroupInfoSchema,
    DiseaseSchema,
    FamilyInfoSchema,
    FamilyRelationSchema,
    InterventionSchema,
    PestSchema,
    SymptomSchema,
)


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

    def _validate_family_id(self, family_id: Any) -> Optional[uuid.UUID]:
        """Validates and converts family_id to UUID."""
        if isinstance(family_id, uuid.UUID):
            return family_id
        if isinstance(family_id, str):
            try:
                return uuid.UUID(family_id)
            except ValueError:
                return None
        return None

    async def _fetch_family_by_uuid(
        self, family_id_uuid: uuid.UUID
    ) -> Optional[Family]:
        """
        Fetches a family by its UUID with related botanical group,
        antagonises, and companion_to.
        """
        query = (
            select(Family)
            .options(
                joinedload(Family.botanical_group),
                joinedload(Family.antagonises),
                joinedload(Family.companion_to),
            )
            .where(Family.id == family_id_uuid)
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def _map_interventions_to_items(
        self,
        item_ids: List[uuid.UUID],
        association_table: Any,
        item_id_column_name: str,
    ) -> defaultdict[uuid.UUID, List[Intervention]]:
        """
        Maps interventions to items (pests or diseases) using an
        association table.
        """
        item_id_column = getattr(association_table.c, item_id_column_name)
        query = (
            select(item_id_column, Intervention)
            .join(Intervention, Intervention.id == association_table.c.intervention_id)
            .where(item_id_column.in_(item_ids))
        )
        result = await self.db.execute(query)
        interventions_map = defaultdict(list)
        for item_id, intervention_obj in result.all():
            interventions_map[item_id].append(intervention_obj)
        return interventions_map

    async def _map_symptoms_to_diseases(
        self, disease_ids: List[uuid.UUID]
    ) -> defaultdict[uuid.UUID, List[Symptom]]:
        """Maps symptoms to diseases."""
        symptoms_map: defaultdict[uuid.UUID, List[Symptom]] = defaultdict(list)
        if not disease_ids:
            return symptoms_map
        symptoms_query = (
            select(disease_symptom.c.disease_id, Symptom)
            .join(Symptom, Symptom.id == disease_symptom.c.symptom_id)
            .where(disease_symptom.c.disease_id.in_(disease_ids))
        )
        symptoms_result = await self.db.execute(symptoms_query)
        for d_id, symptom_obj in symptoms_result.all():
            symptoms_map[d_id].append(symptom_obj)
        return symptoms_map

    async def _fetch_pests_for_family(
        self, family_id_uuid: uuid.UUID
    ) -> List[PestSchema]:
        """Fetches pests and their details for a given family."""
        family_pests_result = await self.db.execute(
            select(Pest)
            .join(family_pest, Pest.id == family_pest.c.pest_id)
            .where(family_pest.c.family_id == family_id_uuid)
        )
        pests = list(family_pests_result.scalars().all())
        if not pests:
            return []

        pest_ids = [pest.id for pest in pests]
        treatments_map = await self._map_interventions_to_items(
            pest_ids, pest_treatment, "pest_id"
        )
        preventions_map = await self._map_interventions_to_items(
            pest_ids, pest_prevention, "pest_id"
        )

        return [
            PestSchema(
                id=pest.id,
                name=pest.name,
                treatments=[
                    InterventionSchema.model_validate(t)
                    for t in treatments_map.get(pest.id, [])
                ]
                or None,
                preventions=[
                    InterventionSchema.model_validate(p)
                    for p in preventions_map.get(pest.id, [])
                ]
                or None,
            )
            for pest in pests
        ]

    async def _fetch_diseases_for_family(
        self, family_id_uuid: uuid.UUID
    ) -> List[DiseaseSchema]:
        """Fetches diseases and their details for a given family."""
        family_diseases_result = await self.db.execute(
            select(Disease)
            .join(family_disease, Disease.id == family_disease.c.disease_id)
            .where(family_disease.c.family_id == family_id_uuid)
        )
        diseases = list(family_diseases_result.scalars().all())
        if not diseases:
            return []

        disease_ids = [disease.id for disease in diseases]
        symptoms_map = await self._map_symptoms_to_diseases(disease_ids)
        treatments_map = await self._map_interventions_to_items(
            disease_ids, disease_treatment, "disease_id"
        )
        preventions_map = await self._map_interventions_to_items(
            disease_ids, disease_prevention, "disease_id"
        )

        return [
            DiseaseSchema(
                id=disease.id,
                name=disease.name,
                symptoms=[
                    SymptomSchema.model_validate(s)
                    for s in symptoms_map.get(disease.id, [])
                ]
                or None,
                treatments=[
                    InterventionSchema.model_validate(t)
                    for t in treatments_map.get(disease.id, [])
                ]
                or None,
                preventions=[
                    InterventionSchema.model_validate(p)
                    for p in preventions_map.get(disease.id, [])
                ]
                or None,
            )
            for disease in diseases
        ]

    async def _fetch_related_families(
        self,
        family_id_uuid: uuid.UUID,
        association_table: Any,
        related_column_name: str,
    ) -> set[Family]:
        """Fetches related (antagonist or companion) families."""
        family_id_col = association_table.c.family_id
        related_family_id_col = getattr(association_table.c, related_column_name)

        query = (
            select(Family)
            .join(
                association_table,
                (Family.id == family_id_col) | (Family.id == related_family_id_col),
            )
            .where(
                or_(
                    family_id_col == family_id_uuid,
                    related_family_id_col == family_id_uuid,
                )
            )
        )
        result = await self.db.execute(query)
        return {
            fam for fam in result.unique().scalars().all() if fam.id != family_id_uuid
        }

    async def get_family_info(self, family_id: Any) -> Optional[FamilyInfoSchema]:
        """
        Retrieves detailed information for a specific family, including pests, diseases,
        their symptoms, treatments, preventions, botanical group information,
        antagonist families, and companion families.
        """
        family_id_uuid = self._validate_family_id(family_id)
        if not family_id_uuid:
            return None

        family = await self._fetch_family_by_uuid(family_id_uuid)
        if not family:
            return None

        pests = await self._fetch_pests_for_family(family_id_uuid)
        diseases = await self._fetch_diseases_for_family(family_id_uuid)
        antagonises = await self._fetch_related_families(
            family_id_uuid, family_antagonist, "antagonist_family_id"
        )
        companion_to = await self._fetch_related_families(
            family_id_uuid, family_companion, "companion_family_id"
        )

        return FamilyInfoSchema(
            id=family.id,
            name=family.name,
            botanical_group=BotanicalGroupInfoSchema(
                id=family.botanical_group.id,
                name=family.botanical_group.name,
                recommended_rotation_years=family.botanical_group.recommended_rotation_years,
            ),
            pests=pests or None,
            diseases=diseases or None,
            antagonises=[
                FamilyRelationSchema.model_validate(ant) for ant in antagonises
            ]
            or None,
            companion_to=[
                FamilyRelationSchema.model_validate(comp) for comp in companion_to
            ]
            or None,
        )
