from dataclasses import dataclass
from typing import Literal

from core.state import CardProposal, LoopResult, Question, TodoItem


@dataclass
class ToolCallEvent:
    tool_name: str
    arguments_summary: str


@dataclass
class ToolResultEvent:
    tool_name: str
    success: bool
    summary: str
    duration_ms: int


@dataclass
class TextChunkEvent:
    chunk: str


@dataclass
class AskQuestionEvent:
    questions: list[Question]


@dataclass
class ThinkingEvent:
    content: str


@dataclass
class DoneEvent:
    loop_result: LoopResult
    msg_id: str | None = None


@dataclass
class ChatRenamedEvent:
    chat_id: str
    title: str


@dataclass
class TodoUpdateEvent:
    todos: list[TodoItem]


@dataclass
class CardProposalsEvent:
    proposals: list[CardProposal]


@dataclass
class PipelineEvent:
    source: Literal["insights", "dashboard"]
    event: ToolCallEvent | ToolResultEvent | ThinkingEvent | TextChunkEvent | DoneEvent
