"""Add is_email_verified column to User model

Revision ID: 851e27ae4553
Revises: 51f783d3456b
Create Date: 2025-04-04 20:55:37.412030

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "851e27ae4553"
down_revision: Union[str, None] = "51f783d3456b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("user", sa.Column("is_email_verified", sa.Boolean(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user", "is_email_verified")
