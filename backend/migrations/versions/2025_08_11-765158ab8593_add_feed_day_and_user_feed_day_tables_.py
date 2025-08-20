"""add feed, day and user feed day tables, seed feeds

Revision ID: 765158ab8593
Revises: fd5d387c3559
Create Date: 2025-08-11 19:09:45.911766

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "765158ab8593"
down_revision: Union[str, None] = "fd5d387c3559"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    day_table = op.create_table(
        "day",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=3), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("day_number", name="uq_day_number"),
        sa.UniqueConstraint("name", name="uq_day_name"),
    )
    op.create_index(op.f("ix_day_day_number"), "day", ["day_number"], unique=True)
    op.create_index(op.f("ix_day_id"), "day", ["id"], unique=False)
    feed_table = op.create_table(
        "feed",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_feed_name"),
    )
    op.create_index(op.f("ix_feed_id"), "feed", ["id"], unique=False)
    op.create_table(
        "user_feed_day",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("feed_id", sa.UUID(), nullable=False),
        sa.Column("day_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["day_id"], ["day.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feed_id"], ["feed.id"], ondelete="CASCADE"),
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
    op.drop_index("ix_botanical_group_name", table_name="botanical_group")
    op.drop_index("ix_disease_name", table_name="disease")
    op.drop_index("ix_family_name", table_name="family")
    op.drop_index("ix_intervention_name", table_name="intervention")
    op.drop_index("ix_symptom_name", table_name="symptom")
    # ### end Alembic commands ###

    # Seed data for days
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
        day_table,
        [
            {
                "id": day_ids[day["name"]],
                "day_number": day["day_number"],
                "name": day["name"],
            }
            for day in days
        ],
    )

    # Seed data for feeds
    feeds = [
        {"name": "tomato feed"},
        {"name": "blood, fish and bone"},
        {"name": "balanced feed"},
    ]
    feed_ids = {feed["name"]: uuid.uuid4() for feed in feeds}
    op.bulk_insert(
        feed_table,
        [{"id": feed_ids[feed["name"]], "name": feed["name"]} for feed in feeds],
    )

    # Create function and trigger to set default user_feed_day rows for each feed when a new user is created
    op.execute("""
    CREATE OR REPLACE FUNCTION set_default_feed_days_for_new_user()
    RETURNS TRIGGER AS $$
    BEGIN
        INSERT INTO user_feed_day (user_id, feed_id, day_id)
        SELECT
            NEW.user_id,
            f.id,
            (SELECT id FROM day ORDER BY day_number LIMIT 1) -- default to first day
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
    op.create_index("ix_symptom_name", "symptom", ["name"], unique=True)
    op.create_index("ix_intervention_name", "intervention", ["name"], unique=True)
    op.create_index("ix_family_name", "family", ["name"], unique=True)
    op.create_index("ix_disease_name", "disease", ["name"], unique=True)
    op.create_index("ix_botanical_group_name", "botanical_group", ["name"], unique=True)
    op.drop_index(op.f("ix_user_feed_day_user_id"), table_name="user_feed_day")
    op.drop_index(op.f("ix_user_feed_day_feed_id"), table_name="user_feed_day")
    op.drop_index(op.f("ix_user_feed_day_day_id"), table_name="user_feed_day")
    op.drop_table("user_feed_day")
    op.drop_index(op.f("ix_feed_id"), table_name="feed")
    op.drop_table("feed")
    op.drop_index(op.f("ix_day_id"), table_name="day")
    op.drop_index(op.f("ix_day_day_number"), table_name="day")
    op.drop_table("day")
    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS user_feed_day_defaults ON "user";')
    op.execute("DROP FUNCTION IF EXISTS set_default_feed_days_for_new_user();")
