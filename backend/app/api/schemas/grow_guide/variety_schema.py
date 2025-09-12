"""
Variety Schema
- Applies the validation and business logic to a Variety before persistence.
- Implements data integrity rules for grow guide creation and updates.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator
from pydantic.config import ConfigDict

from app.api.schemas.base_schema import SecureBaseModel


class FeedRead(SecureBaseModel):
    """Schema for reading feed information."""

    feed_id: UUID
    feed_name: str

    model_config = ConfigDict(from_attributes=True)


class DayRead(SecureBaseModel):
    """Schema for reading day information."""

    day_id: UUID
    day_number: int
    day_name: str

    model_config = ConfigDict(from_attributes=True)


class FrequencyRead(SecureBaseModel):
    """Schema for reading frequency information."""

    frequency_id: UUID
    frequency_name: str
    frequency_days_per_year: int

    model_config = ConfigDict(from_attributes=True)


class LifecycleRead(SecureBaseModel):
    """Schema for reading lifecycle information."""

    lifecycle_id: UUID
    lifecycle_name: str
    productivity_years: int

    model_config = ConfigDict(from_attributes=True)


class PlantingConditionsRead(SecureBaseModel):
    """Schema for reading planting conditions."""

    planting_condition_id: UUID
    planting_condition: str

    model_config = ConfigDict(from_attributes=True)


class WeekRead(SecureBaseModel):
    """Schema for reading week information."""

    week_id: UUID
    week_number: int
    week_start_date: str
    week_end_date: str

    model_config = ConfigDict(from_attributes=True)


class MonthRead(SecureBaseModel):
    """Schema for reading month information."""

    month_id: UUID
    month_number: int
    month_name: str

    model_config = ConfigDict(from_attributes=True)


class FamilyRead(SecureBaseModel):
    """Schema for reading family information."""

    family_id: UUID
    family_name: str

    model_config = ConfigDict(from_attributes=True)


class VarietyWaterDayCreate(SecureBaseModel):
    """Schema for creating variety water day associations."""

    day_id: UUID = Field(..., description="The ID of the day for watering")


class VarietyWaterDayRead(SecureBaseModel):
    """Schema for reading variety water day associations."""

    day: DayRead

    model_config = ConfigDict(from_attributes=True)


class VarietyCreate(SecureBaseModel):
    """Schema for creating a variety."""

    variety_name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the variety"
    )
    family_id: UUID = Field(..., description="Required family ID")
    lifecycle_id: UUID = Field(..., description="Required lifecycle ID")

    # Sowing details (both required)
    sow_week_start_id: UUID = Field(..., description="Required sowing start week")
    sow_week_end_id: UUID = Field(..., description="Required sowing end week")

    # Transplant details (both must be provided together)
    transplant_week_start_id: Optional[UUID] = Field(
        None, description="Transplant start week"
    )
    transplant_week_end_id: Optional[UUID] = Field(
        None, description="Transplant end week"
    )

    planting_conditions_id: UUID = Field(
        ..., description="Required planting conditions ID"
    )

    # Soil and spacing details
    soil_ph: float = Field(..., ge=0.0, le=14.0, description="Required soil pH (0-14)")
    row_width_cm: Optional[int] = Field(
        None, ge=1, le=1000, description="Row width in cm"
    )
    plant_depth_cm: int = Field(
        ..., ge=1, le=100, description="Required plant depth in cm"
    )
    plant_space_cm: int = Field(
        ..., ge=1, le=1000, description="Required plant spacing in cm"
    )

    # Feed details (all three must be provided together)
    feed_id: Optional[UUID] = Field(None, description="Feed type ID")
    feed_week_start_id: Optional[UUID] = Field(None, description="Feed start week")
    feed_frequency_id: Optional[UUID] = Field(None, description="Feed frequency ID")

    # Watering details (required)
    water_frequency_id: UUID = Field(..., description="Required water frequency ID")

    # High temperature details
    high_temp_degrees: Optional[int] = Field(
        None, ge=-50, le=60, description="High temperature threshold"
    )
    high_temp_water_frequency_id: Optional[UUID] = Field(
        None, description="High temp water frequency ID"
    )

    # Harvest details (both required)
    harvest_week_start_id: UUID = Field(..., description="Required harvest start week")
    harvest_week_end_id: UUID = Field(..., description="Required harvest end week")

    # Prune details (both must be provided together)
    prune_week_start_id: Optional[UUID] = Field(None, description="Prune start week")
    prune_week_end_id: Optional[UUID] = Field(None, description="Prune end week")

    notes: Optional[str] = Field(
        None, min_length=5, max_length=500, description="Optional notes"
    )
    is_public: bool = Field(default=False, description="Whether the variety is public")

    @field_validator("variety_name")
    @classmethod
    def validate_variety_name(cls, v: str) -> str:
        """Strip whitespace from variety name."""
        return v.strip()

    @model_validator(mode="before")
    @classmethod
    def coerce_empty_strings_to_none(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce blank string ("") entries for optional UUID fields to None.

        Frontend form libraries often submit "" for unselected optional selects.
        Pydantic's UUID parsing treats this as invalid UUID; we normalize here.
        """
        optional_uuid_fields = [
            "transplant_week_start_id",
            "transplant_week_end_id",
            "feed_id",
            "feed_week_start_id",
            "feed_frequency_id",
            "high_temp_water_frequency_id",
            "prune_week_start_id",
            "prune_week_end_id",
        ]
        for field in optional_uuid_fields:
            if values.get(field) == "":
                values[field] = None
        return values


