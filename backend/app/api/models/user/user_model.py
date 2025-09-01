"""
User Models
- Defines SQLAlchemy ORM models for the User and UserAllotment tables.
- Includes utility methods for password hashing and verification.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import bcrypt
import structlog
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)

if TYPE_CHECKING:
    from app.api.models.grow_guide.calendar_model import Day
    from app.api.models.grow_guide.guide_options_model import Feed
    from app.api.models.grow_guide.variety_model import Variety

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
    registered_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_active_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    allotment: Mapped[Optional["UserAllotment"]] = relationship(
        "UserAllotment",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    feed_days: Mapped[list["UserFeedDay"]] = relationship(
        "UserFeedDay", back_populates="user", cascade="all, delete-orphan"
    )
    varieties: Mapped[list["Variety"]] = relationship(
        "Variety",
        back_populates="user",
        foreign_keys="[Variety.owner_user_id]",
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


class UserFeedDay(Base):
    """UserFeedDay model representing a user's preferred day for each type of plant feed."""

    __tablename__ = "user_feed_day"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    feed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed.feed_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    day_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("day.day_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="feed_days")
    feed: Mapped["Feed"] = relationship("Feed", back_populates="user_feed_days")
    day: Mapped["Day"] = relationship("Day")
