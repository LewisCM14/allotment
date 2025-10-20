"""initial migration

Revision ID: 9505eadaea48
Revises:
Create Date: 2025-10-16 20:17:35.964496

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9505eadaea48"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "botanical_group",
        sa.Column("botanical_group_id", sa.UUID(), nullable=False),
        sa.Column("botanical_group_name", sa.String(length=50), nullable=False),
        sa.Column("rotate_years", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "botanical_group_name = LOWER(botanical_group_name)",
            name="ck_botanical_group_name_lower",
        ),
        sa.PrimaryKeyConstraint("botanical_group_id"),
        sa.UniqueConstraint("botanical_group_name"),
        sa.UniqueConstraint("botanical_group_name", name="uq_botanical_group_name"),
    )
    op.create_index(
        op.f("ix_botanical_group_botanical_group_id"),
        "botanical_group",
        ["botanical_group_id"],
        unique=False,
    )
    op.create_table(
        "day",
        sa.Column("day_id", sa.UUID(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("day_name", sa.String(length=3), nullable=False),
        sa.PrimaryKeyConstraint("day_id"),
        sa.UniqueConstraint("day_name", name="uq_day_name"),
        sa.UniqueConstraint("day_number", name="uq_day_number"),
    )
    op.create_index(op.f("ix_day_day_id"), "day", ["day_id"], unique=False)
    op.create_index(op.f("ix_day_day_number"), "day", ["day_number"], unique=True)
    op.create_table(
        "disease",
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.Column("disease_name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("disease_id"),
        sa.UniqueConstraint("disease_name"),
        sa.UniqueConstraint("disease_name", name="uq_disease_name"),
    )
    op.create_index(
        op.f("ix_disease_disease_id"), "disease", ["disease_id"], unique=False
    )
    op.create_table(
        "feed",
        sa.Column("feed_id", sa.UUID(), nullable=False),
        sa.Column("feed_name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("feed_id"),
        sa.UniqueConstraint("feed_name", name="uq_feed_name"),
    )
    op.create_index(op.f("ix_feed_feed_id"), "feed", ["feed_id"], unique=False)
    op.create_table(
        "frequency",
        sa.Column("frequency_id", sa.UUID(), nullable=False),
        sa.Column("frequency_name", sa.String(length=50), nullable=False),
        sa.Column("frequency_days_per_year", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("frequency_id"),
        sa.UniqueConstraint("frequency_name", name="uq_frequency_name"),
    )
    op.create_index(
        op.f("ix_frequency_frequency_id"), "frequency", ["frequency_id"], unique=False
    )
    op.create_table(
        "intervention",
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.Column("intervention_name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("intervention_id"),
        sa.UniqueConstraint("intervention_name"),
        sa.UniqueConstraint("intervention_name", name="uq_intervention_name"),
    )
    op.create_index(
        op.f("ix_intervention_intervention_id"),
        "intervention",
        ["intervention_id"],
        unique=False,
    )
    op.create_table(
        "lifecycle",
        sa.Column("lifecycle_id", sa.UUID(), nullable=False),
        sa.Column(
            "lifecycle_name",
            sa.Enum(
                "annual",
                "biennial",
                "perennial",
                "short-lived perennial",
                name="lifecycletype",
                native_enum=False,
                length=50,
            ),
            nullable=False,
        ),
        sa.Column("productivity_years", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("lifecycle_id"),
        sa.UniqueConstraint("lifecycle_name", name="uq_lifecycle_name"),
    )
    op.create_index(
        op.f("ix_lifecycle_lifecycle_id"), "lifecycle", ["lifecycle_id"], unique=False
    )
    op.create_index(
        op.f("ix_lifecycle_lifecycle_name"),
        "lifecycle",
        ["lifecycle_name"],
        unique=True,
    )
    op.create_table(
        "month",
        sa.Column("month_id", sa.UUID(), nullable=False),
        sa.Column("month_number", sa.Integer(), nullable=False),
        sa.Column("month_name", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("month_id"),
        sa.UniqueConstraint("month_name", name="uq_month_name"),
        sa.UniqueConstraint("month_number"),
        sa.UniqueConstraint("month_number", name="uq_month_number"),
    )
    op.create_index(op.f("ix_month_month_id"), "month", ["month_id"], unique=False)
    op.create_table(
        "pest",
        sa.Column("pest_id", sa.UUID(), nullable=False),
        sa.Column("pest_name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("pest_id"),
        sa.UniqueConstraint("pest_name", name="uq_pest_name"),
    )
    op.create_index(op.f("ix_pest_pest_id"), "pest", ["pest_id"], unique=False)
    op.create_index(op.f("ix_pest_pest_name"), "pest", ["pest_name"], unique=True)
    op.create_table(
        "planting_conditions",
        sa.Column("planting_condition_id", sa.UUID(), nullable=False),
        sa.Column("planting_condition", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("planting_condition_id"),
        sa.UniqueConstraint("planting_condition", name="uq_planting_conditions_name"),
    )
    op.create_index(
        op.f("ix_planting_conditions_planting_condition_id"),
        "planting_conditions",
        ["planting_condition_id"],
        unique=False,
    )
    op.create_table(
        "symptom",
        sa.Column("symptom_id", sa.UUID(), nullable=False),
        sa.Column("symptom_name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("symptom_id"),
        sa.UniqueConstraint("symptom_name"),
        sa.UniqueConstraint("symptom_name", name="uq_symptom_name"),
    )
    op.create_index(
        op.f("ix_symptom_symptom_id"), "symptom", ["symptom_id"], unique=False
    )
    op.create_table(
        "user",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("user_password_hash", sa.Text(), nullable=False),
        sa.Column("user_first_name", sa.String(length=50), nullable=False),
        sa.Column("user_country_code", sa.String(length=2), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "registered_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_active_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
        "week",
        sa.Column("week_id", sa.UUID(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("start_month_id", sa.UUID(), nullable=False),
        sa.Column("week_start_date", sa.String(length=5), nullable=False),
        sa.Column("week_end_date", sa.String(length=5), nullable=False),
        sa.CheckConstraint(
            "SUBSTR(week_end_date, 3, 1) = '/'", name="check_week_end_date_slash"
        ),
        sa.CheckConstraint(
            "SUBSTR(week_start_date, 3, 1) = '/'", name="check_week_start_date_slash"
        ),
        sa.CheckConstraint(
            "LENGTH(week_end_date) = 5", name="check_week_end_date_length"
        ),
        sa.CheckConstraint(
            "LENGTH(week_start_date) = 5", name="check_week_start_date_length"
        ),
        sa.PrimaryKeyConstraint("week_id"),
        sa.UniqueConstraint("week_number"),
        sa.UniqueConstraint("week_number", name="uq_week_number"),
    )
    op.create_index(op.f("ix_week_week_id"), "week", ["week_id"], unique=False)
    op.create_table(
        "disease_prevention",
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["disease_id"], ["disease.disease_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.intervention_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("disease_id", "intervention_id"),
    )
    op.create_table(
        "disease_symptom",
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.Column("symptom_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["disease_id"], ["disease.disease_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["symptom_id"], ["symptom.symptom_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("disease_id", "symptom_id"),
    )
    op.create_table(
        "disease_treatment",
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["disease_id"], ["disease.disease_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.intervention_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("disease_id", "intervention_id"),
    )
    op.create_table(
        "family",
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("family_name", sa.String(length=50), nullable=False),
        sa.Column("botanical_group_id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "family_name = LOWER(family_name)", name="ck_family_name_lower"
        ),
        sa.ForeignKeyConstraint(
            ["botanical_group_id"],
            ["botanical_group.botanical_group_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("family_id"),
        sa.UniqueConstraint("family_name"),
        sa.UniqueConstraint("family_name", name="uq_family_name"),
    )
    op.create_index(op.f("ix_family_family_id"), "family", ["family_id"], unique=False)
    op.create_table(
        "frequency_default_day",
        sa.Column("frequency_id", sa.UUID(), nullable=False),
        sa.Column("day_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["day_id"], ["day.day_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["frequency_id"], ["frequency.frequency_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("frequency_id", "day_id"),
        sa.UniqueConstraint("frequency_id", "day_id", name="uq_frequency_day_pair"),
    )
    op.create_index(
        op.f("ix_frequency_default_day_day_id"),
        "frequency_default_day",
        ["day_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_frequency_default_day_frequency_id"),
        "frequency_default_day",
        ["frequency_id"],
        unique=False,
    )
    op.create_table(
        "pest_prevention",
        sa.Column("pest_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.intervention_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["pest_id"], ["pest.pest_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pest_id", "intervention_id"),
    )
    op.create_table(
        "pest_treatment",
        sa.Column("pest_id", sa.UUID(), nullable=False),
        sa.Column("intervention_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["intervention_id"], ["intervention.intervention_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["pest_id"], ["pest.pest_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pest_id", "intervention_id"),
    )
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
    op.create_table(
        "user_feed_day",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("feed_id", sa.UUID(), nullable=False),
        sa.Column("day_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["day_id"], ["day.day_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feed_id"], ["feed.feed_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "feed_id"),
    )
    op.create_index(
        op.f("ix_user_feed_day_day_id"), "user_feed_day", ["day_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_feed_day_feed_id"), "user_feed_day", ["feed_id"], unique=False
    )
    op.create_index(
        op.f("ix_user_feed_day_user_id"), "user_feed_day", ["user_id"], unique=False
    )
    op.create_table(
        "family_antagonist",
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("antagonist_family_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["antagonist_family_id"], ["family.family_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.family_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("family_id", "antagonist_family_id"),
    )
    op.create_table(
        "family_companion",
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("companion_family_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["companion_family_id"], ["family.family_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.family_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("family_id", "companion_family_id"),
    )
    op.create_table(
        "family_disease",
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("disease_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["disease_id"], ["disease.disease_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.family_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("family_id", "disease_id"),
    )
    op.create_table(
        "family_pest",
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("pest_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.family_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["pest_id"], ["pest.pest_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("family_id", "pest_id"),
    )
    op.create_table(
        "variety",
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("variety_id", sa.UUID(), nullable=False),
        sa.Column("variety_name", sa.String(length=100), nullable=False),
        sa.Column("family_id", sa.UUID(), nullable=False),
        sa.Column("lifecycle_id", sa.UUID(), nullable=False),
        sa.Column("sow_week_start_id", sa.UUID(), nullable=False),
        sa.Column("sow_week_end_id", sa.UUID(), nullable=False),
        sa.Column("transplant_week_start_id", sa.UUID(), nullable=True),
        sa.Column("transplant_week_end_id", sa.UUID(), nullable=True),
        sa.Column("planting_conditions_id", sa.UUID(), nullable=False),
        sa.Column("soil_ph", sa.Float(), nullable=False),
        sa.Column("row_width_cm", sa.Integer(), nullable=True),
        sa.Column("plant_depth_cm", sa.Integer(), nullable=False),
        sa.Column("plant_space_cm", sa.Integer(), nullable=False),
        sa.Column("feed_id", sa.UUID(), nullable=True),
        sa.Column("feed_week_start_id", sa.UUID(), nullable=True),
        sa.Column("feed_frequency_id", sa.UUID(), nullable=True),
        sa.Column("water_frequency_id", sa.UUID(), nullable=False),
        sa.Column("high_temp_degrees", sa.Integer(), nullable=False),
        sa.Column("high_temp_water_frequency_id", sa.UUID(), nullable=False),
        sa.Column("harvest_week_start_id", sa.UUID(), nullable=False),
        sa.Column("harvest_week_end_id", sa.UUID(), nullable=False),
        sa.Column("prune_week_start_id", sa.UUID(), nullable=True),
        sa.Column("prune_week_end_id", sa.UUID(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(feed_id IS NULL AND feed_week_start_id IS NULL AND feed_frequency_id IS NULL) OR (feed_id IS NOT NULL AND feed_week_start_id IS NOT NULL AND feed_frequency_id IS NOT NULL)",
            name="check_feed_details_together",
        ),
        sa.CheckConstraint(
            "(high_temp_degrees IS NULL AND high_temp_water_frequency_id IS NULL) OR (high_temp_degrees IS NOT NULL AND high_temp_water_frequency_id IS NOT NULL)",
            name="check_high_temp_pairing",
        ),
        sa.CheckConstraint(
            "(prune_week_start_id IS NULL AND prune_week_end_id IS NULL) OR (prune_week_start_id IS NOT NULL AND prune_week_end_id IS NOT NULL)",
            name="check_prune_weeks_together",
        ),
        sa.CheckConstraint(
            "(transplant_week_start_id IS NULL AND transplant_week_end_id IS NULL) OR (transplant_week_start_id IS NOT NULL AND transplant_week_end_id IS NOT NULL)",
            name="check_transplant_weeks_together",
        ),
        sa.CheckConstraint(
            "notes IS NULL OR (LENGTH(notes) >= 5 AND LENGTH(notes) <= 500)",
            name="check_notes_length",
        ),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["family.family_id"],
        ),
        sa.ForeignKeyConstraint(
            ["feed_frequency_id"],
            ["frequency.frequency_id"],
        ),
        sa.ForeignKeyConstraint(
            ["feed_id"],
            ["feed.feed_id"],
        ),
        sa.ForeignKeyConstraint(
            ["feed_week_start_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["harvest_week_end_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["harvest_week_start_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["high_temp_water_frequency_id"],
            ["frequency.frequency_id"],
        ),
        sa.ForeignKeyConstraint(
            ["lifecycle_id"],
            ["lifecycle.lifecycle_id"],
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"], ["user.user_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["planting_conditions_id"],
            ["planting_conditions.planting_condition_id"],
        ),
        sa.ForeignKeyConstraint(
            ["prune_week_end_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["prune_week_start_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sow_week_end_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["sow_week_start_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["transplant_week_end_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["transplant_week_start_id"],
            ["week.week_id"],
        ),
        sa.ForeignKeyConstraint(
            ["water_frequency_id"],
            ["frequency.frequency_id"],
        ),
        sa.PrimaryKeyConstraint("variety_id"),
        sa.UniqueConstraint(
            "owner_user_id", "variety_name", name="uq_user_variety_name"
        ),
    )
    op.create_index(
        op.f("ix_variety_family_id"), "variety", ["family_id"], unique=False
    )
    op.create_index(
        op.f("ix_variety_feed_frequency_id"),
        "variety",
        ["feed_frequency_id"],
        unique=False,
    )
    op.create_index(op.f("ix_variety_feed_id"), "variety", ["feed_id"], unique=False)
    op.create_index(
        op.f("ix_variety_feed_week_start_id"),
        "variety",
        ["feed_week_start_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_harvest_week_end_id"),
        "variety",
        ["harvest_week_end_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_harvest_week_start_id"),
        "variety",
        ["harvest_week_start_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_high_temp_water_frequency_id"),
        "variety",
        ["high_temp_water_frequency_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_lifecycle_id"), "variety", ["lifecycle_id"], unique=False
    )
    op.create_index(
        op.f("ix_variety_owner_user_id"), "variety", ["owner_user_id"], unique=False
    )
    op.create_index(
        op.f("ix_variety_planting_conditions_id"),
        "variety",
        ["planting_conditions_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_prune_week_end_id"),
        "variety",
        ["prune_week_end_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_prune_week_start_id"),
        "variety",
        ["prune_week_start_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_sow_week_end_id"), "variety", ["sow_week_end_id"], unique=False
    )
    op.create_index(
        op.f("ix_variety_sow_week_start_id"),
        "variety",
        ["sow_week_start_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_transplant_week_end_id"),
        "variety",
        ["transplant_week_end_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_transplant_week_start_id"),
        "variety",
        ["transplant_week_start_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_variety_id"), "variety", ["variety_id"], unique=False
    )
    op.create_index(
        op.f("ix_variety_water_frequency_id"),
        "variety",
        ["water_frequency_id"],
        unique=False,
    )
    op.create_table(
        "user_active_variety",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("variety_id", sa.UUID(), nullable=False),
        sa.Column(
            "activated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["variety_id"], ["variety.variety_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "variety_id"),
    )
    op.create_index(
        op.f("ix_user_active_variety_user_id"),
        "user_active_variety",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_active_variety_variety_id"),
        "user_active_variety",
        ["variety_id"],
        unique=False,
    )
    op.create_table(
        "variety_water_day",
        sa.Column("variety_id", sa.UUID(), nullable=False),
        sa.Column("day_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["day_id"], ["day.day_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["variety_id"], ["variety.variety_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("variety_id", "day_id"),
    )
    op.create_index(
        op.f("ix_variety_water_day_day_id"),
        "variety_water_day",
        ["day_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_variety_water_day_variety_id"),
        "variety_water_day",
        ["variety_id"],
        unique=False,
    )
    # Seed data
    # Botanical groups
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
        sa.Table(
            "botanical_group",
            sa.MetaData(),
            sa.Column("botanical_group_id", sa.UUID()),
            sa.Column("botanical_group_name", sa.String()),
            sa.Column("rotate_years", sa.Integer()),
        ),
        [
            {
                "botanical_group_id": botanical_group_ids[bg["name"]],
                "botanical_group_name": bg["name"],
                "rotate_years": bg["recommended_rotation_years"],
            }
            for bg in botanical_groups
        ],
    )

    # Families
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
        sa.Table(
            "family",
            sa.MetaData(),
            sa.Column("family_id", sa.UUID()),
            sa.Column("family_name", sa.String()),
            sa.Column("botanical_group_id", sa.UUID()),
        ),
        [
            {
                "family_id": family_ids[f["name"]],
                "family_name": f["name"],
                "botanical_group_id": botanical_group_ids[f["botanical_group"]],
            }
            for f in families
        ],
    )

    # Family companions
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
        op.bulk_insert(
            sa.Table(
                "family_companion",
                sa.MetaData(),
                sa.Column("family_id", sa.UUID()),
                sa.Column("companion_family_id", sa.UUID()),
            ),
            family_companions_seed_data,
        )

    # Family antagonists
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
        op.bulk_insert(
            sa.Table(
                "family_antagonist",
                sa.MetaData(),
                sa.Column("family_id", sa.UUID()),
                sa.Column("antagonist_family_id", sa.UUID()),
            ),
            family_antagonists_seed_data,
        )

    # Diseases
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
        sa.Table(
            "disease",
            sa.MetaData(),
            sa.Column("disease_id", sa.UUID()),
            sa.Column("disease_name", sa.String()),
        ),
        [
            {
                "disease_id": disease_ids[disease["name"]],
                "disease_name": disease["name"],
            }
            for disease in diseases
        ],
    )

    # Pests
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
        sa.Table(
            "pest",
            sa.MetaData(),
            sa.Column("pest_id", sa.UUID()),
            sa.Column("pest_name", sa.String()),
        ),
        [
            {"pest_id": pest_ids[pest["name"]], "pest_name": pest["name"]}
            for pest in pests
        ],
    )

    # Symptoms
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
        sa.Table(
            "symptom",
            sa.MetaData(),
            sa.Column("symptom_id", sa.UUID()),
            sa.Column("symptom_name", sa.String()),
        ),
        [
            {
                "symptom_id": symptom_ids[symptom["name"]],
                "symptom_name": symptom["name"],
            }
            for symptom in symptoms
        ],
    )

    # Interventions
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
        sa.Table(
            "intervention",
            sa.MetaData(),
            sa.Column("intervention_id", sa.UUID()),
            sa.Column("intervention_name", sa.String()),
        ),
        [
            {
                "intervention_id": intervention_ids[intervention["name"]],
                "intervention_name": intervention["name"],
            }
            for intervention in interventions
        ],
    )

    # Disease prevention
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
        op.bulk_insert(
            sa.Table(
                "disease_prevention",
                sa.MetaData(),
                sa.Column("disease_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            disease_prevention_data,
        )

    # Disease treatment
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
        op.bulk_insert(
            sa.Table(
                "disease_treatment",
                sa.MetaData(),
                sa.Column("disease_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            disease_treatment_data,
        )

    # Disease symptom
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
        op.bulk_insert(
            sa.Table(
                "disease_symptom",
                sa.MetaData(),
                sa.Column("disease_id", sa.UUID()),
                sa.Column("symptom_id", sa.UUID()),
            ),
            disease_symptom_data,
        )

    # Pest prevention
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
        op.bulk_insert(
            sa.Table(
                "pest_prevention",
                sa.MetaData(),
                sa.Column("pest_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            pest_prevention_data,
        )

    # Pest treatment
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
        op.bulk_insert(
            sa.Table(
                "pest_treatment",
                sa.MetaData(),
                sa.Column("pest_id", sa.UUID()),
                sa.Column("intervention_id", sa.UUID()),
            ),
            pest_treatment_data,
        )

    # Family disease and pest data (dynamically generated)
    connection = op.get_bind()
    family_table = sa.Table(
        "family",
        sa.MetaData(),
        sa.Column("family_id", sa.UUID()),
        sa.Column("family_name", sa.String()),
    )
    family_rows = connection.execute(
        sa.select(family_table.c.family_id, family_table.c.family_name)
    ).fetchall()
    family_name_to_id = {name: id for id, name in family_rows}

    family_disease_seed_data = []
    disease_links = {
        "blight": ["tomato", "potato", "sweet pepper"],
        "downy mildew": [
            "lettuce",
            "onion",
            "shallot",
            "celery",
            "cucumber",
            "parsley",
            "leek",
            "garlic",
        ],
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
        "botrytis": [
            "strawberry",
            "raspberry",
            "blackberry",
            "blueberry",
            "leek",
            "garlic",
        ],
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
    op.bulk_insert(
        sa.Table(
            "family_disease",
            sa.MetaData(),
            sa.Column("family_id", sa.UUID()),
            sa.Column("disease_id", sa.UUID()),
        ),
        family_disease_seed_data,
    )

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
    op.bulk_insert(
        sa.Table(
            "family_pest",
            sa.MetaData(),
            sa.Column("family_id", sa.UUID()),
            sa.Column("pest_id", sa.UUID()),
        ),
        family_pest_seed_data,
    )

    # Days
    days = [
        {"day_number": 1, "name": "mon"},
        {"day_number": 2, "name": "tue"},
        {"day_number": 3, "name": "wen"},
        {"day_number": 4, "name": "thu"},
        {"day_number": 5, "name": "fri"},
        {"day_number": 6, "name": "sat"},
        {"day_number": 7, "name": "sun"},
    ]
    day_ids = {day["name"]: uuid.uuid4() for day in days}
    op.bulk_insert(
        sa.Table(
            "day",
            sa.MetaData(),
            sa.Column("day_id", sa.UUID()),
            sa.Column("day_number", sa.Integer()),
            sa.Column("day_name", sa.String()),
        ),
        [
            {
                "day_id": day_ids[day["name"]],
                "day_number": day["day_number"],
                "day_name": day["name"],
            }
            for day in days
        ],
    )

    # Feeds
    feeds = [
        {"name": "tomato feed"},
        {"name": "blood, fish and bone"},
        {"name": "balanced feed"},
        {"name": "ericaceous fertilizer"},
    ]
    feed_ids = {feed["name"]: uuid.uuid4() for feed in feeds}
    op.bulk_insert(
        sa.Table(
            "feed",
            sa.MetaData(),
            sa.Column("feed_id", sa.UUID()),
            sa.Column("feed_name", sa.String()),
        ),
        [
            {"feed_id": feed_ids[feed["name"]], "feed_name": feed["name"]}
            for feed in feeds
        ],
    )

    # Months
    months = [
        {"number": 1, "name": "January"},
        {"number": 2, "name": "February"},
        {"number": 3, "name": "March"},
        {"number": 4, "name": "April"},
        {"number": 5, "name": "May"},
        {"number": 6, "name": "June"},
        {"number": 7, "name": "July"},
        {"number": 8, "name": "August"},
        {"number": 9, "name": "September"},
        {"number": 10, "name": "October"},
        {"number": 11, "name": "November"},
        {"number": 12, "name": "December"},
    ]
    month_ids = {month["name"]: uuid.uuid4() for month in months}
    op.bulk_insert(
        sa.Table(
            "month",
            sa.MetaData(),
            sa.Column("month_id", sa.UUID()),
            sa.Column("month_number", sa.Integer()),
            sa.Column("month_name", sa.String()),
        ),
        [
            {
                "month_id": month_ids[month["name"]],
                "month_number": month["number"],
                "month_name": month["name"],
            }
            for month in months
        ],
    )

    # Weeks (52 weeks of the year with proper 7-day ranges totaling 365 days)
    week_dates = [
        (1, 1, "01/01", "01/07"),
        (2, 1, "01/08", "01/14"),
        (3, 1, "01/15", "01/21"),
        (4, 1, "01/22", "01/28"),
        (5, 1, "01/29", "02/04"),
        (6, 2, "02/05", "02/11"),
        (7, 2, "02/12", "02/18"),
        (8, 2, "02/19", "02/25"),
        (9, 2, "02/26", "03/04"),
        (10, 3, "03/05", "03/11"),
        (11, 3, "03/12", "03/18"),
        (12, 3, "03/19", "03/25"),
        (13, 3, "03/26", "04/01"),
        (14, 4, "04/02", "04/08"),
        (15, 4, "04/09", "04/15"),
        (16, 4, "04/16", "04/22"),
        (17, 4, "04/23", "04/29"),
        (18, 4, "04/30", "05/06"),
        (19, 5, "05/07", "05/13"),
        (20, 5, "05/14", "05/20"),
        (21, 5, "05/21", "05/27"),
        (22, 5, "05/28", "06/03"),
        (23, 6, "06/04", "06/10"),
        (24, 6, "06/11", "06/17"),
        (25, 6, "06/18", "06/24"),
        (26, 6, "06/25", "07/01"),
        (27, 7, "07/02", "07/08"),
        (28, 7, "07/09", "07/15"),
        (29, 7, "07/16", "07/22"),
        (30, 7, "07/23", "07/29"),
        (31, 7, "07/30", "08/05"),
        (32, 8, "08/06", "08/12"),
        (33, 8, "08/13", "08/19"),
        (34, 8, "08/20", "08/26"),
        (35, 8, "08/27", "09/02"),
        (36, 9, "09/03", "09/09"),
        (37, 9, "09/10", "09/16"),
        (38, 9, "09/17", "09/23"),
        (39, 9, "09/24", "09/30"),
        (40, 9, "10/01", "10/07"),
        (41, 10, "10/08", "10/14"),
        (42, 10, "10/15", "10/21"),
        (43, 10, "10/22", "10/28"),
        (44, 10, "10/29", "11/04"),
        (45, 11, "11/05", "11/11"),
        (46, 11, "11/12", "11/18"),
        (47, 11, "11/19", "11/25"),
        (48, 11, "11/26", "12/02"),
        (49, 12, "12/03", "12/09"),
        (50, 12, "12/10", "12/16"),
        (51, 12, "12/17", "12/23"),
        (52, 12, "12/24", "12/31"),
    ]
    # Create mapping from month number to month UUID
    month_number_to_uuid = {
        1: month_ids["January"],
        2: month_ids["February"],
        3: month_ids["March"],
        4: month_ids["April"],
        5: month_ids["May"],
        6: month_ids["June"],
        7: month_ids["July"],
        8: month_ids["August"],
        9: month_ids["September"],
        10: month_ids["October"],
        11: month_ids["November"],
        12: month_ids["December"],
    }

    week_ids = {week_num: uuid.uuid4() for week_num in range(1, 53)}
    op.bulk_insert(
        sa.Table(
            "week",
            sa.MetaData(),
            sa.Column("week_id", sa.UUID()),
            sa.Column("week_number", sa.Integer()),
            sa.Column("start_month_id", sa.UUID()),
            sa.Column("week_start_date", sa.String()),
            sa.Column("week_end_date", sa.String()),
        ),
        [
            {
                "week_id": week_ids[week_num],
                "week_number": week_num,
                "start_month_id": month_number_to_uuid[month_num],
                "week_start_date": start_date,
                "week_end_date": end_date,
            }
            for week_num, month_num, start_date, end_date in week_dates
        ],
    )

    lifecycles = [
        {"name": "annual", "productivity_years": 1},
        {"name": "biennial", "productivity_years": 2},
        {"name": "perennial", "productivity_years": 10},
        {"name": "short-lived perennial", "productivity_years": 4},
    ]
    lifecycle_ids = {lifecycle["name"]: uuid.uuid4() for lifecycle in lifecycles}
    op.bulk_insert(
        sa.Table(
            "lifecycle",
            sa.MetaData(),
            sa.Column("lifecycle_id", sa.UUID()),
            sa.Column("lifecycle_name", sa.String()),
            sa.Column("productivity_years", sa.Integer()),
        ),
        [
            {
                "lifecycle_id": lifecycle_ids[lifecycle["name"]],
                "lifecycle_name": lifecycle["name"],
                "productivity_years": lifecycle["productivity_years"],
            }
            for lifecycle in lifecycles
        ],
    )

    # Planting conditions
    planting_conditions = [
        {"condition": "full sun"},
        {"condition": "partial sun"},
        {"condition": "partial shade"},
        {"condition": "full shade"},
        {"condition": "greenhouse"},
    ]
    planting_condition_ids = {
        pc["condition"]: uuid.uuid4() for pc in planting_conditions
    }
    op.bulk_insert(
        sa.Table(
            "planting_conditions",
            sa.MetaData(),
            sa.Column("planting_condition_id", sa.UUID()),
            sa.Column("planting_condition", sa.String()),
        ),
        [
            {
                "planting_condition_id": planting_condition_ids[pc["condition"]],
                "planting_condition": pc["condition"],
            }
            for pc in planting_conditions
        ],
    )

    # Frequencies
    frequencies = [
        {"name": "daily", "days_per_year": 365},
        {"name": "alternate days", "days_per_year": 208},
        {"name": "thrice weekly", "days_per_year": 156},
        {"name": "weekly", "days_per_year": 52},
        {"name": "fortnightly", "days_per_year": 26},
        {"name": "yearly", "days_per_year": 1},
    ]
    frequency_ids = {freq["name"]: uuid.uuid4() for freq in frequencies}
    op.bulk_insert(
        sa.Table(
            "frequency",
            sa.MetaData(),
            sa.Column("frequency_id", sa.UUID()),
            sa.Column("frequency_name", sa.String()),
            sa.Column("frequency_days_per_year", sa.Integer()),
        ),
        [
            {
                "frequency_id": frequency_ids[freq["name"]],
                "frequency_name": freq["name"],
                "frequency_days_per_year": freq["days_per_year"],
            }
            for freq in frequencies
        ],
    )

    # Frequency default days
    frequency_default_days = [
        {"frequency_id": frequency_ids["daily"], "day_id": day_ids["mon"]},
        {"frequency_id": frequency_ids["daily"], "day_id": day_ids["tue"]},
        {"frequency_id": frequency_ids["daily"], "day_id": day_ids["wen"]},
        {"frequency_id": frequency_ids["daily"], "day_id": day_ids["thu"]},
        {"frequency_id": frequency_ids["daily"], "day_id": day_ids["fri"]},
        {"frequency_id": frequency_ids["daily"], "day_id": day_ids["sat"]},
        {"frequency_id": frequency_ids["daily"], "day_id": day_ids["sun"]},
        {"frequency_id": frequency_ids["alternate days"], "day_id": day_ids["mon"]},
        {"frequency_id": frequency_ids["alternate days"], "day_id": day_ids["wen"]},
        {"frequency_id": frequency_ids["alternate days"], "day_id": day_ids["fri"]},
        {"frequency_id": frequency_ids["alternate days"], "day_id": day_ids["sun"]},
        {"frequency_id": frequency_ids["thrice weekly"], "day_id": day_ids["tue"]},
        {"frequency_id": frequency_ids["thrice weekly"], "day_id": day_ids["thu"]},
        {"frequency_id": frequency_ids["thrice weekly"], "day_id": day_ids["sat"]},
        {"frequency_id": frequency_ids["weekly"], "day_id": day_ids["sun"]},
        {"frequency_id": frequency_ids["fortnightly"], "day_id": day_ids["sun"]},
        {"frequency_id": frequency_ids["yearly"], "day_id": day_ids["sun"]},
    ]

    if frequency_default_days:
        op.bulk_insert(
            sa.Table(
                "frequency_default_day",
                sa.MetaData(),
                sa.Column("frequency_id", sa.UUID()),
                sa.Column("day_id", sa.UUID()),
            ),
            frequency_default_days,
        )

    # Create function and trigger to set default user_feed_day rows for each feed when a new user is created
    op.execute("""
    CREATE OR REPLACE FUNCTION set_default_feed_days_for_new_user()
    RETURNS TRIGGER AS $$
    BEGIN
        INSERT INTO user_feed_day (user_id, feed_id, day_id)
        SELECT
            NEW.user_id,
            f.feed_id,
            (SELECT day_id FROM day ORDER BY day_number LIMIT 1) -- default to first day
        FROM feed f;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER user_feed_day_defaults
    AFTER INSERT ON "user"
    FOR EACH ROW
    EXECUTE FUNCTION set_default_feed_days_for_new_user();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS user_feed_day_defaults ON "user";')
    op.execute("DROP FUNCTION IF EXISTS set_default_feed_days_for_new_user();")
    op.drop_index(
        op.f("ix_variety_water_day_variety_id"), table_name="variety_water_day"
    )
    op.drop_index(op.f("ix_variety_water_day_day_id"), table_name="variety_water_day")
    op.drop_table("variety_water_day")
    op.drop_index(
        op.f("ix_user_active_variety_variety_id"), table_name="user_active_variety"
    )
    op.drop_index(
        op.f("ix_user_active_variety_user_id"), table_name="user_active_variety"
    )
    op.drop_table("user_active_variety")
    op.drop_index(op.f("ix_variety_water_frequency_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_variety_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_transplant_week_start_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_transplant_week_end_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_sow_week_start_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_sow_week_end_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_prune_week_start_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_prune_week_end_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_planting_conditions_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_owner_user_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_lifecycle_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_high_temp_water_frequency_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_harvest_week_start_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_harvest_week_end_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_feed_week_start_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_feed_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_feed_frequency_id"), table_name="variety")
    op.drop_index(op.f("ix_variety_family_id"), table_name="variety")
    op.drop_table("variety")
    op.drop_table("family_pest")
    op.drop_table("family_disease")
    op.drop_table("family_companion")
    op.drop_table("family_antagonist")
    op.drop_index(op.f("ix_user_feed_day_user_id"), table_name="user_feed_day")
    op.drop_index(op.f("ix_user_feed_day_feed_id"), table_name="user_feed_day")
    op.drop_index(op.f("ix_user_feed_day_day_id"), table_name="user_feed_day")
    op.drop_table("user_feed_day")
    op.drop_index(
        op.f("ix_user_allotment_user_allotment_id"), table_name="user_allotment"
    )
    op.drop_table("user_allotment")
    op.drop_table("pest_treatment")
    op.drop_table("pest_prevention")
    op.drop_index(
        op.f("ix_frequency_default_day_frequency_id"),
        table_name="frequency_default_day",
    )
    op.drop_index(
        op.f("ix_frequency_default_day_day_id"), table_name="frequency_default_day"
    )
    op.drop_table("frequency_default_day")
    op.drop_index(op.f("ix_family_family_id"), table_name="family")
    op.drop_table("family")
    op.drop_table("disease_treatment")
    op.drop_table("disease_symptom")
    op.drop_table("disease_prevention")
    op.drop_index(op.f("ix_week_week_id"), table_name="week")
    op.drop_table("week")
    op.drop_index(op.f("ix_user_user_id"), table_name="user")
    op.drop_index(op.f("ix_user_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_symptom_symptom_id"), table_name="symptom")
    op.drop_table("symptom")
    op.drop_index(
        op.f("ix_planting_conditions_planting_condition_id"),
        table_name="planting_conditions",
    )
    op.drop_table("planting_conditions")
    op.drop_index(op.f("ix_pest_pest_name"), table_name="pest")
    op.drop_index(op.f("ix_pest_pest_id"), table_name="pest")
    op.drop_table("pest")
    op.drop_index(op.f("ix_month_month_id"), table_name="month")
    op.drop_table("month")
    op.drop_index(op.f("ix_lifecycle_lifecycle_name"), table_name="lifecycle")
    op.drop_index(op.f("ix_lifecycle_lifecycle_id"), table_name="lifecycle")
    op.drop_table("lifecycle")
    op.drop_index(op.f("ix_intervention_intervention_id"), table_name="intervention")
    op.drop_table("intervention")
    op.drop_index(op.f("ix_frequency_frequency_id"), table_name="frequency")
    op.drop_table("frequency")
    op.drop_index(op.f("ix_feed_feed_id"), table_name="feed")
    op.drop_table("feed")
    op.drop_index(op.f("ix_disease_disease_id"), table_name="disease")
    op.drop_table("disease")
    op.drop_index(op.f("ix_day_day_number"), table_name="day")
    op.drop_index(op.f("ix_day_day_id"), table_name="day")
    op.drop_table("day")
    op.drop_index(
        op.f("ix_botanical_group_botanical_group_id"), table_name="botanical_group"
    )
    op.drop_table("botanical_group")
