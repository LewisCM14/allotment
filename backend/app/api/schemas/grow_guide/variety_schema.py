# """
# Variety Schema
# - Applies the validation and business logic to a Variety before persistence.
# - Implements data integrity rules for grow guide creation and updates.
# """

# from typing import Optional
# from uuid import UUID

# from pydantic import ConfigDict, Field, field_validator, model_validator

# from app.api.schemas.base_schema import SecureBaseModel
# from app.api.schemas.validators import validate_text_field, validate_notes_field


# class VarietyBase(SecureBaseModel):
#     """Base schema for Variety with common fields."""

#     variety_name: str = Field(
#         ...,
#         min_length=2,
#         max_length=100,
#         description="Name of the variety (lowercase, hyphens and spaces only)"
#     )

#     # Optional fields
#     lifecycle_id: Optional[UUID] = Field(None, description="Lifecycle type")
#     planting_conditions_id: Optional[UUID] = Field(None, description="Planting conditions")

#     # Week ranges - must be paired if provided
#     sow_week_start: Optional[int] = Field(None, ge=1, le=52, description="Sowing start week")
#     sow_week_end: Optional[int] = Field(None, ge=1, le=52, description="Sowing end week")

#     transplant_week_start: Optional[int] = Field(None, ge=1, le=52, description="Transplant start week")
#     transplant_week_end: Optional[int] = Field(None, ge=1, le=52, description="Transplant end week")

#     harvest_week_start: Optional[int] = Field(None, ge=1, le=52, description="Harvest start week")
#     harvest_week_end: Optional[int] = Field(None, ge=1, le=52, description="Harvest end week")

#     prune_week_start: Optional[int] = Field(None, ge=1, le=52, description="Pruning start week")
#     prune_week_end: Optional[int] = Field(None, ge=1, le=52, description="Pruning end week")

#     # Feeding - all must be provided together if any are provided
#     feed_id: Optional[UUID] = Field(None, description="Feed type")
#     feed_week_start: Optional[int] = Field(None, ge=1, le=52, description="Feeding start week")
#     feed_frequency_id: Optional[UUID] = Field(None, description="Feeding frequency")

#     # Water frequency
#     water_frequency_id: Optional[UUID] = Field(None, description="Watering frequency")

#     # Optional notes (exempt from general VARCHAR constraint)
#     notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

#     # Publication status
#     is_public: bool = Field(default=False, description="Whether guide is public")

#     @field_validator("variety_name")
#     @classmethod
#     def validate_variety_name(cls, v: str) -> str:
#         """Validate variety name according to data integrity rules."""
#         return validate_text_field(cls, v, "variety_name")

#     @field_validator("notes")
#     @classmethod
#     def validate_notes(cls, v: Optional[str]) -> Optional[str]:
#         """Validate notes field (exempt from general constraints)."""
#         if v is None:
#             return v
#         return validate_notes_field(v, "notes", max_length=1000)

#     @model_validator(mode='after')
#     def validate_week_pairs_and_feed_group(self):
#         """Validate that week pairs are provided together and feed fields are complete."""

#         # Validate week pairs - if one is provided, both must be provided
#         week_pairs = [
#             ("transplant_week_start", "transplant_week_end"),
#             ("prune_week_start", "prune_week_end"),
#         ]

#         for start_field, end_field in week_pairs:
#             start_val = getattr(self, start_field)
#             end_val = getattr(self, end_field)

#             if (start_val is None) != (end_val is None):
#                 raise ValueError(f"Both {start_field} and {end_field} must be provided together")

#             if start_val is not None and end_val is not None and start_val > end_val:
#                 raise ValueError(f"{start_field} cannot be greater than {end_field}")

#         # Validate feed group - all three must be provided together
#         feed_fields = [self.feed_id, self.feed_week_start, self.feed_frequency_id]
#         provided_feed_fields = [f for f in feed_fields if f is not None]

#         if 0 < len(provided_feed_fields) < 3:
#             raise ValueError("feed_id, feed_week_start, and feed_frequency_id must all be provided together")

#         return self


# class VarietyCreate(VarietyBase):
#     """Schema for creating a new variety."""
#     pass


# class VarietyUpdate(SecureBaseModel):
#     """Schema for updating an existing variety."""

#     variety_name: Optional[str] = Field(
#         None,
#         min_length=2,
#         max_length=100,
#         description="Name of the variety"
#     )

#     lifecycle_id: Optional[UUID] = Field(None, description="Lifecycle type")
#     planting_conditions_id: Optional[UUID] = Field(None, description="Planting conditions")

#     sow_week_start: Optional[int] = Field(None, ge=1, le=52)
#     sow_week_end: Optional[int] = Field(None, ge=1, le=52)

#     transplant_week_start: Optional[int] = Field(None, ge=1, le=52)
#     transplant_week_end: Optional[int] = Field(None, ge=1, le=52)

#     harvest_week_start: Optional[int] = Field(None, ge=1, le=52)
#     harvest_week_end: Optional[int] = Field(None, ge=1, le=52)

#     prune_week_start: Optional[int] = Field(None, ge=1, le=52)
#     prune_week_end: Optional[int] = Field(None, ge=1, le=52)

#     feed_id: Optional[UUID] = Field(None, description="Feed type")
#     feed_week_start: Optional[int] = Field(None, ge=1, le=52)
#     feed_frequency_id: Optional[UUID] = Field(None, description="Feeding frequency")

#     water_frequency_id: Optional[UUID] = Field(None, description="Watering frequency")

#     notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
#     is_public: Optional[bool] = Field(None, description="Whether guide is public")

#     @field_validator("variety_name")
#     @classmethod
#     def validate_variety_name(cls, v: Optional[str]) -> Optional[str]:
#         """Validate variety name if provided."""
#         if v is None:
#             return v
#         return validate_text_field(cls, v, "variety_name")

#     @field_validator("notes")
#     @classmethod
#     def validate_notes(cls, v: Optional[str]) -> Optional[str]:
#         """Validate notes field."""
#         if v is None:
#             return v
#         return validate_notes_field(v, "notes", max_length=1000)


# class VarietyRead(SecureBaseModel):
#     """Schema for reading a variety."""

#     id: UUID
#     owner_id: UUID
#     variety_name: str
#     lifecycle_id: Optional[UUID] = None
#     planting_conditions_id: Optional[UUID] = None

#     sow_week_start: Optional[int] = None
#     sow_week_end: Optional[int] = None
#     transplant_week_start: Optional[int] = None
#     transplant_week_end: Optional[int] = None
#     harvest_week_start: Optional[int] = None
#     harvest_week_end: Optional[int] = None
#     prune_week_start: Optional[int] = None
#     prune_week_end: Optional[int] = None

#     feed_id: Optional[UUID] = None
#     feed_week_start: Optional[int] = None
#     feed_frequency_id: Optional[UUID] = None
#     water_frequency_id: Optional[UUID] = None

#     notes: Optional[str] = None
#     is_public: bool

#     model_config = ConfigDict(from_attributes=True)
