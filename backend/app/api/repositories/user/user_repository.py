"""
User Repository
- Encapsulates database operations for User model
"""

from typing import Tuple
from uuid import UUID

import bcrypt
import structlog
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth import create_access_token
from app.api.models import User
from app.api.schemas.user.user_schema import UserCreate

logger = structlog.get_logger()


class UserRepository:
    """User repository for database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, user_data: UserCreate) -> Tuple[User, str]:
        """Create a new user.

        Args:
            user_data: Validated user data

        Returns:
            Tuple[User, str]: Created user and access token

        Raises:
            HTTPException:
                - 409: Email already exists
                - 500: Database error
        """
        logger.info(
            "Attempting to create new user",
            email=user_data.user_email,
            country_code=user_data.user_country_code,
        )
        try:
            try:
                hashed_password = bcrypt.hashpw(
                    user_data.user_password.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
            except (TypeError, ValueError):
                logger.error("Password hashing failed", error="REDACTED")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing password",
                )

            # Create user instance
            new_user = User()
            new_user.user_email = user_data.user_email
            new_user.user_password_hash = hashed_password
            new_user.user_first_name = user_data.user_first_name
            new_user.user_country_code = user_data.user_country_code
            new_user.is_email_verified = False

            try:
                self.db.add(new_user)
                await self.db.commit()
                await self.db.refresh(new_user)
                logger.info(
                    "User created successfully",
                    user_id=str(new_user.user_id),
                    email=new_user.user_email,
                )
            except IntegrityError as e:
                await self.db.rollback()
                logger.warning(
                    "Email already exists", email=user_data.user_email, error=str(e)
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )
            except SQLAlchemyError as e:
                await self.db.rollback()
                logger.error(
                    "Database error during user creation",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user",
                )

            try:
                access_token = create_access_token(user_id=str(new_user.user_id))
                logger.info("Access token generated", user_id=str(new_user.user_id))
            except Exception as e:
                logger.error(
                    "Token generation failed",
                    user_id=str(new_user.user_id),
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating access token",
                )
            return new_user, access_token

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during user creation",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    async def verify_email(self, user_id: str) -> None:
        """Mark a user's email as verified.

        Args:
            user_id: The ID of the user to update

        Raises:
            HTTPException: If the user is not found or the update fails
        """
        logger.info("Attempting to verify email", user_id=user_id)
        try:
            user_uuid = UUID(user_id)

            user = await self.db.get(User, user_uuid)
            if not user:
                logger.warning("User not found", user_id=user_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            user.is_email_verified = True
            await self.db.commit()
            logger.info("Email verified successfully", user_id=user_id)
        except ValueError:
            logger.error("Invalid user_id format", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format",
            )
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(
                "Database error during email verification",
                user_id=user_id,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify email",
            )
