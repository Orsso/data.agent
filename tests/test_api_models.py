"""Tests for api/models.py — Pydantic schemas and converter functions."""

from uuid import uuid4

from api.models import (
    AddDashboardCardRequest,
    CreateProjectRequest,
    MessageRequest,
    card_response,
    chat_response,
    project_response,
    source_response,
)
from tests.conftest import make_card_row, make_chat_row, make_project_row, make_source_row

# ── Request model defaults ────────────────────────────────────────────────


class TestRequestDefaults:
    def test_create_project_model_default(self):
        # INTENTION: Verify CreateProjectRequest.model defaults to None
        # FALSIFIABILITÉ: Would fail if default changes
        req = CreateProjectRequest(name="Test")
        assert req.model is None

    def test_message_request_selected_cards_default(self):
        # INTENTION: Verify selected_card_ids defaults to None
        # FALSIFIABILITÉ: Would fail if it's required
        req = MessageRequest(message="Hello")
        assert req.selected_card_ids is None

    def test_add_dashboard_card_optional_fields(self):
        # INTENTION: Verify code, value, fig default to None
        # FALSIFIABILITÉ: Would fail if any is required
        req = AddDashboardCardRequest(type="metric", title="Revenue")
        assert req.code is None
        assert req.value is None
        assert req.fig is None


# ── source_response ──────────────────────────────────────────────────────


class TestSourceResponse:
    def test_maps_all_fields(self):
        # INTENTION: Verify source_response maps row attributes to response fields
        # FALSIFIABILITÉ: Would fail if a field mapping is wrong
        row = make_source_row()
        resp = source_response(row)
        assert resp.id == str(row.id)
        assert resp.name == row.name
        assert resp.origin == row.origin
        assert resp.row_count == row.row_count
        assert resp.columns == row.columns
        assert resp.created_at == row.created_at


# ── project_response ─────────────────────────────────────────────────────


class TestProjectResponse:
    def test_maps_all_fields(self):
        # INTENTION: Verify project_response maps all row attributes correctly
        # FALSIFIABILITÉ: Would fail if a field mapping is wrong
        source = make_source_row()
        chat = make_chat_row()
        row = make_project_row(sources=[source], chats=[chat, chat])
        resp = project_response(row)
        assert resp.id == str(row.id)
        assert resp.name == row.name
        assert resp.chat_count == 2
        assert len(resp.sources) == 1

    def test_suggested_questions_none_becomes_empty(self):
        # INTENTION: Verify suggested_questions=None is replaced by []
        # FALSIFIABILITÉ: Would fail if `or []` is removed from project_response
        row = make_project_row(suggested_questions=None)
        resp = project_response(row)
        assert resp.suggested_questions == []

    def test_suggested_questions_preserved(self):
        # INTENTION: Verify existing questions are passed through
        # FALSIFIABILITÉ: Would fail if questions are always overwritten
        row = make_project_row(suggested_questions=["Q1", "Q2"])
        resp = project_response(row)
        assert resp.suggested_questions == ["Q1", "Q2"]


# ── chat_response ────────────────────────────────────────────────────────


class TestChatResponse:
    def test_maps_all_fields(self):
        # INTENTION: Verify chat_response maps row attributes correctly
        # FALSIFIABILITÉ: Would fail if field mapping is wrong
        pid = uuid4()
        row = make_chat_row(project_id=pid, title="My Chat")
        resp = chat_response(row)
        assert resp.id == str(row.id)
        assert resp.project_id == str(pid)
        assert resp.title == "My Chat"
        assert resp.pending_questions == row.pending_questions
        assert resp.created_at == row.created_at


# ── card_response ────────────────────────────────────────────────────────


class TestCardResponse:
    def test_maps_all_fields(self):
        # INTENTION: Verify card_response maps all fields including content, layout, position
        # FALSIFIABILITÉ: Would fail if any field mapping is wrong
        row = make_card_row(content=[{"type": "text"}], layout={"x": 0, "y": 0}, position=3)
        resp = card_response(row)
        assert resp.id == str(row.id)
        assert resp.type == row.type
        assert resp.title == row.title
        assert resp.code == row.code
        assert resp.value == row.value
        assert resp.fig == row.fig
        assert resp.content == [{"type": "text"}]
        assert resp.layout == {"x": 0, "y": 0}
        assert resp.position == 3

    def test_nullable_fields(self):
        # INTENTION: Verify code, value, fig, content, layout can all be None
        # FALSIFIABILITÉ: Would fail if Pydantic validation rejects None
        row = make_card_row(code=None, value=None, fig=None, content=None, layout=None)
        resp = card_response(row)
        assert resp.code is None
        assert resp.value is None
        assert resp.fig is None
        assert resp.content is None
        assert resp.layout is None
