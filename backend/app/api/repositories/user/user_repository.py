"""
User Repository
- Encapsulates database operations for User model
"""

from typing import Tuple

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models import User
from app.api.schemas.user.user_schema import UserCreate
from app.api.v1.auth import create_access_token


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
        try:
            try:
                hashed_password = bcrypt.hashpw(
                    user_data.user_password.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
            except (TypeError, ValueError):
                # add logging here
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

            # Database operations with proper transaction handling
            try:
                self.db.add(new_user)
                await self.db.commit()
                await self.db.refresh(new_user)
            except IntegrityError:
                await self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )
            except SQLAlchemyError:
                await self.db.rollback()
                # add logging here
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user",
                )

            try:
                access_token = create_access_token(user_id=str(new_user.user_id))
            except Exception:
                # add logging here
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating access token",
                )
            return new_user, access_token

        except HTTPException:
            raise
        except Exception:
            # add logging here
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )
