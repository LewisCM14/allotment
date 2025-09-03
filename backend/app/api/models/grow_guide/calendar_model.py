"""
Models the Day, Week & Month Tables
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

if TYPE_CHECKING:
    from app.api.models.user.user_model import UserFeedDay


class Day(Base):
    """Day model representing the seven days of the week."""

    __tablename__ = "day"

    day_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )
    day_name: Mapped[str] = mapped_column(String(3), nullable=False)

    # Relationship to UserFeedDay
    user_feed_days: Mapped[list["UserFeedDay"]] = relationship(
        "UserFeedDay", back_populates="day"
    )

    __table_args__ = (
        UniqueConstraint("day_name", name="uq_day_name"),
        UniqueConstraint("day_number", name="uq_day_number"),
    )


class Week(Base):
    """Week model representing the 52 weeks of the year with start and end dates."""

    __tablename__ = "week"

    week_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    week_number: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
    )
    start_month_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    week_start_date: Mapped[str] = mapped_column(
        String(5), nullable=False
    )  # Format: MM/DD
    week_end_date: Mapped[str] = mapped_column(
        String(5), nullable=False
    )  # Format: MM/DD

    __table_args__ = (
        UniqueConstraint("week_number", name="uq_week_number"),
        # Cross-compatible format constraints
        CheckConstraint(
            "LENGTH(week_start_date) = 5",
            name="check_week_start_date_length"
        ),
        CheckConstraint(
            "LENGTH(week_end_date) = 5",
            name="check_week_end_date_length"
        ),
        CheckConstraint(
            "SUBSTR(week_start_date, 3, 1) = '/'",
            name="check_week_start_date_slash"
        ),
        CheckConstraint(
            "SUBSTR(week_end_date, 3, 1) = '/'",
            name="check_week_end_date_slash"
        ),
    )


class Month(Base):
    """Month model representing the twelve months of the year."""

    __tablename__ = "month"

    month_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    month_number: Mapped[int] = mapped_column(
        nullable=False,
        unique=True,
    )
    month_name: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        UniqueConstraint("month_number", name="uq_month_number"),
        UniqueConstraint("month_name", name="uq_month_name"),
    )
