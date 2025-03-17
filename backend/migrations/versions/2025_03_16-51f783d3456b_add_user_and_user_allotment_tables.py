"""Add User and User Allotment Tables

Revision ID: 51f783d3456b
Revises:
Create Date: 2025-03-16 18:16:49.183279

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "51f783d3456b"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("user_password_hash", sa.Text(), nullable=False),
        sa.Column("user_first_name", sa.String(length=50), nullable=False),
        sa.Column("user_country_code", sa.String(length=2), nullable=False),
        sa.CheckConstraint(
            "LENGTH(user_country_code) = 2", name="correct_country_code_format"
        ),
        sa.CheckConstraint("LENGTH(user_email) >= 7", name="min_length_user_email"),
        sa.CheckConstraint(
            "LENGTH(user_first_name) >= 2", name="min_length_user_first_name"
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_user_email"), "user", ["user_email"], unique=True)
    op.create_index(op.f("ix_user_user_id"), "user", ["user_id"], unique=False)
    op.create_table(
        "user_allotment",
        sa.Column("user_allotment_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("allotment_postal_zip_code", sa.String(length=7), nullable=False),
        sa.Column("allotment_width_meters", sa.Float(), nullable=False),
        sa.Column("allotment_length_meters", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "LENGTH(allotment_postal_zip_code) >= 5",
            name="min_length_allotment_postal_zip_code",
        ),
        sa.CheckConstraint(
            "allotment_length_meters >= 1.0 AND allotment_length_meters <= 100.0",
            name="check_length_range",
        ),
        sa.CheckConstraint(
            "allotment_width_meters >= 1.0 AND allotment_width_meters <= 100.0",
            name="check_width_range",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_allotment_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_user_allotment_user_allotment_id"),
        "user_allotment",
        ["user_allotment_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_user_allotment_user_allotment_id"), table_name="user_allotment"
    )
    op.drop_table("user_allotment")
    op.drop_index(op.f("ix_user_user_id"), table_name="user")
    op.drop_index(op.f("ix_user_user_email"), table_name="user")
    op.drop_table("user")
