"""
User Repository
- Encapsulates database operations for User model
"""

from typing import Tuple

import bcrypt
import structlog
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User
from app.api.schemas.user.user_schema import UserCreate
from app.api.v1.auth import create_access_token

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
            except (TypeError, ValueError) as e:
                logger.error(
                    "Password hashing failed", error=str(e), error_type=type(e).__name__
                )
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
