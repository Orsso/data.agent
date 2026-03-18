"""Tests for core/state.py — dataclasses, discriminator, make_loop_result."""

from pydantic import TypeAdapter

from core.models.turn import TurnState
from core.state import (
    CardSchema,
    ChartCardSchema,
    Choice,
    LoopResult,
    MetricCardSchema,
    Question,
    TodoItem,
    _card_discriminator,
    make_loop_result,
)

# ── Dataclass defaults ───────────────────────────────────────────────────


class TestDefaults:
    def test_choice_defaults(self):
        # INTENTION: Verify Choice("x") has description=""
        # FALSIFIABILITÉ: Would fail if default changes
        c = Choice(label="Yes")
        assert c.description == ""

    def test_question_defaults(self):
        # INTENTION: Verify Question("q") defaults: empty options, multi_select=False, selected_answer=None
        # FALSIFIABILITÉ: Would fail if any default changes
        q = Question(question="Which?")
        assert q.options == []
        assert q.multi_select is False
        assert q.selected_answer is None

    def test_question_header_default(self):
        # INTENTION: Verify Question header defaults to ""
        # FALSIFIABILITÉ: Would fail if default changes
        q = Question(question="Which?")
        assert q.header == ""

    def test_todo_item_default_status(self):
        # INTENTION: Verify TodoItem defaults to "pending"
        # FALSIFIABILITÉ: Would fail if default differs
        t = TodoItem(id="1", content="Do X")
        assert t.status == "pending"

    def test_loop_result_defaults(self):
        # INTENTION: Verify LoopResult defaults: pending=False, empty figs, None code, etc.
        # FALSIFIABILITÉ: Would fail if defaults change
        lr = LoopResult(content="text")
        assert lr.pending is False
        assert lr.figs == []
        assert lr.code is None
        assert lr.cards == []
        assert lr.result is None
        assert lr.error is None


# ── CardSchema discriminator ─────────────────────────────────────────────


class TestCardDiscriminator:
    def test_dict_input(self):
        # INTENTION: Verify _card_discriminator extracts "type" from dict
        # FALSIFIABILITÉ: Would fail if dict access is wrong
        assert _card_discriminator({"type": "metric"}) == "metric"
        assert _card_discriminator({"type": "chart"}) == "chart"

    def test_object_input(self):
        # INTENTION: Verify _card_discriminator uses getattr on objects
        # FALSIFIABILITÉ: Would fail if getattr is wrong
        m = MetricCardSchema(type="metric", title="T", value="V")
        assert _card_discriminator(m) == "metric"

    def test_none_for_unknown(self):
        # INTENTION: Verify _card_discriminator returns None for objects without type
        # FALSIFIABILITÉ: Would fail if fallback differs
        assert _card_discriminator("no type here") is None

    def test_metric_card_schema(self):
        # INTENTION: Verify MetricCardSchema validates correctly
        # FALSIFIABILITÉ: Would fail if schema rejects valid input
        m = MetricCardSchema(type="metric", title="Revenue", value="$1M")
        assert m.type == "metric"
        assert m.title == "Revenue"
        assert m.value == "$1M"

    def test_chart_card_schema_defaults(self):
        # INTENTION: Verify ChartCardSchema accepts fig=None as default
        # FALSIFIABILITÉ: Would fail if fig is required
        c = ChartCardSchema(type="chart", title="Sales")
        assert c.fig is None

    def test_card_schema_metric_via_type_adapter(self):
        # INTENTION: Verify Pydantic discriminator routes to MetricCardSchema
        # FALSIFIABILITÉ: Would fail if discriminator routing is broken
        adapter = TypeAdapter(CardSchema)
        result = adapter.validate_python({"type": "metric", "title": "T", "value": "V"})
        assert isinstance(result, MetricCardSchema)

    def test_card_schema_chart_via_type_adapter(self):
        # INTENTION: Verify Pydantic discriminator routes to ChartCardSchema
        # FALSIFIABILITÉ: Would fail if discriminator routing is broken
        adapter = TypeAdapter(CardSchema)
        result = adapter.validate_python({"type": "chart", "title": "T"})
        assert isinstance(result, ChartCardSchema)


# ── make_loop_result ─────────────────────────────────────────────────────


class TestMakeLoopResult:
    def test_assembles_from_parts_and_turn(self):
        # INTENTION: Verify make_loop_result assembles LoopResult from content_parts + turn
        # FALSIFIABILITÉ: Would fail if any field is not transferred
        turn = TurnState()
        turn.figs = [{"data": []}]
        turn.code = "df.head()"
        turn.cards = [{"type": "metric"}]
        turn.result = {"key": "value"}

        lr = make_loop_result(["Hello ", "world"], turn)
        assert lr.content == "Hello world"
        assert lr.figs == [{"data": []}]
        assert lr.code == "df.head()"
        assert lr.cards == [{"type": "metric"}]
        assert lr.result == {"key": "value"}

    def test_strips_content(self):
        # INTENTION: Verify whitespace is stripped from joined content
        # FALSIFIABILITÉ: Would fail if .strip() is removed
        turn = TurnState()
        lr = make_loop_result(["  ", " text ", "  "], turn)
        assert lr.content == "text"

    def test_empty_content_parts(self):
        # INTENTION: Verify empty content_parts produces empty string
        # FALSIFIABILITÉ: Would fail if join fails on empty list
        turn = TurnState()
        lr = make_loop_result([], turn)
        assert lr.content == ""
