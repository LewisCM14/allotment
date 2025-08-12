"""
Common Schema Validators
- Provides reusable validation functions for Pydantic schemas
- Implements the general VARCHAR constraint rule: lowercase, hyphens, and spaces only
"""

import re


def validate_general_text_field(value: str, field_name: str) -> str:
    """
    Validate text field according to general data integrity rule.

    Rules:
    - Only lowercase letters, hyphens, and single spaces allowed
    - No special characters except hyphens
    - No consecutive spaces
    - No leading/trailing spaces

    Args:
        value: The string value to validate
        field_name: Name of the field being validated (for error messages)

    Returns:
        str: The validated and normalized value (lowercase, trimmed)

    Raises:
        ValueError: If validation fails
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    # Normalize: strip and convert to lowercase
    normalized = value.strip().lower()

    # Check for invalid characters (only letters, hyphens, and single spaces allowed)
    if not re.match(r"^[a-z]+(?:[- ][a-z]+)*$", normalized):
        raise ValueError(
            f"{field_name} can only contain lowercase letters, hyphens, and single spaces between words"
        )

    # Check for consecutive spaces (should be handled by regex, but double-check)
    if "  " in normalized:
        raise ValueError(f"{field_name} cannot contain consecutive spaces")

    return normalized


def validate_notes_field(value: str, field_name: str, max_length: int = 500) -> str:
    """
    Validate notes field (exempt from general data integrity rule).

    Args:
        value: The string value to validate
        field_name: Name of the field being validated
        max_length: Maximum allowed length

    Returns:
        str: The validated value (trimmed but not lowercased)

    Raises:
        ValueError: If validation fails
    """
    if not value:
        return value

    # Only trim whitespace, don't enforce character restrictions for notes
    normalized = value.strip()

    if len(normalized) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters")

    return normalized


def validate_text_field(v: str, field_name: str = "field") -> str:
    """
    Generic Pydantic validator for text fields following the general data integrity rule.
    Can be used with @field_validator decorator.

    Example:
        @field_validator("name")
        @classmethod
        def validate_name(cls, v: str) -> str:
            return validate_text_field(v, "name")

        @field_validator("family_name")
        @classmethod
        def validate_family_name(cls, v: str) -> str:
            return validate_text_field(v, "family_name")
    """
    return validate_general_text_field(v, field_name)
