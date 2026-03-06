"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE tier_enum AS ENUM ('S', 'A', 'B', 'C')")
    op.execute("CREATE TYPE augment_tier_enum AS ENUM ('Silver', 'Gold', 'Prismatic')")

    op.create_table(
        "comps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tier", sa.Enum("S", "A", "B", "C", name="tier_enum"), nullable=False),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("top4_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_placement", sa.Float(), nullable=False, server_default="4"),
        sa.Column("play_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("core_units", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("board_positions", postgresql.JSONB(), nullable=False, server_default="'[]'"),
        sa.Column("recommended_augments", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("entry_conditions", postgresql.JSONB(), nullable=False, server_default="'[]'"),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("patch_version", sa.String(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
    )

    op.create_table(
        "champions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("cost", sa.Integer(), nullable=False),
        sa.Column("traits", postgresql.JSONB(), nullable=False, server_default="'[]'"),
        sa.Column("best_items", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("item_reasoning", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("image_url", sa.String(), nullable=True),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("components", postgresql.JSONB(), nullable=False, server_default="'[]'"),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("is_component", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "augments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tier", sa.Enum("Silver", "Gold", "Prismatic", name="augment_tier_enum"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("comp_synergy", postgresql.JSONB(), nullable=False, server_default="'[]'"),
    )

    op.create_table(
        "match_raw",
        sa.Column("match_id", sa.String(), primary_key=True),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("participants", postgresql.JSONB(), nullable=False, server_default="'[]'"),
        sa.Column("patch_version", sa.String(), nullable=False),
        sa.Column("collected_at", sa.TIMESTAMP(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("match_raw")
    op.drop_table("augments")
    op.drop_table("items")
    op.drop_table("champions")
    op.drop_table("comps")
    op.execute("DROP TYPE IF EXISTS tier_enum")
    op.execute("DROP TYPE IF EXISTS augment_tier_enum")
