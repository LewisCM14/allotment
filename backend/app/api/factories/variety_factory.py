"""
Variety Factory
- Responsible for creating Variety domain objects.
- Applies business rules and validations during the creation process.
- Ensures that only valid Variety objects are created before persistence.
"""

import uuid
from typing import Any, Dict, List
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

                # Create a temporary object for validation
                temp_data = VarietyCreate(
                    variety_name=variety_data.variety_name or variety.variety_name,
                    family_id=variety_data.family_id
                    if variety_data.family_id is not None
                    else variety.family_id,
                    lifecycle_id=variety_data.lifecycle_id or variety.lifecycle_id,
                    sow_week_start_id=variety_data.sow_week_start_id
                    if variety_data.sow_week_start_id is not None
                    else variety.sow_week_start_id,
                    sow_week_end_id=variety_data.sow_week_end_id
                    if variety_data.sow_week_end_id is not None
                    else variety.sow_week_end_id,
                    transplant_week_start_id=variety_data.transplant_week_start_id
                    if variety_data.transplant_week_start_id is not None
                    else variety.transplant_week_start_id,
                    transplant_week_end_id=variety_data.transplant_week_end_id
                    if variety_data.transplant_week_end_id is not None
                    else variety.transplant_week_end_id,
                    planting_conditions_id=variety_data.planting_conditions_id
                    or variety.planting_conditions_id,
                    soil_ph=variety_data.soil_ph
                    if variety_data.soil_ph is not None
                    else variety.soil_ph,
                    row_width_cm=variety_data.row_width_cm
                    if variety_data.row_width_cm is not None
                    else variety.row_width_cm,
                    plant_depth_cm=variety_data.plant_depth_cm
                    if variety_data.plant_depth_cm is not None
                    else variety.plant_depth_cm,
                    plant_space_cm=variety_data.plant_space_cm
                    if variety_data.plant_space_cm is not None
                    else variety.plant_space_cm,
                    feed_id=variety_data.feed_id
                    if variety_data.feed_id is not None
                    else variety.feed_id,
                    feed_week_start_id=variety_data.feed_week_start_id
                    if variety_data.feed_week_start_id is not None
                    else variety.feed_week_start_id,
                    feed_frequency_id=variety_data.feed_frequency_id
                    if variety_data.feed_frequency_id is not None
                    else variety.feed_frequency_id,
                    water_frequency_id=variety_data.water_frequency_id
                    if variety_data.water_frequency_id is not None
                    else variety.water_frequency_id,
                    high_temp_degrees=variety_data.high_temp_degrees
                    if variety_data.high_temp_degrees is not None
                    else variety.high_temp_degrees,
                    high_temp_water_frequency_id=variety_data.high_temp_water_frequency_id
                    if variety_data.high_temp_water_frequency_id is not None
                    else variety.high_temp_water_frequency_id,
                    harvest_week_start_id=variety_data.harvest_week_start_id
                    if variety_data.harvest_week_start_id is not None
                    else variety.harvest_week_start_id,
                    harvest_week_end_id=variety_data.harvest_week_end_id
                    if variety_data.harvest_week_end_id is not None
                    else variety.harvest_week_end_id,
                    prune_week_start_id=variety_data.prune_week_start_id
                    if variety_data.prune_week_start_id is not None
                    else variety.prune_week_start_id,
                    prune_week_end_id=variety_data.prune_week_end_id
                    if variety_data.prune_week_end_id is not None
                    else variety.prune_week_end_id,
                    notes=variety_data.notes
                    if variety_data.notes is not None
                    else variety.notes,
                    is_public=variety_data.is_public
                    if variety_data.is_public is not None
                    else variety.is_public,
                    water_days=variety_data.water_days or [],
                )

                # Validate business rules
                VarietyFactory._validate_transplant_weeks(temp_data)
                VarietyFactory._validate_prune_weeks(temp_data)
                VarietyFactory._validate_feed_details(temp_data)

                # Update variety object
                if variety_data.variety_name is not None:
                    variety.variety_name = variety_data.variety_name
                if variety_data.family_id is not None:
                    variety.family_id = variety_data.family_id
                if variety_data.lifecycle_id is not None:
                    variety.lifecycle_id = variety_data.lifecycle_id

                # Update other fields if provided
                if variety_data.sow_week_start_id is not None:
                    variety.sow_week_start_id = variety_data.sow_week_start_id
                if variety_data.sow_week_end_id is not None:
                    variety.sow_week_end_id = variety_data.sow_week_end_id
                if variety_data.transplant_week_start_id is not None:
                    variety.transplant_week_start_id = (
                        variety_data.transplant_week_start_id
                    )
                if variety_data.transplant_week_end_id is not None:
                    variety.transplant_week_end_id = variety_data.transplant_week_end_id
                if variety_data.planting_conditions_id is not None:
                    variety.planting_conditions_id = variety_data.planting_conditions_id
                if variety_data.soil_ph is not None:
                    variety.soil_ph = variety_data.soil_ph
                if variety_data.row_width_cm is not None:
                    variety.row_width_cm = variety_data.row_width_cm
                if variety_data.plant_depth_cm is not None:
                    variety.plant_depth_cm = variety_data.plant_depth_cm
                if variety_data.plant_space_cm is not None:
                    variety.plant_space_cm = variety_data.plant_space_cm
                if variety_data.feed_id is not None:
                    variety.feed_id = variety_data.feed_id
                if variety_data.feed_week_start_id is not None:
                    variety.feed_week_start_id = variety_data.feed_week_start_id
                if variety_data.feed_frequency_id is not None:
                    variety.feed_frequency_id = variety_data.feed_frequency_id
                if variety_data.water_frequency_id is not None:
                    variety.water_frequency_id = variety_data.water_frequency_id
                if variety_data.high_temp_degrees is not None:
                    variety.high_temp_degrees = variety_data.high_temp_degrees
                if variety_data.high_temp_water_frequency_id is not None:
                    variety.high_temp_water_frequency_id = (
                        variety_data.high_temp_water_frequency_id
                    )
                if variety_data.harvest_week_start_id is not None:
                    variety.harvest_week_start_id = variety_data.harvest_week_start_id
                if variety_data.harvest_week_end_id is not None:
                    variety.harvest_week_end_id = variety_data.harvest_week_end_id
                if variety_data.prune_week_start_id is not None:
                    variety.prune_week_start_id = variety_data.prune_week_start_id
                if variety_data.prune_week_end_id is not None:
                    variety.prune_week_end_id = variety_data.prune_week_end_id
                if variety_data.notes is not None:
                    variety.notes = variety_data.notes
                if variety_data.is_public is not None:
                    variety.is_public = variety_data.is_public

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
