"""
Models the User & User Allotment Tables
"""

import uuid

import bcrypt
from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.api.core.database import Base


class User(Base):
    __tablename__ = "user"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    user_email = Column(String(255), unique=True, nullable=False, index=True)
    user_password_hash = Column(Text, nullable=False)
    user_first_name = Column(String(50), nullable=False)
    user_country_code = Column(String(2), nullable=False)

    allotment = relationship(
        "UserAllotment",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str):
        """Hash and store the password."""
        self.user_password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verify a password."""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.user_password_hash.encode("utf-8")
        )

    __table_args__ = (
        CheckConstraint("LENGTH(user_email) >= 7", name="min_length_user_email"),
        CheckConstraint(
            "LENGTH(user_first_name) >= 2", name="min_length_user_first_name"
        ),
        CheckConstraint(
            "LENGTH(user_country_code) = 2", name="correct_country_code_format"
        ),
    )


class UserAllotment(Base):
    __tablename__ = "user_allotment"

    user_allotment_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    allotment_postal_zip_code = Column(String(7), nullable=False)
    allotment_width_meters = Column(Float, nullable=False)
    allotment_length_meters = Column(Float, nullable=False)

    user = relationship("User", back_populates="allotment")

    __table_args__ = (
        CheckConstraint(
            "LENGTH(allotment_postal_zip_code) >= 5",
            name="min_length_allotment_postal_zip_code",
        ),
        CheckConstraint(
            "allotment_width_meters >= 1.0 AND allotment_width_meters <= 100.0",
            name="check_width_range",
        ),
        CheckConstraint(
            "allotment_length_meters >= 1.0 AND allotment_length_meters <= 100.0",
            name="check_length_range",
        ),
    )
