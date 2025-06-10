"""
Family Schemas
- Defines Pydantic schemas for family-related API operations.
- These schemas are used for request validation and response serialization.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from app.api.schemas.base_schema import SecureBaseModel


class FamilyBaseSchema(SecureBaseModel):
    """Base schema for Family, used for nesting within BotanicalGroupSchema."""

    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class FamilyRelationSchema(SecureBaseModel):
    """Schema for representing related families (antagonists/companions)."""

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
    treatments: Optional[List["InterventionSchema"]] = Field(default=None)
    preventions: Optional[List["InterventionSchema"]] = Field(default=None)

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
    symptoms: Optional[List[SymptomSchema]] = Field(default=None)
    treatments: Optional[List[InterventionSchema]] = Field(default=None)
    preventions: Optional[List[InterventionSchema]] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class BotanicalGroupInfoSchema(SecureBaseModel):
    """Schema for BotanicalGroup information within family details."""

    id: UUID
    name: str
    recommended_rotation_years: int | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class FamilyInfoSchema(SecureBaseModel):
    """Schema for detailed family information, including pests, diseases, and botanical group."""

    id: UUID
    name: str
    botanical_group: BotanicalGroupInfoSchema
    pests: Optional[List[PestSchema]] = Field(default=None)
    diseases: Optional[List[DiseaseSchema]] = Field(default=None)
    antagonises: Optional[List[FamilyRelationSchema]] = Field(default=None)
    companion_to: Optional[List[FamilyRelationSchema]] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


# For forward references
PestSchema.model_rebuild()
DiseaseSchema.model_rebuild()
FamilyInfoSchema.model_rebuild()
