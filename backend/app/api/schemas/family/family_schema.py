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
