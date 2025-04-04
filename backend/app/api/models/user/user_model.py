"""
Models the User & User Allotment Tables

This module defines the SQLAlchemy ORM models for:
- User: Stores user account information
- UserAllotment: Stores user allotment details with dimensions and location
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

import bcrypt
import structlog
from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

logger = structlog.get_logger()


class User(Base):
    """User model representing registered users in the system."""

    __tablename__ = "user"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    user_email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    user_password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    user_first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    user_country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    allotment: Mapped[Optional["UserAllotment"]] = relationship(
        "UserAllotment",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        """Hash and store the password.

        Args:
            password: The plain text password to hash
        """
        try:
            self.user_password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            logger.info(
                "Password set successfully",
                user_id=str(self.user_id),
                user_email=self.user_email,
            )
        except Exception as e:
            logger.error(
                "Failed to set password",
                user_id=str(self.user_id),
                user_email=self.user_email,
                error=str(e),
            )
            raise

    def check_password(self, password: str) -> bool:
        """Verify a password.

        Args:
            password: The plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            is_valid = bcrypt.checkpw(
                password.encode("utf-8"), self.user_password_hash.encode("utf-8")
            )
            logger.info(
                "Password verification attempt",
                user_id=str(self.user_id),
                user_email=self.user_email,
                success=is_valid,
            )
            return is_valid
        except Exception as e:
            logger.error(
                "Password verification error",
                user_id=str(self.user_id),
                user_email=self.user_email,
                error=str(e),
            )
            raise

    __table_args__ = (
        CheckConstraint("LENGTH(user_email) >= 7", name="min_length_user_email"),
        CheckConstraint(
            "LENGTH(user_first_name) >= 2", name="min_length_user_first_name"
        ),
        CheckConstraint(
            "LENGTH(user_country_code) = 2", name="correct_country_code_format"
        ),
    )


class UserAllotment(Base):
    """UserAllotment model representing a user's allotment details."""

    __tablename__ = "user_allotment"

    user_allotment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    allotment_postal_zip_code: Mapped[str] = mapped_column(String(7), nullable=False)
    allotment_width_meters: Mapped[float] = mapped_column(Float, nullable=False)
    allotment_length_meters: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="allotment")

    __table_args__ = (
        CheckConstraint(
            "LENGTH(allotment_postal_zip_code) >= 5",
            name="min_length_allotment_postal_zip_code",
        ),
        CheckConstraint(
            "allotment_width_meters >= 1.0 AND allotment_width_meters <= 100.0",
            name="check_width_range",
        ),
        CheckConstraint(
            "allotment_length_meters >= 1.0 AND allotment_length_meters <= 100.0",
            name="check_length_range",
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        logger.info(
            "UserAllotment created",
            user_id=str(self.user_id),
            allotment_id=str(self.user_allotment_id),
            postal_code=self.allotment_postal_zip_code,
            dimensions=f"{self.allotment_width_meters}x{self.allotment_length_meters}",
        )
