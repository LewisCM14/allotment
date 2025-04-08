"""
User Factory
- Responsible for creating User domain objects.
- Applies business rules and validations during the creation process.
- Ensures that only valid User objects are created before persistence.
"""

import re

import structlog

from app.api.core.logging import log_timing
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.user.user_model import User
from app.api.schemas.user.user_schema import UserCreate

logger = structlog.get_logger()


class ValidationError(ValueError):
    """Custom exception for user validation errors."""

    def __init__(self, message: str, field: str = "unknown") -> None:
        """Initialize validation error with message and field.

        Args:
            message: Error message
            field: The field that failed validation
        """
        super().__init__(message)
        self.field = field


class UserFactory:
    """Factory for creating User objects."""

    @staticmethod
    def create_user(user_data: UserCreate) -> User:
        """Create a User object with validated data."""
        safe_context = {
            "email": user_data.user_email,
            "first_name": user_data.user_first_name,
            "country_code": user_data.user_country_code,
            "request_id": request_id_ctx_var.get(),
        }

        try:
            with log_timing("user_creation", **safe_context):
                logger.debug("Validating user data", **safe_context)

                UserFactory.validate_first_name(user_data.user_first_name)
                UserFactory.validate_country_code(user_data.user_country_code)
                UserFactory.validate_password(user_data.user_password)

                user = User()
                user.user_email = user_data.user_email
                user.user_first_name = user_data.user_first_name
                user.user_country_code = user_data.user_country_code
                user.is_email_verified = False
                user.set_password(user_data.user_password)

                logger.info("User object created successfully", **safe_context)
                return user

        except ValidationError as e:
            logger.warning(
                "User validation failed",
                error=sanitize_error_message(str(e)),
                field=e.field,
                **safe_context,
            )
            raise
        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.error(
                "Unexpected error during user creation",
                error=sanitized_error,
                error_type=type(e).__name__,
                **safe_context,
            )
            raise

    @staticmethod
    def validate_first_name(first_name: str) -> None:
        """Validate the user's first name."""
        field = "first_name"
        context = {
            "field": field,
            "first_name": first_name,
            "request_id": request_id_ctx_var.get(),
        }

        try:
            if len(first_name) < 2:
                logger.debug(
                    "First name too short",
                    length=len(first_name),
                    min_length=2,
                    **context,
                )
                raise ValidationError(
                    "First name must be at least 2 characters long", field
                )
            if len(first_name) > 50:
                logger.debug(
                    "First name too long",
                    length=len(first_name),
                    max_length=50,
                    **context,
                )
                raise ValidationError(
                    "First name cannot be longer than 50 characters", field
                )
            if not re.match(r"^[a-zA-Z]+(?:[- ][a-zA-Z]+)*$", first_name):
                logger.debug("First name contains invalid characters", **context)
                raise ValidationError(
                    "First name can only contain letters, spaces, and hyphens", field
                )

            logger.debug("First name validation passed", **context)
        except ValidationError:
            raise

    @staticmethod
    def validate_country_code(country_code: str) -> None:
        """Validate the user's country code."""
        field = "country_code"
        context = {
            "field": field,
            "country_code": country_code,
            "request_id": request_id_ctx_var.get(),
        }

        try:
            if len(country_code) != 2:
                logger.debug(
                    "Invalid country code length",
                    length=len(country_code),
                    expected=2,
                    **context,
                )
                raise ValidationError(
                    "Country code must be exactly 2 characters", field
                )

            logger.debug("Country code validation passed", **context)
        except ValidationError:
            raise

    @staticmethod
    def validate_password(password: str) -> None:
        """Validate password complexity."""
        field = "password"
        # Only log password metadata, never the content
        context = {
            "field": field,
            "password_length": len(password),
            "request_id": request_id_ctx_var.get(),
        }

        try:
            if len(password) < 8:
                logger.debug("Password too short", min_length=8, **context)
                raise ValidationError(
                    "Password must be at least 8 characters long", field
                )
            if len(password) > 30:
                logger.debug("Password too long", max_length=30, **context)
                raise ValidationError(
                    "Password cannot be longer than 30 characters", field
                )

            # Check password complexity requirements
            complexity_checks = {
                "uppercase letter": any(c.isupper() for c in password),
                "lowercase letter": any(c.islower() for c in password),
                "digit": any(c.isdigit() for c in password),
                "special character": any(not c.isalnum() for c in password),
            }

            # Collect missing requirements
            requirements = [
                req for req, passed in complexity_checks.items() if not passed
            ]

            if requirements:
                logger.debug(
                    "Password missing requirements",
                    missing_requirements=requirements,
                    requirement_count=len(requirements),
                    **context,
                )
                raise ValidationError(
                    f"Password must contain {', '.join(requirements)}", field
                )

            logger.debug("Password validation passed", **context)
        except ValidationError:
            raise
