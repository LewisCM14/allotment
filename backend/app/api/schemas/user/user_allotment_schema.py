"""
User Allotment Schema
- Applies the validation and business logic to a Users Allotment before persistence.
"""

from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator
from pydantic.config import ConfigDict

from app.api.schemas.base_schema import SecureBaseModel


class UserAllotmentBase(SecureBaseModel):
    allotment_postal_zip_code: str = Field(
        ..., min_length=5, max_length=7, description="Postal/zip code"
    )
    allotment_width_meters: float = Field(
        ..., ge=1.0, le=100.0, description="Width in meters (1-100)"
    )
    allotment_length_meters: float = Field(
        ..., ge=1.0, le=100.0, description="Length in meters (1-100)"
    )

    @field_validator("allotment_postal_zip_code")
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        if not v.replace(" ", "").isalnum():
            raise ValueError("Postal code must be alphanumeric (spaces allowed)")
        return v


class UserAllotmentCreate(UserAllotmentBase):
    pass


class UserAllotmentUpdate(SecureBaseModel):
    allotment_postal_zip_code: Optional[str] = Field(None, min_length=5, max_length=7)
    allotment_width_meters: Optional[float] = Field(None, ge=1.0, le=100.0)
    allotment_length_meters: Optional[float] = Field(None, ge=1.0, le=100.0)


class UserAllotmentRead(SecureBaseModel):
    """Schema for reading a user allotment."""

    user_allotment_id: UUID
    user_id: UUID
    allotment_postal_zip_code: str
    allotment_width_meters: float
    allotment_length_meters: float

    model_config = ConfigDict(from_attributes=True)
