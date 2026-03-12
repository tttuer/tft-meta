"""add champion splash_url

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("champions", sa.Column("splash_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("champions", "splash_url")
