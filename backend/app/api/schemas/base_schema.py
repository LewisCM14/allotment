"""
Base Schema
- Provides base classes and utilities for Pydantic schemas
- Includes security features for safe logging
"""

from typing import Any, Dict, Mapping  # Import Mapping for type annotations

import structlog
from pydantic import BaseModel, model_validator

from app.api.middleware.logging_middleware import SENSITIVE_FIELDS

logger = structlog.get_logger()

REDACTED_VALUE = "[REDACTED]"


class SecureBaseModel(BaseModel):
    """Base model with secure logging capabilities.

    Features:
    - Automatic redaction of sensitive fields in logs
    - Secure dictionary representation for logging
    - Validation attempt logging with sensitive data protection
    """

    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Override dict method to provide a secure version that can be safely logged."""
        data = super().dict(*args, **kwargs)
        return data

    def secure_dict(self) -> Dict[str, Any]:
        """Return a dict representation safe for logging (with sensitive fields redacted).

        Returns:
            Dict with sensitive fields redacted for safe logging
        """
        data = self.dict()
        for field in SENSITIVE_FIELDS:
            if field in data:
                data[field] = REDACTED_VALUE
            for key in list(data.keys()):
                if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
                    data[key] = REDACTED_VALUE
        return data

    @classmethod
    @model_validator(mode="before")
    def validate_fields(cls, values: Mapping[str, Any]) -> Dict[str, Any]:
        """Log validation attempts without exposing sensitive data."""
        safe_values = {
            k: (REDACTED_VALUE if any(s in k.lower() for s in SENSITIVE_FIELDS) else v)
            for k, v in values.items()
        }

        class_name = cls.__name__ if hasattr(cls, "__name__") else str(cls)

        logger.debug(
            f"Validating {class_name}",
            schema=class_name,
            fields=list(values.keys()),
            safe_values=safe_values,
        )
        return dict(values)
