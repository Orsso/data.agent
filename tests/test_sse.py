"""Tests for api/sse.py — SSE serialization."""

import json
from dataclasses import dataclass
from enum import Enum

import pytest

from api.sse import _event_to_data, _serialize, event_to_sse, pipeline_event_to_sse, stream_events
from core.events import (
    AskQuestionEvent,
    CardProposalsEvent,
    ChatRenamedEvent,
    DoneEvent,
    PipelineEvent,
    TextChunkEvent,
    ThinkingEvent,
    TodoUpdateEvent,
    ToolCallEvent,
    ToolResultEvent,
)
from core.state import (
    CardProposal,
    Choice,
    LoopResult,
    Question,
    TodoItem,
)

# ── _serialize ────────────────────────────────────────────────────────────


class TestSerialize:
    def test_dataclass(self):
        # INTENTION: Verify dataclass instances are serialized to dicts
        # FALSIFIABILITÉ: Would fail if is_dataclass check is wrong
        result = _serialize(Choice(label="Yes", description="Confirm"))
        assert result == {"label": "Yes", "description": "Confirm"}

    def test_enum(self):
        # INTENTION: Verify Enum instances return their .value
        # FALSIFIABILITÉ: Would fail if str(enum) is used instead
        class Color(Enum):
            RED = "red"

        assert _serialize(Color.RED) == "red"

    def test_primitives(self):
        # INTENTION: Verify str/int/float/bool/None pass through unchanged
        # FALSIFIABILITÉ: Would fail if type check excludes one
        assert _serialize("hello") == "hello"
        assert _serialize(42) == 42
        assert _serialize(3.14) == 3.14
        assert _serialize(True) is True
        assert _serialize(None) is None

    def test_list_recursive(self):
        # INTENTION: Verify lists are recursed into
        # FALSIFIABILITÉ: Would fail if list items are not individually serialized
        result = _serialize([Choice("A"), Choice("B")])
        assert result == [{"label": "A", "description": ""}, {"label": "B", "description": ""}]

    def test_dict_recursive(self):
        # INTENTION: Verify dicts are recursed into (values serialized)
        # FALSIFIABILITÉ: Would fail if dict values are left as-is
        result = _serialize({"choice": Choice("X")})
        assert result == {"choice": {"label": "X", "description": ""}}

    def test_unknown_type_to_str(self):
        # INTENTION: Verify unknown types fall back to str()
        # FALSIFIABILITÉ: Would fail if an exception is raised
        result = _serialize(object())
        assert isinstance(result, str)

    def test_nested_dataclass(self):
        # INTENTION: Verify nested dataclasses are recursively serialized
        # FALSIFIABILITÉ: Would fail if inner dataclass stays as object
        q = Question(question="Pick?", options=[Choice("A"), Choice("B")])
        result = _serialize(q)
        assert isinstance(result, dict)
        assert result["question"] == "Pick?"
        assert len(result["options"]) == 2
        assert result["options"][0] == {"label": "A", "description": ""}


# ── _event_to_data ───────────────────────────────────────────────────────


