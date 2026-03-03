import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from core.constants import DEFAULT_MODEL


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    model: Mapped[str] = mapped_column(
        String(100), nullable=False, default=DEFAULT_MODEL
    )
    suggested_questions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    sources: Mapped[list["SourceRow"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    chats: Mapped[list["ChatRow"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    dashboard_cards: Mapped[list["DashboardCardRow"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class SourceRow(Base):
    __tablename__ = "sources"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_source_project_name"),
        Index("idx_sources_project", "project_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    origin: Mapped[str] = mapped_column(String(20), nullable=False, default="upload")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    columns: Mapped[list] = mapped_column(JSONB, nullable=False)
    profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    project: Mapped[ProjectRow] = relationship(back_populates="sources")


class ChatRow(Base):
    __tablename__ = "chats"
    __table_args__ = (Index("idx_chats_project", "project_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[ProjectRow] = relationship(back_populates="chats")
    messages: Mapped[list["MessageRow"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )


class MessageRow(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_chat", "chat_id"),
        Index("idx_messages_chat_created", "chat_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_steps: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    todos: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    thinking: Mapped[str | None] = mapped_column(Text, nullable=True)
    thinking_duration_s: Mapped[float | None] = mapped_column(nullable=True)
    figs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    chat: Mapped[ChatRow] = relationship(back_populates="messages")


class DashboardCardRow(Base):
    __tablename__ = "dashboard_cards"
    __table_args__ = (Index("idx_dashboard_cards_project", "project_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    fig: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    project: Mapped[ProjectRow] = relationship(back_populates="dashboard_cards")
