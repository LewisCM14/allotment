"""
User Active Variety Factory
- Responsible for creating UserActiveVariety association objects.
- Applies minimal validation before persistence.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict

import structlog

from app.api.core.logging import log_timing
from app.api.middleware.exception_handler import BusinessLogicError
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.user.user_model import UserActiveVariety

logger = structlog.get_logger()


class UserActiveVarietyFactory:
    """Factory for creating UserActiveVariety objects."""

    @staticmethod
    def create(user_id: uuid.UUID, variety_id: uuid.UUID) -> UserActiveVariety:
        """Create a UserActiveVariety association with validated identifiers."""
        if not isinstance(user_id, uuid.UUID) or not isinstance(variety_id, uuid.UUID):
            raise BusinessLogicError(
                message="User ID and Variety ID must be valid UUID instances.",
                status_code=400,
            )

        context: Dict[str, Any] = {
            "user_id": str(user_id),
            "variety_id": str(variety_id),
            "request_id": request_id_ctx_var.get(),
            "operation": "create_user_active_variety",
        }

        try:
            with log_timing(
                "create_user_active_variety", request_id=context["request_id"]
            ):
                logger.info("Creating user active variety association", **context)
                association = UserActiveVariety()
                association.user_id = user_id
                association.variety_id = variety_id
                return association
        except Exception as exc:
            sanitized_error = sanitize_error_message(str(exc))
            logger.error(
                "Failed to create user active variety association",
                error=sanitized_error,
                error_type=type(exc).__name__,
                **context,
            )
            raise BusinessLogicError(
                message="Unable to create user active variety association.",
                status_code=500,
            ) from exc
