"""Add thinking_duration_s column to messages.

Revision ID: 002
Revises: 001
Create Date: 2026-02-28
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("thinking_duration_s", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "thinking_duration_s")
