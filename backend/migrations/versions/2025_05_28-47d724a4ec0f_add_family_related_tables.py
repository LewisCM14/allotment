"""add family related tables

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
    botanical_group_table = op.create_table('botanical_group',
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
    family_table = op.create_table('family',
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
    family_antagonist_table = op.create_table('family_antagonist',
    sa.Column('family_id', sa.Integer(), nullable=False),
    sa.Column('antagonist_family_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['antagonist_family_id'], ['family.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('family_id', 'antagonist_family_id')
    )
    family_companion_table = op.create_table('family_companion',
    sa.Column('family_id', sa.Integer(), nullable=False),
    sa.Column('companion_family_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['companion_family_id'], ['family.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('family_id', 'companion_family_id')
    )

    op.bulk_insert(botanical_group_table,
        [
            {'name': 'Nightshade', 'recommended_rotation_years': 2},
            {'name': 'Allium', 'recommended_rotation_years': 2},
            {'name': 'Brassica', 'recommended_rotation_years': 1},
            {'name': 'Brassicaceae', 'recommended_rotation_years': 2},
            {'name': 'Legume', 'recommended_rotation_years': 3},
            {'name': 'Root Vegetable', 'recommended_rotation_years': 4},
            {'name': 'Cereals & Grasses', 'recommended_rotation_years': 3},
            {'name': 'Gourd', 'recommended_rotation_years': 4},
            {'name': 'Rosaceae', 'recommended_rotation_years': 4},
            {'name': 'Ribes', 'recommended_rotation_years': None},
            {'name': 'Rubus', 'recommended_rotation_years': None},
            {'name': 'Ericaceae', 'recommended_rotation_years': None},
            {'name': 'Mediterranean Herb', 'recommended_rotation_years': None},
            {'name': 'Mint', 'recommended_rotation_years': 3},
            {'name': 'Umbellifers', 'recommended_rotation_years': 2},
            {'name': 'Daisy', 'recommended_rotation_years': 3},
            {'name': 'Amaranthaceae', 'recommended_rotation_years': 1},
            {'name': 'Asparagaceae', 'recommended_rotation_years': None},
        ]
    )
    conn = op.get_bind()
    meta = sa.MetaData()
    botanical_group_query_table = sa.Table(
        'botanical_group', meta,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String)
    )

    botanical_groups_from_db = conn.execute(sa.select(botanical_group_query_table)).fetchall()
    botanical_group_name_to_id = {bg.name: bg.id for bg in botanical_groups_from_db}

    families_seed_data = [
        {'name': 'Radish', 'botanical_group_id': botanical_group_name_to_id['Brassicaceae']},
        {'name': 'Squash', 'botanical_group_id': botanical_group_name_to_id['Gourd']},
        {'name': 'Basil', 'botanical_group_id': botanical_group_name_to_id['Mint']},
        {'name': 'Parsley', 'botanical_group_id': botanical_group_name_to_id['Umbellifers']},
        {'name': 'Celery', 'botanical_group_id': botanical_group_name_to_id['Umbellifers']},
        {'name': 'Lettuce', 'botanical_group_id': botanical_group_name_to_id['Daisy']},
        {'name': 'Spinach', 'botanical_group_id': botanical_group_name_to_id['Amaranthaceae']},
        {'name': 'Asparagus', 'botanical_group_id': botanical_group_name_to_id['Asparagaceae']},
        {'name': 'Onion', 'botanical_group_id': botanical_group_name_to_id['Allium']},
        {'name': 'Shallot', 'botanical_group_id': botanical_group_name_to_id['Allium']},
        {'name': 'Leek', 'botanical_group_id': botanical_group_name_to_id['Allium']},
        {'name': 'Garlic', 'botanical_group_id': botanical_group_name_to_id['Allium']},
        {'name': 'Tomato', 'botanical_group_id': botanical_group_name_to_id['Nightshade']},
        {'name': 'Sweet Pepper', 'botanical_group_id': botanical_group_name_to_id['Nightshade']},
        {'name': 'Potato', 'botanical_group_id': botanical_group_name_to_id['Nightshade']},
        {'name': 'Broccoli', 'botanical_group_id': botanical_group_name_to_id['Brassica']},
        {'name': 'Brussels Sprout', 'botanical_group_id': botanical_group_name_to_id['Brassica']},
        {'name': 'Cauliflower', 'botanical_group_id': botanical_group_name_to_id['Brassica']},
        {'name': 'Runner Bean', 'botanical_group_id': botanical_group_name_to_id['Legume']},
        {'name': 'Sugar Snap Pea', 'botanical_group_id': botanical_group_name_to_id['Legume']},
        {'name': 'Carrot', 'botanical_group_id': botanical_group_name_to_id['Root Vegetable']},
        {'name': 'Parsnip', 'botanical_group_id': botanical_group_name_to_id['Root Vegetable']},
        {'name': 'Beetroot', 'botanical_group_id': botanical_group_name_to_id['Root Vegetable']},
        {'name': 'Sweetcorn', 'botanical_group_id': botanical_group_name_to_id['Cereals & Grasses']},
        {'name': 'Pumpkin', 'botanical_group_id': botanical_group_name_to_id['Gourd']},
        {'name': 'Cucumber', 'botanical_group_id': botanical_group_name_to_id['Gourd']},
        {'name': 'Rosemary', 'botanical_group_id': botanical_group_name_to_id['Mediterranean Herb']},
        {'name': 'Blueberry', 'botanical_group_id': botanical_group_name_to_id['Ericaceae']},
        {'name': 'Cranberry', 'botanical_group_id': botanical_group_name_to_id['Ericaceae']},
        {'name': 'Strawberry', 'botanical_group_id': botanical_group_name_to_id['Rosaceae']},
        {'name': 'Raspberry', 'botanical_group_id': botanical_group_name_to_id['Rubus']},
        {'name': 'Blackberry', 'botanical_group_id': botanical_group_name_to_id['Rubus']},
        {'name': 'Gooseberry', 'botanical_group_id': botanical_group_name_to_id['Ribes']},
        {'name': 'Jostaberry', 'botanical_group_id': botanical_group_name_to_id['Ribes']},
        {'name': 'Redcurrant', 'botanical_group_id': botanical_group_name_to_id['Ribes']},
        {'name': 'Blackcurrant', 'botanical_group_id': botanical_group_name_to_id['Ribes']},
    ]
    op.bulk_insert(family_table, families_seed_data)

    family_query_table = sa.Table(
        'family', meta,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String)
    )
    families_from_db = conn.execute(sa.select(family_query_table)).fetchall()
    family_name_to_id = {f.name: f.id for f in families_from_db}
    
    family_companions_seed_data = [
        {'family_id': family_name_to_id['Onion'], 'companion_family_id': family_name_to_id['Parsley']},
        {'family_id': family_name_to_id['Onion'], 'companion_family_id': family_name_to_id['Spinach']},
        {'family_id': family_name_to_id['Beetroot'], 'companion_family_id': family_name_to_id['Onion']},
        {'family_id': family_name_to_id['Shallot'], 'companion_family_id': family_name_to_id['Parsley']},
        {'family_id': family_name_to_id['Shallot'], 'companion_family_id': family_name_to_id['Spinach']},
        {'family_id': family_name_to_id['Beetroot'], 'companion_family_id': family_name_to_id['Shallot']},
        {'family_id': family_name_to_id['Beetroot'], 'companion_family_id': family_name_to_id['Lettuce']},
        {'family_id': family_name_to_id['Carrot'], 'companion_family_id': family_name_to_id['Leek']},
        {'family_id': family_name_to_id['Cauliflower'], 'companion_family_id': family_name_to_id['Spinach']},
        {'family_id': family_name_to_id['Cauliflower'], 'companion_family_id': family_name_to_id['Celery']},
        {'family_id': family_name_to_id['Cauliflower'], 'companion_family_id': family_name_to_id['Sugar Snap Pea']},
        {'family_id': family_name_to_id['Tomato'], 'companion_family_id': family_name_to_id['Basil']},
        {'family_id': family_name_to_id['Tomato'], 'companion_family_id': family_name_to_id['Parsley']},
        {'family_id': family_name_to_id['Sweetcorn'], 'companion_family_id': family_name_to_id['Runner Bean']},
        {'family_id': family_name_to_id['Sweetcorn'], 'companion_family_id': family_name_to_id['Squash']},
        {'family_id': family_name_to_id['Cucumber'], 'companion_family_id': family_name_to_id['Radish']},
        {'family_id': family_name_to_id['Blueberry'], 'companion_family_id': family_name_to_id['Cranberry']},
    ]
    if family_companions_seed_data:
        op.bulk_insert(family_companion_table, family_companions_seed_data)

    family_antagonists_seed_data = [
        {'family_id': family_name_to_id['Garlic'], 'antagonist_family_id': family_name_to_id['Sugar Snap Pea']},
        {'family_id': family_name_to_id['Garlic'], 'antagonist_family_id': family_name_to_id['Runner Bean']},
        {'family_id': family_name_to_id['Onion'], 'antagonist_family_id': family_name_to_id['Runner Bean']},
        {'family_id': family_name_to_id['Shallot'], 'antagonist_family_id': family_name_to_id['Runner Bean']},
        {'family_id': family_name_to_id['Tomato'], 'antagonist_family_id': family_name_to_id['Potato']},
        {'family_id': family_name_to_id['Tomato'], 'antagonist_family_id': family_name_to_id['Cauliflower']},
        {'family_id': family_name_to_id['Tomato'], 'antagonist_family_id': family_name_to_id['Broccoli']},
        {'family_id': family_name_to_id['Tomato'], 'antagonist_family_id': family_name_to_id['Brussels Sprout']},
        {'family_id': family_name_to_id['Tomato'], 'antagonist_family_id': family_name_to_id['Strawberry']},
        {'family_id': family_name_to_id['Leek'], 'antagonist_family_id': family_name_to_id['Runner Bean']},
        {'family_id': family_name_to_id['Leek'], 'antagonist_family_id': family_name_to_id['Sugar Snap Pea']},
        {'family_id': family_name_to_id['Cucumber'], 'antagonist_family_id': family_name_to_id['Potato']},
        {'family_id': family_name_to_id['Cauliflower'], 'antagonist_family_id': family_name_to_id['Strawberry']},
        {'family_id': family_name_to_id['Redcurrant'], 'antagonist_family_id': family_name_to_id['Potato']},
        {'family_id': family_name_to_id['Blackcurrant'], 'antagonist_family_id': family_name_to_id['Potato']},
        {'family_id': family_name_to_id['Gooseberry'], 'antagonist_family_id': family_name_to_id['Potato']},
        {'family_id': family_name_to_id['Blueberry'], 'antagonist_family_id': family_name_to_id['Potato']},
        {'family_id': family_name_to_id['Redcurrant'], 'antagonist_family_id': family_name_to_id['Tomato']},
        {'family_id': family_name_to_id['Blackcurrant'], 'antagonist_family_id': family_name_to_id['Tomato']},
        {'family_id': family_name_to_id['Gooseberry'], 'antagonist_family_id': family_name_to_id['Tomato']},
        {'family_id': family_name_to_id['Blueberry'], 'antagonist_family_id': family_name_to_id['Tomato']},
        {'family_id': family_name_to_id['Redcurrant'], 'antagonist_family_id': family_name_to_id['Sweet Pepper']},
        {'family_id': family_name_to_id['Blackcurrant'], 'antagonist_family_id': family_name_to_id['Sweet Pepper']},
        {'family_id': family_name_to_id['Gooseberry'], 'antagonist_family_id': family_name_to_id['Sweet Pepper']},
        {'family_id': family_name_to_id['Blueberry'], 'antagonist_family_id': family_name_to_id['Sweet Pepper']},
    ]
    if family_antagonists_seed_data:
        op.bulk_insert(family_antagonist_table, family_antagonists_seed_data)

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
