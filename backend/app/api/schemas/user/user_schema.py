"""
User Schema
- Applies the validation and business logic to a User before persistence.
"""

from typing import Annotated

from pydantic import BaseModel, EmailStr, Field
from pydantic.types import StringConstraints


class UserCreate(BaseModel):
    """
    Schema for user registration

    user_password: password must contain at least two uppercase letters, one special character, two digits, three lowercase letters, and is at least eight characters long.
    user_first_name: can only contain letters, hyphens, and spaces. No consecutive spaces or hyphens. No leading or trailing spaces/hyphens.
    """

    user_email: EmailStr = Field(
        description="User's email address", examples=["user@example.com"]
    )
    user_password: Annotated[
        str,
        StringConstraints(
            min_length=8,
            max_length=30,
            pattern=r"^(?=.*[A-Z].*[A-Z])(?=.*[!@#$&*])(?=.*[0-9].*[0-9])(?=.*[a-z].*[a-z].*[a-z]).{8,}$",
        ),
    ] = Field(
        description="Password must contain: 2 uppercase, 1 special char, 2 digits, 3 lowercase",
        examples=["TestPass123!@"],
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
