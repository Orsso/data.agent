"""Add dashboard_content column to projects.

Revision ID: 006
Revises: 005
Create Date: 2026-03-11
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("dashboard_content", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "dashboard_content")
