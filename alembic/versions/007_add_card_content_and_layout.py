"""Add content and layout columns to dashboard_cards.

Revision ID: 007
Revises: 006
Create Date: 2026-03-11
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("dashboard_cards", sa.Column("content", JSONB, nullable=True))
    op.add_column("dashboard_cards", sa.Column("layout", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("dashboard_cards", "layout")
    op.drop_column("dashboard_cards", "content")
