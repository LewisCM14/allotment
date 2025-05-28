"""
Botanical Group Model
- Defines the SQLAlchemy ORM model for the Botanical Group table.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

if TYPE_CHECKING:
    from .family_model import Family


class BotanicalGroup(Base):
    """BotanicalGroup model representing plant botanical groups."""

    __tablename__ = "botanical_group"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    recommended_rotation_years: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    families: Mapped[List["Family"]] = relationship(
        "Family", back_populates="botanical_group"
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_botanical_group_name"),
        CheckConstraint("name = LOWER(name)", name="ck_botanical_group_name_lower"),
        CheckConstraint(
            name.regexp_match(r"^[a-z0-9]+([ -][a-z0-9]+)*$"),
            name="ck_botanical_group_name_format",
        ),
    )

    def __repr__(self) -> str:
        return f"<BotanicalGroup(id={self.id}, name='{self.name}')>"
