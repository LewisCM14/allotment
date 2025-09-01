"""
Botanical Group Model
- Defines the SQLAlchemy ORM model for the Botanical Group table.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List

import structlog
from sqlalchemy import CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.api.core.database import Base

logger = structlog.get_logger()

if TYPE_CHECKING:
    from .family_model import Family


class BotanicalGroup(Base):
    """BotanicalGroup model representing plant botanical groups."""

    __tablename__ = "botanical_group"

    botanical_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    botanical_group_name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    rotate_years: Mapped[int | None] = mapped_column(Integer, nullable=True)

    families: Mapped[List["Family"]] = relationship(
        "Family", back_populates="botanical_group"
    )

    __table_args__ = (
        UniqueConstraint("botanical_group_name", name="uq_botanical_group_name"),
        CheckConstraint(
            "botanical_group_name = LOWER(botanical_group_name)",
            name="ck_botanical_group_name_lower",
        ),
    )

    def __repr__(self) -> str:
        logger.debug(
            "BotanicalGroup repr called",
            id=self.botanical_group_id,
            name=self.botanical_group_name,
        )
        return f"<BotanicalGroup(id={self.botanical_group_id}, name='{self.botanical_group_name}')>"
