"""
Models the Pest & Family Pest Tables
"""

import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.api.core.database import Base


class Pest(Base):
    __tablename__ = "pest"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    # ...add relationships to interventions, families, etc. as needed...

    __table_args__ = (UniqueConstraint("name", name="uq_pest_name"),)

    def __repr__(self) -> str:
        return f"<Pest(id={self.id}, name='{self.name}')>"
