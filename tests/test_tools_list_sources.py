"""Tests for core/tools/list_sources.py — list_sources tool."""

import json

from core.models.sources import DataSource, SourceRegistry
from core.state import ColumnProfile, DataProfile
from core.tools.list_sources import list_sources


def _make_src(name, row_count=10, columns=None):
    cols = columns or ["col1"]
    return DataSource(
        name=name,
        profile=DataProfile(
            row_count=row_count,
            columns=[ColumnProfile(c, "int64", None, 0.0, row_count, ["1"]) for c in cols],
        ),
        origin="csv",
        row_count=row_count,
        columns=cols,
    )


class TestListSources:
    def test_empty_registry(self, runnable_config, tool_context):
        # INTENTION: Verify empty registry returns "No data sources loaded."
        # FALSIFIABILITÉ: Would fail if message differs
        tool_context.sources = SourceRegistry()
        result = list_sources.invoke({}, config=runnable_config)
        assert result == "No data sources loaded."

    def test_with_data(self, runnable_config):
        # INTENTION: Verify returns JSON with sources array containing name, rows, columns
        # FALSIFIABILITÉ: Would fail if key names differ
        result = list_sources.invoke({}, config=runnable_config)
        parsed = json.loads(result)
        assert "sources" in parsed
        assert len(parsed["sources"]) == 1
        src = parsed["sources"][0]
        assert src["name"] == "sales"
        assert "rows" in src
        assert "columns" in src

    def test_multiple_sources(self, runnable_config, tool_context):
        # INTENTION: Verify multiple sources all appear in output
        # FALSIFIABILITÉ: Would fail if only the first source is returned
        tool_context.sources.add("users", _make_src("users", 50, ["user_id", "email"]))
        result = list_sources.invoke({}, config=runnable_config)
        parsed = json.loads(result)
        assert len(parsed["sources"]) == 2
        names = {s["name"] for s in parsed["sources"]}
        assert "sales" in names
        assert "users" in names
