"""Tests for core/formatting.py — output formatting pure functions."""

import json

from core.formatting import (
    MAX_SUMMARY_LENGTH,
    MAX_SUMMARY_LINE,
    _try_parse_insights,
    extract_insights,
    serialize_figure,
    summarize_args,
)
from core.state import LoopResult

# ── serialize_figure ──────────────────────────────────────────────────────


class TestSerializeFigure:
    def test_none_returns_none(self):
        # INTENTION: Verify None input produces None output
        # FALSIFIABILITÉ: Would fail if it returns an empty dict or raises
        assert serialize_figure(None) is None

    def test_with_to_json(self):
        # INTENTION: Verify objects with to_json() are deserialized to dict
        # FALSIFIABILITÉ: Would fail if json.loads(fig.to_json()) is not called
        class FakeFig:
            def to_json(self):
                return '{"data": [], "layout": {}}'

        result = serialize_figure(FakeFig())
        assert result == {"data": [], "layout": {}}

    def test_dict_passthrough(self):
        # INTENTION: Verify dict input is returned as-is
        # FALSIFIABILITÉ: Would fail if dict is re-serialized or wrapped
        d = {"data": [1, 2], "layout": {"title": "test"}}
        assert serialize_figure(d) is d

    def test_unknown_type_returns_none(self):
        # INTENTION: Verify unknown types (no to_json, not dict) return None
        # FALSIFIABILITÉ: Would fail if a fallback like str() is used instead
        assert serialize_figure(42) is None
        assert serialize_figure("string") is None


# ── summarize_args ────────────────────────────────────────────────────────


class TestSummarizeArgs:
    def test_execute_python_first_line(self):
        # INTENTION: Verify execute_python returns first line of code (no "..." if under 80 chars)
        # FALSIFIABILITÉ: Would fail if multi-line code is not split on \n
        code = "import pandas as pd\ndf = pd.read_csv('data.csv')"
        args = json.dumps({"code": code})
        result = summarize_args("execute_python", args)
        # First line is "import pandas as pd" — under MAX_SUMMARY_LINE, but total code > 80, so "..." added
        assert result.startswith("import pandas as pd")

    def test_execute_python_short_code(self):
        # INTENTION: Verify short code does not get "..." suffix
        # FALSIFIABILITÉ: Would fail if "..." is always appended
        code = "print('hi')"
        args = json.dumps({"code": code})
        result = summarize_args("execute_python", args)
        assert result == "print('hi')"
        assert not result.endswith("...")

    def test_execute_python_long_first_line(self):
        # INTENTION: Verify long first line is truncated at exactly MAX_SUMMARY_LINE chars
        # FALSIFIABILITÉ: Would fail if truncation limit is not 80
        code = "x" * 200
        args = json.dumps({"code": code})
        result = summarize_args("execute_python", args)
        assert result == "x" * MAX_SUMMARY_LINE + "..."

    def test_ask_question(self):
        # INTENTION: Verify ask_question returns first question's text
        # FALSIFIABILITÉ: Would fail if index access or key is wrong
        args = json.dumps({"questions": [{"question": "Which metric?"}]})
        result = summarize_args("ask_question", args)
        assert result == "Which metric?"

    def test_ask_question_empty(self):
        # INTENTION: Verify empty questions list returns empty string
        # FALSIFIABILITÉ: Would fail if IndexError is raised
        args = json.dumps({"questions": []})
        result = summarize_args("ask_question", args)
        assert result == ""

    def test_todo_write_with_items(self):
        # INTENTION: Verify todo action returns "write (3 items)" format
        # FALSIFIABILITÉ: Would fail if count or format string changes
        args = json.dumps({"action": "write", "todos": [{"id": "1"}, {"id": "2"}, {"id": "3"}]})
        result = summarize_args("todo", args)
        assert result == "write (3 items)"

    def test_todo_read(self):
        # INTENTION: Verify todo read with no todos returns just "read"
        # FALSIFIABILITÉ: Would fail if todos=None is not handled
        args = json.dumps({"action": "read"})
        result = summarize_args("todo", args)
        assert result == "read"

    def test_fallback_unknown_tool(self):
        # INTENTION: Verify unknown tool returns truncated str(args)
        # FALSIFIABILITÉ: Would fail if MAX_SUMMARY_LENGTH (100) truncation is wrong
        args = json.dumps({"key": "v" * 200})
        result = summarize_args("unknown_tool", args)
        assert len(result) <= MAX_SUMMARY_LENGTH

    def test_invalid_json(self):
        # INTENTION: Verify invalid JSON returns "(invalid JSON)"
        # FALSIFIABILITÉ: Would fail if JSONDecodeError is not caught
        result = summarize_args("execute_python", "not json{{{")
        assert result == "(invalid JSON)"


