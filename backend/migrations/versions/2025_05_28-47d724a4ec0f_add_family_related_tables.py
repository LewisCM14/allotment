"""add family related tables

Revision ID: 47d724a4ec0f
Revises: 851e27ae4553
Create Date: 2025-05-28 21:01:40.130255

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "47d724a4ec0f"
down_revision: Union[str, None] = "851e27ae4553"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    botanical_group_table = op.create_table(
        "botanical_group",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("recommended_rotation_years", sa.Integer(), nullable=True),
        sa.CheckConstraint("name = LOWER(name)", name="ck_botanical_group_name_lower"),
        sa.UniqueConstraint("name", name="uq_botanical_group_name"),
    )
    op.create_index(
        op.f("ix_botanical_group_id"), "botanical_group", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_botanical_group_name"), "botanical_group", ["name"], unique=True
    )
    family_table = op.create_table(
        "family",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column(
            "botanical_group_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.CheckConstraint("name = LOWER(name)", name="ck_family_name_lower"),
        sa.ForeignKeyConstraint(
            ["botanical_group_id"], ["botanical_group.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("name", name="uq_family_name"),
    )
    op.create_index(op.f("ix_family_id"), "family", ["id"], unique=False)
    op.create_index(op.f("ix_family_name"), "family", ["name"], unique=True)
    family_antagonist_table = op.create_table(
        "family_antagonist",
        sa.Column(
            "family_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "antagonist_family_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["antagonist_family_id"], ["family.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("family_id", "antagonist_family_id"),
    )
    family_companion_table = op.create_table(
        "family_companion",
        sa.Column(
            "family_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "companion_family_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["companion_family_id"], ["family.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("family_id", "companion_family_id"),
    )

    botanical_groups = [
        {"name": "nightshade", "recommended_rotation_years": 2},
        {"name": "allium", "recommended_rotation_years": 2},
        {"name": "brassica", "recommended_rotation_years": 1},
        {"name": "brassicaceae", "recommended_rotation_years": 2},
        {"name": "legume", "recommended_rotation_years": 3},
        {"name": "root vegetable", "recommended_rotation_years": 4},
        {"name": "cereals and grasses", "recommended_rotation_years": 3},
        {"name": "gourd", "recommended_rotation_years": 4},
        {"name": "rosaceae", "recommended_rotation_years": 4},
        {"name": "ribes", "recommended_rotation_years": None},
        {"name": "rubus", "recommended_rotation_years": None},
        {"name": "ericaceae", "recommended_rotation_years": None},
        {"name": "mediterranean herb", "recommended_rotation_years": None},
        {"name": "mint", "recommended_rotation_years": 3},
        {"name": "umbellifers", "recommended_rotation_years": 2},
        {"name": "daisy", "recommended_rotation_years": 3},
        {"name": "amaranthaceae", "recommended_rotation_years": 1},
        {"name": "asparagaceae", "recommended_rotation_years": None},
    ]
    botanical_group_ids = {bg["name"]: uuid.uuid4() for bg in botanical_groups}
    op.bulk_insert(
        botanical_group_table,
        [
            {
                "id": botanical_group_ids[bg["name"]],
                "name": bg["name"],
                "recommended_rotation_years": bg["recommended_rotation_years"],
            }
            for bg in botanical_groups
        ],
    )

    families = [
        {"name": "radish", "botanical_group": "brassicaceae"},
        {"name": "squash", "botanical_group": "gourd"},
        {"name": "basil", "botanical_group": "mint"},
        {"name": "parsley", "botanical_group": "umbellifers"},
        {"name": "celery", "botanical_group": "umbellifers"},
        {"name": "lettuce", "botanical_group": "daisy"},
        {"name": "spinach", "botanical_group": "amaranthaceae"},
        {"name": "asparagus", "botanical_group": "asparagaceae"},
        {"name": "onion", "botanical_group": "allium"},
        {"name": "shallot", "botanical_group": "allium"},
        {"name": "leek", "botanical_group": "allium"},
        {"name": "garlic", "botanical_group": "allium"},
        {"name": "tomato", "botanical_group": "nightshade"},
        {"name": "sweet pepper", "botanical_group": "nightshade"},
        {"name": "potato", "botanical_group": "nightshade"},
        {"name": "broccoli", "botanical_group": "brassica"},
        {"name": "brussels sprout", "botanical_group": "brassica"},
        {"name": "cauliflower", "botanical_group": "brassica"},
        {"name": "runner bean", "botanical_group": "legume"},
        {"name": "sugar snap pea", "botanical_group": "legume"},
        {"name": "carrot", "botanical_group": "root vegetable"},
        {"name": "parsnip", "botanical_group": "root vegetable"},
        {"name": "beetroot", "botanical_group": "root vegetable"},
        {"name": "sweetcorn", "botanical_group": "cereals and grasses"},
        {"name": "pumpkin", "botanical_group": "gourd"},
        {"name": "cucumber", "botanical_group": "gourd"},
        {"name": "rosemary", "botanical_group": "mediterranean herb"},
        {"name": "lavender", "botanical_group": "mediterranean herb"},
        {"name": "sage", "botanical_group": "mediterranean herb"},
        {"name": "thyme", "botanical_group": "mediterranean herb"},
        {"name": "blueberry", "botanical_group": "ericaceae"},
        {"name": "cranberry", "botanical_group": "ericaceae"},
        {"name": "strawberry", "botanical_group": "rosaceae"},
        {"name": "raspberry", "botanical_group": "rubus"},
        {"name": "blackberry", "botanical_group": "rubus"},
        {"name": "gooseberry", "botanical_group": "ribes"},
        {"name": "jostaberry", "botanical_group": "ribes"},
        {"name": "redcurrant", "botanical_group": "ribes"},
        {"name": "blackcurrant", "botanical_group": "ribes"},
        {"name": "borage", "botanical_group": "daisy"},
        {"name": "marigolds", "botanical_group": "daisy"},
        {"name": "daffodils", "botanical_group": "asparagaceae"},
    ]
    family_ids = {f["name"]: uuid.uuid4() for f in families}
    op.bulk_insert(
        family_table,
        [
            {
                "id": family_ids[f["name"]],
                "name": f["name"],
                "botanical_group_id": botanical_group_ids[f["botanical_group"]],
            }
            for f in families
        ],
    )

    family_companions_seed_data = [
        {
            "family_id": family_ids["onion"],
            "companion_family_id": family_ids["parsley"],
        },
        {
            "family_id": family_ids["onion"],
            "companion_family_id": family_ids["spinach"],
        },
        {
            "family_id": family_ids["beetroot"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["shallot"],
            "companion_family_id": family_ids["parsley"],
        },
        {
            "family_id": family_ids["shallot"],
            "companion_family_id": family_ids["spinach"],
        },
        {
            "family_id": family_ids["beetroot"],
            "companion_family_id": family_ids["shallot"],
        },
        {
            "family_id": family_ids["beetroot"],
            "companion_family_id": family_ids["lettuce"],
        },
        {"family_id": family_ids["carrot"], "companion_family_id": family_ids["leek"]},
        {
            "family_id": family_ids["cauliflower"],
            "companion_family_id": family_ids["spinach"],
        },
        {
            "family_id": family_ids["cauliflower"],
            "companion_family_id": family_ids["celery"],
        },
        {
            "family_id": family_ids["cauliflower"],
            "companion_family_id": family_ids["sugar snap pea"],
        },
        {"family_id": family_ids["tomato"], "companion_family_id": family_ids["basil"]},
        {
            "family_id": family_ids["tomato"],
            "companion_family_id": family_ids["parsley"],
        },
        {
            "family_id": family_ids["sweetcorn"],
            "companion_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["sweetcorn"],
            "companion_family_id": family_ids["squash"],
        },
        {
            "family_id": family_ids["cucumber"],
            "companion_family_id": family_ids["radish"],
        },
        {
            "family_id": family_ids["blueberry"],
            "companion_family_id": family_ids["cranberry"],
        },
        {
            "family_id": family_ids["borage"],
            "companion_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["borage"],
            "companion_family_id": family_ids["strawberry"],
        },
        {
            "family_id": family_ids["borage"],
            "companion_family_id": family_ids["squash"],
        },
        {
            "family_id": family_ids["marigolds"],
            "companion_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["marigolds"],
            "companion_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["thyme"],
            "companion_family_id": family_ids["carrot"],
        },
        {
            "family_id": family_ids["thyme"],
            "companion_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["sage"],
            "companion_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["sage"],
            "companion_family_id": family_ids["cauliflower"],
        },
        {
            "family_id": family_ids["sage"],
            "companion_family_id": family_ids["brussels sprout"],
        },
        {
            "family_id": family_ids["sage"],
            "companion_family_id": family_ids["carrot"],
        },
        {
            "family_id": family_ids["sage"],
            "companion_family_id": family_ids["strawberry"],
        },
        {
            "family_id": family_ids["basil"],
            "companion_family_id": family_ids["asparagus"],
        },
        {
            "family_id": family_ids["tomato"],
            "companion_family_id": family_ids["asparagus"],
        },
        {
            "family_id": family_ids["parsley"],
            "companion_family_id": family_ids["asparagus"],
        },
        {
            "family_id": family_ids["marigolds"],
            "companion_family_id": family_ids["asparagus"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "companion_family_id": family_ids["sweetcorn"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "companion_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "companion_family_id": family_ids["radish"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["rosemary"],
            "companion_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["rosemary"],
            "companion_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["rosemary"],
            "companion_family_id": family_ids["carrot"],
        },
        {
            "family_id": family_ids["rosemary"],
            "companion_family_id": family_ids["sage"],
        },
        {
            "family_id": family_ids["rosemary"],
            "companion_family_id": family_ids["thyme"],
        },
        {
            "family_id": family_ids["rosemary"],
            "companion_family_id": family_ids["lavender"],
        },
        {
            "family_id": family_ids["lavender"],
            "companion_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["lavender"],
            "companion_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["lavender"],
            "companion_family_id": family_ids["thyme"],
        },
        {
            "family_id": family_ids["lavender"],
            "companion_family_id": family_ids["sage"],
        },
        {
            "family_id": family_ids["lavender"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["lavender"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["potato"],
            "companion_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["potato"],
            "companion_family_id": family_ids["sugar snap pea"],
        },
        {
            "family_id": family_ids["potato"],
            "companion_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["potato"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["sweet pepper"],
            "companion_family_id": family_ids["basil"],
        },
        {
            "family_id": family_ids["sweet pepper"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["sweet pepper"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["sweet pepper"],
            "companion_family_id": family_ids["carrot"],
        },
        {
            "family_id": family_ids["sweet pepper"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["sweet pepper"],
            "companion_family_id": family_ids["lettuce"],
        },
        {
            "family_id": family_ids["sweet pepper"],
            "companion_family_id": family_ids["spinach"],
        },
        {
            "family_id": family_ids["gooseberry"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["gooseberry"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["gooseberry"],
            "companion_family_id": family_ids["sage"],
        },
        {
            "family_id": family_ids["blackcurrant"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["blackcurrant"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["blackcurrant"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["blackcurrant"],
            "companion_family_id": family_ids["sage"],
        },
        {
            "family_id": family_ids["redcurrant"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["redcurrant"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["redcurrant"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["redcurrant"],
            "companion_family_id": family_ids["sage"],
        },
        {
            "family_id": family_ids["jostaberry"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["jostaberry"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["jostaberry"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["jostaberry"],
            "companion_family_id": family_ids["sage"],
        },
        {
            "family_id": family_ids["parsnip"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["parsnip"],
            "companion_family_id": family_ids["garlic"],
        },
        {"family_id": family_ids["parsnip"], "companion_family_id": family_ids["leek"]},
        {
            "family_id": family_ids["parsnip"],
            "companion_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["parsnip"],
            "companion_family_id": family_ids["sugar snap pea"],
        },
        {
            "family_id": family_ids["parsnip"],
            "companion_family_id": family_ids["radish"],
        },
        {
            "family_id": family_ids["blackberry"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["blackberry"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["blackberry"],
            "companion_family_id": family_ids["shallot"],
        },
        {
            "family_id": family_ids["blackberry"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["blackberry"],
            "companion_family_id": family_ids["strawberry"],
        },
        {
            "family_id": family_ids["raspberry"],
            "companion_family_id": family_ids["garlic"],
        },
        {
            "family_id": family_ids["raspberry"],
            "companion_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["raspberry"],
            "companion_family_id": family_ids["shallot"],
        },
        {
            "family_id": family_ids["raspberry"],
            "companion_family_id": family_ids["marigolds"],
        },
        {
            "family_id": family_ids["raspberry"],
            "companion_family_id": family_ids["strawberry"],
        },
    ]
    if family_companions_seed_data:
        op.bulk_insert(family_companion_table, family_companions_seed_data)

    family_antagonists_seed_data = [
        {
            "family_id": family_ids["parsley"],
            "antagonist_family_id": family_ids["carrot"],
        },
        {
            "family_id": family_ids["parsley"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["celery"],
            "antagonist_family_id": family_ids["parsnip"],
        },
        {
            "family_id": family_ids["raspberry"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["raspberry"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["raspberry"],
            "antagonist_family_id": family_ids["blackberry"],
        },
        {
            "family_id": family_ids["blackberry"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["blackberry"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["parsnip"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["parsnip"],
            "antagonist_family_id": family_ids["carrot"],
        },
        {
            "family_id": family_ids["carrot"],
            "antagonist_family_id": family_ids["celery"],
        },
        {
            "family_id": family_ids["beetroot"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["beetroot"],
            "antagonist_family_id": family_ids["cauliflower"],
        },
        {
            "family_id": family_ids["jostaberry"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["jostaberry"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["potato"],
            "antagonist_family_id": family_ids["sweet pepper"],
        },
        {
            "family_id": family_ids["rosemary"],
            "antagonist_family_id": family_ids["cucumber"],
        },
        {
            "family_id": family_ids["rosemary"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["squash"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["squash"],
            "antagonist_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["squash"],
            "antagonist_family_id": family_ids["cauliflower"],
        },
        {
            "family_id": family_ids["squash"],
            "antagonist_family_id": family_ids["brussels sprout"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "antagonist_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "antagonist_family_id": family_ids["cauliflower"],
        },
        {
            "family_id": family_ids["pumpkin"],
            "antagonist_family_id": family_ids["carrot"],
        },
        {
            "family_id": family_ids["garlic"],
            "antagonist_family_id": family_ids["sugar snap pea"],
        },
        {
            "family_id": family_ids["garlic"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["onion"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["shallot"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["tomato"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["tomato"],
            "antagonist_family_id": family_ids["cauliflower"],
        },
        {
            "family_id": family_ids["tomato"],
            "antagonist_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["tomato"],
            "antagonist_family_id": family_ids["brussels sprout"],
        },
        {
            "family_id": family_ids["tomato"],
            "antagonist_family_id": family_ids["strawberry"],
        },
        {
            "family_id": family_ids["leek"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["leek"],
            "antagonist_family_id": family_ids["sugar snap pea"],
        },
        {
            "family_id": family_ids["cucumber"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["cauliflower"],
            "antagonist_family_id": family_ids["strawberry"],
        },
        {
            "family_id": family_ids["redcurrant"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["blackcurrant"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["gooseberry"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["blueberry"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["redcurrant"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["blackcurrant"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["gooseberry"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["blueberry"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["redcurrant"],
            "antagonist_family_id": family_ids["sweet pepper"],
        },
        {
            "family_id": family_ids["blackcurrant"],
            "antagonist_family_id": family_ids["sweet pepper"],
        },
        {
            "family_id": family_ids["gooseberry"],
            "antagonist_family_id": family_ids["sweet pepper"],
        },
        {
            "family_id": family_ids["blueberry"],
            "antagonist_family_id": family_ids["sweet pepper"],
        },
        {
            "family_id": family_ids["marigolds"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["marigolds"],
            "antagonist_family_id": family_ids["sugar snap pea"],
        },
        {
            "family_id": family_ids["lavender"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["lavender"],
            "antagonist_family_id": family_ids["sugar snap pea"],
        },
        {
            "family_id": family_ids["borage"],
            "antagonist_family_id": family_ids["onion"],
        },
        {
            "family_id": family_ids["sage"],
            "antagonist_family_id": family_ids["runner bean"],
        },
        {
            "family_id": family_ids["sage"],
            "antagonist_family_id": family_ids["sugar snap pea"],
        },
        {
            "family_id": family_ids["onion"],
            "antagonist_family_id": family_ids["asparagus"],
        },
        {
            "family_id": family_ids["garlic"],
            "antagonist_family_id": family_ids["asparagus"],
        },
        {
            "family_id": family_ids["shallot"],
            "antagonist_family_id": family_ids["asparagus"],
        },
        {
            "family_id": family_ids["potato"],
            "antagonist_family_id": family_ids["radish"],
        },
        {
            "family_id": family_ids["sweetcorn"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["sweetcorn"],
            "antagonist_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["sweetcorn"],
            "antagonist_family_id": family_ids["cauliflower"],
        },
        {
            "family_id": family_ids["sweetcorn"],
            "antagonist_family_id": family_ids["brussels sprout"],
        },
        {
            "family_id": family_ids["lettuce"],
            "antagonist_family_id": family_ids["parsley"],
        },
        {
            "family_id": family_ids["lettuce"],
            "antagonist_family_id": family_ids["celery"],
        },
        {
            "family_id": family_ids["lettuce"],
            "antagonist_family_id": family_ids["broccoli"],
        },
        {
            "family_id": family_ids["cranberry"],
            "antagonist_family_id": family_ids["tomato"],
        },
        {
            "family_id": family_ids["cranberry"],
            "antagonist_family_id": family_ids["potato"],
        },
        {
            "family_id": family_ids["cranberry"],
            "antagonist_family_id": family_ids["sweet pepper"],
        },
    ]
    if family_antagonists_seed_data:
        op.bulk_insert(family_antagonist_table, family_antagonists_seed_data)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("family_companion")
    op.drop_table("family_antagonist")
    op.drop_index(op.f("ix_family_name"), table_name="family")
    op.drop_index(op.f("ix_family_id"), table_name="family")
    op.drop_table("family")
    op.drop_index(op.f("ix_botanical_group_name"), table_name="botanical_group")
    op.drop_index(op.f("ix_botanical_group_id"), table_name="botanical_group")
    op.drop_table("botanical_group")
