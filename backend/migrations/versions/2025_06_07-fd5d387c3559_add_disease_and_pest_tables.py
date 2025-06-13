"""add disease and pest tables

Revision ID: fd5d387c3559
Revises: 47d724a4ec0f
Create Date: 2025-06-07 21:55:18.297000

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fd5d387c3559"
down_revision: Union[str, None] = "47d724a4ec0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    disease_table = op.create_table(
        "disease",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_disease_name"),
    )
    op.create_index(op.f("ix_disease_id"), "disease", ["id"], unique=False)
    op.create_index(op.f("ix_disease_name"), "disease", ["name"], unique=True)
    intervention_table = op.create_table(
        "intervention",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_intervention_name"),
    )
    op.create_index(op.f("ix_intervention_id"), "intervention", ["id"], unique=False)
    op.create_index(op.f("ix_intervention_name"), "intervention", ["name"], unique=True)
    pest_table = op.create_table(
        "pest",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_pest_name"),
    )
    op.create_index(op.f("ix_pest_id"), "pest", ["id"], unique=False)
    op.create_index(op.f("ix_pest_name"), "pest", ["name"], unique=True)
    symptom_table = op.create_table(
        "symptom",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_symptom_name"),
    )
    op.create_index(op.f("ix_symptom_id"), "symptom", ["id"], unique=False)
    op.create_index(op.f("ix_symptom_name"), "symptom", ["name"], unique=True)
    disease_prevention_table = op.create_table(
        "disease_prevention",
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["disease_id"], ["disease.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("disease_id", "intervention_id"),
    )
    disease_symptom_table = op.create_table(
        "disease_symptom",
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.Column("symptom_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["disease_id"], ["disease.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["symptom_id"], ["symptom.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("disease_id", "symptom_id"),
    )
    disease_treatment_table = op.create_table(
        "disease_treatment",
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["disease_id"], ["disease.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("disease_id", "intervention_id"),
    )
    pest_prevention_table = op.create_table(
        "pest_prevention",
        sa.Column("pest_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["pest_id"], ["pest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pest_id", "intervention_id"),
    )
    pest_treatment_table = op.create_table(
        "pest_treatment",
        sa.Column("pest_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["pest_id"], ["pest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pest_id", "intervention_id"),
    )
    family_disease_table = op.create_table(
        "family_disease",
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["disease_id"], ["disease.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("family_id", "disease_id"),
    )
    family_pest_table = op.create_table(
        "family_pest",
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("pest_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pest_id"], ["pest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("family_id", "pest_id"),
    )

    diseases = [
        {"name": "blight"},
        {"name": "downy mildew"},
        {"name": "club root"},
        {"name": "powdery mildew"},
        {"name": "botrytis"},
        {"name": "rust"},
        {"name": "blossom end rot"},
    ]
    disease_ids = {disease["name"]: uuid.uuid4() for disease in diseases}
    op.bulk_insert(
        disease_table,
        [
            {"id": disease_ids[disease["name"]], "name": disease["name"]}
            for disease in diseases
        ],
    )

    pests = [
        {"name": "slugs"},
        {"name": "birds"},
        {"name": "aphids"},
        {"name": "caterpillars"},
        {"name": "whiteflies"},
        {"name": "spider mites"},
        {"name": "gooseberry sawfly"},
        {"name": "leek moth"},
        {"name": "root fly"},
    ]
    pest_ids = {pest["name"]: uuid.uuid4() for pest in pests}
    op.bulk_insert(
        pest_table,
        [{"id": pest_ids[pest["name"]], "name": pest["name"]} for pest in pests],
    )

    symptoms = [
        {"name": "yellowing leaves"},
        {"name": "wilting foliage"},
        {"name": "spotted leaves"},
        {"name": "stunted growth"},
        {"name": "rotting fruit"},
        {"name": "distorted leaves"},
        {"name": "white powdery coating"},
        {"name": "leaf curling"},
        {"name": "black spots"},
        {"name": "mildew smell"},
        {"name": "dry leaf edges"},
    ]
    symptom_ids = {symptom["name"]: uuid.uuid4() for symptom in symptoms}
    op.bulk_insert(
        symptom_table,
        [
            {"id": symptom_ids[symptom["name"]], "name": symptom["name"]}
            for symptom in symptoms
        ],
    )

    interventions = [
        {"name": "netting"},
        {"name": "fungicide"},
        {"name": "crop rotation"},
        {"name": "companion planting"},
        {"name": "pesticide"},
        {"name": "manual removal"},
        {"name": "slug pellets"},
        {"name": "insecticidal soap"},
        {"name": "mulching"},
        {"name": "cabbage collars"},
        {"name": "cloches"},
        {"name": "pruning"},
        {"name": "fleece protection"},
        {"name": "consistent watering"},
        {"name": "support structures"},
        {"name": "thinning leaves"},
        {"name": "biological control"},
        {"name": "neem oil"},
        {"name": "sulfur fungicide"},
        {"name": "bacillus thuringiensis"},
    ]
    intervention_ids = {
        intervention["name"]: uuid.uuid4() for intervention in interventions
    }
    op.bulk_insert(
        intervention_table,
        [
            {"id": intervention_ids[intervention["name"]], "name": intervention["name"]}
            for intervention in interventions
        ],
    )

    disease_prevention_data = [
        {
            "disease_id": disease_ids["club root"],
            "intervention_id": intervention_ids["crop rotation"],
        },
        {
            "disease_id": disease_ids["downy mildew"],
            "intervention_id": intervention_ids["crop rotation"],
        },
        {
            "disease_id": disease_ids["downy mildew"],
            "intervention_id": intervention_ids["mulching"],
        },
        {
            "disease_id": disease_ids["downy mildew"],
            "intervention_id": intervention_ids["cloches"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "intervention_id": intervention_ids["mulching"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "intervention_id": intervention_ids["sulfur fungicide"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "intervention_id": intervention_ids["support structures"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "intervention_id": intervention_ids["crop rotation"],
        },
        {
            "disease_id": disease_ids["blight"],
            "intervention_id": intervention_ids["crop rotation"],
        },
        {
            "disease_id": disease_ids["blight"],
            "intervention_id": intervention_ids["mulching"],
        },
        {
            "disease_id": disease_ids["blight"],
            "intervention_id": intervention_ids["cloches"],
        },
        {
            "disease_id": disease_ids["blight"],
            "intervention_id": intervention_ids["fungicide"],
        },
        {
            "disease_id": disease_ids["rust"],
            "intervention_id": intervention_ids["fungicide"],
        },
        {
            "disease_id": disease_ids["rust"],
            "intervention_id": intervention_ids["crop rotation"],
        },
        {
            "disease_id": disease_ids["blossom end rot"],
            "intervention_id": intervention_ids["consistent watering"],
        },
        {
            "disease_id": disease_ids["blossom end rot"],
            "intervention_id": intervention_ids["mulching"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "intervention_id": intervention_ids["pruning"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "intervention_id": intervention_ids["thinning leaves"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "intervention_id": intervention_ids["support structures"],
        },
    ]
    if disease_prevention_data:
        op.bulk_insert(disease_prevention_table, disease_prevention_data)

    disease_treatment_data = [
        {
            "disease_id": disease_ids["blight"],
            "intervention_id": intervention_ids["fungicide"],
        },
        {
            "disease_id": disease_ids["downy mildew"],
            "intervention_id": intervention_ids["fungicide"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "intervention_id": intervention_ids["fungicide"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "intervention_id": intervention_ids["neem oil"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "intervention_id": intervention_ids["sulfur fungicide"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "intervention_id": intervention_ids["pruning"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "intervention_id": intervention_ids["fungicide"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "intervention_id": intervention_ids["thinning leaves"],
        },
        {
            "disease_id": disease_ids["rust"],
            "intervention_id": intervention_ids["fungicide"],
        },
        {
            "disease_id": disease_ids["club root"],
            "intervention_id": intervention_ids["crop rotation"],
        },
        {
            "disease_id": disease_ids["blossom end rot"],
            "intervention_id": intervention_ids["consistent watering"],
        },
        {
            "disease_id": disease_ids["blossom end rot"],
            "intervention_id": intervention_ids["mulching"],
        },
    ]
    if disease_treatment_data:
        op.bulk_insert(disease_treatment_table, disease_treatment_data)

    disease_symptom_data = [
        {
            "disease_id": disease_ids["blight"],
            "symptom_id": symptom_ids["yellowing leaves"],
        },
        {"disease_id": disease_ids["blight"], "symptom_id": symptom_ids["black spots"]},
        {
            "disease_id": disease_ids["blight"],
            "symptom_id": symptom_ids["wilting foliage"],
        },
        {
            "disease_id": disease_ids["downy mildew"],
            "symptom_id": symptom_ids["spotted leaves"],
        },
        {
            "disease_id": disease_ids["downy mildew"],
            "symptom_id": symptom_ids["yellowing leaves"],
        },
        {
            "disease_id": disease_ids["downy mildew"],
            "symptom_id": symptom_ids["wilting foliage"],
        },
        {
            "disease_id": disease_ids["club root"],
            "symptom_id": symptom_ids["stunted growth"],
        },
        {
            "disease_id": disease_ids["club root"],
            "symptom_id": symptom_ids["wilting foliage"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "symptom_id": symptom_ids["white powdery coating"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "symptom_id": symptom_ids["leaf curling"],
        },
        {
            "disease_id": disease_ids["powdery mildew"],
            "symptom_id": symptom_ids["dry leaf edges"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "symptom_id": symptom_ids["rotting fruit"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "symptom_id": symptom_ids["black spots"],
        },
        {
            "disease_id": disease_ids["botrytis"],
            "symptom_id": symptom_ids["wilting foliage"],
        },
        {
            "disease_id": disease_ids["rust"],
            "symptom_id": symptom_ids["spotted leaves"],
        },
        {
            "disease_id": disease_ids["rust"],
            "symptom_id": symptom_ids["yellowing leaves"],
        },
        {
            "disease_id": disease_ids["rust"],
            "symptom_id": symptom_ids["distorted leaves"],
        },
        {
            "disease_id": disease_ids["blossom end rot"],
            "symptom_id": symptom_ids["rotting fruit"],
        },
        {
            "disease_id": disease_ids["blossom end rot"],
            "symptom_id": symptom_ids["black spots"],
        },
        {
            "disease_id": disease_ids["blossom end rot"],
            "symptom_id": symptom_ids["dry leaf edges"],
        },
    ]
    if disease_symptom_data:
        op.bulk_insert(disease_symptom_table, disease_symptom_data)

    pest_prevention_data = [
        {
            "pest_id": pest_ids["slugs"],
            "intervention_id": intervention_ids["slug pellets"],
        },
        {
            "pest_id": pest_ids["slugs"],
            "intervention_id": intervention_ids["manual removal"],
        },
        {"pest_id": pest_ids["slugs"], "intervention_id": intervention_ids["mulching"]},
        {
            "pest_id": pest_ids["slugs"],
            "intervention_id": intervention_ids["cabbage collars"],
        },
        {
            "pest_id": pest_ids["slugs"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {"pest_id": pest_ids["birds"], "intervention_id": intervention_ids["netting"]},
        {
            "pest_id": pest_ids["birds"],
            "intervention_id": intervention_ids["cabbage collars"],
        },
        {
            "pest_id": pest_ids["root fly"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {
            "pest_id": pest_ids["root fly"],
            "intervention_id": intervention_ids["cabbage collars"],
        },
        {
            "pest_id": pest_ids["leek moth"],
            "intervention_id": intervention_ids["fleece protection"],
        },
        {
            "pest_id": pest_ids["leek moth"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {
            "pest_id": pest_ids["aphids"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {
            "pest_id": pest_ids["aphids"],
            "intervention_id": intervention_ids["biological control"],
        },
        {
            "pest_id": pest_ids["aphids"],
            "intervention_id": intervention_ids["pesticide"],
        },
        {
            "pest_id": pest_ids["whiteflies"],
            "intervention_id": intervention_ids["biological control"],
        },
        {
            "pest_id": pest_ids["whiteflies"],
            "intervention_id": intervention_ids["pesticide"],
        },
        {
            "pest_id": pest_ids["whiteflies"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["manual removal"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["netting"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["biological control"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["pesticide"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["fleece protection"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["bacillus thuringiensis"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {
            "pest_id": pest_ids["spider mites"],
            "intervention_id": intervention_ids["biological control"],
        },
        {
            "pest_id": pest_ids["spider mites"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {
            "pest_id": pest_ids["gooseberry sawfly"],
            "intervention_id": intervention_ids["companion planting"],
        },
        {
            "pest_id": pest_ids["gooseberry sawfly"],
            "intervention_id": intervention_ids["netting"],
        },
    ]
    if pest_prevention_data:
        op.bulk_insert(pest_prevention_table, pest_prevention_data)

    pest_treatment_data = [
        {
            "pest_id": pest_ids["gooseberry sawfly"],
            "intervention_id": intervention_ids["insecticidal soap"],
        },
        {
            "pest_id": pest_ids["leek moth"],
            "intervention_id": intervention_ids["fleece protection"],
        },
        {
            "pest_id": pest_ids["root fly"],
            "intervention_id": intervention_ids["fleece protection"],
        },
        {
            "pest_id": pest_ids["aphids"],
            "intervention_id": intervention_ids["insecticidal soap"],
        },
        {
            "pest_id": pest_ids["aphids"],
            "intervention_id": intervention_ids["neem oil"],
        },
        {
            "pest_id": pest_ids["spider mites"],
            "intervention_id": intervention_ids["pruning"],
        },
        {
            "pest_id": pest_ids["spider mites"],
            "intervention_id": intervention_ids["neem oil"],
        },
        {
            "pest_id": pest_ids["slugs"],
            "intervention_id": intervention_ids["manual removal"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["manual removal"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["bacillus thuringiensis"],
        },
        {
            "pest_id": pest_ids["aphids"],
            "intervention_id": intervention_ids["pesticide"],
        },
        {
            "pest_id": pest_ids["whiteflies"],
            "intervention_id": intervention_ids["pesticide"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["insecticidal soap"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["neem oil"],
        },
        {
            "pest_id": pest_ids["caterpillars"],
            "intervention_id": intervention_ids["pesticide"],
        },
    ]
    if pest_treatment_data:
        op.bulk_insert(pest_treatment_table, pest_treatment_data)

    connection = op.get_bind()
    family_table = sa.Table(
        "family",
        sa.MetaData(),
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String),
    )
    family_rows = connection.execute(
        sa.select(family_table.c.id, family_table.c.name)
    ).fetchall()
    family_name_to_id = {name: id for id, name in family_rows}

    family_disease_seed_data = []
    disease_links = {
        "blight": ["tomato", "potato", "sweet pepper"],
        "downy mildew": ["lettuce", "onion", "shallot", "celery", "cucumber", "parsley", "leek", "garlic"],
        "club root": [
            "broccoli",
            "cauliflower",
            "brussels sprout",
            "radish",
            "carrot",
            "parsnip",
            "beetroot",
            "asparagus",
        ],
        "powdery mildew": [
            "pumpkin",
            "squash",
            "cucumber",
            "rosemary",
            "lettuce",
            "lavender",
            "sage",
            "thyme",
            "basil",
            "blackcurrant",
            "redcurrant",
            "jostaberry",
            "blackberry",
            "parsley",
        ],
        "botrytis": ["strawberry", "raspberry", "blackberry", "blueberry", "leek", "garlic"],
        "rust": [
            "runner bean",
            "sugar snap pea",
            "spinach",
            "lettuce",
            "asparagus",
            "sweetcorn",
            "blackberry",
            "leek",
            "garlic",
        ],
        "blossom end rot": ["tomato", "sweet pepper", "pumpkin", "squash"],
    }
    for disease, families in disease_links.items():
        for fam in families:
            if fam in family_name_to_id:
                family_disease_seed_data.append(
                    {
                        "family_id": family_name_to_id[fam],
                        "disease_id": disease_ids[disease],
                    }
                )
    op.bulk_insert(family_disease_table, family_disease_seed_data)

    family_pest_seed_data = []
    pest_links = {
        "caterpillars": [
            "broccoli",
            "cauliflower",
            "brussels sprout",
            "lettuce",
            "tomato",
        ],
        "slugs": [
            "spinach",
            "beetroot",
            "pumpkin",
            "parsley",
            "lettuce",
            "strawberry",
            "rosemary",
            "lavender",
            "sage",
            "thyme",
            "basil",
            "asparagus",
            "radish",
            "runner bean",
            "celery",
            "sugar snap pea",
        ],
        "aphids": [
            "gooseberry",
            "raspberry",
            "sweet pepper",
            "potato",
            "cucumber",
            "broccoli",
            "cauliflower",
            "brussels sprout",
            "asparagus",
            "radish",
            "sweetcorn",
            "lettuce",
            "blueberry",
            "squash",
            "blackcurrant",
            "redcurrant",
            "jostaberry",
            "blackberry",
            "celery",
            "sugar snap pea",
        ],
        "whiteflies": ["tomato", "sweet pepper", "lettuce", "cucumber", "celery"],
        "birds": [
            "garlic",
            "strawberry",
            "broccoli",
            "cauliflower",
            "brussels sprout",
            "peas",
            "beans",
            "lettuce",
        ],
        "gooseberry sawfly": ["gooseberry", "redcurrant", "blackcurrant"],
        "leek moth": ["leek", "onion", "shallot", "garlic"],
        "root fly": ["carrot", "parsnip", "onion", "shallot", "leek", "beetroot"],
        "spider mites": [
            "tomato",
            "sweet pepper",
            "strawberry",
            "squash",
            "runner bean",
        ],
    }
    for pest, families in pest_links.items():
        for fam in families:
            if fam in family_name_to_id:
                family_pest_seed_data.append(
                    {"family_id": family_name_to_id[fam], "pest_id": pest_ids[pest]}
                )
    op.bulk_insert(family_pest_table, family_pest_seed_data)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("family_pest")
    op.drop_table("family_disease")
    op.drop_table("pest_treatment")
    op.drop_table("pest_prevention")
    op.drop_table("disease_treatment")
    op.drop_table("disease_symptom")
    op.drop_table("disease_prevention")
    op.drop_index(op.f("ix_symptom_name"), table_name="symptom")
    op.drop_index(op.f("ix_symptom_id"), table_name="symptom")
    op.drop_table("symptom")
    op.drop_index(op.f("ix_pest_name"), table_name="pest")
    op.drop_index(op.f("ix_pest_id"), table_name="pest")
    op.drop_table("pest")
    op.drop_index(op.f("ix_intervention_name"), table_name="intervention")
    op.drop_index(op.f("ix_intervention_id"), table_name="intervention")
    op.drop_table("intervention")
    op.drop_index(op.f("ix_disease_name"), table_name="disease")
    op.drop_index(op.f("ix_disease_id"), table_name="disease")
    op.drop_table("disease")
