"""
Variety Factory
- Responsible for creating Variety domain objects.
- Applies business rules and validations during the creation process.
- Ensures that only valid Variety objects are created before persistence.
"""

import uuid
from typing import AbstractSet, Any, Dict, List, Optional, Set, cast
from uuid import UUID

import structlog

from app.api.core.logging import log_timing
from app.api.middleware.error_codes import GENERAL_VALIDATION_ERROR
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.grow_guide.variety_model import Variety, VarietyWaterDay
from app.api.schemas.grow_guide.variety_schema import VarietyCreate, VarietyUpdate

logger = structlog.get_logger()


class VarietyFactoryValidationError(BaseApplicationError):
    """Exception for variety factory validation errors with HTTP status details."""

    def __init__(self, message: str, field: str, status_code: int = 422) -> None:
        self.field = field
        super().__init__(
            status_code=status_code,
            message=f"{message} (Field: {field})",
            error_code=GENERAL_VALIDATION_ERROR,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a JSON-serializable dict."""
        return {
            "detail": self.message,
            "field": self.field,
            "status_code": self.status_code,
            "error_code": self.error_code,
        }


class VarietyFactory:
    """Factory for creating Variety objects."""

    @staticmethod
    def create_variety(variety_data: VarietyCreate, owner_user_id: UUID) -> Variety:
        """Create a Variety object with validated data."""
        operation_id = str(uuid.uuid4())
        safe_context: Dict[str, Any] = {
            "variety_name": variety_data.variety_name,
            "owner_user_id": str(owner_user_id),
            "request_id": request_id_ctx_var.get(),
            "operation": "variety_creation",
            "operation_id": operation_id,
        }

        try:
            with log_timing("variety_creation", request_id=safe_context["request_id"]):
                logger.info("Starting variety creation", **safe_context)

                # Validate business rules
                VarietyFactory._validate_transplant_weeks(variety_data)
                VarietyFactory._validate_prune_weeks(variety_data)
                VarietyFactory._validate_feed_details(variety_data)

                # Create variety object
                variety = Variety()
                variety.owner_user_id = owner_user_id
                variety.variety_name = variety_data.variety_name
                variety.family_id = variety_data.family_id
                variety.lifecycle_id = variety_data.lifecycle_id

                # Sowing details
                variety.sow_week_start_id = variety_data.sow_week_start_id
                variety.sow_week_end_id = variety_data.sow_week_end_id

                # Transplant details
                variety.transplant_week_start_id = variety_data.transplant_week_start_id
                variety.transplant_week_end_id = variety_data.transplant_week_end_id

                variety.planting_conditions_id = variety_data.planting_conditions_id

                # Soil and spacing details
                variety.soil_ph = variety_data.soil_ph
                variety.row_width_cm = variety_data.row_width_cm
                variety.plant_depth_cm = variety_data.plant_depth_cm
                variety.plant_space_cm = variety_data.plant_space_cm

                # Feed details
                variety.feed_id = variety_data.feed_id
                variety.feed_week_start_id = variety_data.feed_week_start_id
                variety.feed_frequency_id = variety_data.feed_frequency_id

                # Watering details
                variety.water_frequency_id = variety_data.water_frequency_id

                # High temperature details
                variety.high_temp_degrees = variety_data.high_temp_degrees
                variety.high_temp_water_frequency_id = (
                    variety_data.high_temp_water_frequency_id
                )

                # Harvest details
                variety.harvest_week_start_id = variety_data.harvest_week_start_id
                variety.harvest_week_end_id = variety_data.harvest_week_end_id

                # Prune details
                variety.prune_week_start_id = variety_data.prune_week_start_id
                variety.prune_week_end_id = variety_data.prune_week_end_id

                variety.notes = variety_data.notes
                variety.is_public = variety_data.is_public

                logger.info("Variety object created successfully", **safe_context)
                return variety

        except VarietyFactoryValidationError as e:
            logger.error(
                "Variety validation failed",
                error=sanitize_error_message(str(e)),
                field=e.field,
                **safe_context,
            )
            raise
        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.critical(
                "Unexpected error during variety creation",
                error=sanitized_error,
                error_type=type(e).__name__,
                **safe_context,
            )
            raise BusinessLogicError(
                message="An unexpected error occurred during variety creation",
                status_code=500,
            )

    @staticmethod
    def update_variety(variety: Variety, variety_data: VarietyUpdate) -> Variety:
        """Update a Variety object with validated data."""
        operation_id = str(uuid.uuid4())
        safe_context: Dict[str, Any] = {
            "variety_id": str(variety.variety_id),
            "request_id": request_id_ctx_var.get(),
            "operation": "variety_update",
            "operation_id": operation_id,
        }

        try:
            with log_timing("variety_update", request_id=safe_context["request_id"]):
                logger.info("Starting variety update", **safe_context)

                if hasattr(variety_data, "model_fields_set"):
                    raw_fields_any: Any = getattr(variety_data, "model_fields_set")
                elif hasattr(variety_data, "__fields_set__"):
                    raw_fields_any = getattr(variety_data, "__fields_set__")
                else:
                    raw_fields_any = set()
                provided_fields: AbstractSet[str] = cast(
                    AbstractSet[str], raw_fields_any
                )

                # Create temporary object for validation based on the intended new state
                temp_data = VarietyFactory._create_temp_variety_data(
                    variety, variety_data, provided_fields
                )

                # Validate business rules
                VarietyFactory._validate_transplant_weeks(temp_data)
                VarietyFactory._validate_prune_weeks(temp_data)
                VarietyFactory._validate_feed_details(temp_data)

                # Update variety object with new data
                VarietyFactory._apply_variety_updates(variety, variety_data)

                logger.info("Variety updated successfully", **safe_context)
                return variety

        except VarietyFactoryValidationError as e:
            logger.error(
                "Variety update validation failed",
                error=sanitize_error_message(str(e)),
                field=e.field,
                **safe_context,
            )
            raise
        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.critical(
                "Unexpected error during variety update",
                error=sanitized_error,
                error_type=type(e).__name__,
                **safe_context,
            )
            raise BusinessLogicError(
                message="An unexpected error occurred during variety update",
                status_code=500,
            )

    @staticmethod
    def create_water_days(
        variety_id: UUID, water_day_data: List[Dict[str, Any]]
    ) -> List[VarietyWaterDay]:
        """Create VarietyWaterDay objects."""
        operation_id = str(uuid.uuid4())
        safe_context: Dict[str, Any] = {
            "variety_id": str(variety_id),
            "water_days_count": len(water_day_data),
            "request_id": request_id_ctx_var.get(),
            "operation": "water_days_creation",
            "operation_id": operation_id,
        }

        try:
            with log_timing(
                "water_days_creation", request_id=safe_context["request_id"]
            ):
                logger.info("Creating water days", **safe_context)

                water_days = []
                for day_data in water_day_data:
                    water_day = VarietyWaterDay()
                    water_day.variety_id = variety_id
                    water_day.day_id = day_data["day_id"]
                    water_days.append(water_day)

                logger.info("Water days created successfully", **safe_context)
                return water_days

        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.critical(
                "Unexpected error during water days creation",
                error=sanitized_error,
                error_type=type(e).__name__,
                **safe_context,
            )
            raise BusinessLogicError(
                message="An unexpected error occurred during water days creation",
                status_code=500,
            )

    @staticmethod
    def _create_temp_variety_data(
        variety: Variety, variety_data: VarietyUpdate, provided_fields: AbstractSet[str]
    ) -> VarietyCreate:
        """Create a temporary VarietyCreate object for validation purposes."""

        def effective[T](field: str, new_value: Optional[T], fallback_value: T) -> T:
            """Return new_value if the field was provided (even if None), else fallback."""
            if field in provided_fields:
                return cast(T, new_value)  # may be None for Optional[T]
            return fallback_value

        return VarietyCreate(
            variety_name=effective(
                "variety_name", variety_data.variety_name, variety.variety_name
            ),
            family_id=effective("family_id", variety_data.family_id, variety.family_id),
            lifecycle_id=effective(
                "lifecycle_id", variety_data.lifecycle_id, variety.lifecycle_id
            ),
            sow_week_start_id=effective(
                "sow_week_start_id",
                variety_data.sow_week_start_id,
                variety.sow_week_start_id,
            ),
            sow_week_end_id=effective(
                "sow_week_end_id", variety_data.sow_week_end_id, variety.sow_week_end_id
            ),
            transplant_week_start_id=effective(
                "transplant_week_start_id",
                variety_data.transplant_week_start_id,
                variety.transplant_week_start_id,
            ),
            transplant_week_end_id=effective(
                "transplant_week_end_id",
                variety_data.transplant_week_end_id,
                variety.transplant_week_end_id,
            ),
            planting_conditions_id=effective(
                "planting_conditions_id",
                variety_data.planting_conditions_id,
                variety.planting_conditions_id,
            ),
            soil_ph=effective("soil_ph", variety_data.soil_ph, variety.soil_ph),
            row_width_cm=effective(
                "row_width_cm", variety_data.row_width_cm, variety.row_width_cm
            ),
            plant_depth_cm=effective(
                "plant_depth_cm", variety_data.plant_depth_cm, variety.plant_depth_cm
            ),
            plant_space_cm=effective(
                "plant_space_cm", variety_data.plant_space_cm, variety.plant_space_cm
            ),
            feed_id=effective("feed_id", variety_data.feed_id, variety.feed_id),
            feed_week_start_id=effective(
                "feed_week_start_id",
                variety_data.feed_week_start_id,
                variety.feed_week_start_id,
            ),
            feed_frequency_id=effective(
                "feed_frequency_id",
                variety_data.feed_frequency_id,
                variety.feed_frequency_id,
            ),
            water_frequency_id=effective(
                "water_frequency_id",
                variety_data.water_frequency_id,
                variety.water_frequency_id,
            ),
            high_temp_degrees=effective(
                "high_temp_degrees",
                variety_data.high_temp_degrees,
                variety.high_temp_degrees,
            ),
            high_temp_water_frequency_id=effective(
                "high_temp_water_frequency_id",
                variety_data.high_temp_water_frequency_id,
                variety.high_temp_water_frequency_id,
            ),
            harvest_week_start_id=effective(
                "harvest_week_start_id",
                variety_data.harvest_week_start_id,
                variety.harvest_week_start_id,
            ),
            harvest_week_end_id=effective(
                "harvest_week_end_id",
                variety_data.harvest_week_end_id,
                variety.harvest_week_end_id,
            ),
            prune_week_start_id=effective(
                "prune_week_start_id",
                variety_data.prune_week_start_id,
                variety.prune_week_start_id,
            ),
            prune_week_end_id=effective(
                "prune_week_end_id",
                variety_data.prune_week_end_id,
                variety.prune_week_end_id,
            ),
            notes=effective("notes", variety_data.notes, variety.notes),
            is_public=effective("is_public", variety_data.is_public, variety.is_public),
        )

    @staticmethod
    def _apply_variety_updates(variety: Variety, variety_data: VarietyUpdate) -> None:
        """Apply update data to the variety object."""
        # Define mapping of update fields to variety attributes
        field_mappings = [
            ("variety_name", "variety_name"),
            ("family_id", "family_id"),
            ("lifecycle_id", "lifecycle_id"),
            ("sow_week_start_id", "sow_week_start_id"),
            ("sow_week_end_id", "sow_week_end_id"),
            ("transplant_week_start_id", "transplant_week_start_id"),
            ("transplant_week_end_id", "transplant_week_end_id"),
            ("planting_conditions_id", "planting_conditions_id"),
            ("soil_ph", "soil_ph"),
            ("row_width_cm", "row_width_cm"),
            ("plant_depth_cm", "plant_depth_cm"),
            ("plant_space_cm", "plant_space_cm"),
            ("feed_id", "feed_id"),
            ("feed_week_start_id", "feed_week_start_id"),
            ("feed_frequency_id", "feed_frequency_id"),
            ("water_frequency_id", "water_frequency_id"),
            ("high_temp_degrees", "high_temp_degrees"),
            ("high_temp_water_frequency_id", "high_temp_water_frequency_id"),
            ("harvest_week_start_id", "harvest_week_start_id"),
            ("harvest_week_end_id", "harvest_week_end_id"),
            ("prune_week_start_id", "prune_week_start_id"),
            ("prune_week_end_id", "prune_week_end_id"),
            ("notes", "notes"),
            ("is_public", "is_public"),
        ]

        # Avoid evaluating deprecated attributes eagerly to prevent warnings
        if hasattr(variety_data, "model_fields_set"):
            raw_fields_any: Any = getattr(variety_data, "model_fields_set")
        elif hasattr(variety_data, "__fields_set__"):
            raw_fields_any = getattr(variety_data, "__fields_set__")
        else:
            raw_fields_any = set()
        # Explicitly annotate after casting for mypy; treat unknown contents as AbstractSet[str]
        raw_fields: AbstractSet[str] = cast(AbstractSet[str], raw_fields_any)
        provided_fields: Set[str] = set(raw_fields)

        # Apply updates only for fields present in the payload; this allows explicit nulls to clear values.
        for update_field, variety_field in field_mappings:
            if update_field in provided_fields:
                new_value = getattr(variety_data, update_field)
                setattr(variety, variety_field, new_value)

    @staticmethod
    def _validate_transplant_weeks(variety_data: VarietyCreate) -> None:
        """Validate that transplant weeks are provided together."""
        transplant_start = variety_data.transplant_week_start_id
        transplant_end = variety_data.transplant_week_end_id

        # Either both or neither should be provided
        if (transplant_start is None) != (transplant_end is None):
            raise VarietyFactoryValidationError(
                "Transplant week start and end must be provided together",
                "transplant_weeks",
            )

    @staticmethod
    def _validate_prune_weeks(variety_data: VarietyCreate) -> None:
        """Validate that prune weeks are provided together."""
        prune_start = variety_data.prune_week_start_id
        prune_end = variety_data.prune_week_end_id

        # Either both or neither should be provided
        if (prune_start is None) != (prune_end is None):
            raise VarietyFactoryValidationError(
                "Prune week start and end must be provided together", "prune_weeks"
            )

    @staticmethod
    def _validate_feed_details(variety_data: VarietyCreate) -> None:
        """Validate that feed details are provided together."""
        feed_id = variety_data.feed_id
        feed_week = variety_data.feed_week_start_id
        feed_frequency = variety_data.feed_frequency_id

        # Either all three or none should be provided
        feed_fields = [feed_id, feed_week, feed_frequency]
        non_none_count = sum(1 for field in feed_fields if field is not None)

        if non_none_count != 0 and non_none_count != 3:
            raise VarietyFactoryValidationError(
                "Feed ID, feed week start, and feed frequency must all be provided together",
                "feed_details",
            )
