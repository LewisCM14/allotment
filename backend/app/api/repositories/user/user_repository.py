"""
User Repository
- Encapsulates database operations for User model
"""

from typing import Tuple

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.models import User
from app.api.schemas.user.user_schema import UserCreate
from app.api.v1.auth import create_access_token


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, user_data: UserCreate) -> Tuple[User, str]:
        """Create a new user.

        Args:
            user_data: Validated user data from request

        Returns:
            Tuple[User, str]: Created user and access token

        Raises:
            HTTPException: If user creation fails
        """
        try:
            # Hash password
            hashed_password = bcrypt.hashpw(
                user_data.user_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # Create user instance
            new_user = User()
            new_user.user_email = user_data.user_email
            new_user.user_password_hash = hashed_password
            new_user.user_first_name = user_data.user_first_name
            new_user.user_country_code = user_data.user_country_code

            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            # Generate access token
            access_token = create_access_token(user_id=str(new_user.user_id))
            return new_user, access_token

        except IntegrityError:
            self.db.rollback()
            raise
