"""
User Schemas
- Defines Pydantic schemas for user-related API operations.
- These schemas are used for request validation and response serialization.
"""

from app.api.schemas.base_schema import SecureBaseModel
from pydantic import ConfigDict, EmailStr, Field


class UserCreate(SecureBaseModel):
    """Schema for user registration."""

    user_email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    user_password: str = Field(
        ...,
        min_length=8,
        max_length=30,
        description="Password must be between 8 and 30 characters",
        examples=["SecurePass123!"],
    )
    user_first_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="First name must be between 2 and 50 characters",
        examples=["John"],
    )
    user_country_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code",
        examples=["GB"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": "user@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "John",
                "user_country_code": "GB",
            }
        }
    )


class UserLogin(SecureBaseModel):
    """Schema for user login."""

    user_email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    user_password: str = Field(
        ...,
        min_length=8,
        max_length=30,
        description="User's password",
        examples=["SecurePass123!"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": "user@example.com",
                "user_password": "SecurePass123!",
            }
        }
    )


class TokenResponse(SecureBaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."],
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
        examples=["eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
        examples=["bearer"],
    )
    user_first_name: str | None = Field(
        default=None,
        description="User's first name",
        examples=["John"],
    )
    is_email_verified: bool = Field(
        default=False,
        description="Indicates if the user's email is verified",
        examples=[True, False],
    )
    user_id: str = Field(
        ...,
        description="The unique ID of the user",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "user_first_name": "John",
                "is_email_verified": True,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class RefreshRequest(SecureBaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(
        ...,
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
