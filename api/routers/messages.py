import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_project_manager, require_chat
from api.models import (
    MessageHistoryItem,
    MessageRequest,
    MessageResumeRequest,
    TodoItemResponse,
    ToolStepResponse,
)
from api.sse import event_to_sse, stream_events
from core.project_manager import ProjectManager
from core.state import Answer
from db import get_db, get_session_factory
from db.repositories.chats import ChatRepository
from db.repositories.messages import MessageRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/projects/{project_id}/chats/{chat_id}/messages",
    tags=["messages"],
)


@router.get("", response_model=list[MessageHistoryItem])
async def list_messages(
    project_id: str,
    chat_id: str,
    db: AsyncSession = Depends(get_db),
):
    _project_row, _chat_row = await require_chat(project_id, chat_id, db)
    rows = await MessageRepository(db).list_by_chat(uuid.UUID(chat_id))
    return [
        MessageHistoryItem(
            id=str(r.id),
            role=r.role,
            content=r.content,
            thinking=r.thinking,
            thinking_duration_s=r.thinking_duration_s,
            tool_steps=[
                ToolStepResponse(
                    tool_name=s["tool_name"],
                    summary=s["summary"],
                    success=s["success"],
                    duration_ms=s["duration_ms"],
                )
                for s in r.tool_steps
            ] if r.tool_steps else None,
            figure_count=len(r.figs) if r.figs else 0,
            todos=[
                TodoItemResponse(id=t["id"], content=t["content"], status=t["status"])
                for t in r.todos
            ] if r.todos else None,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("")
async def send_message(
    project_id: str,
    chat_id: str,
    req: MessageRequest,
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    project_row, _chat_row = await require_chat(project_id, chat_id, db)
    pm.get_or_load(project_id, model=project_row.model)
    await pm.hydrate(project_id, db)
    thread = pm.get_chat_thread(project_id, chat_id)
    logger.info('Message [project=%s, chat=%s]: "%.80s"', project_id, chat_id, req.message)

    msg_count_before = len(thread.chat.messages)
    event_gen = thread.run_chat(req.message, req.selected_card_ids)

    return _streaming_response_with_persistence(event_gen, thread, chat_id, msg_count_before)


@router.post("/resume")
async def resume_message(
    project_id: str,
    chat_id: str,
    req: MessageResumeRequest,
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    project_row, _chat_row = await require_chat(project_id, chat_id, db)
    pm.get_or_load(project_id, model=project_row.model)
    await pm.hydrate(project_id, db)
    thread = pm.get_chat_thread(project_id, chat_id)
    answers = [Answer(question=qid, answer=ans) for qid, ans in req.answers.items()]

    msg_count_before = len(thread.chat.messages)
    event_gen = thread.resume_chat(answers)

    return _streaming_response_with_persistence(event_gen, thread, chat_id, msg_count_before)


@router.get("/{message_id}/figures")
async def get_message_figures(
    project_id: str,
    chat_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    project_row, _chat_row = await require_chat(project_id, chat_id, db)
    pm.get_or_load(project_id, model=project_row.model)
    thread = pm.get_chat_thread(project_id, chat_id)

    for msg in thread.chat.messages:
        if msg.msg_id == message_id:
            logger.debug(
                "Figures found in memory [chat=%s, msg=%s]: %d fig(s)",
                chat_id, message_id, len(msg.figs) if msg.figs else 0,
            )
            return msg.figs or []

    if thread.chat.pending_msg_id == message_id:
        logger.debug(
            "Figures found in pending turn [chat=%s, msg=%s]: %d fig(s)",
            chat_id, message_id, len(thread.turn.figs),
        )
        return list(thread.turn.figs)

    try:
        mid = uuid.UUID(message_id)
    except ValueError as exc:
        logger.warning(
            "Figure request with non-UUID message_id [chat=%s, msg=%s]",
            chat_id, message_id,
        )
        raise HTTPException(404, "Message not found") from exc

    repo_figs = await MessageRepository(db).get_figures(mid)
    if repo_figs:
        logger.debug(
            "Figures found in DB [chat=%s, msg=%s]: %d fig(s)",
            chat_id, message_id, len(repo_figs),
        )
        return repo_figs

    logger.warning(
        "Figures not found anywhere [chat=%s, msg=%s, in_memory_msgs=%d, pending_msg=%s]",
        chat_id, message_id, len(thread.chat.messages), thread.chat.pending_msg_id,
    )
    raise HTTPException(404, "Message not found")


def _streaming_response_with_persistence(event_gen, thread, chat_id, msg_count_before):
    async def _wrapped():
        async for chunk in stream_events(event_gen, serializer=event_to_sse):
            yield chunk

        new_messages = thread.chat.messages[msg_count_before:]
        if new_messages:
            try:
                factory = get_session_factory()
                async with factory() as session:
                    repo = MessageRepository(session)
                    cid = uuid.UUID(chat_id)
                    base_ts = datetime.now(UTC)
                    for i, msg in enumerate(new_messages):
                        figs_json = msg.figs if msg.figs else None
                        tool_steps_json = (
                            [
                                {
                                    "tool_name": s.tool_name,
                                    "summary": s.summary,
                                    "success": s.success,
                                    "duration_ms": s.duration_ms,
                                }
                                for s in msg.tool_steps
                            ]
                            if msg.tool_steps
                            else None
                        )
                        todos_json = (
                            [
                                {"id": t.id, "content": t.content, "status": t.status}
                                for t in msg.todos
                            ]
                            if msg.todos
                            else None
                        )
                        await repo.create(
                            chat_id=cid,
                            role=msg.role,
                            content=msg.content,
                            code=msg.code,
                            tool_steps=tool_steps_json,
                            todos=todos_json,
                            thinking=msg.thinking,
                            thinking_duration_s=msg.thinking_duration_s,
                            figs=figs_json,
                            created_at=base_ts + timedelta(microseconds=i),
                        )
                    await session.commit()
                    logger.info(
                        "Persisted %d message(s) [chat=%s]",
                        len(new_messages), chat_id,
                    )
            except Exception:
                logger.error("Failed to persist messages [chat=%s]", chat_id, exc_info=True)

        pending_title = thread.consume_pending_title()
        if pending_title:
            try:
                factory = get_session_factory()
                async with factory() as session:
                    await ChatRepository(session).update_title(
                        uuid.UUID(chat_id), pending_title
                    )
                    await session.commit()
                    logger.info(
                        "Chat title persisted [chat=%s]: %s", chat_id, pending_title
                    )
            except Exception:
                logger.error("Failed to persist chat title [chat=%s]", chat_id, exc_info=True)

    return StreamingResponse(
        _wrapped(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