class TestEventToData:
    def test_thinking_event(self):
        # INTENTION: Verify ThinkingEvent produces {"type": "thinking", "content": ...}
        # FALSIFIABILITÉ: Would fail if type string or key name differs
        data = _event_to_data(ThinkingEvent(content="Analyzing data..."))
        assert data == {"type": "thinking", "content": "Analyzing data..."}

    def test_tool_call_event(self):
        # INTENTION: Verify ToolCallEvent produces correct keys
        # FALSIFIABILITÉ: Would fail if "args" key name changes
        data = _event_to_data(
            ToolCallEvent(tool_name="execute_python", arguments_summary="df.head()")
        )
        assert data == {"type": "tool_call", "tool_name": "execute_python", "args": "df.head()"}

    def test_tool_result_event(self):
        # INTENTION: Verify ToolResultEvent includes success, summary, duration_ms
        # FALSIFIABILITÉ: Would fail if any field is omitted
        data = _event_to_data(
            ToolResultEvent(
                tool_name="execute_python",
                success=True,
                summary="[Chart generated]",
                duration_ms=150,
            )
        )
        assert data["type"] == "tool_result"
        assert data["success"] is True
        assert data["duration_ms"] == 150

    def test_text_chunk_event(self):
        # INTENTION: Verify TextChunkEvent produces {"type": "text_chunk", "chunk": ...}
        # FALSIFIABILITÉ: Would fail if key name differs
        data = _event_to_data(TextChunkEvent(chunk="Hello "))
        assert data == {"type": "text_chunk", "chunk": "Hello "}

    def test_ask_question_event(self):
        # INTENTION: Verify AskQuestionEvent serializes questions list
        # FALSIFIABILITÉ: Would fail if questions are not passed through _serialize
        q = Question(question="Which?", options=[Choice("A")])
        data = _event_to_data(AskQuestionEvent(questions=[q]))
        assert data["type"] == "ask_question"
        assert len(data["questions"]) == 1
        assert data["questions"][0]["question"] == "Which?"

    def test_chat_renamed_event(self):
        # INTENTION: Verify ChatRenamedEvent produces chat_id and title
        # FALSIFIABILITÉ: Would fail if keys differ
        data = _event_to_data(ChatRenamedEvent(chat_id="abc", title="New Title"))
        assert data == {"type": "chat_renamed", "chat_id": "abc", "title": "New Title"}

    def test_todo_update_event(self):
        # INTENTION: Verify TodoUpdateEvent serializes todos list
        # FALSIFIABILITÉ: Would fail if todos are not serialized
        todo = TodoItem(id="1", content="Step 1", status="pending")
        data = _event_to_data(TodoUpdateEvent(todos=[todo]))
        assert data["type"] == "todo_update"
        assert data["todos"][0]["content"] == "Step 1"

    def test_card_proposals_event(self):
        # INTENTION: Verify CardProposalsEvent serializes proposals
        # FALSIFIABILITÉ: Would fail if proposals are not serialized
        proposal = CardProposal(
            proposal_id="p1",
            card_id="c1",
            card_title="Rev",
            current_fig=None,
            current_code=None,
            current_value=None,
            proposed_fig={"data": []},
            proposed_code="code",
            proposed_value=None,
        )
        data = _event_to_data(CardProposalsEvent(proposals=[proposal]))
        assert data["type"] == "card_proposals"
        assert data["proposals"][0]["proposal_id"] == "p1"

    def test_done_event_basic(self):
        # INTENTION: Verify DoneEvent includes pending, content, has_figures, figure_count, msg_id
        # FALSIFIABILITÉ: Would fail if any key is missing
        loop = LoopResult(content="Done.", figs=[{"data": []}])
        data = _event_to_data(DoneEvent(loop_result=loop, msg_id="m1"))
        assert data["type"] == "done"
        assert data["pending"] is False
        assert data["content"] == "Done."
        assert data["has_figures"] is True
        assert data["figure_count"] == 1
        assert data["msg_id"] == "m1"

    def test_done_event_with_code(self):
        # INTENTION: Verify DoneEvent with code includes "code" key
        # FALSIFIABILITÉ: Would fail if the conditional `if loop.code` is wrong
        loop = LoopResult(content="", code="print('hi')")
        data = _event_to_data(DoneEvent(loop_result=loop))
        assert "code" in data
        assert data["code"] == "print('hi')"

    def test_done_event_with_error(self):
        # INTENTION: Verify DoneEvent with error includes "error" key
        # FALSIFIABILITÉ: Would fail if the conditional `if loop.error` is wrong
        loop = LoopResult(content="", error="Something broke")
        data = _event_to_data(DoneEvent(loop_result=loop))
        assert "error" in data
        assert data["error"] == "Something broke"

    def test_done_event_no_code_no_error(self):
        # INTENTION: Verify DoneEvent without code/error omits those keys
        # FALSIFIABILITÉ: Would fail if keys are always present
        loop = LoopResult(content="Result")
        data = _event_to_data(DoneEvent(loop_result=loop))
        assert "code" not in data
        assert "error" not in data

    def test_unknown_event_type(self):
        # INTENTION: Verify unknown event type returns {"type": "unknown"} without raising
        # FALSIFIABILITÉ: Would fail if an exception is raised
        @dataclass
        class FakeEvent:
            value: str

        data = _event_to_data(FakeEvent(value="test"))
        assert data == {"type": "unknown"}


# ── event_to_sse ─────────────────────────────────────────────────────────


class TestEventToSse:
    def test_format(self):
        # INTENTION: Verify SSE format is "data: {json}\n\n"
        # FALSIFIABILITÉ: Would fail if framing is wrong (missing newlines, prefix)
        event = TextChunkEvent(chunk="hi")
        sse = event_to_sse(event)
        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")
        parsed = json.loads(sse[len("data: ") : -2])
        assert parsed["type"] == "text_chunk"


# ── pipeline_event_to_sse ────────────────────────────────────────────────


class TestPipelineEventToSse:
    def test_adds_source_field(self):
        # INTENTION: Verify pipeline_event_to_sse adds "source" field to data
        # FALSIFIABILITÉ: Would fail if source is missing from output
        inner = TextChunkEvent(chunk="hi")
        pe = PipelineEvent(source="insights", event=inner)
        sse = pipeline_event_to_sse(pe)
        parsed = json.loads(sse[len("data: ") : -2])
        assert parsed["source"] == "insights"
        assert parsed["type"] == "text_chunk"


# ── stream_events ────────────────────────────────────────────────────────


class TestStreamEvents:
    @pytest.mark.asyncio
    async def test_skips_none(self):
        # INTENTION: Verify None events are skipped
        # FALSIFIABILITÉ: Would fail if None causes a crash or yields output
        async def gen():
            yield None
            yield TextChunkEvent(chunk="hi")

        results = [line async for line in stream_events(gen())]
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_yields_all_non_none(self):
        # INTENTION: Verify all non-None events produce SSE output
        # FALSIFIABILITÉ: Would fail if events are dropped
        async def gen():
            yield TextChunkEvent(chunk="a")
            yield TextChunkEvent(chunk="b")
            yield TextChunkEvent(chunk="c")

        results = [line async for line in stream_events(gen())]
        assert len(results) == 3
