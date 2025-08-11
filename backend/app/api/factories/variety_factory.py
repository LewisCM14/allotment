# """
# Variety Factory
# - Responsible for creating Variety domain objects.
# - Applies business rules and validations during the creation process.
# - Ensures that only valid Variety objects are created before persistence.
# """

# import uuid
# from typing import Any, Dict

# import structlog

# from app.api.core.logging import log_timing
# from app.api.middleware.error_codes import GENERAL_VALIDATION_ERROR
# from app.api.middleware.exception_handler import (
#     BaseApplicationError,
#     BusinessLogicError,
# )
# from app.api.middleware.logging_middleware import (
#     request_id_ctx_var,
#     sanitize_error_message,
# )
# from app.api.models.grow_guide.variety_model import Variety
# from app.api.schemas.grow_guide.variety_schema import VarietyCreate
# from app.api.schemas.validators import validate_name_field

# logger = structlog.get_logger()


# class VarietyFactoryValidationError(BaseApplicationError):
#     """Exception for variety factory validation errors with HTTP status details."""

#     def __init__(self, message: str, field: str, status_code: int = 422) -> None:
#         self.field = field
#         super().__init__(
#             status_code=status_code,
#             message=f"{message} (Field: {field})",
#             error_code=GENERAL_VALIDATION_ERROR,
#         )

#     def to_dict(self) -> Dict[str, Any]:
#         """Convert the error to a JSON-serializable dict."""
#         return {
#             "detail": self.message,
#             "field": self.field,
#             "status_code": self.status_code,
#             "error_code": self.error_code,
#         }


# class VarietyFactory:
#     """Factory for creating Variety objects."""

#     @staticmethod
#     def create_variety(variety_data: VarietyCreate, owner_id: uuid.UUID) -> Variety:
#         """Create a Variety object with validated data."""
#         operation_id = str(uuid.uuid4())
#         safe_context: Dict[str, Any] = {
#             "variety_name": variety_data.variety_name,
#             "owner_id": str(owner_id),
#             "request_id": request_id_ctx_var.get(),
#             "operation": "variety_creation",
#             "operation_id": operation_id,
#         }

#         try:
#             with log_timing("variety_creation", request_id=safe_context["request_id"]):
#                 logger.info("Starting variety creation", **safe_context)

#                 # Validate the variety name using common validator
#                 VarietyFactory.validate_variety_name(variety_data.variety_name)

#                 # Validate business logic constraints
#                 VarietyFactory.validate_week_pairs(variety_data)
#                 VarietyFactory.validate_feed_group(variety_data)

#                 # Create the variety object
#                 variety = Variety()
#                 variety.owner_id = owner_id
#                 variety.variety_name = variety_data.variety_name.lower().strip()
#                 variety.lifecycle_id = variety_data.lifecycle_id
#                 variety.planting_conditions_id = variety_data.planting_conditions_id

#                 # Set week fields
#                 variety.sow_week_start = variety_data.sow_week_start
#                 variety.sow_week_end = variety_data.sow_week_end
#                 variety.transplant_week_start = variety_data.transplant_week_start
#                 variety.transplant_week_end = variety_data.transplant_week_end
#                 variety.harvest_week_start = variety_data.harvest_week_start
#                 variety.harvest_week_end = variety_data.harvest_week_end
#                 variety.prune_week_start = variety_data.prune_week_start
#                 variety.prune_week_end = variety_data.prune_week_end

#                 # Set feed fields
#                 variety.feed_id = variety_data.feed_id
#                 variety.feed_week_start = variety_data.feed_week_start
#                 variety.feed_frequency_id = variety_data.feed_frequency_id
#                 variety.water_frequency_id = variety_data.water_frequency_id

#                 # Set optional fields
#                 variety.notes = variety_data.notes
#                 variety.is_public = variety_data.is_public

#                 logger.info("Variety object created successfully", **safe_context)
#                 return variety

#         except VarietyFactoryValidationError as e:
#             logger.error(
#                 "Variety validation failed",
#                 error=sanitize_error_message(str(e)),
#                 field=e.field,
#                 **safe_context,
#             )
#             raise
#         except Exception as e:
#             sanitized_error = sanitize_error_message(str(e))
#             logger.critical(
#                 "Unexpected error during variety creation",
#                 error=sanitized_error,
#                 error_type=type(e).__name__,
#                 **safe_context,
#             )
#             raise BusinessLogicError(
#                 message="An unexpected error occurred during variety creation",
#                 status_code=500,
#             )

#     @staticmethod
#     def validate_variety_name(variety_name: str) -> None:
#         """Validate the variety name using the common validator."""
#         field = "variety_name"
#         context = {
#             "field": field,
#             "variety_name": variety_name,
#             "request_id": request_id_ctx_var.get(),
#         }

#         try:
#             # Use the common validator
#             validate_name_field(None, variety_name)
#             logger.debug("Variety name validation passed", **context)
#         except ValueError as e:
#             logger.debug("Variety name validation failed", error=str(e), **context)
#             raise VarietyFactoryValidationError(str(e), field)

#     @staticmethod
#     def validate_week_pairs(variety_data: VarietyCreate) -> None:
#         """Validate that week pairs are provided together."""
#         field = "week_pairs"
#         context = {
#             "field": field,
#             "request_id": request_id_ctx_var.get(),
#         }

#         # Check transplant pair
#         if (variety_data.transplant_week_start is None) != (variety_data.transplant_week_end is None):
#             raise VarietyFactoryValidationError(
#                 "Both transplant_week_start and transplant_week_end must be provided together",
#                 field
#             )

#         # Check prune pair
#         if (variety_data.prune_week_start is None) != (variety_data.prune_week_end is None):
#             raise VarietyFactoryValidationError(
#                 "Both prune_week_start and prune_week_end must be provided together",
#                 field
#             )

#         logger.debug("Week pairs validation passed", **context)

#     @staticmethod
#     def validate_feed_group(variety_data: VarietyCreate) -> None:
#         """Validate that feed fields are provided together."""
#         field = "feed_group"
#         context = {
#             "field": field,
#             "request_id": request_id_ctx_var.get(),
#         }

#         feed_fields = [
#             variety_data.feed_id,
#             variety_data.feed_week_start,
#             variety_data.feed_frequency_id
#         ]
#         provided_fields = [f for f in feed_fields if f is not None]

#         if 0 < len(provided_fields) < 3:
#             raise VarietyFactoryValidationError(
#                 "feed_id, feed_week_start, and feed_frequency_id must all be provided together",
#                 field
#             )

#         logger.debug("Feed group validation passed", **context)
