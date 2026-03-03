from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from db.models import ChatRow, DashboardCardRow, ProjectRow, SourceRow


class CreateProjectRequest(BaseModel):
    name: str
    model: str | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class SourceResponse(BaseModel):
    id: str
    name: str
    origin: str
    row_count: int
    columns: list[str]
    created_at: datetime


def source_response(row: SourceRow) -> SourceResponse:
    return SourceResponse(
        id=str(row.id),
        name=row.name,
        origin=row.origin,
        row_count=row.row_count,
        columns=row.columns,
        created_at=row.created_at,
    )


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    status: str
    model: str
    suggested_questions: list[str]
    sources: list[SourceResponse]
    chat_count: int
    created_at: datetime
    updated_at: datetime


def project_response(row: ProjectRow) -> ProjectResponse:
    sources = [source_response(s) for s in row.sources]
    return ProjectResponse(
        id=str(row.id),
        name=row.name,
        description=row.description,
        status=row.status,
        model=row.model,
        suggested_questions=row.suggested_questions or [],
        sources=sources,
        chat_count=len(row.chats),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ProjectListItem(BaseModel):
    id: str
    name: str
    description: str | None
    status: str
    source_count: int
    source_names: list[str]
    chat_count: int
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectListItem]


class CreateChatRequest(BaseModel):
    title: str | None = None


class RenameChatRequest(BaseModel):
    title: str


class ChatResponse(BaseModel):
    id: str
    project_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime


def chat_response(row: ChatRow) -> ChatResponse:
    return ChatResponse(
        id=str(row.id),
        project_id=str(row.project_id),
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class MessageRequest(BaseModel):
    message: str
    selected_card_ids: list[str] | None = None


class MessageResumeRequest(BaseModel):
    answers: dict[str, str]


class TodoItemResponse(BaseModel):
    id: str
    content: str
    status: Literal["pending", "in_progress", "completed"]


class ToolStepResponse(BaseModel):
    tool_name: str
    summary: str
    success: bool
    duration_ms: int


class MessageHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    thinking: str | None = None
    thinking_duration_s: float | None = None
    tool_steps: list[ToolStepResponse] | None = None
    figure_count: int
    todos: list[TodoItemResponse] | None = None
    created_at: datetime


class DashboardCardResponse(BaseModel):
    id: str
    type: str
    title: str
    code: str | None
    value: str | None
    fig: dict | None
    position: int


def card_response(row: DashboardCardRow) -> DashboardCardResponse:
    return DashboardCardResponse(
        id=str(row.id),
        type=row.type,
        title=row.title,
        code=row.code,
        value=row.value,
        fig=row.fig,
        position=row.position,
    )


class AddDashboardCardRequest(BaseModel):
    type: str
    title: str
    code: str | None = None
    value: str | None = None
    fig: dict | None = None
