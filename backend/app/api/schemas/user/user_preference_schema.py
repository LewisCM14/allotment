"""
User Preference Schema
- Applies validation and business logic for user feed day preferences.
"""

from typing import List
from uuid import UUID

from pydantic import Field
from pydantic.config import ConfigDict

from app.api.schemas.base_schema import SecureBaseModel
from app.api.schemas.grow_guide.variety_schema import DayRead, FeedRead


class FeedDayRead(SecureBaseModel):
    """Schema for reading a feed with its associated day."""

    feed_id: UUID
    feed_name: str
    day_id: UUID
    day_name: str

    model_config = ConfigDict(from_attributes=True)


class UserFeedDayUpdate(SecureBaseModel):
    """Schema for updating a user's feed day preference."""

    day_id: UUID = Field(..., description="The ID of the preferred day")


class UserPreferencesRead(SecureBaseModel):
    """Schema for reading all user preferences with available options."""

    user_feed_days: List[FeedDayRead]
    available_feeds: List[FeedRead]
    available_days: List[DayRead]

    model_config = ConfigDict(from_attributes=True)
