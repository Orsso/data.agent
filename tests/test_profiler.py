"""Tests for core/profiler.py — pure data profiling functions."""

import pandas as pd

from core.profiler import _detect_format, _profile_column, build_profile, format_profile
from core.state import ColumnProfile, DataProfile

# ── build_profile ──────────────────────────────────────────────────────────


class TestBuildProfile:
    def test_row_count(self, sample_df):
        # INTENTION: Verify build_profile returns the correct row count
        # FALSIFIABILITÉ: Would fail if row_count != len(df)
        profile = build_profile(sample_df)
        assert profile.row_count == len(sample_df) == 10

    def test_column_count(self, sample_df):
        # INTENTION: Verify one ColumnProfile is produced per DataFrame column
        # FALSIFIABILITÉ: Would fail if some columns are skipped or duplicated
        profile = build_profile(sample_df)
        assert len(profile.columns) == len(sample_df.columns) == 8

    def test_column_names_match(self, sample_df):
        # INTENTION: Verify column names in profile match DataFrame column names
        # FALSIFIABILITÉ: Would fail if column naming is incorrect
        profile = build_profile(sample_df)
        profile_names = [col.name for col in profile.columns]
        assert profile_names == list(sample_df.columns)


# ── _profile_column ───────────────────────────────────────────────────────


class TestProfileColumn:
    def test_dtype(self):
        # INTENTION: Verify _profile_column captures str(series.dtype)
        # FALSIFIABILITÉ: Would fail if dtype is transformed or wrong
        series = pd.Series([1, 2, 3], name="nums")
        col = _profile_column(series)
        assert col.dtype == "int64"

    def test_nulls_pct(self):
        # INTENTION: Verify null percentage is correctly computed
        # FALSIFIABILITÉ: Would fail if mean/round math is wrong (expected 50.0 for 2/4 nulls)
        series = pd.Series([1.0, None, 3.0, None], name="x")
        col = _profile_column(series)
        assert col.nulls_pct == 50.0

    def test_nulls_pct_zero(self):
        # INTENTION: Verify 0% nulls for a column with no nulls
        # FALSIFIABILITÉ: Would fail if null detection is wrong
        series = pd.Series([1, 2, 3], name="x")
        col = _profile_column(series)
        assert col.nulls_pct == 0.0

    def test_cardinality(self):
        # INTENTION: Verify cardinality equals nunique()
        # FALSIFIABILITÉ: Would fail if wrong counting method is used
        series = pd.Series(["a", "b", "a", "c"], name="x")
        col = _profile_column(series)
        assert col.cardinality == 3

    def test_sample_values_are_strings(self):
        # INTENTION: Verify top-3 value_counts entries are returned as strings
        # FALSIFIABILITÉ: Would fail if values are not str-converted or count differs
        series = pd.Series([10, 20, 20, 30, 30, 30], name="x")
        col = _profile_column(series)
        assert all(isinstance(v, str) for v in col.sample_values)
        assert len(col.sample_values) <= 3

    def test_sample_values_order(self):
        # INTENTION: Verify sample values are ordered by frequency (most common first)
        # FALSIFIABILITÉ: Would fail if value_counts ordering is lost
        series = pd.Series(["rare", "common", "common", "common", "mid", "mid"], name="x")
        col = _profile_column(series)
        assert col.sample_values[0] == "common"


# ── _detect_format ────────────────────────────────────────────────────────
# NOTE: In pandas 3.x (Python 3.13), the default string dtype is "str", not
# "object". The _detect_format function checks `series.dtype != "object"` as
# its first guard. This means format detection is BROKEN for default string
# columns in pandas 3.x. See BUGLOG.md for details.
#
# Tests below use dtype="object" explicitly to exercise the detection logic
# independently of this dtype bug.


