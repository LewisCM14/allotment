"""add disease and pest tables

Revision ID: fd5d387c3559
Revises: 47d724a4ec0f
Create Date: 2025-06-07 21:55:18.297000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd5d387c3559'
down_revision: Union[str, None] = '47d724a4ec0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    disease_table = op.create_table('disease',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_disease_name')
    )
    op.create_index(op.f('ix_disease_id'), 'disease', ['id'], unique=False)
    op.create_index(op.f('ix_disease_name'), 'disease', ['name'], unique=True)
    intervention_table = op.create_table('intervention',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_intervention_name')
    )
    op.create_index(op.f('ix_intervention_id'), 'intervention', ['id'], unique=False)
    op.create_index(op.f('ix_intervention_name'), 'intervention', ['name'], unique=True)
    pest_table = op.create_table('pest',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_pest_name')
    )
    op.create_index(op.f('ix_pest_id'), 'pest', ['id'], unique=False)
    op.create_index(op.f('ix_pest_name'), 'pest', ['name'], unique=True)
    symptom_table = op.create_table('symptom',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_symptom_name')
    )
    op.create_index(op.f('ix_symptom_id'), 'symptom', ['id'], unique=False)
    op.create_index(op.f('ix_symptom_name'), 'symptom', ['name'], unique=True)
    disease_prevention_table = op.create_table('disease_prevention',
    sa.Column('disease_id', sa.UUID(), nullable=False),
    sa.Column('intervention_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['disease_id'], ['disease.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['intervention_id'], ['intervention.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('disease_id', 'intervention_id')
    )
    disease_symptom_table = op.create_table('disease_symptom',
    sa.Column('disease_id', sa.UUID(), nullable=False),
    sa.Column('symptom_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['disease_id'], ['disease.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['symptom_id'], ['symptom.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('disease_id', 'symptom_id')
    )
    disease_treatment_table = op.create_table('disease_treatment',
    sa.Column('disease_id', sa.UUID(), nullable=False),
    sa.Column('intervention_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['disease_id'], ['disease.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['intervention_id'], ['intervention.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('disease_id', 'intervention_id')
    )
    pest_prevention_table = op.create_table('pest_prevention',
    sa.Column('pest_id', sa.UUID(), nullable=False),
    sa.Column('intervention_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['intervention_id'], ['intervention.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pest_id'], ['pest.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('pest_id', 'intervention_id')
    )
    pest_treatment_table = op.create_table('pest_treatment',
    sa.Column('pest_id', sa.UUID(), nullable=False),
    sa.Column('intervention_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['intervention_id'], ['intervention.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pest_id'], ['pest.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('pest_id', 'intervention_id')
    )
    family_disease_table = op.create_table('family_disease',
    sa.Column('family_id', sa.UUID(), nullable=False),
    sa.Column('disease_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['disease_id'], ['disease.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('family_id', 'disease_id')
    )
    family_pest_table = op.create_table('family_pest',
    sa.Column('family_id', sa.UUID(), nullable=False),
    sa.Column('pest_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['family_id'], ['family.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['pest_id'], ['pest.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('family_id', 'pest_id')
    )

    diseases = [
        {"name": "blight"},
        {"name": "downy mildew"},
        {"name": "club root"},
    ]
    disease_ids = {disease["name"]: uuid.uuid4() for disease in diseases}
    op.bulk_insert(
        disease_table,
        [{"id": disease_ids[disease["name"]], "name": disease["name"]} for disease in diseases]
    )

    pests = [
        {"name": "slugs"},
        {"name": "birds"},
        {"name": "aphids"},
        {"name": "caterpillars"},
        {"name": "whiteflies"},
        {"name": "spider mites"},
    ]
    pest_ids = {pest["name"]: uuid.uuid4() for pest in pests}
    op.bulk_insert(
        pest_table,
        [{"id": pest_ids[pest["name"]], "name": pest["name"]} for pest in pests]
    )

    symptoms = [
        {"name": "yellowing leaves"},
    ]
    symptom_ids = {symptom["name"]: uuid.uuid4() for symptom in symptoms}
    op.bulk_insert(
        symptom_table,
        [{"id": symptom_ids[symptom["name"]], "name": symptom["name"]} for symptom in symptoms]
    )

    interventions = [
        {"name": "netting"},
        {"name": "fungicide"},
        {"name": "crop rotation"},
        {"name": "companion planting"},
        {"name": "pesticide"},
        {"name": "herbicide"},
        {"name": "manual removal"},
        {"name": "slug pellets"},
    ]
    intervention_ids = {intervention["name"]: uuid.uuid4() for intervention in interventions}
    op.bulk_insert(
        intervention_table,
        [{"id": intervention_ids[intervention["name"]], "name": intervention["name"]} for intervention in interventions]
    )

    disease_prevention_data = [
        {
            "disease_id": disease_ids["club root"],
            "intervention_id": intervention_ids["crop rotation"]
        }
    ]
    if disease_prevention_data:
        op.bulk_insert(disease_prevention_table, disease_prevention_data)

        
    disease_treatment_data = [
        {
            "disease_id": disease_ids["downy mildew"],
            "intervention_id": intervention_ids["fungicide"]
        }
    ]
    if disease_treatment_data:
        op.bulk_insert(disease_treatment_table, disease_treatment_data)

    disease_symptom_data = [
        {
            "disease_id": disease_ids["blight"],
            "symptom_id": symptom_ids["yellowing leaves"]
        }
    ]
    if disease_symptom_data:
        op.bulk_insert(disease_symptom_table, disease_symptom_data)

    pest_prevention_data = [
        {
            "pest_id": pest_ids["birds"],
            "intervention_id": intervention_ids["netting"]
        }
    ]
    if pest_prevention_data:
        op.bulk_insert(pest_prevention_table, pest_prevention_data)

    pest_treatment_data = [
        {
            "pest_id": pest_ids["slugs"],
            "intervention_id": intervention_ids["slug pellets"]
        }
    ]
    if pest_treatment_data:
        op.bulk_insert(pest_treatment_table, pest_treatment_data)

    connection = op.get_bind()
    family_table_for_query = sa.Table(
        "family",
        sa.MetaData(),
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String, unique=True),
    )
    
    families_from_db_result = connection.execute(sa.select(family_table_for_query.c.id, family_table_for_query.c.name)).fetchall()
    family_name_to_id = {name: id for id, name in families_from_db_result}

    family_disease_seed_data = []
    if "tomato" in family_name_to_id and "blight" in disease_ids:
        family_disease_seed_data.append({
            "family_id": family_name_to_id["tomato"],
            "disease_id": disease_ids["blight"]
        })

    if "potato" in family_name_to_id and "blight" in disease_ids:
        family_disease_seed_data.append({
            "family_id": family_name_to_id["potato"],
            "disease_id": disease_ids["blight"]
        })

    if "broccoli" in family_name_to_id and "club root" in disease_ids:
        family_disease_seed_data.append({
            "family_id": family_name_to_id["broccoli"],
            "disease_id": disease_ids["club root"]
        })

    if "cauliflower" in family_name_to_id and "club root" in disease_ids:
        family_disease_seed_data.append({
            "family_id": family_name_to_id["cauliflower"],
            "disease_id": disease_ids["club root"]
        })

    if "lettuce" in family_name_to_id and "downy mildew" in disease_ids:
        family_disease_seed_data.append({
            "family_id": family_name_to_id["lettuce"],
            "disease_id": disease_ids["downy mildew"]
        })
    
    if family_disease_seed_data:
        op.bulk_insert(family_disease_table, family_disease_seed_data)


    family_pest_seed_data = []

    if "broccoli" in family_name_to_id and "caterpillars" in pest_ids:
        family_pest_seed_data.append({
            "family_id": family_name_to_id["broccoli"],
            "pest_id": pest_ids["caterpillars"]
        })
    if "cauliflower" in family_name_to_id and "caterpillars" in pest_ids:
        family_pest_seed_data.append({
            "family_id": family_name_to_id["cauliflower"],
            "pest_id": pest_ids["caterpillars"]
        })

    if "lettuce" in family_name_to_id and "slugs" in pest_ids:
        family_pest_seed_data.append({
            "family_id": family_name_to_id["lettuce"],
            "pest_id": pest_ids["slugs"]
        })

    if "tomato" in family_name_to_id and "whiteflies" in pest_ids:
        family_pest_seed_data.append({
            "family_id": family_name_to_id["tomato"],
            "pest_id": pest_ids["whiteflies"]
        })

    if "sweet pepper" in family_name_to_id and "aphids" in pest_ids:
        family_pest_seed_data.append({
            "family_id": family_name_to_id["sweet pepper"],
            "pest_id": pest_ids["aphids"]
        })

    if family_pest_seed_data:
        op.bulk_insert(family_pest_table, family_pest_seed_data)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('family_pest')
    op.drop_table('family_disease')
    op.drop_table('pest_treatment')
    op.drop_table('pest_prevention')
    op.drop_table('disease_treatment')
    op.drop_table('disease_symptom')
    op.drop_table('disease_prevention')
    op.drop_index(op.f('ix_symptom_name'), table_name='symptom')
    op.drop_index(op.f('ix_symptom_id'), table_name='symptom')
    op.drop_table('symptom')
    op.drop_index(op.f('ix_pest_name'), table_name='pest')
    op.drop_index(op.f('ix_pest_id'), table_name='pest')
    op.drop_table('pest')
    op.drop_index(op.f('ix_intervention_name'), table_name='intervention')
    op.drop_index(op.f('ix_intervention_id'), table_name='intervention')
    op.drop_table('intervention')
    op.drop_index(op.f('ix_disease_name'), table_name='disease')
    op.drop_index(op.f('ix_disease_id'), table_name='disease')
    op.drop_table('disease')
