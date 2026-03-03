import uuid

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.project_manager import ProjectManager
from db.models import ChatRow, ProjectRow
from db.repositories.chats import ChatRepository
from db.repositories.projects import ProjectRepository


def get_project_manager(request: Request) -> ProjectManager:
    return request.app.state.project_manager


async def require_project(project_id: str, db: AsyncSession) -> ProjectRow:
    try:
        pid = uuid.UUID(project_id)
    except ValueError as exc:
        raise HTTPException(400, "Invalid project ID") from exc
    row = await ProjectRepository(db).get(pid)
    if row is None:
        raise HTTPException(404, "Project not found")
    return row


async def require_chat(
    project_id: str, chat_id: str, db: AsyncSession
) -> tuple[ProjectRow, ChatRow]:
    project_row = await require_project(project_id, db)
    try:
        cid = uuid.UUID(chat_id)
    except ValueError as exc:
        raise HTTPException(400, "Invalid chat ID") from exc
    row = await ChatRepository(db).get(cid)
    if row is None or str(row.project_id) != project_id:
        raise HTTPException(404, "Chat not found")
    return project_row, row
