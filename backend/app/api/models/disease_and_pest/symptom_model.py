"""
Models the Disease & Disease Symptom Tables
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

if TYPE_CHECKING:
    from app.api.models.disease_and_pest.disease_model import Disease


class Symptom(Base):
    __tablename__ = "symptom"
    symptom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    symptom_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Relationships
    diseases: Mapped[List["Disease"]] = relationship(
        "Disease", secondary="disease_symptom", back_populates="symptoms"
    )

    __table_args__ = (UniqueConstraint("symptom_name", name="uq_symptom_name"),)
