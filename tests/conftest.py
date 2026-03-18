"""Shared fixtures for the backend test suite."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pandas as pd
import pytest

from core.models.sources import DataSource, SourceRegistry
from core.models.turn import TurnState
from core.profiler import build_profile
from core.state import ColumnProfile, DataProfile, LoopResult
from core.tools.context import ToolContext

# ---------------------------------------------------------------------------
# Sample DataFrame — exercises every _detect_format branch
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """DataFrame with mixed column types for profiler tests."""
    return pd.DataFrame(
        {
            "id": list(range(1, 11)),
            "price": [
                "$1,234",
                "$5,678",
                "$900",
                "$12",
                "$3,456",
                "$789",
                "$100",
                "$2,345",
                "$67",
                "$8,901",
            ],
            "discount": ["10%", "20%", "30%", "15%", "25%", "5%", "40%", "35%", "50%", "45%"],
            "tags": ["A|B", "C|D", "E|F", "A|C", "B|D", "A|E", "C|F", "B|E", "D|F", "A|D"],
            "date": [
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-05",
                "2024-05-18",
                "2024-06-22",
                "2024-07-30",
                "2024-08-14",
                "2024-09-01",
                "2024-10-25",
            ],
            "score_str": ["42", "87", "15", "93", "66", "71", "38", "54", "29", "100"],
            "name": [
                "Alice",
                "Bob",
                "Charlie",
                "Diana",
                "Eve",
                "Frank",
                "Grace",
                "Hank",
                "Ivy",
                "Jack",
            ],
            "with_nulls": [1.0, None, 3.0, None, 5.0, None, 7.0, None, 9.0, None],
        }
    )


@pytest.fixture
def sample_profile(sample_df) -> DataProfile:
    return build_profile(sample_df)


@pytest.fixture
def sample_column_profile() -> ColumnProfile:
    return ColumnProfile(
        name="test_col",
        dtype="int64",
        format=None,
        nulls_pct=0.0,
        cardinality=10,
        sample_values=["1", "2", "3"],
    )


@pytest.fixture
def sample_data_source(sample_profile) -> DataSource:
    return DataSource(
        name="sales",
        profile=sample_profile,
        origin="csv",
        row_count=10,
        columns=["id", "price", "discount", "tags", "date", "score_str", "name", "with_nulls"],
        sample_text="   id  price discount tags  ...\n0   1 $1,234      10%  A|B  ...",
    )


@pytest.fixture
def source_registry(sample_data_source) -> SourceRegistry:
    reg = SourceRegistry()
    reg.add("sales", sample_data_source)
    return reg


@pytest.fixture
def turn_state() -> TurnState:
    return TurnState()


@pytest.fixture
def tool_context(source_registry, turn_state) -> ToolContext:
    # Structure matches core/tools/context.py — ToolContext dataclass
    return ToolContext(
        project_id="test-project-id",
        sandbox=AsyncMock(),
        sources=source_registry,
        turn=turn_state,
        todos=[],
    )


@pytest.fixture
def runnable_config(tool_context):
    # Structure matches get_tool_context in core/tools/context.py:21
    # config["configurable"]["tool_context"]
    return {"configurable": {"tool_context": tool_context}}


@pytest.fixture
def sample_loop_result() -> LoopResult:
    return LoopResult(
        content="Analysis complete.",
        figs=[{"data": [], "layout": {}}],
        code="import pandas as pd\ndf.describe()",
    )


# ---------------------------------------------------------------------------
# Row factories — mimic SQLAlchemy model attributes from db/models.py
# ---------------------------------------------------------------------------


def make_project_row(**overrides):
    """Factory for a mock ProjectRow (db/models.py)."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "name": "Test Project",
        "description": "A test project",
        "status": "ready",
        "model": "gemini-3-flash-preview",
        "suggested_questions": ["What trends?", "Show distribution"],
        "dashboard_content": None,
        "sources": [],
        "chats": [],
        "dashboard_cards": [],
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_source_row(**overrides):
    """Factory for a mock SourceRow (db/models.py)."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "name": "sales",
        "origin": "csv",
        "row_count": 100,
        "columns": ["id", "price", "name"],
        "profile": {"row_count": 100, "columns": []},
        "created_at": now,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_chat_row(**overrides):
    """Factory for a mock ChatRow (db/models.py)."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "title": "Test Chat",
        "pending_questions": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_card_row(**overrides):
    """Factory for a mock DashboardCardRow (db/models.py)."""
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "type": "chart",
        "title": "Revenue Chart",
        "code": "fig = px.bar(df, x='month', y='revenue')",
        "value": None,
        "fig": {"data": [], "layout": {}},
        "content": None,
        "layout": None,
        "position": 0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)
