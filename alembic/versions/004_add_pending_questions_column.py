"""Add pending_questions column to chats.

Revision ID: 004
Revises: 003
Create Date: 2026-03-10
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chats", sa.Column("pending_questions", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("chats", "pending_questions")
