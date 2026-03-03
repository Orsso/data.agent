"""Initial schema — projects, sources, chats, messages, dashboard_cards.

Revision ID: 001
Revises: None
Create Date: 2026-02-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="created"),
        sa.Column("model", sa.String(100), nullable=False, server_default="gemini-3-flash-preview"),
        sa.Column("suggested_questions", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("origin", sa.String(20), nullable=False, server_default="upload"),
        sa.Column("row_count", sa.Integer, nullable=False),
        sa.Column("columns", JSONB, nullable=False),
        sa.Column("profile", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "name", name="uq_source_project_name"),
    )
    op.create_index("idx_sources_project", "sources", ["project_id"])

    op.create_table(
        "chats",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_chats_project", "chats", ["project_id"])

    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_id", UUID(as_uuid=True), sa.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False, server_default=""),
        sa.Column("code", sa.Text, nullable=True),
        sa.Column("tool_steps", JSONB, nullable=True),
        sa.Column("todos", JSONB, nullable=True),
        sa.Column("thinking", sa.Text, nullable=True),
        sa.Column("figs", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_messages_chat", "messages", ["chat_id"])
    op.create_index("idx_messages_chat_created", "messages", ["chat_id", "created_at"])

    op.create_table(
        "dashboard_cards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("code", sa.Text, nullable=True),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("fig", JSONB, nullable=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("idx_dashboard_cards_project", "dashboard_cards", ["project_id"])


def downgrade() -> None:
    op.drop_table("dashboard_cards")
    op.drop_table("messages")
    op.drop_table("chats")
    op.drop_table("sources")
    op.drop_table("projects")