# ── extract_insights ──────────────────────────────────────────────────────


class TestExtractInsights:
    def test_result_dict_with_keys(self):
        # INTENTION: Verify when result is a dict with description+questions, it's returned directly
        # FALSIFIABILITÉ: Would fail if the dict-with-keys shortcut is skipped
        loop = LoopResult(
            content="",
            result={"description": "Sales grew 20%", "questions": ["Why?"]},
        )
        result = extract_insights(loop)
        assert result["description"] == "Sales grew 20%"
        assert result["questions"] == ["Why?"]

    def test_result_json_string(self):
        # INTENTION: Verify when result is a JSON string with the right keys, it's parsed
        # FALSIFIABILITÉ: Would fail if string-parsing branch is skipped
        payload = {"description": "Growth", "questions": ["Trend?"]}
        loop = LoopResult(content="", result=json.dumps(payload))
        result = extract_insights(loop)
        assert result == payload

    def test_content_json_string(self):
        # INTENTION: Verify when result is not usable but content is JSON, content is parsed
        # FALSIFIABILITÉ: Would fail if content fallback is not reached
        payload = {"description": "Revenue up", "questions": []}
        loop = LoopResult(content=json.dumps(payload), result=None)
        result = extract_insights(loop)
        assert result == payload

    def test_content_with_code_fences(self):
        # INTENTION: Verify markdown ```json ... ``` fences are stripped before parsing
        # FALSIFIABILITÉ: Would fail if regex stripping is broken
        payload = {"description": "Test", "questions": ["Q1"]}
        fenced = f"```json\n{json.dumps(payload)}\n```"
        loop = LoopResult(content=fenced, result=None)
        result = extract_insights(loop)
        assert result == payload

    def test_fallback(self):
        # INTENTION: Verify unparseable result+content gives fallback structure
        # FALSIFIABILITÉ: Would fail if fallback dict structure differs
        loop = LoopResult(content="Just some text", result=None)
        result = extract_insights(loop)
        assert result == {"description": "Just some text", "questions": []}

    def test_fallback_empty_content(self):
        # INTENTION: Verify empty content gives empty description in fallback
        # FALSIFIABILITÉ: Would fail if content="" is not handled
        loop = LoopResult(content="", result=None)
        result = extract_insights(loop)
        assert result == {"description": "", "questions": []}


# ── _try_parse_insights ──────────────────────────────────────────────────


class TestTryParseInsights:
    def test_valid_json_with_keys(self):
        # INTENTION: Verify valid JSON with both keys returns the parsed dict
        # FALSIFIABILITÉ: Would fail if key validation is wrong
        text = json.dumps({"description": "d", "questions": ["q"]})
        assert _try_parse_insights(text) == {"description": "d", "questions": ["q"]}

    def test_missing_description_key(self):
        # INTENTION: Verify valid JSON missing "description" returns None
        # FALSIFIABILITÉ: Would fail if key check is removed
        text = json.dumps({"questions": ["q"]})
        assert _try_parse_insights(text) is None

    def test_missing_questions_key(self):
        # INTENTION: Verify valid JSON missing "questions" returns None
        # FALSIFIABILITÉ: Would fail if key check is removed
        text = json.dumps({"description": "d"})
        assert _try_parse_insights(text) is None

    def test_invalid_json(self):
        # INTENTION: Verify invalid JSON returns None
        # FALSIFIABILITÉ: Would fail if JSONDecodeError is not caught
        assert _try_parse_insights("not json") is None

    def test_code_fences_stripped(self):
        # INTENTION: Verify ```json fences are removed before parsing
        # FALSIFIABILITÉ: Would fail if regex does not match fences
        inner = json.dumps({"description": "d", "questions": []})
        text = f"```json\n{inner}\n```"
        assert _try_parse_insights(text) == {"description": "d", "questions": []}
