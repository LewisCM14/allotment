"""
Family Schemas
- Defines Pydantic schemas for family-related API operations.
- These schemas are used for request validation and response serialization.
"""

from typing import List
from uuid import UUID

from pydantic import ConfigDict, Field

from app.api.schemas.base_schema import SecureBaseModel


class FamilyBaseSchema(SecureBaseModel):
    """Base schema for Family, used for nesting within BotanicalGroupSchema."""

    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class BotanicalGroupSchema(SecureBaseModel):
    """Schema for BotanicalGroup, including its families."""

    id: UUID
    name: str
    recommended_rotation_years: int | None = Field(default=None)
    families: List[FamilyBaseSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PestSchema(SecureBaseModel):
    """Schema for Pest, including treatments and preventions."""

    id: UUID
    name: str
    treatments: List["InterventionSchema"] = Field(default_factory=list)
    preventions: List["InterventionSchema"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SymptomSchema(SecureBaseModel):
    """Schema for Symptom."""

    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class InterventionSchema(SecureBaseModel):
    """Schema for Intervention."""

    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class DiseaseSchema(SecureBaseModel):
    """Schema for Disease, including symptoms, treatments, and preventions."""

    id: UUID
    name: str
    symptoms: List[SymptomSchema] = Field(default_factory=list)
    treatments: List[InterventionSchema] = Field(default_factory=list)
    preventions: List[InterventionSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class FamilyInfoSchema(SecureBaseModel):
    """Schema for detailed family information, including pests, diseases, interventions, and symptoms."""

    id: UUID
    name: str
    pests: List[PestSchema] = Field(default_factory=list)
    diseases: List[DiseaseSchema] = Field(default_factory=list)
    interventions: List[InterventionSchema] = Field(default_factory=list)
    symptoms: List[SymptomSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# For forward references
PestSchema.model_rebuild()
DiseaseSchema.model_rebuild()
FamilyInfoSchema.model_rebuild()
