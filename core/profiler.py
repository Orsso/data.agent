import re

import pandas as pd

from core.state import ColumnProfile, DataProfile

SAMPLE_SIZE = 100
CURRENCY_RE = re.compile(r"^[₹$€£¥]\s?[\d,.]+")

_FORMAT_HINTS = {
    "currency": "strip currency symbols and commas before numeric ops: .str.replace('[₹$€£¥,]', '', regex=True).astype(float)",
    "percentage": "strip '%' before numeric ops: .str.rstrip('%').astype(float)",
    "pipe_separated": "multi-valued, split with .str.split('|').explode() before grouping",
    "numeric_string": "stored as text but numeric, convert: pd.to_numeric(col, errors='coerce')",
    "date_string": "stored as text but date, convert: pd.to_datetime(col, format='mixed')",
}


def build_profile(df: pd.DataFrame) -> DataProfile:
    columns = [_profile_column(df[col]) for col in df.columns]
    return DataProfile(row_count=len(df), columns=columns)


def format_profile(profile: DataProfile) -> str:
    lines = ["Column profiles:"]
    for col in profile.columns:
        parts = [f"- {col.name}: {col.dtype}"]
        inner = []
        if col.format:
            inner.append(col.format)
        inner.append(f"{col.nulls_pct}% nulls")
        inner.append(f"{col.cardinality} unique")
        parts.append(f" ({', '.join(inner)})")
        if col.sample_values:
            quoted = [f'"{v}"' for v in col.sample_values]
            parts.append(f" - e.g. {', '.join(quoted)}")
        if col.format and col.format in _FORMAT_HINTS:
            parts.append(f"\n  ⚠ {_FORMAT_HINTS[col.format]}")
        lines.append("".join(parts))
    return "\n".join(lines)


def _profile_column(series: pd.Series) -> ColumnProfile:
    dtype = str(series.dtype)
    nulls_pct = round(series.isna().mean() * 100, 1)
    cardinality = series.nunique()
    top_values = series.value_counts().head(3).index.tolist()
    sample_values = [str(v) for v in top_values]
    fmt = _detect_format(series)
    return ColumnProfile(
        name=series.name,
        dtype=dtype,
        format=fmt,
        nulls_pct=nulls_pct,
        cardinality=cardinality,
        sample_values=sample_values,
    )


def _detect_format(series: pd.Series) -> str | None:
    if series.dtype != "object":
        return None
    non_null = series.dropna()
    if len(non_null) == 0:
        return None
    sample = non_null.sample(n=min(SAMPLE_SIZE, len(non_null)), random_state=42).astype(str)
    n = len(sample)

    currency_count = sum(1 for v in sample if CURRENCY_RE.match(v))
    if currency_count / n > 0.5:
        return "currency"

    pct_count = sum(1 for v in sample if v.strip().endswith("%"))
    if pct_count / n > 0.5:
        return "percentage"

    pipe_count = sum(1 for v in sample if "|" in v)
    if pipe_count / n > 0.3:
        return "pipe_separated"

    coerced = pd.to_numeric(sample, errors="coerce")
    if coerced.notna().sum() / n > 0.8:
        return "numeric_string"

    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    if parsed.notna().sum() / n > 0.5:
        return "date_string"

    return None
