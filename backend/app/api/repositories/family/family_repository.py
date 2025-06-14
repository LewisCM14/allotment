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

    async def get_family_info(self, family_id: Any) -> Optional[FamilyInfoSchema]:
        """
        Retrieves detailed information for a specific family, including pests, diseases,
        their symptoms, treatments, preventions, botanical group information,
        antagonist families, and companion families.
        """
        if isinstance(family_id, str):
            try:
                family_id_uuid = uuid.UUID(family_id)
            except ValueError:
                return None
        elif isinstance(family_id, uuid.UUID):
            family_id_uuid = family_id
        else:
            return None  # Or raise an error for unsupported type

        # Fetch family with botanical group, antagonises, and companion_to relationships
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
        family = result.unique().scalar_one_or_none()

        if family is None:
            return None

        pest_info_list: List[PestSchema] = []
        disease_info_list: List[DiseaseSchema] = []

        # Fetch pests for this family
        family_pests_result = await self.db.execute(
            select(Pest)
            .join(family_pest, Pest.id == family_pest.c.pest_id)
            .where(family_pest.c.family_id == family_id_uuid)
        )
        pests = list(family_pests_result.scalars().all())

        if pests:
            pest_ids = [pest.id for pest in pests]

            pest_treatments_map = defaultdict(list)
            treatments_query = (
                select(pest_treatment.c.pest_id, Intervention)
                .join(Intervention, Intervention.id == pest_treatment.c.intervention_id)
                .where(pest_treatment.c.pest_id.in_(pest_ids))
            )
            treatments_result = await self.db.execute(treatments_query)
            for p_id, intervention_obj in treatments_result.all():
                pest_treatments_map[p_id].append(intervention_obj)

            pest_preventions_map = defaultdict(list)
            preventions_query = (
                select(pest_prevention.c.pest_id, Intervention)
                .join(
                    Intervention, Intervention.id == pest_prevention.c.intervention_id
                )
                .where(pest_prevention.c.pest_id.in_(pest_ids))
            )
            preventions_result = await self.db.execute(preventions_query)
            for p_id, intervention_obj in preventions_result.all():
                pest_preventions_map[p_id].append(intervention_obj)

            for pest in pests:
                treatments = pest_treatments_map.get(pest.id, [])
                preventions = pest_preventions_map.get(pest.id, [])
                pest_info_list.append(
                    PestSchema(
                        id=pest.id,
                        name=pest.name,
                        treatments=[
                            InterventionSchema.model_validate(t) for t in treatments
                        ]
                        if treatments
                        else None,
                        preventions=[
                            InterventionSchema.model_validate(p) for p in preventions
                        ]
                        if preventions
                        else None,
                    )
                )

        # Fetch diseases for this family
        family_diseases_result = await self.db.execute(
            select(Disease)
            .join(family_disease, Disease.id == family_disease.c.disease_id)
            .where(family_disease.c.family_id == family_id_uuid)
        )
        diseases = list(family_diseases_result.scalars().all())

        if diseases:
            disease_ids = [disease.id for disease in diseases]

            disease_symptoms_map = defaultdict(list)
            symptoms_query = (
                select(disease_symptom.c.disease_id, Symptom)
                .join(Symptom, Symptom.id == disease_symptom.c.symptom_id)
                .where(disease_symptom.c.disease_id.in_(disease_ids))
            )
            symptoms_result = await self.db.execute(symptoms_query)
            for d_id, symptom_obj in symptoms_result.all():
                disease_symptoms_map[d_id].append(symptom_obj)

            disease_treatments_map = defaultdict(list)
            disease_treatments_query = (
                select(disease_treatment.c.disease_id, Intervention)
                .join(
                    Intervention, Intervention.id == disease_treatment.c.intervention_id
                )
                .where(disease_treatment.c.disease_id.in_(disease_ids))
            )
            disease_treatments_result = await self.db.execute(disease_treatments_query)
            for d_id, intervention_obj in disease_treatments_result.all():
                disease_treatments_map[d_id].append(intervention_obj)

            disease_preventions_map = defaultdict(list)
            disease_preventions_query = (
                select(disease_prevention.c.disease_id, Intervention)
                .join(
                    Intervention,
                    Intervention.id == disease_prevention.c.intervention_id,
                )
                .where(disease_prevention.c.disease_id.in_(disease_ids))
            )
            disease_preventions_result = await self.db.execute(
                disease_preventions_query
            )
            for d_id, intervention_obj in disease_preventions_result.all():
                disease_preventions_map[d_id].append(intervention_obj)

            for disease in diseases:
                symptoms = disease_symptoms_map.get(disease.id, [])
                treatments = disease_treatments_map.get(disease.id, [])
                preventions = disease_preventions_map.get(disease.id, [])
                disease_info_list.append(
                    DiseaseSchema(
                        id=disease.id,
                        name=disease.name,
                        symptoms=[SymptomSchema.model_validate(s) for s in symptoms]
                        if symptoms
                        else None,
                        treatments=[
                            InterventionSchema.model_validate(t) for t in treatments
                        ]
                        if treatments
                        else None,
                        preventions=[
                            InterventionSchema.model_validate(p) for p in preventions
                        ]
                        if preventions
                        else None,
                    )
                )

        antagonist_query = (
            select(Family)
            .join(
                family_antagonist,
                (Family.id == family_antagonist.c.family_id)
                | (Family.id == family_antagonist.c.antagonist_family_id),
            )
            .where(
                or_(
                    family_antagonist.c.family_id == family_id_uuid,
                    family_antagonist.c.antagonist_family_id == family_id_uuid,
                )
            )
        )
        antagonist_result = await self.db.execute(antagonist_query)
        antagonist_families = set()
        for fam in antagonist_result.unique().scalars().all():
            if fam.id != family_id_uuid:
                antagonist_families.add(fam)

        companion_query = (
            select(Family)
            .join(
                family_companion,
                (Family.id == family_companion.c.family_id)
                | (Family.id == family_companion.c.companion_family_id),
            )
            .where(
                or_(
                    family_companion.c.family_id == family_id_uuid,
                    family_companion.c.companion_family_id == family_id_uuid,
                )
            )
        )
        companion_result = await self.db.execute(companion_query)
        companion_families = set()
        for fam in companion_result.unique().scalars().all():
            if fam.id != family_id_uuid:
                companion_families.add(fam)

        return FamilyInfoSchema(
            id=family.id,
            name=family.name,
            botanical_group=BotanicalGroupInfoSchema(
                id=family.botanical_group.id,
                name=family.botanical_group.name,
                recommended_rotation_years=family.botanical_group.recommended_rotation_years,
            ),
            pests=pest_info_list if pest_info_list else None,
            diseases=disease_info_list if disease_info_list else None,
            antagonises=[
                FamilyRelationSchema.model_validate(ant) for ant in antagonist_families
            ]
            if antagonist_families
            else None,
            companion_to=[
                FamilyRelationSchema.model_validate(comp) for comp in companion_families
            ]
            if companion_families
            else None,
        )
