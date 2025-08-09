"""
Family Models
- Defines SQLAlchemy ORM models for the Family table and its
  self-referential many-to-many relationships for antagonists and companions.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

if TYPE_CHECKING:
    from app.api.models.disease_and_pest.disease_model import Disease
    from app.api.models.disease_and_pest.pest_model import Pest

    from .botanical_group_model import BotanicalGroup

family_antagonists_assoc = Table(
    "family_antagonist",
    Base.metadata,
    Column(
        "family_id",
        UUID(as_uuid=True),
        ForeignKey("family.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "antagonist_family_id",
        UUID(as_uuid=True),
        ForeignKey("family.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

family_companions_assoc = Table(
    "family_companion",
    Base.metadata,
    Column(
        "family_id",
        UUID(as_uuid=True),
        ForeignKey("family.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "companion_family_id",
        UUID(as_uuid=True),
        ForeignKey("family.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Family(Base):
    """Family model representing plant families."""

    __tablename__ = "family"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    botanical_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("botanical_group.id", ondelete="RESTRICT"),
        nullable=False,
    )

    botanical_group: Mapped["BotanicalGroup"] = relationship(
        "BotanicalGroup", back_populates="families"
    )

    # Families that this family antagonizes
    antagonises: Mapped[List["Family"]] = relationship(
        "Family",
        secondary=family_antagonists_assoc,
        primaryjoin=id == family_antagonists_assoc.c.family_id,
        secondaryjoin=id == family_antagonists_assoc.c.antagonist_family_id,
        back_populates="antagonised_by",
    )

    # Families that antagonize this family
    antagonised_by: Mapped[List["Family"]] = relationship(
        "Family",
        secondary=family_antagonists_assoc,
        primaryjoin=id == family_antagonists_assoc.c.antagonist_family_id,
        secondaryjoin=id == family_antagonists_assoc.c.family_id,
        back_populates="antagonises",
    )

    # Families that this family is a companion to
    companion_to: Mapped[List["Family"]] = relationship(
        "Family",
        secondary=family_companions_assoc,
        primaryjoin=id == family_companions_assoc.c.family_id,
        secondaryjoin=id == family_companions_assoc.c.companion_family_id,
        back_populates="companion_with",
    )

    # Families that are companions with this family
    companion_with: Mapped[List["Family"]] = relationship(
        "Family",
        secondary=family_companions_assoc,
        primaryjoin=id == family_companions_assoc.c.companion_family_id,
        secondaryjoin=id == family_companions_assoc.c.family_id,
        back_populates="companion_to",
    )

    # Diseases and pests relationships
    diseases: Mapped[List["Disease"]] = relationship(
        "Disease", secondary="family_disease", back_populates="families"
    )
    pests: Mapped[List["Pest"]] = relationship(
        "Pest", secondary="family_pest", back_populates="families"
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_family_name"),
        CheckConstraint("name = LOWER(name)", name="ck_family_name_lower"),
        CheckConstraint(
            "name ~ '^[a-z0-9]+([ -][a-z0-9]+)*$'",
            name="ck_family_name_format",
        ),
    )

    def __repr__(self) -> str:
        return f"<Family(id={self.id}, name='{self.name}')>"