class TestDetectFormat:
    def test_default_string_dtype_is_detected(self):
        # INTENTION: Verify format detection works with pandas 3.x default "str" dtype
        # FALSIFIABILITÉ: Would fail if dtype guard rejects non-"object" strings
        series = pd.Series(["$100", "$200", "$300", "$400"], name="x")
        # In pandas 3.x, dtype is "str" not "object" — both must be accepted
        assert _detect_format(series) == "currency"

    def test_currency(self):
        # INTENTION: Verify >50% currency-like values are detected
        # FALSIFIABILITÉ: Would fail if regex or threshold is wrong
        series = pd.Series(
            ["$1,234", "$56", "€789", "text", "$100", "$200"],
            dtype="object",
            name="x",
        )
        assert _detect_format(series) == "currency"

    def test_currency_below_threshold(self):
        # INTENTION: Verify exactly 50% currency does NOT trigger (strict >0.5)
        # FALSIFIABILITÉ: Would fail if threshold is >= instead of >
        series = pd.Series(["$100", "text"], dtype="object", name="x")
        assert _detect_format(series) != "currency"

    def test_percentage(self):
        # INTENTION: Verify >50% percentage values are detected
        # FALSIFIABILITÉ: Would fail if endswith check or threshold is wrong
        series = pd.Series(["10%", "20%", "30%", "text"], dtype="object", name="x")
        assert _detect_format(series) == "percentage"

    def test_pipe_separated(self):
        # INTENTION: Verify >30% pipe-containing values are detected
        # FALSIFIABILITÉ: Would fail if pipe check or 0.3 threshold is wrong
        series = pd.Series(["A|B", "C|D", "plain", "plain", "plain"], dtype="object", name="x")
        assert _detect_format(series) == "pipe_separated"

    def test_numeric_string(self):
        # INTENTION: Verify >80% numeric-coercible strings are detected
        # FALSIFIABILITÉ: Would fail if to_numeric coercion or 0.8 threshold is wrong
        series = pd.Series(["42", "87", "15", "93", "text"], dtype="object", name="x")
        # 4/5 = 0.8 — NOT > 0.8
        assert _detect_format(series) != "numeric_string"

        series_high = pd.Series(["42", "87", "15", "93", "66", "text"], dtype="object", name="x")
        # 5/6 ≈ 0.833 > 0.8
        assert _detect_format(series_high) == "numeric_string"

    def test_date_string(self):
        # INTENTION: Verify >50% date-parseable strings are detected
        # FALSIFIABILITÉ: Would fail if to_datetime parsing or threshold is wrong
        series = pd.Series(
            ["2024-01-15", "2024-02-20", "2024-03-10", "text"],
            dtype="object",
            name="x",
        )
        assert _detect_format(series) == "date_string"

    def test_non_object_dtype_returns_none(self):
        # INTENTION: Verify non-object columns skip format detection
        # FALSIFIABILITÉ: Would fail if dtype check at start is removed
        series = pd.Series([1, 2, 3], name="x")
        assert _detect_format(series) is None

    def test_all_nulls_returns_none(self):
        # INTENTION: Verify all-NaN object column returns None without division error
        # FALSIFIABILITÉ: Would fail if len(non_null)==0 check is missing
        series = pd.Series([None, None, None], dtype="object", name="x")
        assert _detect_format(series) is None

    def test_priority_currency_over_numeric(self):
        # INTENTION: "$100" matches both currency regex and numeric coercion;
        #   currency is checked first so it should win
        # FALSIFIABILITÉ: Would fail if detection order changes
        series = pd.Series(
            ["$100", "$200", "$300", "$400", "$500"],
            dtype="object",
            name="x",
        )
        assert _detect_format(series) == "currency"


# ── format_profile ────────────────────────────────────────────────────────


class TestFormatProfile:
    def test_output_starts_with_header(self, sample_profile):
        # INTENTION: Verify format_profile output starts with "Column profiles:"
        # FALSIFIABILITÉ: Would fail if header text changes
        text = format_profile(sample_profile)
        assert text.startswith("Column profiles:")

    def test_each_column_has_line(self, sample_profile):
        # INTENTION: Verify each column gets a "- name:" line in output
        # FALSIFIABILITÉ: Would fail if a column is missing from output
        text = format_profile(sample_profile)
        for col in sample_profile.columns:
            assert f"- {col.name}:" in text

    def test_format_hint_displayed(self):
        # INTENTION: Verify columns with a known format get the warning emoji hint
        # FALSIFIABILITÉ: Would fail if _FORMAT_HINTS lookup or emoji line is broken
        profile = DataProfile(
            row_count=5,
            columns=[
                ColumnProfile("price", "object", "currency", 0.0, 5, ["$100"]),
            ],
        )
        text = format_profile(profile)
        assert "⚠" in text
        assert "currency" in text.lower() or "strip currency" in text

    def test_no_hint_without_format(self):
        # INTENTION: Verify columns with format=None do not get the warning line
        # FALSIFIABILITÉ: Would fail if hint is unconditionally added
        profile = DataProfile(
            row_count=5,
            columns=[
                ColumnProfile("id", "int64", None, 0.0, 5, ["1", "2", "3"]),
            ],
        )
        text = format_profile(profile)
        assert "⚠" not in text
