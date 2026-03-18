"""Tests for core/tools/execute_python.py — _format_output + execute_python tool."""

from unittest.mock import AsyncMock

import pytest

from core.constants import RESULT_DICT_MAX_CHARS, RESULT_OTHER_MAX_CHARS, STDOUT_MAX_CHARS
from core.sandbox.exceptions import SandboxError, SandboxTimeoutError
from core.tools.exceptions import CodeExecutionError, ToolError
from core.tools.execute_python import _format_output, execute_python

# ── _format_output (pure function) ───────────────────────────────────────


class TestFormatOutput:
    def test_single_fig(self):
        # INTENTION: Verify single figure shows "[Chart generated]"
        # FALSIFIABILITÉ: Would fail if text differs
        result = _format_output(None, [{"data": []}], [], {}, "", total_figs=1)
        assert "[Chart generated]" in result

    def test_multiple_figs(self):
        # INTENTION: Verify multiple figures shows "[N charts generated]"
        # FALSIFIABILITÉ: Would fail if count format differs
        result = _format_output(None, [{"d": []}, {"d": []}], [], {}, "", total_figs=2)
        assert "[2 charts generated]" in result

    def test_total_figs_shown(self):
        # INTENTION: Verify "[N charts total this turn]" when total_figs > len(figs)
        # FALSIFIABILITÉ: Would fail if comparison is wrong
        result = _format_output(None, [{"d": []}], [], {}, "", total_figs=3)
        assert "[3 charts total this turn]" in result

    def test_result_records(self):
        # INTENTION: Verify list-of-dicts result shows row count and sample
        # FALSIFIABILITÉ: Would fail if isinstance check is wrong
        records = [{"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}]
        result = _format_output(records, [], [], {}, "")
        assert "4 rows" in result
        assert "Sample" in result

    def test_result_dict_truncated(self):
        # INTENTION: Verify dict result is truncated at RESULT_DICT_MAX_CHARS
        # FALSIFIABILITÉ: Would fail if truncation limit differs
        big_dict = {"key": "v" * 3000}
        result = _format_output(big_dict, [], [], {}, "")
        assert len(result) <= RESULT_DICT_MAX_CHARS + 50  # tolerance for formatting

    def test_result_scalar(self):
        # INTENTION: Verify scalar result is str-converted and truncated
        # FALSIFIABILITÉ: Would fail if truncation limit differs
        result = _format_output("x" * 500, [], [], {}, "")
        assert len(result) <= RESULT_OTHER_MAX_CHARS + 10

    def test_card_updates_message(self):
        # INTENTION: Verify card_updates shows "[N card update(s) proposed]"
        # FALSIFIABILITÉ: Would fail if text format differs
        result = _format_output(None, [], [], {"c1": {"d": []}, "c2": {"d": []}}, "")
        assert "[2 card update(s) proposed]" in result

    def test_cards_message(self):
        # INTENTION: Verify cards shows "[N cards generated]"
        # FALSIFIABILITÉ: Would fail if text differs
        result = _format_output(None, [], [{"type": "metric"}, {"type": "chart"}], {}, "")
        assert "[2 cards generated]" in result

    def test_stdout_only(self):
        # INTENTION: Verify stdout is shown (truncated at STDOUT_MAX_CHARS) when no figs/result
        # FALSIFIABILITÉ: Would fail if stdout branch is not reached
        stdout_text = "x" * 1000
        result = _format_output(None, [], [], {}, stdout_text)
        assert len(result) <= STDOUT_MAX_CHARS + 10

    def test_no_output(self):
        # INTENTION: Verify "Code executed with no output." when everything is empty
        # FALSIFIABILITÉ: Would fail if text differs
        result = _format_output(None, [], [], {}, "")
        assert result == "Code executed with no output."


# ── execute_python tool (async) ──────────────────────────────────────────


class TestExecutePython:
    @pytest.mark.asyncio
    async def test_empty_code_raises(self, runnable_config):
        # INTENTION: Verify whitespace-only code raises ToolError
        # FALSIFIABILITÉ: Would fail if empty check is removed
        with pytest.raises(ToolError, match="Empty code"):
            await execute_python.ainvoke({"code": "   "}, config=runnable_config)

    @pytest.mark.asyncio
    async def test_success(self, runnable_config, tool_context):
        # INTENTION: Verify normal execution returns formatted output and updates turn state
        # FALSIFIABILITÉ: Would fail if state update is skipped
        # Mock based on real sandbox response structure (execute_python.py:63-67)
        tool_context.sandbox.ensure_container = AsyncMock()
        tool_context.sandbox.execute = AsyncMock(
            return_value={
                "figures": [{"data": [], "layout": {}}],
                "cards": [],
                "card_updates": {},
                "result": None,
                "stdout": "",
                "error": None,
            }
        )
        result = await execute_python.ainvoke({"code": "fig = px.bar(df)"}, config=runnable_config)
        assert "[Chart generated]" in result
        assert len(tool_context.turn.figs) == 1
        assert tool_context.turn.code == "fig = px.bar(df)"

    @pytest.mark.asyncio
    async def test_timeout_raises(self, runnable_config, tool_context):
        # INTENTION: Verify SandboxTimeoutError maps to ToolError
        # FALSIFIABILITÉ: Would fail if exception is not caught
        tool_context.sandbox.ensure_container = AsyncMock()
        tool_context.sandbox.execute = AsyncMock(side_effect=SandboxTimeoutError("timed out"))
        with pytest.raises(ToolError, match="timed out"):
            await execute_python.ainvoke(
                {"code": "import time; time.sleep(999)"},
                config=runnable_config,
            )

    @pytest.mark.asyncio
    async def test_sandbox_error_raises(self, runnable_config, tool_context):
        # INTENTION: Verify SandboxError maps to ToolError
        # FALSIFIABILITÉ: Would fail if exception is not caught
        tool_context.sandbox.ensure_container = AsyncMock()
        tool_context.sandbox.execute = AsyncMock(side_effect=SandboxError("container crashed"))
        with pytest.raises(ToolError, match="Sandbox unavailable"):
            await execute_python.ainvoke({"code": "print(1)"}, config=runnable_config)

    @pytest.mark.asyncio
    async def test_code_error_raises(self, runnable_config, tool_context):
        # INTENTION: Verify response with "error" key raises CodeExecutionError
        # FALSIFIABILITÉ: Would fail if error handling is wrong
        tool_context.sandbox.ensure_container = AsyncMock()
        tool_context.sandbox.execute = AsyncMock(
            return_value={
                "figures": [],
                "cards": [],
                "card_updates": {},
                "result": None,
                "stdout": "",
                "error": "NameError: name 'df' is not defined",
            }
        )
        with pytest.raises(CodeExecutionError, match="NameError"):
            await execute_python.ainvoke({"code": "df.head()"}, config=runnable_config)

    @pytest.mark.asyncio
    async def test_fig_warning_when_cards_selected(self, runnable_config, tool_context):
        # INTENTION: Verify warning when figs produced but selected_card_ids set without card_updates
        # FALSIFIABILITÉ: Would fail if warning condition is wrong
        tool_context.turn.selected_card_ids = ["card-1"]
        tool_context.sandbox.ensure_container = AsyncMock()
        tool_context.sandbox.execute = AsyncMock(
            return_value={
                "figures": [{"data": [], "layout": {}}],
                "cards": [],
                "card_updates": {},
                "result": None,
                "stdout": "",
                "error": None,
            }
        )
        result = await execute_python.ainvoke(
            {"code": "fig = px.bar(df)"},
            config=runnable_config,
        )
        assert "WARNING" in result
        assert "card_updates" in result
