"""
User Repository
- Encapsulate the logic required to access the: User, User Allotment, User Feed Day and User Active Varieties tables.
"""

from typing import Tuple

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.models import User
from app.api.schemas.user import UserCreate
from app.api.v1.auth import create_access_token


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> Tuple[User, str]:
        """
        Hashes the user's password and stores the user in the database.

        Args:
            user_data: Validated user data from the request

        Returns:
            Tuple containing the created user and access token

        Raises:
            HTTPException: If user creation fails or email already exists
        """
        try:
            hashed_password = bcrypt.hashpw(
                user_data.user_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            new_user = User(
                user_email=user_data.user_email,
                user_password_hash=hashed_password,
                user_first_name=user_data.user_first_name,
                user_country_code=user_data.user_country_code,
            )

            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            # Generate JWT Token
            access_token = create_access_token(user_id=str(new_user.user_id))
            return new_user, access_token

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            ) from e