class VarietyUpdate(SecureBaseModel):
    """Schema for updating a variety."""

    variety_name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Name of the variety"
    )
    family_id: Optional[UUID] = Field(None, description="Family ID")
    lifecycle_id: Optional[UUID] = Field(None, description="Lifecycle ID")

    # Sowing details
    sow_week_start_id: Optional[UUID] = Field(None, description="Sowing start week")
    sow_week_end_id: Optional[UUID] = Field(None, description="Sowing end week")

    # Transplant details
    transplant_week_start_id: Optional[UUID] = Field(
        None, description="Transplant start week"
    )
    transplant_week_end_id: Optional[UUID] = Field(
        None, description="Transplant end week"
    )

    planting_conditions_id: Optional[UUID] = Field(
        None, description="Planting conditions ID"
    )

    # Soil and spacing details
    soil_ph: Optional[float] = Field(
        None, ge=0.0, le=14.0, description="Soil pH (0-14)"
    )
    row_width_cm: Optional[int] = Field(
        None, ge=1, le=1000, description="Row width in cm"
    )
    plant_depth_cm: Optional[int] = Field(
        None, ge=1, le=100, description="Plant depth in cm"
    )
    plant_space_cm: Optional[int] = Field(
        None, ge=1, le=1000, description="Plant spacing in cm"
    )

    # Feed details
    feed_id: Optional[UUID] = Field(None, description="Feed type ID")
    feed_week_start_id: Optional[UUID] = Field(None, description="Feed start week")
    feed_frequency_id: Optional[UUID] = Field(None, description="Feed frequency ID")

    # Watering details
    water_frequency_id: Optional[UUID] = Field(None, description="Water frequency ID")

    # High temperature details
    high_temp_degrees: Optional[int] = Field(
        None, ge=-50, le=60, description="High temperature threshold"
    )
    high_temp_water_frequency_id: Optional[UUID] = Field(
        None, description="High temp water frequency ID"
    )

    # Harvest details
    harvest_week_start_id: Optional[UUID] = Field(
        None, description="Harvest start week"
    )
    harvest_week_end_id: Optional[UUID] = Field(None, description="Harvest end week")

    # Prune details
    prune_week_start_id: Optional[UUID] = Field(None, description="Prune start week")
    prune_week_end_id: Optional[UUID] = Field(None, description="Prune end week")

    notes: Optional[str] = Field(
        None, min_length=5, max_length=500, description="Optional notes"
    )
    is_public: Optional[bool] = Field(None, description="Whether the variety is public")

    @field_validator("variety_name")
    @classmethod
    def validate_variety_name(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace from variety name."""
        if v is not None:
            return v.strip()
        return v

    @model_validator(mode="before")
    @classmethod
    def coerce_empty_strings_to_none(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        optional_uuid_fields = [
            "family_id",
            "lifecycle_id",
            "sow_week_start_id",
            "sow_week_end_id",
            "transplant_week_start_id",
            "transplant_week_end_id",
            "planting_conditions_id",
            "feed_id",
            "feed_week_start_id",
            "feed_frequency_id",
            "water_frequency_id",
            "high_temp_water_frequency_id",
            "harvest_week_start_id",
            "harvest_week_end_id",
            "prune_week_start_id",
            "prune_week_end_id",
        ]
        for field in optional_uuid_fields:
            if values.get(field) == "":
                values[field] = None
        return values


class VarietyRead(SecureBaseModel):
    """Schema for reading a variety with all related information."""

    variety_id: UUID
    variety_name: str
    owner_user_id: UUID

    # Related objects
    family: FamilyRead
    lifecycle: LifecycleRead
    planting_conditions: PlantingConditionsRead

    # Sowing details (required)
    sow_week_start_id: UUID
    sow_week_end_id: UUID

    # Transplant details
    transplant_week_start_id: Optional[UUID] = None
    transplant_week_end_id: Optional[UUID] = None

    # Soil and spacing details
    soil_ph: float
    row_width_cm: Optional[int] = None
    plant_depth_cm: int
    plant_space_cm: int

    # Feed details
    feed: Optional[FeedRead] = None
    feed_week_start_id: Optional[UUID] = None
    feed_frequency: Optional[FrequencyRead] = None

    # Watering details (required)
    water_frequency: FrequencyRead

    # High temperature details
    high_temp_degrees: Optional[int] = None
    high_temp_water_frequency: Optional[FrequencyRead] = None

    # Harvest details (required)
    harvest_week_start_id: UUID
    harvest_week_end_id: UUID

    # Prune details
    prune_week_start_id: Optional[UUID] = None
    prune_week_end_id: Optional[UUID] = None

    notes: Optional[str] = None
    is_public: bool
    last_updated: datetime

    # Water days
    water_days: List[VarietyWaterDayRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class VarietyListRead(SecureBaseModel):
    """Schema for reading a simplified list of varieties."""

    variety_id: UUID
    variety_name: str
    lifecycle: LifecycleRead
    is_public: bool
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


class VarietyOptionsRead(SecureBaseModel):
    """Schema for reading all available options for variety creation/editing."""

    lifecycles: List[LifecycleRead]
    planting_conditions: List[PlantingConditionsRead]
    frequencies: List[FrequencyRead]
    # Subset of frequencies allowed for feed scheduling (restricted vs watering)
    feed_frequencies: List[FrequencyRead]
    feeds: List[FeedRead]
    weeks: List[WeekRead]
    families: List[FamilyRead]
    days: List[DayRead]

    model_config = ConfigDict(from_attributes=True)
