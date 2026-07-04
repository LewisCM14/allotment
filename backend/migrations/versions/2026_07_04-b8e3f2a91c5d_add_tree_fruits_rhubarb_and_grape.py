"""add tree fruits, rhubarb and grape families with pests and diseases

Revision ID: b8e3f2a91c5d
Revises: 9505eadaea48
Create Date: 2026-07-04 00:00:00.000000

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8e3f2a91c5d"
down_revision: Union[str, None] = "9505eadaea48"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tree fruit (apple, pear, plum, cherry), rhubarb and grape families
    along with their botanical groups, companion/antagonist relationships,
    pests, diseases, symptoms and interventions."""

    connection = op.get_bind()

    # ── New botanical groups ──────────────────────────────────────────────────
    new_botanical_groups = [
        # Distinct from the existing 'rosaceae' group (strawberry, 4-year rotation)
        # as tree fruits are permanent plantings that do not rotate.
        {"name": "rosaceae tree fruit", "rotate_years": None},
        # Rhubarb family.
        {"name": "polygonaceae", "rotate_years": None},
        # Grape family.
        {"name": "vitaceae", "rotate_years": None},
    ]
    new_bg_ids = {bg["name"]: uuid.uuid4() for bg in new_botanical_groups}
    op.bulk_insert(
        sa.Table(
            "botanical_group",
            sa.MetaData(),
            sa.Column("botanical_group_id", sa.UUID()),
            sa.Column("botanical_group_name", sa.String()),
            sa.Column("rotate_years", sa.Integer()),
        ),
        [
            {
                "botanical_group_id": new_bg_ids[bg["name"]],
                "botanical_group_name": bg["name"],
                "rotate_years": bg["rotate_years"],
            }
            for bg in new_botanical_groups
        ],
    )

    # ── New families ──────────────────────────────────────────────────────────
    new_families = [
        {"name": "apple", "botanical_group": "rosaceae tree fruit"},
        {"name": "pear", "botanical_group": "rosaceae tree fruit"},
        {"name": "plum", "botanical_group": "rosaceae tree fruit"},
        {"name": "cherry", "botanical_group": "rosaceae tree fruit"},
        {"name": "rhubarb", "botanical_group": "polygonaceae"},
        {"name": "grape", "botanical_group": "vitaceae"},
    ]
    new_family_ids = {f["name"]: uuid.uuid4() for f in new_families}
    op.bulk_insert(
        sa.Table(
            "family",
            sa.MetaData(),
            sa.Column("family_id", sa.UUID()),
            sa.Column("family_name", sa.String()),
            sa.Column("botanical_group_id", sa.UUID()),
        ),
        [
            {
                "family_id": new_family_ids[f["name"]],
                "family_name": f["name"],
                "botanical_group_id": new_bg_ids[f["botanical_group"]],
            }
            for f in new_families
        ],
    )

    # ── Query all family IDs (existing + new) ─────────────────────────────────
    family_table = sa.Table(
        "family",
        sa.MetaData(),
        sa.Column("family_id", sa.UUID()),
        sa.Column("family_name", sa.String()),
    )
    family_name_to_id = {
        name: fid
        for fid, name in connection.execute(
            sa.select(family_table.c.family_id, family_table.c.family_name)
        ).fetchall()
    }

    # ── Companion planting ────────────────────────────────────────────────────
    new_companions = [
        # Rhubarb — alliums and aromatic herbs deter aphids and crown-feeding pests.
        {"family": "rhubarb", "companion": "garlic"},
        {"family": "rhubarb", "companion": "onion"},
        {"family": "rhubarb", "companion": "thyme"},
        {"family": "rhubarb", "companion": "sage"},
        # Apple — alliums suppress scab spores; aromatics/flowers attract pollinators
        # and deter aphids, codling moth and winter moth.
        {"family": "apple", "companion": "garlic"},
        {"family": "apple", "companion": "onion"},
        {"family": "apple", "companion": "marigolds"},
        {"family": "apple", "companion": "lavender"},
        {"family": "apple", "companion": "borage"},
        {"family": "apple", "companion": "thyme"},
        {"family": "apple", "companion": "rosemary"},
        # Pear — same rationale as apple.
        {"family": "pear", "companion": "garlic"},
        {"family": "pear", "companion": "onion"},
        {"family": "pear", "companion": "marigolds"},
        {"family": "pear", "companion": "lavender"},
        {"family": "pear", "companion": "borage"},
        {"family": "pear", "companion": "thyme"},
        # Plum — alliums and aromatics deter aphids; borage attracts beneficial insects.
        {"family": "plum", "companion": "garlic"},
        {"family": "plum", "companion": "onion"},
        {"family": "plum", "companion": "marigolds"},
        {"family": "plum", "companion": "borage"},
        {"family": "plum", "companion": "lavender"},
        {"family": "plum", "companion": "thyme"},
        # Cherry — same rationale as plum; lavender and borage attract pollinators
        # which is especially important for fruiting.
        {"family": "cherry", "companion": "garlic"},
        {"family": "cherry", "companion": "onion"},
        {"family": "cherry", "companion": "marigolds"},
        {"family": "cherry", "companion": "borage"},
        {"family": "cherry", "companion": "lavender"},
        {"family": "cherry", "companion": "thyme"},
        # Grape — garlic and alliums deter aphids and beetles; aromatic herbs
        # and flowers attract pollinators and beneficial predatory insects.
        {"family": "grape", "companion": "garlic"},
        {"family": "grape", "companion": "onion"},
        {"family": "grape", "companion": "borage"},
        {"family": "grape", "companion": "marigolds"},
        {"family": "grape", "companion": "lavender"},
        {"family": "grape", "companion": "thyme"},
        {"family": "grape", "companion": "rosemary"},
    ]
    companions_data = [
        {
            "family_id": family_name_to_id[c["family"]],
            "companion_family_id": family_name_to_id[c["companion"]],
        }
        for c in new_companions
        if c["family"] in family_name_to_id and c["companion"] in family_name_to_id
    ]
    if companions_data:
        op.bulk_insert(
            sa.Table(
                "family_companion",
                sa.MetaData(),
                sa.Column("family_id", sa.UUID()),
                sa.Column("companion_family_id", sa.UUID()),
            ),
            companions_data,
        )

    # ── Antagonist planting ───────────────────────────────────────────────────
    new_antagonists = [
        # Rhubarb — shares foliar fungal susceptibility with nightshades and
        # competes for similar heavy-feeding soil nutrients.
        {"family": "rhubarb", "antagonist": "potato"},
        {"family": "rhubarb", "antagonist": "tomato"},
        # Tree fruits — proximity to nightshades increases botrytis and blight
        # pressure shared across crops; potatoes are also significant hosts for
        # common soil pathogens that affect Rosaceae roots.
        {"family": "apple", "antagonist": "potato"},
        {"family": "apple", "antagonist": "tomato"},
        {"family": "pear", "antagonist": "potato"},
        {"family": "pear", "antagonist": "tomato"},
        {"family": "plum", "antagonist": "potato"},
        {"family": "plum", "antagonist": "tomato"},
        {"family": "cherry", "antagonist": "potato"},
        {"family": "cherry", "antagonist": "tomato"},
        # Grape — brassica root exudates can inhibit vine root development;
        # nightshades share downy mildew and botrytis pressure with vines.
        {"family": "grape", "antagonist": "potato"},
        {"family": "grape", "antagonist": "tomato"},
        {"family": "grape", "antagonist": "cabbage"},
        {"family": "grape", "antagonist": "broccoli"},
        {"family": "grape", "antagonist": "cauliflower"},
    ]
    antagonists_data = [
        {
            "family_id": family_name_to_id[a["family"]],
            "antagonist_family_id": family_name_to_id[a["antagonist"]],
        }
        for a in new_antagonists
        if a["family"] in family_name_to_id and a["antagonist"] in family_name_to_id
    ]
    if antagonists_data:
        op.bulk_insert(
            sa.Table(
                "family_antagonist",
                sa.MetaData(),
                sa.Column("family_id", sa.UUID()),
                sa.Column("antagonist_family_id", sa.UUID()),
            ),
            antagonists_data,
        )

    # ── New symptoms ──────────────────────────────────────────────────────────
    new_symptoms = [
        {"name": "dark scabby lesions"},
        {"name": "silvery leaf surface"},
        {"name": "sunken brown patches"},
    ]
    new_symptom_ids = {s["name"]: uuid.uuid4() for s in new_symptoms}
    op.bulk_insert(
        sa.Table(
            "symptom",
            sa.MetaData(),
            sa.Column("symptom_id", sa.UUID()),
            sa.Column("symptom_name", sa.String()),
        ),
        [
            {"symptom_id": new_symptom_ids[s["name"]], "symptom_name": s["name"]}
            for s in new_symptoms
        ],
    )

    # ── Query all symptom IDs (existing + new) ────────────────────────────────
    symptom_table = sa.Table(
        "symptom",
        sa.MetaData(),
        sa.Column("symptom_id", sa.UUID()),
        sa.Column("symptom_name", sa.String()),
    )
    symptom_name_to_id = {
        name: sid
        for sid, name in connection.execute(
            sa.select(symptom_table.c.symptom_id, symptom_table.c.symptom_name)
        ).fetchall()
    }

    # ── New interventions ─────────────────────────────────────────────────────
    new_interventions = [
        {"name": "pheromone traps"},
        {"name": "grease bands"},
        {"name": "copper fungicide"},
    ]
    new_intervention_ids = {i["name"]: uuid.uuid4() for i in new_interventions}
    op.bulk_insert(
        sa.Table(
            "intervention",
            sa.MetaData(),
            sa.Column("intervention_id", sa.UUID()),
            sa.Column("intervention_name", sa.String()),
        ),
        [
            {
                "intervention_id": new_intervention_ids[i["name"]],
                "intervention_name": i["name"],
            }
            for i in new_interventions
        ],
    )

    # ── Query all intervention IDs (existing + new) ───────────────────────────
    intervention_table = sa.Table(
        "intervention",
        sa.MetaData(),
        sa.Column("intervention_id", sa.UUID()),
        sa.Column("intervention_name", sa.String()),
    )
    intervention_name_to_id = {
        name: iid
        for iid, name in connection.execute(
            sa.select(
                intervention_table.c.intervention_id,
                intervention_table.c.intervention_name,
            )
        ).fetchall()
    }

    # ── New diseases ──────────────────────────────────────────────────────────
    new_diseases = [
        {"name": "apple scab"},
        {"name": "silver leaf"},
        {"name": "brown rot"},
        {"name": "canker"},
        {"name": "crown rot"},
    ]
    new_disease_ids = {d["name"]: uuid.uuid4() for d in new_diseases}
    op.bulk_insert(
        sa.Table(
            "disease",
            sa.MetaData(),
            sa.Column("disease_id", sa.UUID()),
            sa.Column("disease_name", sa.String()),
        ),
        [
            {"disease_id": new_disease_ids[d["name"]], "disease_name": d["name"]}
            for d in new_diseases
        ],
    )

    # ── New pests ─────────────────────────────────────────────────────────────
    new_pests = [
        {"name": "codling moth"},
        {"name": "vine weevil"},
        {"name": "winter moth"},
    ]
    new_pest_ids = {p["name"]: uuid.uuid4() for p in new_pests}
    op.bulk_insert(
        sa.Table(
            "pest",
            sa.MetaData(),
            sa.Column("pest_id", sa.UUID()),
            sa.Column("pest_name", sa.String()),
        ),
        [
            {"pest_id": new_pest_ids[p["name"]], "pest_name": p["name"]}
            for p in new_pests
        ],
    )

    # ── Query all disease/pest IDs (existing + new) ───────────────────────────
    disease_table = sa.Table(
        "disease",
        sa.MetaData(),
        sa.Column("disease_id", sa.UUID()),
        sa.Column("disease_name", sa.String()),
    )
    disease_name_to_id = {
        name: did
        for did, name in connection.execute(
            sa.select(disease_table.c.disease_id, disease_table.c.disease_name)
        ).fetchall()
    }

    pest_table = sa.Table(
        "pest",
        sa.MetaData(),
        sa.Column("pest_id", sa.UUID()),
        sa.Column("pest_name", sa.String()),
    )
    pest_name_to_id = {
        name: pid
        for pid, name in connection.execute(
            sa.select(pest_table.c.pest_id, pest_table.c.pest_name)
        ).fetchall()
    }

    # ── Disease symptoms ──────────────────────────────────────────────────────
    disease_symptom_data = [
        # Apple scab (Venturia inaequalis)
        {"disease": "apple scab", "symptom": "dark scabby lesions"},
        {"disease": "apple scab", "symptom": "spotted leaves"},
        {"disease": "apple scab", "symptom": "yellowing leaves"},
        # Silver leaf (Chondrostereum purpureum)
        {"disease": "silver leaf", "symptom": "silvery leaf surface"},
        {"disease": "silver leaf", "symptom": "wilting foliage"},
        {"disease": "silver leaf", "symptom": "stunted growth"},
        # Brown rot (Monilinia spp.)
        {"disease": "brown rot", "symptom": "rotting fruit"},
        {"disease": "brown rot", "symptom": "spotted leaves"},
        {"disease": "brown rot", "symptom": "wilting foliage"},
        # Canker (Neonectria ditissima / Pseudomonas syringae)
        {"disease": "canker", "symptom": "sunken brown patches"},
        {"disease": "canker", "symptom": "stunted growth"},
        {"disease": "canker", "symptom": "yellowing leaves"},
        # Crown rot (Phytophthora spp.)
        {"disease": "crown rot", "symptom": "wilting foliage"},
        {"disease": "crown rot", "symptom": "stunted growth"},
        {"disease": "crown rot", "symptom": "yellowing leaves"},
        {"disease": "crown rot", "symptom": "rotting fruit"},
    ]
    disease_symptom_rows = [
        {
            "disease_id": disease_name_to_id[row["disease"]],
            "symptom_id": symptom_name_to_id[row["symptom"]],
        }
        for row in disease_symptom_data
        if row["disease"] in disease_name_to_id
        and row["symptom"] in symptom_name_to_id
    ]
    if disease_symptom_rows:
        op.bulk_insert(
            sa.Table(
                "disease_symptom",
                sa.MetaData(),
                sa.Column("disease_id", sa.UUID()),
                sa.Column("symptom_id", sa.UUID()),
            ),
            disease_symptom_rows,
        )

    # ── Disease prevention ────────────────────────────────────────────────────
    disease_prevention_data = [
        {"disease": "apple scab", "intervention": "pruning"},
        {"disease": "apple scab", "intervention": "copper fungicide"},
        {"disease": "apple scab", "intervention": "mulching"},
        {"disease": "silver leaf", "intervention": "pruning"},
        {"disease": "silver leaf", "intervention": "fungicide"},
        {"disease": "brown rot", "intervention": "pruning"},
        {"disease": "brown rot", "intervention": "fungicide"},
        {"disease": "brown rot", "intervention": "netting"},
        {"disease": "canker", "intervention": "pruning"},
        {"disease": "canker", "intervention": "copper fungicide"},
        {"disease": "canker", "intervention": "mulching"},
        {"disease": "crown rot", "intervention": "mulching"},
        {"disease": "crown rot", "intervention": "consistent watering"},
    ]
    disease_prevention_rows = [
        {
            "disease_id": disease_name_to_id[row["disease"]],
            "intervention_id": intervention_name_to_id[row["intervention"]],
        }
        for row in disease_prevention_data
        if row["disease"] in disease_name_to_id
        and row["intervention"] in intervention_name_to_id
    ]
    if disease_prevention_rows:
        op.bulk_insert(
            sa.Table(
                "disease_prevention",
                sa.MetaData(),
                sa.Column("disease_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            disease_prevention_rows,
        )

    # ── Disease treatment ─────────────────────────────────────────────────────
    disease_treatment_data = [
        {"disease": "apple scab", "intervention": "fungicide"},
        {"disease": "apple scab", "intervention": "copper fungicide"},
        {"disease": "apple scab", "intervention": "pruning"},
        {"disease": "silver leaf", "intervention": "pruning"},
        {"disease": "brown rot", "intervention": "pruning"},
        {"disease": "brown rot", "intervention": "fungicide"},
        {"disease": "brown rot", "intervention": "manual removal"},
        {"disease": "canker", "intervention": "pruning"},
        {"disease": "canker", "intervention": "copper fungicide"},
        {"disease": "crown rot", "intervention": "fungicide"},
    ]
    disease_treatment_rows = [
        {
            "disease_id": disease_name_to_id[row["disease"]],
            "intervention_id": intervention_name_to_id[row["intervention"]],
        }
        for row in disease_treatment_data
        if row["disease"] in disease_name_to_id
        and row["intervention"] in intervention_name_to_id
    ]
    if disease_treatment_rows:
        op.bulk_insert(
            sa.Table(
                "disease_treatment",
                sa.MetaData(),
                sa.Column("disease_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            disease_treatment_rows,
        )

    # ── Pest prevention ───────────────────────────────────────────────────────
    pest_prevention_data = [
        # Codling moth (Cydia pomonella) — pheromone traps intercept males before
        # mating; physical netting blocks egg-laying females.
        {"pest": "codling moth", "intervention": "pheromone traps"},
        {"pest": "codling moth", "intervention": "netting"},
        {"pest": "codling moth", "intervention": "neem oil"},
        # Vine weevil (Otiorhynchus sulcatus) — biological control (Steinernema
        # nematodes) is the primary prevention for container/bed-grown vines.
        {"pest": "vine weevil", "intervention": "biological control"},
        {"pest": "vine weevil", "intervention": "netting"},
        {"pest": "vine weevil", "intervention": "mulching"},
        # Winter moth (Operophtera brumata) — grease bands on trunks stop wingless
        # females from climbing to lay eggs in the canopy.
        {"pest": "winter moth", "intervention": "grease bands"},
        {"pest": "winter moth", "intervention": "netting"},
    ]
    pest_prevention_rows = [
        {
            "pest_id": pest_name_to_id[row["pest"]],
            "intervention_id": intervention_name_to_id[row["intervention"]],
        }
        for row in pest_prevention_data
        if row["pest"] in pest_name_to_id
        and row["intervention"] in intervention_name_to_id
    ]
    if pest_prevention_rows:
        op.bulk_insert(
            sa.Table(
                "pest_prevention",
                sa.MetaData(),
                sa.Column("pest_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            pest_prevention_rows,
        )

    # ── Pest treatment ────────────────────────────────────────────────────────
    pest_treatment_data = [
        {"pest": "codling moth", "intervention": "pheromone traps"},
        {"pest": "codling moth", "intervention": "manual removal"},
        {"pest": "codling moth", "intervention": "pesticide"},
        {"pest": "vine weevil", "intervention": "biological control"},
        {"pest": "vine weevil", "intervention": "pesticide"},
        {"pest": "vine weevil", "intervention": "manual removal"},
        {"pest": "winter moth", "intervention": "grease bands"},
        {"pest": "winter moth", "intervention": "manual removal"},
        {"pest": "winter moth", "intervention": "bacillus thuringiensis"},
    ]
    pest_treatment_rows = [
        {
            "pest_id": pest_name_to_id[row["pest"]],
            "intervention_id": intervention_name_to_id[row["intervention"]],
        }
        for row in pest_treatment_data
        if row["pest"] in pest_name_to_id
        and row["intervention"] in intervention_name_to_id
    ]
    if pest_treatment_rows:
        op.bulk_insert(
            sa.Table(
                "pest_treatment",
                sa.MetaData(),
                sa.Column("pest_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            pest_treatment_rows,
        )

    # ── Family disease links ──────────────────────────────────────────────────
    # Existing diseases (powdery mildew, downy mildew, botrytis, rust) are
    # referenced by name from the queried disease_name_to_id map.
    disease_links = {
        "apple scab": ["apple", "pear"],
        "silver leaf": ["apple", "pear", "plum", "cherry"],
        "brown rot": ["apple", "pear", "plum", "cherry", "grape"],
        "canker": ["apple", "pear", "cherry"],
        "crown rot": ["rhubarb"],
        "powdery mildew": ["apple", "pear", "grape", "rhubarb"],
        "downy mildew": ["grape"],
        "botrytis": ["apple", "pear", "plum", "cherry", "grape", "rhubarb"],
        "rust": ["plum"],
    }
    family_disease_rows = [
        {
            "family_id": family_name_to_id[fam],
            "disease_id": disease_name_to_id[disease],
        }
        for disease, families in disease_links.items()
        for fam in families
        if fam in family_name_to_id and disease in disease_name_to_id
    ]
    if family_disease_rows:
        op.bulk_insert(
            sa.Table(
                "family_disease",
                sa.MetaData(),
                sa.Column("family_id", sa.UUID()),
                sa.Column("disease_id", sa.UUID()),
            ),
            family_disease_rows,
        )

    # ── Family pest links ─────────────────────────────────────────────────────
    # Existing pests (aphids, birds, slugs, spider mites) are referenced by name
    # from the queried pest_name_to_id map.
    pest_links = {
        "aphids": ["apple", "pear", "plum", "cherry", "grape", "rhubarb"],
        "birds": ["apple", "pear", "plum", "cherry", "grape"],
        "slugs": ["rhubarb"],
        "spider mites": ["grape"],
        "codling moth": ["apple", "pear", "plum", "cherry"],
        "vine weevil": ["grape"],
        "winter moth": ["apple", "pear", "plum", "cherry"],
    }
    family_pest_rows = [
        {
            "family_id": family_name_to_id[fam],
            "pest_id": pest_name_to_id[pest],
        }
        for pest, families in pest_links.items()
        for fam in families
        if fam in family_name_to_id and pest in pest_name_to_id
    ]
    if family_pest_rows:
        op.bulk_insert(
            sa.Table(
                "family_pest",
                sa.MetaData(),
                sa.Column("family_id", sa.UUID()),
                sa.Column("pest_id", sa.UUID()),
            ),
            family_pest_rows,
        )


def downgrade() -> None:
    """Remove all data inserted by this migration."""

    connection = op.get_bind()

    # Family deletions cascade to: family_companion, family_antagonist,
    # family_disease, family_pest via ON DELETE CASCADE.
    connection.execute(
        sa.text(
            "DELETE FROM family WHERE family_name IN "
            "('apple', 'pear', 'plum', 'cherry', 'rhubarb', 'grape')"
        )
    )

    # Botanical group deletions are safe once the families above are removed
    # (FK is RESTRICT, so families must be deleted first).
    connection.execute(
        sa.text(
            "DELETE FROM botanical_group WHERE botanical_group_name IN "
            "('rosaceae tree fruit', 'polygonaceae', 'vitaceae')"
        )
    )

    # Pest deletions cascade to: pest_prevention, pest_treatment, family_pest.
    connection.execute(
        sa.text(
            "DELETE FROM pest WHERE pest_name IN "
            "('codling moth', 'vine weevil', 'winter moth')"
        )
    )

    # Disease deletions cascade to: disease_symptom, disease_prevention,
    # disease_treatment, family_disease.
    connection.execute(
        sa.text(
            "DELETE FROM disease WHERE disease_name IN "
            "('apple scab', 'silver leaf', 'brown rot', 'canker', 'crown rot')"
        )
    )

    connection.execute(
        sa.text(
            "DELETE FROM symptom WHERE symptom_name IN "
            "('dark scabby lesions', 'silvery leaf surface', 'sunken brown patches')"
        )
    )

    connection.execute(
        sa.text(
            "DELETE FROM intervention WHERE intervention_name IN "
            "('pheromone traps', 'grease bands', 'copper fungicide')"
        )
    )
