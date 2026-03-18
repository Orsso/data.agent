"""Tests for core/project_manager.py — _reconstruct_profile."""

from core.project_manager import _reconstruct_profile
from core.state import DataProfile


class TestReconstructProfile:
    def test_full_dict(self):
        # INTENTION: Verify dict with all fields reconstructs to DataProfile correctly
        # FALSIFIABILITÉ: Would fail if any field mapping is wrong
        d = {
            "row_count": 100,
            "columns": [
                {
                    "name": "price",
                    "dtype": "object",
                    "format": "currency",
                    "nulls_pct": 5.0,
                    "cardinality": 50,
                    "sample_values": ["$100", "$200", "$300"],
                },
                {
                    "name": "id",
                    "dtype": "int64",
                    "format": None,
                    "nulls_pct": 0.0,
                    "cardinality": 100,
                    "sample_values": ["1", "2", "3"],
                },
            ],
        }
        profile = _reconstruct_profile(d)
        assert isinstance(profile, DataProfile)
        assert profile.row_count == 100
        assert len(profile.columns) == 2
        assert profile.columns[0].name == "price"
        assert profile.columns[0].format == "currency"
        assert profile.columns[0].nulls_pct == 5.0
        assert profile.columns[1].name == "id"

    def test_missing_optional_fields(self):
        # INTENTION: Verify missing format, nulls_pct, cardinality, sample_values use defaults
        # FALSIFIABILITÉ: Would fail if .get() defaults are wrong
        d = {
            "row_count": 50,
            "columns": [
                {"name": "col1", "dtype": "int64"},
            ],
        }
        profile = _reconstruct_profile(d)
        col = profile.columns[0]
        assert col.format is None
        assert col.nulls_pct == 0.0
        assert col.cardinality == 0
        assert col.sample_values == []

    def test_empty_columns(self):
        # INTENTION: Verify empty columns list produces DataProfile with no columns
        # FALSIFIABILITÉ: Would fail if empty list is rejected
        d = {"row_count": 0, "columns": []}
        profile = _reconstruct_profile(d)
        assert profile.columns == []
        assert profile.row_count == 0

    def test_missing_row_count(self):
        # INTENTION: Verify missing row_count defaults to 0
        # FALSIFIABILITÉ: Would fail if .get("row_count", 0) is removed
        d = {"columns": []}
        profile = _reconstruct_profile(d)
        assert profile.row_count == 0
