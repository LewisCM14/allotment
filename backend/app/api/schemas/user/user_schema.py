"""
User Schemas
- Defines Pydantic schemas for user-related API operations.
- These schemas are used for request validation and response serialization.
"""

from pydantic import ConfigDict, EmailStr, Field

from app.api.schemas.base_schema import SecureBaseModel

# Constants for user schemas
USER_EMAIL_DESC = "User's email address"
USER_EMAIL_EXAMPLE = "user@example.com"
USER_PASSWORD_EXAMPLE = "SecurePass123!"
NEW_PASSWORD_EXAMPLE = "NewSecurePass123!"
JWT_EXAMPLE = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
FIRST_NAME_EXAMPLE = "John"
USER_ID_EXAMPLE = "123e4567-e89b-12d3-a456-426614174000"
NEW_PASSWORD_DESC = "New password"


class UserCreate(SecureBaseModel):
    """Schema for user registration."""

    user_email: EmailStr = Field(
        ...,
        description=USER_EMAIL_DESC,
        examples=[USER_EMAIL_EXAMPLE],
    )
    user_password: str = Field(
        ...,
        min_length=8,
        max_length=30,
        description="Password must be between 8 and 30 characters",
        examples=[USER_PASSWORD_EXAMPLE],
    )
    user_first_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="First name must be between 2 and 50 characters",
        examples=[FIRST_NAME_EXAMPLE],
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
                "user_email": USER_EMAIL_EXAMPLE,
                "user_password": USER_PASSWORD_EXAMPLE,
                "user_first_name": FIRST_NAME_EXAMPLE,
                "user_country_code": "GB",
            }
        }
    )


class UserLogin(SecureBaseModel):
    """Schema for user login."""

    user_email: EmailStr = Field(
        ...,
        description=USER_EMAIL_DESC,
        examples=[USER_EMAIL_EXAMPLE],
    )
    user_password: str = Field(
        ...,
        min_length=8,
        max_length=30,
        description="User's password",
        examples=[USER_PASSWORD_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": USER_EMAIL_EXAMPLE,
                "user_password": USER_PASSWORD_EXAMPLE,
            }
        }
    )


class TokenResponse(SecureBaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=[JWT_EXAMPLE],
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
        examples=[JWT_EXAMPLE],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
        examples=["bearer"],
    )
    user_first_name: str | None = Field(
        default=None,
        description="User's first name",
        examples=[FIRST_NAME_EXAMPLE],
    )
    is_email_verified: bool = Field(
        default=False,
        description="Indicates if the user's email is verified",
        examples=[True, False],
    )
    user_id: str = Field(
        ...,
        description="The unique ID of the user",
        examples=[USER_ID_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": JWT_EXAMPLE,
                "refresh_token": JWT_EXAMPLE,
                "token_type": "bearer",
                "user_first_name": FIRST_NAME_EXAMPLE,
                "is_email_verified": True,
                "user_id": USER_ID_EXAMPLE,
            }
        }
    )


class RefreshRequest(SecureBaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(
        ...,
        description="JWT refresh token to exchange for a new access token",
        examples=[JWT_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": JWT_EXAMPLE,
            }
        }
    )


class MessageResponse(SecureBaseModel):
    """Schema for simple message responses."""

    message: str = Field(
        ...,
        description="Response message",
        examples=["Operation completed successfully"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
            }
        }
    )


class VerificationStatusResponse(SecureBaseModel):
    """Schema for email verification status response."""

    is_email_verified: bool = Field(
        ...,
        description="Indicates if the user's email is verified",
        examples=[True, False],
    )
    user_id: str = Field(
        ...,
        description="The unique ID of the user",
        examples=[USER_ID_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_email_verified": True,
                "user_id": USER_ID_EXAMPLE,
            }
        }
    )


class PasswordResetRequest(SecureBaseModel):
    """Schema for password reset request."""

    user_email: EmailStr = Field(
        ...,
        description=USER_EMAIL_DESC,
        examples=[USER_EMAIL_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": USER_EMAIL_EXAMPLE,
            }
        }
    )


class EmailRequest(SecureBaseModel):
    """Schema for requests requiring only user email."""

    user_email: EmailStr = Field(
        ...,
        description=USER_EMAIL_DESC,
        examples=[USER_EMAIL_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_email": USER_EMAIL_EXAMPLE,
            }
        }
    )


class PasswordUpdate(SecureBaseModel):
    """Schema for updating password when token is in path."""

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=30,
        description=NEW_PASSWORD_DESC,
        examples=[NEW_PASSWORD_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_password": NEW_PASSWORD_EXAMPLE,
            }
        }
    )


class PasswordResetAction(SecureBaseModel):
    """Schema for password reset with token."""

    token: str = Field(
        ...,
        description="JWT reset token",
        examples=[JWT_EXAMPLE],
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=30,
        description=NEW_PASSWORD_DESC,
        examples=[NEW_PASSWORD_EXAMPLE],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": JWT_EXAMPLE,
                "new_password": NEW_PASSWORD_EXAMPLE,
            }
        }
    )
