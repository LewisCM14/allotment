"""add family realted tables

Revision ID: 47d724a4ec0f
Revises: 851e27ae4553
Create Date: 2025-05-28 21:01:40.130255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47d724a4ec0f'
down_revision: Union[str, None] = '851e27ae4553'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('botanical_group',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('recommended_rotation_years', sa.Integer(), nullable=True),
    sa.CheckConstraint("name ~ '^[a-z0-9]+([ -][a-z0-9]+)*$'", name='ck_botanical_group_name_format'),
    sa.CheckConstraint('name = LOWER(name)', name='ck_botanical_group_name_lower'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_botanical_group_name')
    )
    op.create_index(op.f('ix_botanical_group_id'), 'botanical_group', ['id'], unique=False)
    op.create_index(op.f('ix_botanical_group_name'), 'botanical_group', ['name'], unique=True)
    op.create_table('family',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('botanical_group_id', sa.Integer(), nullable=False),
    sa.CheckConstraint("name ~ '^[a-z0-9]+([ -][a-z0-9]+)*$'", name='ck_family_name_format'),
    sa.CheckConstraint('name = LOWER(name)', name='ck_family_name_lower'),
    sa.ForeignKeyConstraint(['botanical_group_id'], ['botanical_group.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_family_name')
    )
    op.create_index(op.f('ix_family_id'), 'family', ['id'], unique=False)
    op.create_index(op.f('ix_family_name'), 'family', ['name'], unique=True)
    op.create_table('family_antagonist',
    sa.Column('family_id', sa.Integer(), nullable=False),
    sa.Column('antagonist_family_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['antagonist_family_id'], ['family.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('family_id', 'antagonist_family_id')
    )
    op.create_table('family_companion',
    sa.Column('family_id', sa.Integer(), nullable=False),
    sa.Column('companion_family_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['companion_family_id'], ['family.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('family_id', 'companion_family_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('family_companion')
    op.drop_table('family_antagonist')
    op.drop_index(op.f('ix_family_name'), table_name='family')
    op.drop_index(op.f('ix_family_id'), table_name='family')
    op.drop_table('family')
    op.drop_index(op.f('ix_botanical_group_name'), table_name='botanical_group')
    op.drop_index(op.f('ix_botanical_group_id'), table_name='botanical_group')
    op.drop_table('botanical_group')
