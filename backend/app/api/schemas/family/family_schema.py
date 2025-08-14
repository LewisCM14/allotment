"""
Family Schemas
- Defines Pydantic schemas for family-related API operations.
- These schemas are used for request validation and response serialization.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator

from app.api.schemas.base_schema import SecureBaseModel
from app.api.schemas.validators import validate_text_field


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


# Admin Panel not yet implemented
class FamilyCreate(SecureBaseModel):  # pragma: no cover
    """Schema for creating a family (admin only)."""

    name: str = Field(..., description="Family name")
    botanical_group_id: UUID = Field(..., description="Botanical group ID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_text_field(v, "name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "tomato",
                "botanical_group_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class BotanicalGroupCreate(SecureBaseModel):  # pragma: no cover
    """Schema for creating a botanical group (admin only)."""

    name: str = Field(..., description="Botanical group name")
    recommended_rotation_years: int | None = Field(
        default=None, description="Rotation years"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_text_field(v, "name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "nightshade",
                "recommended_rotation_years": 3,
            }
        }
    )


class PestCreate(SecureBaseModel):  # pragma: no cover
    """Schema for creating a pest (admin only)."""

    name: str = Field(..., description="Pest name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_text_field(v, "name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "aphid",
            }
        }
    )


class DiseaseCreate(SecureBaseModel):  # pragma: no cover
    """Schema for creating a disease (admin only)."""

    name: str = Field(..., description="Disease name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_text_field(v, "name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "blight",
            }
        }
    )


class InterventionCreate(SecureBaseModel):  # pragma: no cover
    """Schema for creating an intervention (admin only)."""

    name: str = Field(..., description="Intervention name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_text_field(v, "name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "neem-oil",
            }
        }
    )


class SymptomCreate(SecureBaseModel):  # pragma: no cover
    """Schema for creating a symptom (admin only)."""

    name: str = Field(..., description="Symptom name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_text_field(v, "name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "yellow-leaves",
            }
        }
    )
