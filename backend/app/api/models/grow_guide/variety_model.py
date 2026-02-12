"""
Models the Variety & Variety Water Day Tables
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

WEEK_FK = "week.week_id"
FREQUENCY_FK = "frequency.frequency_id"

if TYPE_CHECKING:
    from app.api.models.family.family_model import Family
    from app.api.models.grow_guide.calendar_model import Day
    from app.api.models.grow_guide.guide_options_model import (
        Feed,
        Frequency,
        Lifecycle,
        PlantingConditions,
    )
    from app.api.models.user.user_model import User, UserActiveVariety


class Variety(Base):
    """Variety model representing grow guides for different plant varieties."""

    __tablename__ = "variety"

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variety_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    variety_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Family relationship
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family.family_id"),
        nullable=False,
        index=True,
    )
    family: Mapped["Family"] = relationship("Family")

    # Lifecycle relationship
    lifecycle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lifecycle.lifecycle_id"),
        nullable=False,
        index=True,
    )
    lifecycle: Mapped["Lifecycle"] = relationship(
        "Lifecycle", back_populates="varieties"
    )

    # Sowing details
    sow_week_start_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=False,
        index=True,
    )
    sow_week_end_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=False,
        index=True,
    )

    # Transplant details
    transplant_week_start_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=True,
        index=True,
    )
    transplant_week_end_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=True,
        index=True,
    )

    # Planting conditions relationship
    planting_conditions_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("planting_conditions.planting_condition_id"),
        nullable=False,
        index=True,
    )
    planting_conditions: Mapped["PlantingConditions"] = relationship(
        "PlantingConditions", back_populates="varieties"
    )

    # Soil and spacing details
    soil_ph: Mapped[float] = mapped_column(Float, nullable=False)
    row_width_cm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    plant_depth_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    plant_space_cm: Mapped[int] = mapped_column(Integer, nullable=False)

    # Feed details
    feed_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feed.feed_id"),
        nullable=True,
        index=True,
    )
    feed: Mapped[Optional["Feed"]] = relationship("Feed")
    feed_week_start_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=True,
        index=True,
    )
    feed_frequency_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(FREQUENCY_FK),
        nullable=True,
        index=True,
    )
    feed_frequency: Mapped[Optional["Frequency"]] = relationship(
        "Frequency", foreign_keys=[feed_frequency_id]
    )

    # Watering details
    water_frequency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(FREQUENCY_FK),
        nullable=False,
        index=True,
    )
    water_frequency: Mapped["Frequency"] = relationship(
        "Frequency", foreign_keys=[water_frequency_id]
    )

    # High temperature details
    high_temp_degrees: Mapped[int] = mapped_column(Integer, nullable=False)
    high_temp_water_frequency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(FREQUENCY_FK),
        nullable=False,
        index=True,
    )
    high_temp_water_frequency: Mapped["Frequency"] = relationship(
        "Frequency", foreign_keys=[high_temp_water_frequency_id]
    )

    # Harvest details
    harvest_week_start_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=False,
        index=True,
    )
    harvest_week_end_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=False,
        index=True,
    )

    # Prune details
    prune_week_start_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=True,
        index=True,
    )
    prune_week_end_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(WEEK_FK),
        nullable=True,
        index=True,
    )

    # Additional details
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # User relationship
    user: Mapped["User"] = relationship(
        "User", back_populates="varieties", foreign_keys=[owner_user_id]
    )

    # Water days relationship
    water_days: Mapped[list["VarietyWaterDay"]] = relationship(
        "VarietyWaterDay", back_populates="variety", cascade="all, delete-orphan"
    )
    active_users: Mapped[list["UserActiveVariety"]] = relationship(
        "UserActiveVariety", back_populates="variety", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Ensure transplant weeks are provided together
        CheckConstraint(
            "(transplant_week_start_id IS NULL AND transplant_week_end_id IS NULL) OR "
            "(transplant_week_start_id IS NOT NULL AND transplant_week_end_id IS NOT NULL)",
            name="check_transplant_weeks_together",
        ),
        # Ensure prune weeks are provided together
        CheckConstraint(
            "(prune_week_start_id IS NULL AND prune_week_end_id IS NULL) OR "
            "(prune_week_start_id IS NOT NULL AND prune_week_end_id IS NOT NULL)",
            name="check_prune_weeks_together",
        ),
        # Ensure feed details are provided together
        CheckConstraint(
            "(feed_id IS NULL AND feed_week_start_id IS NULL AND feed_frequency_id IS NULL) OR "
            "(feed_id IS NOT NULL AND feed_week_start_id IS NOT NULL AND feed_frequency_id IS NOT NULL)",
            name="check_feed_details_together",
        ),
        # High temp symmetric pairing
        CheckConstraint(
            "(high_temp_degrees IS NULL AND high_temp_water_frequency_id IS NULL) OR "
            "(high_temp_degrees IS NOT NULL AND high_temp_water_frequency_id IS NOT NULL)",
            name="check_high_temp_pairing",
        ),
        # Ensure combination of user_id and name is unique
        UniqueConstraint("owner_user_id", "variety_name", name="uq_user_variety_name"),
        # Ensure notes length is between 5 and 500 characters when provided
        CheckConstraint(
            "notes IS NULL OR (LENGTH(notes) >= 5 AND LENGTH(notes) <= 500)",
            name="check_notes_length",
        ),
    )


class VarietyWaterDay(Base):
    """Junction table linking varieties to their watering days."""

    __tablename__ = "variety_water_day"

    variety_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("variety.variety_id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
    )
    day_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("day.day_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    # Relationships
    variety: Mapped["Variety"] = relationship("Variety", back_populates="water_days")
    day: Mapped["Day"] = relationship("Day")
