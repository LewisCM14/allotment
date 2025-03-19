"""
User Schema
- Applies the validation and business logic to a User before persistence.
"""

import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic.types import StringConstraints


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
        description="Password must contain: 2 uppercase, 1 special char, 2 digits, 3 lowercase",
        examples=["TestPass123!@"],
    )

    user_first_name: Annotated[
        str,
        StringConstraints(
            min_length=2,
            max_length=50,
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
        if len(v) < 2:
            raise ValueError("First name must be at least 2 characters long")
        if len(v) > 50:
            raise ValueError("First name cannot be longer than 50 characters")
        if not re.match(r"^[a-zA-Z]+(?:[- ][a-zA-Z]+)*$", v):
            raise ValueError("First name can only contain letters, spaces, and hyphens")
        return v

    @field_validator("user_country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Validate country code format."""
        if len(v) != 2:
            raise ValueError("Country code must be exactly 2 characters")
        return v.upper()

    @field_validator("user_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least two uppercase letters")

        uppercase_count = sum(1 for c in v if c.isupper())
        if uppercase_count < 2:
            raise ValueError("Password must contain at least two uppercase letters")

        if not any(c in "!@#$&*" for c in v):
            raise ValueError(
                "Password must contain at least one special character (!@#$&*)"
            )

        digit_count = sum(1 for c in v if c.isdigit())
        if digit_count < 2:
            raise ValueError("Password must contain at least two digits")

        lowercase_count = sum(1 for c in v if c.islower())
        if lowercase_count < 3:
            raise ValueError("Password must contain at least three lowercase letters")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "user_password": "TestPass123!@",
                "user_first_name": "John Smith",
                "user_country_code": "GB",
            }
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "user@example.com",
                "user_password": "TestPass123!@",
            }
        }


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        description="JWT access token",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."],
    )

    token_type: str = Field(
        default="bearer", description="Token type", examples=["bearer"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
            }
        }
