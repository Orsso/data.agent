"""Tests for api/deps.py — FastAPI dependency injection."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.deps import get_project_manager, require_chat, require_project

# ── get_project_manager ──────────────────────────────────────────────────


class TestGetProjectManager:
    def test_returns_from_app_state(self):
        # INTENTION: Verify get_project_manager returns request.app.state.project_manager
        # FALSIFIABILITÉ: Would fail if attribute access is wrong
        pm = MagicMock()
        request = MagicMock()
        request.app.state.project_manager = pm
        assert get_project_manager(request) is pm


# ── require_project ──────────────────────────────────────────────────────


class TestRequireProject:
    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_400(self):
        # INTENTION: Verify non-UUID string raises HTTPException(400)
        # FALSIFIABILITÉ: Would fail if UUID validation is removed
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await require_project("not-a-uuid", db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("api.deps.ProjectRepository")
    async def test_not_found_raises_404(self, MockRepo):
        # INTENTION: Verify valid UUID but missing row raises HTTPException(404)
        # FALSIFIABILITÉ: Would fail if None check is removed
        instance = MockRepo.return_value
        instance.get = AsyncMock(return_value=None)
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await require_project(str(uuid4()), db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("api.deps.ProjectRepository")
    async def test_success(self, MockRepo):
        # INTENTION: Verify valid UUID + existing row returns the row
        # FALSIFIABILITÉ: Would fail if return value is wrong
        row = SimpleNamespace(id=uuid4(), name="Test")
        instance = MockRepo.return_value
        instance.get = AsyncMock(return_value=row)
        db = AsyncMock()
        result = await require_project(str(row.id), db)
        assert result is row


# ── require_chat ─────────────────────────────────────────────────────────


class TestRequireChat:
    @pytest.mark.asyncio
    async def test_invalid_project_id_raises_400(self):
        # INTENTION: Verify invalid project UUID raises 400
        # FALSIFIABILITÉ: Would fail if project validation is skipped
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await require_chat("bad-uuid", str(uuid4()), db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("api.deps.ProjectRepository")
    async def test_invalid_chat_id_raises_400(self, MockProjectRepo):
        # INTENTION: Verify valid project but invalid chat UUID raises 400
        # FALSIFIABILITÉ: Would fail if chat UUID validation is skipped
        project_id = uuid4()
        row = SimpleNamespace(id=project_id, name="Test")
        instance = MockProjectRepo.return_value
        instance.get = AsyncMock(return_value=row)
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await require_chat(str(project_id), "bad-uuid", db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @patch("api.deps.ChatRepository")
    @patch("api.deps.ProjectRepository")
    async def test_chat_not_found_raises_404(self, MockProjectRepo, MockChatRepo):
        # INTENTION: Verify chat not in DB raises 404
        # FALSIFIABILITÉ: Would fail if None check is removed
        project_id = uuid4()
        project_row = SimpleNamespace(id=project_id, name="Test")
        MockProjectRepo.return_value.get = AsyncMock(return_value=project_row)
        MockChatRepo.return_value.get = AsyncMock(return_value=None)
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await require_chat(str(project_id), str(uuid4()), db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("api.deps.ChatRepository")
    @patch("api.deps.ProjectRepository")
    async def test_chat_wrong_project_raises_404(self, MockProjectRepo, MockChatRepo):
        # INTENTION: Verify chat existing but belonging to different project raises 404
        # FALSIFIABILITÉ: Would fail if project_id check is removed
        project_id = uuid4()
        other_project_id = uuid4()
        project_row = SimpleNamespace(id=project_id, name="Test")
        chat_row = SimpleNamespace(id=uuid4(), project_id=other_project_id, title="Chat")
        MockProjectRepo.return_value.get = AsyncMock(return_value=project_row)
        MockChatRepo.return_value.get = AsyncMock(return_value=chat_row)
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await require_chat(str(project_id), str(chat_row.id), db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("api.deps.ChatRepository")
    @patch("api.deps.ProjectRepository")
    async def test_success(self, MockProjectRepo, MockChatRepo):
        # INTENTION: Verify returns (project_row, chat_row) tuple
        # FALSIFIABILITÉ: Would fail if return format differs
        project_id = uuid4()
        project_row = SimpleNamespace(id=project_id, name="Test")
        chat_row = SimpleNamespace(id=uuid4(), project_id=project_id, title="Chat")
        MockProjectRepo.return_value.get = AsyncMock(return_value=project_row)
        MockChatRepo.return_value.get = AsyncMock(return_value=chat_row)
        db = AsyncMock()
        result = await require_chat(str(project_id), str(chat_row.id), db)
        assert result == (project_row, chat_row)
