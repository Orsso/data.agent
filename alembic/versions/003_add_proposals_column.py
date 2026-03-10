"""Add proposals column to messages.

Revision ID: 003
Revises: 002
Create Date: 2026-03-10
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("proposals", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "proposals")
