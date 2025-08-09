"""
Models the Intervention Table
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
    from app.api.models.disease_and_pest.pest_model import Pest


class Intervention(Base):
    __tablename__ = "intervention"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Relationships
    treats_diseases: Mapped[List["Disease"]] = relationship(
        "Disease", secondary="disease_treatment", back_populates="treatments"
    )
    prevents_diseases: Mapped[List["Disease"]] = relationship(
        "Disease", secondary="disease_prevention", back_populates="preventions"
    )
    treats_pests: Mapped[List["Pest"]] = relationship(
        "Pest", secondary="pest_treatment", back_populates="treatments"
    )
    prevents_pests: Mapped[List["Pest"]] = relationship(
        "Pest", secondary="pest_prevention", back_populates="preventions"
    )

    __table_args__ = (UniqueConstraint("name", name="uq_intervention_name"),)
