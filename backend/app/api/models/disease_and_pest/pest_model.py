"""
Models the Pest & Family Pest Tables
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

if TYPE_CHECKING:
    from app.api.models.disease_and_pest.intervention_model import Intervention
    from app.api.models.family.family_model import Family

# Association tables
pest_treatment = Table(
    "pest_treatment",
    Base.metadata,
    Column(
        "pest_id",
        UUID(as_uuid=True),
        ForeignKey("pest.pest_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.intervention_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

pest_prevention = Table(
    "pest_prevention",
    Base.metadata,
    Column(
        "pest_id",
        UUID(as_uuid=True),
        ForeignKey("pest.pest_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.intervention_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

family_pest = Table(
    "family_pest",
    Base.metadata,
    Column(
        "family_id",
        UUID(as_uuid=True),
        ForeignKey("family.family_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "pest_id",
        UUID(as_uuid=True),
        ForeignKey("pest.pest_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Pest(Base):
    __tablename__ = "pest"

    pest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    pest_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("pest_name", name="uq_pest_name"),)

    # Relationships
    treatments: Mapped[List["Intervention"]] = relationship(
        "Intervention", secondary=pest_treatment, back_populates="treats_pests"
    )
    preventions: Mapped[List["Intervention"]] = relationship(
        "Intervention", secondary=pest_prevention, back_populates="prevents_pests"
    )
    families: Mapped[List["Family"]] = relationship(
        "Family", secondary=family_pest, back_populates="pests"
    )

    def __repr__(self) -> str:
        return f"<Pest(id={self.pest_id}, name='{self.pest_name}')>"
