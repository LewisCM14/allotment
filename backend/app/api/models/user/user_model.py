"""
User Models
- Defines SQLAlchemy ORM models for the User and UserAllotment tables.
- Includes utility methods for password hashing and verification.
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
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)

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

    @property
    def id(self) -> uuid.UUID:
        return self.user_id

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        log_context = {
            "user_id": str(self.user_id) if self.user_id else "new_user",
            "request_id": request_id_ctx_var.get(),
        }

        try:
            self.user_password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            logger.debug("Password hashed successfully", **log_context)
        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.error(
                "Failed to hash password",
                error=sanitized_error,
                error_type=type(e).__name__,
                **log_context,
            )
            raise

    def check_password(self, password: str) -> bool:
        """Verify a password."""
        log_context = {
            "user_id": str(self.user_id),
            "request_id": request_id_ctx_var.get(),
        }

        try:
            result = bcrypt.checkpw(
                password.encode("utf-8"), self.user_password_hash.encode("utf-8")
            )
            logger.debug("Password verification performed", **log_context)
            return result
        except Exception as e:
            sanitized_error = sanitize_error_message(str(e))
            logger.error(
                "Password verification error",
                error=sanitized_error,
                error_type=type(e).__name__,
                **log_context,
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
        log_context = {
            "user_id": str(self.user_id) if self.user_id else None,
            "allotment_id": str(self.user_allotment_id)
            if self.user_allotment_id
            else None,
            "postal_code": self.allotment_postal_zip_code,
            "width": self.allotment_width_meters,
            "length": self.allotment_length_meters,
            "request_id": request_id_ctx_var.get(),
        }

        # Only calculate area if both width and length are available
        area_sqm = None
        if (
            self.allotment_width_meters is not None
            and self.allotment_length_meters is not None
        ):
            area_sqm = round(
                self.allotment_width_meters * self.allotment_length_meters, 2
            )

        logger.info(
            "UserAllotment created",
            action="allotment_creation",
            area_sqm=area_sqm,
            **log_context,
        )
