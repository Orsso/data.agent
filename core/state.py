from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator, Tag

TodoStatus = Literal["pending", "in_progress", "completed"]
ProposalStatus = Literal["pending", "accepted", "rejected"]


@dataclass
class Choice:
    label: str
    description: str = ""


@dataclass
class Question:
    question: str
    header: str = ""
    options: list[Choice] = field(default_factory=list)
    multi_select: bool = False
    selected_answer: str | None = None


@dataclass
class Answer:
    question: str
    answer: str


@dataclass
class TodoItem:
    id: str
    content: str
    status: TodoStatus = "pending"


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    format: str | None
    nulls_pct: float
    cardinality: int
    sample_values: list[str]


@dataclass
class DataProfile:
    row_count: int
    columns: list[ColumnProfile]


class MetricCardSchema(BaseModel):
    type: Literal["metric"]
    title: str
    value: str


class ChartCardSchema(BaseModel):
    type: Literal["chart"]
    title: str
    fig: dict | None = None


def _card_discriminator(v):
    if isinstance(v, dict):
        return v.get("type")
    return getattr(v, "type", None)


CardSchema = Annotated[
    Annotated[MetricCardSchema, Tag("metric")] | Annotated[ChartCardSchema, Tag("chart")],
    Discriminator(_card_discriminator),
]


@dataclass
class DashboardCard:
    id: str
    type: str
    title: str
    code: str | None = None
    value: str | None = None
    fig: dict | None = None


@dataclass
class ToolStep:
    tool_name: str
    arguments_summary: str
    success: bool
    summary: str
    duration_ms: int


@dataclass
class CardProposal:
    proposal_id: str
    card_id: str
    card_title: str
    current_fig: dict | None
    current_code: str | None
    current_value: str | None
    proposed_fig: dict | None
    proposed_code: str | None
    proposed_value: str | None
    status: ProposalStatus = "pending"


@dataclass
class ChatMessage:
    role: str
    content: str
    msg_id: str
    code: str | None = None
    figs: list[dict] = field(default_factory=list)
    tool_steps: list[ToolStep] = field(default_factory=list)
    todos: list[TodoItem] = field(default_factory=list)
    proposals: list[CardProposal] = field(default_factory=list)
    asked_questions: list["Question"] | None = None
    thinking: str | None = None
    thinking_duration_s: float | None = None


@dataclass
class LoopResult:
    content: str
    pending: bool = False
    figs: list[dict] = field(default_factory=list)
    code: str | None = None
    cards: list[dict] = field(default_factory=list)
    result: dict | None = None
    error: str | None = None


def make_loop_result(content_parts, turn) -> LoopResult:
    content = "".join(content_parts).strip()
    return LoopResult(
        content=content,
        figs=list(turn.figs),
        code=turn.code,
        cards=list(turn.cards),
        result=turn.result,
    )
