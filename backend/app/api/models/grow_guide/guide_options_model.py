"""
Models the Lifecycle, Planting Conditions, Feed, Frequency & Variety Water Day Tables
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

if TYPE_CHECKING:
    from app.api.models.user.user_model import UserFeedDay


class Day(Base):
    """Day model representing the seven days of the week."""

    __tablename__ = "day"

    id: Mapped[uuid.UUID] = mapped_column(
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
    name: Mapped[str] = mapped_column(String(10), nullable=False)

    # Relationship to UserFeedDay
    user_feed_days: Mapped[list["UserFeedDay"]] = relationship(
        "UserFeedDay", back_populates="day"
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_day_name"),
        UniqueConstraint("day_number", name="uq_day_number"),
    )


class Feed(Base):
    """Feed model representing plant feed types."""

    __tablename__ = "feed"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship to UserFeedDay
    user_feed_days: Mapped[list["UserFeedDay"]] = relationship(
        "UserFeedDay", back_populates="feed", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("name", name="uq_feed_name"),)
