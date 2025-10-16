"""
Models the Lifecycle, Planting Conditions, Feed & Frequency Tables
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base
from app.api.models.enums import LifecycleType

if TYPE_CHECKING:
    from app.api.models.grow_guide.calendar_model import Day
    from app.api.models.user.user_model import UserFeedDay

from app.api.models.grow_guide.variety_model import Variety


class Feed(Base):
    """Feed model representing plant feed types."""

    __tablename__ = "feed"

    feed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    feed_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship to UserFeedDay
    user_feed_days: Mapped[list["UserFeedDay"]] = relationship(
        "UserFeedDay", back_populates="feed", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("feed_name", name="uq_feed_name"),)


class Lifecycle(Base):
    """Lifecycle model representing plant lifecycle types."""

    __tablename__ = "lifecycle"

    lifecycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    lifecycle_name: Mapped[LifecycleType] = mapped_column(
        SQLEnum(LifecycleType, native_enum=False, length=50),
        nullable=False,
        unique=True,
        index=True,
    )
    productivity_years: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship to Variety
    varieties: Mapped[list["Variety"]] = relationship(
        "Variety", back_populates="lifecycle", foreign_keys="[Variety.lifecycle_id]"
    )

    __table_args__ = (UniqueConstraint("lifecycle_name", name="uq_lifecycle_name"),)


class PlantingConditions(Base):
    """Planting conditions model representing different planting conditions."""

    __tablename__ = "planting_conditions"

    planting_condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    planting_condition: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationship to Variety
    varieties: Mapped[list["Variety"]] = relationship(
        "Variety",
        back_populates="planting_conditions",
        foreign_keys="[Variety.planting_conditions_id]",
    )

    __table_args__ = (
        UniqueConstraint("planting_condition", name="uq_planting_conditions_name"),
    )


class Frequency(Base):
    """Frequency model representing different frequency units for activities."""

    __tablename__ = "frequency"

    frequency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    frequency_name: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency_days_per_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships to Variety
    default_days: Mapped[list["FrequencyDefaultDay"]] = relationship(
        "FrequencyDefaultDay",
        back_populates="frequency",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("frequency_name", name="uq_frequency_name"),)


class FrequencyDefaultDay(Base):
    """Association table mapping a frequency to its default watering days."""

    __tablename__ = "frequency_default_day"

    frequency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("frequency.frequency_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    day_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("day.day_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    frequency: Mapped["Frequency"] = relationship(
        "Frequency", back_populates="default_days"
    )
    day: Mapped["Day"] = relationship("Day")

    __table_args__ = (
        UniqueConstraint("frequency_id", "day_id", name="uq_frequency_day_pair"),
    )
