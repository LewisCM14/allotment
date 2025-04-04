"""
User Schema
- Applies the validation and business logic to a User before persistence.
"""

import re
from typing import Annotated

import structlog
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.types import StringConstraints

logger = structlog.get_logger()


class UserCreate(BaseModel):
    """
    Schema for user registration

    user_first_name: can only contain letters, hyphens, and spaces.
    No consecutive spaces or hyphens. No leading or trailing spaces/hyphens.
    """

    user_email: EmailStr = Field(
        description="User's email address", examples=["user@example.com"]
    )

    user_password: Annotated[
        str,
        StringConstraints(
            min_length=8,
            max_length=30,
        ),
    ] = Field(
        description="Password must contain at least: 1 uppercase letter, 1 number, and 1 special character",
        examples=["TestPass1!"],
    )

    user_first_name: Annotated[
        str,
        StringConstraints(
            min_length=2, max_length=50, pattern=r"^[a-zA-Z]+(?:[- ][a-zA-Z]+)*$"
        ),
    ] = Field(
        description="First name with optional hyphen or space", examples=["John Smith"]
    )

    user_country_code: Annotated[
        str, StringConstraints(min_length=2, max_length=2, to_upper=True)
    ] = Field(description="ISO 3166-1 alpha-2 country code", examples=["GB"])

    @field_validator("user_first_name")
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        """Validate first name format."""
        try:
            if len(v) < 2:
                logger.warning("First name too short", value=v, length=len(v))
                raise ValueError("First name must be at least 2 characters long")
            if len(v) > 50:
                logger.warning("First name too long", value=v, length=len(v))
                raise ValueError("First name cannot be longer than 50 characters")
            if not re.match(r"^[a-zA-Z]+(?:[- ][a-zA-Z]+)*$", v):
                logger.warning("Invalid first name format", value=v)
                raise ValueError(
                    "First name can only contain letters, spaces, and hyphens"
                )
            logger.debug("First name validation successful", value=v)
            return v
        except ValueError as e:
            logger.error("First name validation failed", error=str(e), value=v)
            raise

    @field_validator("user_country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Validate country code format."""
        try:
            if len(v) != 2:
                logger.warning("Invalid country code length", value=v, length=len(v))
                raise ValueError("Country code must be exactly 2 characters")
            logger.debug("Country code validation successful", value=v.upper())
            return v.upper()
        except ValueError as e:
            logger.error("Country code validation failed", error=str(e), value=v)
            raise

    @field_validator("user_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity requirements."""

        uppercase_count = sum(1 for c in v if c.isupper())
        digit_count = sum(1 for c in v if c.isdigit())
        special_chars_set = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~"
        special_chars = any(c in special_chars_set for c in v)

        logger.debug(
            "Password validation",
            uppercase_count=uppercase_count,
            digit_count=digit_count,
            has_special=special_chars,
        )

        errors = []
        if uppercase_count < 1:
            errors.append("one uppercase letter")
        if digit_count < 1:
            errors.append("one digit")
        if not special_chars:
            errors.append(f"one special character ({special_chars_set})")

        if errors:
            logger.warning(
                "Password validation failed",
                uppercase_count=uppercase_count,
                digit_count=digit_count,
                has_special=special_chars,
            )

            error_msg = (
                f"Value error, Password must contain at least: {', '.join(errors)}"
            )
            raise ValueError(error_msg)

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": "user@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "John Smith",
                "user_country_code": "GB",
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for user login."""

    user_email: EmailStr = Field(
        description="User's email address", examples=["user@example.com"]
    )

    user_password: str = Field(
        min_length=8,
        max_length=30,
        description="User's password",
        examples=["TestPass123!@"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": "user@example.com",
                "user_password": "TestPass123!@",
            }
        }
    )


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        description="JWT access token",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."],
    )

    refresh_token: str = Field(
        description="JWT refresh token for obtaining new access tokens",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."],
    )

    token_type: str = Field(
        default="bearer", description="Token type", examples=["bearer"]
    )

    user_first_name: str | None = Field(
        default=None, description="User's first name", examples=["John"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "user_first_name": "John",
            }
        }
    )


class RefreshRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(
        description="JWT refresh token to exchange for a new access token",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            }
        }
    )
