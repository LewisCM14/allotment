"""
Models the Disease & Family Disease Tables
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
    from app.api.models.disease_and_pest.symptom_model import Symptom
    from app.api.models.family.family_model import Family

# Constants
DISEASE_TABLE_REFERENCE = "disease.disease_id"

# Association tables
disease_treatment = Table(
    "disease_treatment",
    Base.metadata,
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey(DISEASE_TABLE_REFERENCE, ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.intervention_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

disease_prevention = Table(
    "disease_prevention",
    Base.metadata,
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey(DISEASE_TABLE_REFERENCE, ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "intervention_id",
        UUID(as_uuid=True),
        ForeignKey("intervention.intervention_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

disease_symptom = Table(
    "disease_symptom",
    Base.metadata,
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey(DISEASE_TABLE_REFERENCE, ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "symptom_id",
        UUID(as_uuid=True),
        ForeignKey("symptom.symptom_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

family_disease = Table(
    "family_disease",
    Base.metadata,
    Column(
        "family_id",
        UUID(as_uuid=True),
        ForeignKey("family.family_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "disease_id",
        UUID(as_uuid=True),
        ForeignKey(DISEASE_TABLE_REFERENCE, ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Disease(Base):
    __tablename__ = "disease"
    disease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    disease_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships
    treatments: Mapped[List["Intervention"]] = relationship(
        "Intervention", secondary=disease_treatment, back_populates="treats_diseases"
    )
    preventions: Mapped[List["Intervention"]] = relationship(
        "Intervention", secondary=disease_prevention, back_populates="prevents_diseases"
    )
    symptoms: Mapped[List["Symptom"]] = relationship(
        "Symptom", secondary=disease_symptom, back_populates="diseases"
    )
    families: Mapped[List["Family"]] = relationship(
        "Family", secondary=family_disease, back_populates="diseases"
    )

    __table_args__ = (UniqueConstraint("disease_name", name="uq_disease_name"),)
