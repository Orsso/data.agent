"""Tests for core/models/sources.py — SourceRegistry."""

from core.models.sources import DataSource, SourceRegistry
from core.state import ColumnProfile, DataProfile


def _make_source(name: str) -> DataSource:
    """Helper to build a minimal DataSource."""
    return DataSource(
        name=name,
        profile=DataProfile(
            row_count=5,
            columns=[
                ColumnProfile("col1", "int64", None, 0.0, 5, ["1", "2", "3"]),
            ],
        ),
        origin="csv",
        row_count=5,
        columns=["col1"],
        sample_text="   col1\n0     1",
    )


# ── SourceRegistry ────────────────────────────────────────────────────────


class TestSourceRegistry:
    def test_empty_registry(self):
        # INTENTION: Verify new registry starts empty
        # FALSIFIABILITÉ: Would fail if initial state is non-empty
        reg = SourceRegistry()
        assert reg.is_empty is True
        assert reg.count == 0
        assert reg.primary is None

    def test_add_sets_primary(self):
        # INTENTION: Verify first added source becomes primary
        # FALSIFIABILITÉ: Would fail if primary logic is wrong
        reg = SourceRegistry()
        reg.add("first", _make_source("first"))
        assert reg.primary is not None
        assert reg.primary.name == "first"
        assert reg.is_empty is False
        assert reg.count == 1

    def test_add_second_keeps_primary(self):
        # INTENTION: Verify adding a second source does not change primary
        # FALSIFIABILITÉ: Would fail if primary is overwritten
        reg = SourceRegistry()
        reg.add("first", _make_source("first"))
        reg.add("second", _make_source("second"))
        assert reg.primary.name == "first"
        assert reg.count == 2

    def test_get_existing(self):
        # INTENTION: Verify get() returns the source by name
        # FALSIFIABILITÉ: Would fail if key lookup is wrong
        reg = SourceRegistry()
        src = _make_source("sales")
        reg.add("sales", src)
        assert reg.get("sales") is src

    def test_get_missing(self):
        # INTENTION: Verify get() returns None for non-existent name
        # FALSIFIABILITÉ: Would fail if KeyError is raised
        reg = SourceRegistry()
        assert reg.get("missing") is None

    def test_get_all_returns_copy(self):
        # INTENTION: Verify get_all() returns a copy, not the internal dict
        # FALSIFIABILITÉ: Would fail if mutating returned dict affects registry
        reg = SourceRegistry()
        reg.add("sales", _make_source("sales"))
        all_sources = reg.get_all()
        all_sources["new"] = _make_source("new")
        assert reg.count == 1  # internal state unchanged

    def test_remove_existing(self):
        # INTENTION: Verify remove() returns True and decreases count
        # FALSIFIABILITÉ: Would fail if delete is broken
        reg = SourceRegistry()
        reg.add("sales", _make_source("sales"))
        assert reg.remove("sales") is True
        assert reg.count == 0
        assert reg.is_empty is True

    def test_remove_missing(self):
        # INTENTION: Verify remove() returns False for non-existent name
        # FALSIFIABILITÉ: Would fail if KeyError is raised
        reg = SourceRegistry()
        assert reg.remove("missing") is False

    def test_remove_primary_promotes_next(self):
        # INTENTION: Verify removing primary promotes the next source
        # FALSIFIABILITÉ: Would fail if promotion logic is wrong
        reg = SourceRegistry()
        reg.add("first", _make_source("first"))
        reg.add("second", _make_source("second"))
        reg.remove("first")
        assert reg.primary is not None
        assert reg.primary.name == "second"

    def test_remove_last_source(self):
        # INTENTION: Verify removing the only source leaves registry empty
        # FALSIFIABILITÉ: Would fail if state is inconsistent
        reg = SourceRegistry()
        reg.add("only", _make_source("only"))
        reg.remove("only")
        assert reg.primary is None
        assert reg.is_empty is True

    def test_combined_context_empty(self):
        # INTENTION: Verify empty registry returns "No data sources loaded."
        # FALSIFIABILITÉ: Would fail if message differs
        reg = SourceRegistry()
        assert reg.combined_context() == "No data sources loaded."

    def test_combined_context_with_sources(self):
        # INTENTION: Verify combined_context includes DataFrame name, row count, columns, profile text
        # FALSIFIABILITÉ: Would fail if any section is missing
        reg = SourceRegistry()
        reg.add("sales", _make_source("sales"))
        ctx = reg.combined_context()
        assert "`sales`" in ctx
        assert "5 rows" in ctx
        assert "col1" in ctx
        assert "Column profiles:" in ctx
