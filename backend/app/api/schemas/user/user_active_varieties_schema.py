"""
User Active Varieties Schema
- Defines request and response payloads for managing user active varieties.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import Field
from pydantic.config import ConfigDict

from app.api.schemas.base_schema import SecureBaseModel


class UserActiveVarietyCreate(SecureBaseModel):
    """Request payload for marking a variety as active for a user."""

    variety_id: UUID = Field(..., description="The ID of the variety to activate")


class ActiveVarietySummary(SecureBaseModel):
    """Minimal representation of a variety linked to an active association."""

    variety_id: UUID
    variety_name: str

    model_config = ConfigDict(from_attributes=True)


class UserActiveVarietyRead(SecureBaseModel):
    """Response schema for a single active variety association."""

    user_id: UUID
    variety: ActiveVarietySummary
    activated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserActiveVarietyListRead(SecureBaseModel):
    """Response schema for all active varieties belonging to a user."""

    active_varieties: List[UserActiveVarietyRead]
