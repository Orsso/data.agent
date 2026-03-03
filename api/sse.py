import json
import logging
from collections.abc import AsyncGenerator, Callable
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from core.events import (
    AskQuestionEvent,
    ChatRenamedEvent,
    DoneEvent,
    PipelineEvent,
    TextChunkEvent,
    ThinkingEvent,
    TodoUpdateEvent,
    ToolCallEvent,
    ToolResultEvent,
)

logger = logging.getLogger(__name__)


def _serialize(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    return str(obj)


def _event_to_data(event) -> dict:
    if isinstance(event, ThinkingEvent):
        return {"type": "thinking", "content": event.content}
    if isinstance(event, ToolCallEvent):
        return {
            "type": "tool_call",
            "tool_name": event.tool_name,
            "args": event.arguments_summary,
        }
    if isinstance(event, ToolResultEvent):
        return {
            "type": "tool_result",
            "tool_name": event.tool_name,
            "success": event.success,
            "summary": event.summary,
            "duration_ms": event.duration_ms,
        }
    if isinstance(event, TextChunkEvent):
        return {"type": "text_chunk", "chunk": event.chunk}
    if isinstance(event, AskQuestionEvent):
        return {
            "type": "ask_question",
            "questions": _serialize(event.questions),
        }
    if isinstance(event, ChatRenamedEvent):
        return {"type": "chat_renamed", "chat_id": event.chat_id, "title": event.title}
    if isinstance(event, TodoUpdateEvent):
        return {"type": "todo_update", "todos": _serialize(event.todos)}
    if isinstance(event, DoneEvent):
        loop = event.loop_result
        d: dict = {
            "type": "done",
            "pending": loop.pending,
            "content": loop.content,
            "has_figures": bool(loop.figs),
            "figure_count": len(loop.figs),
            "msg_id": event.msg_id,
        }
        if loop.error:
            d["error"] = loop.error
        return d
    logger.warning("Unknown event type: %s", type(event).__name__)
    return {"type": "unknown"}


def event_to_sse(event) -> str:
    return f"data: {json.dumps(_event_to_data(event))}\n\n"


def pipeline_event_to_sse(pe: PipelineEvent) -> str:
    data = _event_to_data(pe.event)
    data["source"] = pe.source
    return f"data: {json.dumps(data)}\n\n"


async def stream_events(event_gen, serializer: Callable = event_to_sse) -> AsyncGenerator[str]:
    async for event in event_gen:
        if event is not None:
            yield serializer(event)
