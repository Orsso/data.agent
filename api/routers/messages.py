import logging
import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from api.deps import get_project_manager, require_chat
from api.models import (
    CardProposalResponse,
    MessageHistoryItem,
    MessageRequest,
    MessageResumeRequest,
    QuestionResponse,
    TodoItemResponse,
    ToolStepResponse,
    card_response,
)
from api.sse import event_to_sse, stream_events
from core.project_manager import ProjectManager
from core.state import Answer
from db import get_db, get_session_factory
from db.repositories.chats import ChatRepository
from db.repositories.dashboard_cards import DashboardCardRepository
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
            code=r.code,
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
            ]
            if r.tool_steps
            else None,
            figure_count=len(r.figs) if r.figs else 0,
            todos=[
                TodoItemResponse(id=t["id"], content=t["content"], status=t["status"])
                for t in r.todos
            ]
            if r.todos
            else None,
            proposals=[CardProposalResponse(**p) for p in r.proposals] if r.proposals else None,
            asked_questions=[QuestionResponse(**q) for q in r.asked_questions]
            if r.asked_questions
            else None,
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
    logger.info(
        'Message [project=%s, chat=%s, cards=%s]: "%.80s"',
        project_id,
        chat_id,
        req.selected_card_ids,
        req.message,
    )

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

    # Clear pending questions in DB immediately so navigation won't restore stale questions
    await ChatRepository(db).update_pending_questions(uuid.UUID(chat_id), None)
    await db.commit()

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
                chat_id,
                message_id,
                len(msg.figs) if msg.figs else 0,
            )
            return msg.figs or []

    if thread.chat.pending_msg_id == message_id:
        logger.debug(
            "Figures found in pending turn [chat=%s, msg=%s]: %d fig(s)",
            chat_id,
            message_id,
            len(thread.turn.figs),
        )
        return list(thread.turn.figs)

    try:
        mid = uuid.UUID(message_id)
    except ValueError as exc:
        logger.warning(
            "Figure request with non-UUID message_id [chat=%s, msg=%s]",
            chat_id,
            message_id,
        )
        raise HTTPException(404, "Message not found") from exc

    repo_figs = await MessageRepository(db).get_figures(mid)
    if repo_figs:
        logger.debug(
            "Figures found in DB [chat=%s, msg=%s]: %d fig(s)",
            chat_id,
            message_id,
            len(repo_figs),
        )
        return repo_figs

    logger.warning(
        "Figures not found anywhere [chat=%s, msg=%s, in_memory_msgs=%d, pending_msg=%s]",
        chat_id,
        message_id,
        len(thread.chat.messages),
        thread.chat.pending_msg_id,
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
                        await repo.create(
                            chat_id=cid,
                            role=msg.role,
                            content=msg.content,
                            code=msg.code,
                            tool_steps=[asdict(s) for s in msg.tool_steps]
                            if msg.tool_steps
                            else None,
                            todos=[asdict(t) for t in msg.todos] if msg.todos else None,
                            thinking=msg.thinking,
                            thinking_duration_s=msg.thinking_duration_s,
                            figs=msg.figs if msg.figs else None,
                            proposals=[asdict(p) for p in msg.proposals] if msg.proposals else None,
                            asked_questions=[asdict(q) for q in msg.asked_questions]
                            if msg.asked_questions
                            else None,
                            created_at=base_ts + timedelta(microseconds=i),
                        )
                    await session.commit()
                    logger.info(
                        "Persisted %d message(s) [chat=%s]",
                        len(new_messages),
                        chat_id,
                    )
            except Exception:
                logger.error("Failed to persist messages [chat=%s]", chat_id, exc_info=True)

        pending_title = thread.consume_pending_title()
        pending_qs = thread.chat.pending_questions
        if pending_title or pending_qs is not None:
            try:
                factory = get_session_factory()
                async with factory() as session:
                    chat_repo = ChatRepository(session)
                    cid_uuid = uuid.UUID(chat_id)
                    if pending_title:
                        await chat_repo.update_title(cid_uuid, pending_title)
                        logger.info("Chat title persisted [chat=%s]: %s", chat_id, pending_title)
                    questions_json = [asdict(q) for q in pending_qs] if pending_qs else None
                    await chat_repo.update_pending_questions(cid_uuid, questions_json)
                    if questions_json:
                        logger.info("Pending questions persisted [chat=%s]", chat_id)
                    else:
                        logger.info("Pending questions cleared [chat=%s]", chat_id)
                    await session.commit()
            except Exception:
                logger.error("Failed to persist chat metadata [chat=%s]", chat_id, exc_info=True)

    return StreamingResponse(
        _wrapped(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _find_proposal(db: AsyncSession, chat_id: str, proposal_id: str):
    msg_row = await MessageRepository(db).find_by_proposal(uuid.UUID(chat_id), proposal_id)
    if not msg_row or not msg_row.proposals:
        raise HTTPException(404, "Message or proposals not found")
    for p in msg_row.proposals:
        if p["proposal_id"] == proposal_id:
            return msg_row, p
    raise HTTPException(404, "Proposal not found")


@router.post("/{message_id}/proposals/{proposal_id}/accept")
async def accept_proposal(
    project_id: str,
    chat_id: str,
    message_id: str,
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    await require_chat(project_id, chat_id, db)
    msg_row, proposal = await _find_proposal(db, chat_id, proposal_id)

    card_id = uuid.UUID(proposal["card_id"])
    row = await DashboardCardRepository(db).update_card(
        card_id,
        fig=proposal.get("proposed_fig"),
        code=proposal.get("proposed_code"),
        value=proposal.get("proposed_value"),
    )
    if row is None:
        raise HTTPException(404, "Card no longer exists")

    proposal["status"] = "accepted"
    flag_modified(msg_row, "proposals")
    await db.commit()

    # Update in-memory project state
    project = pm.get_project(project_id)
    if project:
        for card in project.dashboard_cards or []:
            if card.id == str(card_id):
                card.fig = row.fig
                card.code = row.code
                card.value = row.value
                break

    return {"accepted": True, "card": card_response(row)}


@router.post("/{message_id}/proposals/{proposal_id}/reject")
async def reject_proposal(
    project_id: str,
    chat_id: str,
    message_id: str,
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
):
    await require_chat(project_id, chat_id, db)
    msg_row, proposal = await _find_proposal(db, chat_id, proposal_id)

    proposal["status"] = "rejected"
    flag_modified(msg_row, "proposals")
    await db.commit()

    return {"rejected": True}
