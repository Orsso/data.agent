import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_chat, require_project
from api.models import ChatResponse, CreateChatRequest, RenameChatRequest, chat_response
from db import get_db
from db.repositories.chats import ChatRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/chats", tags=["chats"])


@router.post("", response_model=ChatResponse, status_code=201)
async def create_chat(
    project_id: str,
    req: CreateChatRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    project_row = await require_project(project_id, db)
    title = req.title if req else None
    row = await ChatRepository(db).create(project_id=project_row.id, title=title)
    logger.info("Chat created: %s [project=%s]", row.id, project_id)
    return chat_response(row)


@router.get("", response_model=list[ChatResponse])
async def list_chats(project_id: str, db: AsyncSession = Depends(get_db)):
    project_row = await require_project(project_id, db)
    rows = await ChatRepository(db).list_by_project(project_row.id)
    return [chat_response(r) for r in rows]


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(project_id: str, chat_id: str, db: AsyncSession = Depends(get_db)):
    _, chat_row = await require_chat(project_id, chat_id, db)
    return chat_response(chat_row)


@router.patch("/{chat_id}", response_model=ChatResponse)
async def rename_chat(
    project_id: str,
    chat_id: str,
    req: RenameChatRequest,
    db: AsyncSession = Depends(get_db),
):
    _, chat_row = await require_chat(project_id, chat_id, db)
    updated = await ChatRepository(db).update_title(chat_row.id, req.title)
    if updated is None:
        raise HTTPException(404, "Chat not found")
    logger.info("Chat renamed: %s -> '%s' [project=%s]", chat_id, req.title, project_id)
    return chat_response(updated)


@router.delete("/{chat_id}", status_code=200)
async def delete_chat(project_id: str, chat_id: str, db: AsyncSession = Depends(get_db)):
    _, chat_row = await require_chat(project_id, chat_id, db)
    await ChatRepository(db).delete(chat_row.id)
    logger.info("Chat deleted: %s [project=%s]", chat_id, project_id)
    return {"deleted": True}
