"""Integration tests for the 5 database repositories against real PostgreSQL."""

import uuid

import pytest

from db.repositories.chats import ChatRepository
from db.repositories.dashboard_cards import DashboardCardRepository
from db.repositories.messages import MessageRepository
from db.repositories.projects import ProjectRepository
from db.repositories.sources import SourceRepository

# ── ProjectRepository ──────────────────────────────────────────────────


class TestProjectRepository:
    async def test_create_and_get(self, db_session):
        repo = ProjectRepository(db_session)
        row = await repo.create(name="My Project", model="gemini-3-flash-preview")
        assert row.id is not None
        assert row.name == "My Project"
        assert row.status == "created"

        fetched = await repo.get(row.id)
        assert fetched is not None
        assert fetched.name == "My Project"
        assert fetched.sources == []
        assert fetched.chats == []

    async def test_list_all(self, db_session):
        repo = ProjectRepository(db_session)
        await repo.create(name="A")
        await repo.create(name="B")
        rows = await repo.list_all()
        names = {r.name for r in rows}
        assert {"A", "B"}.issubset(names)

    async def test_update_partial(self, db_session):
        repo = ProjectRepository(db_session)
        row = await repo.create(name="Original")
        updated = await repo.update(row.id, description="New desc")
        assert updated.description == "New desc"
        assert updated.name == "Original"

    async def test_update_ignores_unknown_fields(self, db_session):
        repo = ProjectRepository(db_session)
        row = await repo.create(name="Test")
        updated = await repo.update(row.id, nonexistent_field="ignored")
        assert updated.name == "Test"

    async def test_dashboard_content(self, db_session):
        repo = ProjectRepository(db_session)
        row = await repo.create(name="Dashboard Test")
        content = [{"type": "paragraph", "content": "Hello"}]
        await repo.save_dashboard_content(row.id, content)
        result = await repo.get_dashboard_content(row.id)
        assert result == content

    async def test_delete(self, db_session):
        repo = ProjectRepository(db_session)
        row = await repo.create(name="To Delete")
        assert await repo.delete(row.id) is True
        assert await repo.get(row.id) is None

    async def test_delete_nonexistent(self, db_session):
        repo = ProjectRepository(db_session)
        assert await repo.delete(uuid.uuid4()) is False

    async def test_get_nonexistent(self, db_session):
        repo = ProjectRepository(db_session)
        assert await repo.get(uuid.uuid4()) is None

    async def test_eager_loads_sources_and_chats(self, db_session):
        proj_repo = ProjectRepository(db_session)
        project = await proj_repo.create(name="Eager Test")
        await SourceRepository(db_session).create(
            project_id=project.id,
            name="s1",
            origin="csv",
            row_count=10,
            columns=["a", "b"],
        )
        await ChatRepository(db_session).create(project_id=project.id, title="c1")

        fetched = await proj_repo.get(project.id)
        assert len(fetched.sources) == 1
        assert len(fetched.chats) == 1


# ── SourceRepository ───────────────────────────────────────────────────


class TestSourceRepository:
    async def test_create_and_list(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = SourceRepository(db_session)
        s = await repo.create(
            project_id=proj.id,
            name="sales",
            origin="csv",
            row_count=100,
            columns=["id", "price"],
            profile={"row_count": 100, "columns": []},
        )
        assert s.name == "sales"
        rows = await repo.list_by_project(proj.id)
        assert len(rows) == 1

    async def test_get_by_name(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = SourceRepository(db_session)
        await repo.create(
            project_id=proj.id, name="orders", origin="csv", row_count=50, columns=["x"]
        )
        found = await repo.get_by_name(proj.id, "orders")
        assert found is not None
        assert found.row_count == 50
        assert await repo.get_by_name(proj.id, "nonexistent") is None

    async def test_delete(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = SourceRepository(db_session)
        await repo.create(project_id=proj.id, name="tmp", origin="csv", row_count=1, columns=["a"])
        assert await repo.delete(proj.id, "tmp") is True
        assert await repo.delete(proj.id, "tmp") is False

    async def test_unique_constraint(self, db_session):
        """Two sources with the same (project_id, name) should violate the unique constraint."""
        from sqlalchemy.exc import IntegrityError

        proj = await ProjectRepository(db_session).create(name="P")
        repo = SourceRepository(db_session)
        await repo.create(project_id=proj.id, name="dup", origin="csv", row_count=1, columns=["a"])
        with pytest.raises(IntegrityError):
            await repo.create(
                project_id=proj.id, name="dup", origin="csv", row_count=2, columns=["b"]
            )


# ── ChatRepository ─────────────────────────────────────────────────────


class TestChatRepository:
    async def test_crud(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = ChatRepository(db_session)
        chat = await repo.create(project_id=proj.id, title="Hello")
        assert chat.title == "Hello"

        fetched = await repo.get(chat.id)
        assert fetched is not None
        assert fetched.title == "Hello"

        updated = await repo.update_title(chat.id, "Renamed")
        assert updated.title == "Renamed"

        chats = await repo.list_by_project(proj.id)
        assert len(chats) == 1

        assert await repo.delete(chat.id) is True
        assert await repo.get(chat.id) is None

    async def test_pending_questions(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = ChatRepository(db_session)
        chat = await repo.create(project_id=proj.id)
        questions = [{"question": "Which column?", "options": ["a", "b"]}]
        await repo.update_pending_questions(chat.id, questions)
        fetched = await repo.get(chat.id)
        assert fetched.pending_questions == questions

        await repo.update_pending_questions(chat.id, None)
        fetched = await repo.get(chat.id)
        assert fetched.pending_questions is None


# ── MessageRepository ──────────────────────────────────────────────────


class TestMessageRepository:
    async def test_create_and_list(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        chat = await ChatRepository(db_session).create(project_id=proj.id)
        repo = MessageRepository(db_session)

        msg = await repo.create(chat_id=chat.id, role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

        msgs = await repo.list_by_chat(chat.id)
        assert len(msgs) == 1

    async def test_find_by_proposal(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        chat = await ChatRepository(db_session).create(project_id=proj.id)
        repo = MessageRepository(db_session)

        proposal_id = "prop-123"
        await repo.create(
            chat_id=chat.id,
            role="assistant",
            content="Here's a proposal",
            proposals=[{"proposal_id": proposal_id, "card_id": "c1", "status": "pending"}],
        )

        found = await repo.find_by_proposal(chat.id, proposal_id)
        assert found is not None
        assert found.proposals[0]["proposal_id"] == proposal_id

        assert await repo.find_by_proposal(chat.id, "nonexistent") is None

    async def test_get_figures(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        chat = await ChatRepository(db_session).create(project_id=proj.id)
        repo = MessageRepository(db_session)

        figs = [{"data": [], "layout": {"title": "Test"}}]
        msg = await repo.create(chat_id=chat.id, role="assistant", content="chart", figs=figs)
        result = await repo.get_figures(msg.id)
        assert result == figs


# ── DashboardCardRepository ────────────────────────────────────────────


class TestDashboardCardRepository:
    async def test_replace_all(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = DashboardCardRepository(db_session)

        cards = [
            {"type": "chart", "title": "Chart 1", "code": "px.bar(df)"},
            {"type": "kpi", "title": "KPI 1", "value": "42"},
        ]
        rows = await repo.replace_all(proj.id, cards)
        assert len(rows) == 2
        assert rows[0].position == 0
        assert rows[1].position == 1

        # Replace with new set
        rows2 = await repo.replace_all(proj.id, [{"type": "chart", "title": "Only One"}])
        assert len(rows2) == 1
        all_cards = await repo.list_by_project(proj.id)
        assert len(all_cards) == 1

    async def test_create_card_auto_position(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = DashboardCardRepository(db_session)

        c1 = await repo.create_card(project_id=proj.id, type="chart", title="First")
        assert c1.position == 0
        c2 = await repo.create_card(project_id=proj.id, type="kpi", title="Second")
        assert c2.position == 1

    async def test_update_card(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = DashboardCardRepository(db_session)

        card = await repo.create_card(project_id=proj.id, type="chart", title="Old")
        updated = await repo.update_card(card.id, title="New", code="px.line(df)")
        assert updated.title == "New"
        assert updated.code == "px.line(df)"

    async def test_update_card_nonexistent(self, db_session):
        repo = DashboardCardRepository(db_session)
        assert await repo.update_card(uuid.uuid4(), title="X") is None

    async def test_update_layouts(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = DashboardCardRepository(db_session)

        c1 = await repo.create_card(project_id=proj.id, type="chart", title="A")
        c2 = await repo.create_card(project_id=proj.id, type="kpi", title="B")

        layouts = [
            {"id": str(c1.id), "layout": {"x": 0, "y": 0, "w": 6, "h": 4}},
            {"id": str(c2.id), "layout": {"x": 6, "y": 0, "w": 6, "h": 4}},
        ]
        await repo.update_layouts(proj.id, layouts)

        cards = await repo.list_by_project(proj.id)
        layouts_map = {str(c.id): c.layout for c in cards}
        assert layouts_map[str(c1.id)] == {"x": 0, "y": 0, "w": 6, "h": 4}
        assert layouts_map[str(c2.id)] == {"x": 6, "y": 0, "w": 6, "h": 4}

    async def test_delete_card(self, db_session):
        proj = await ProjectRepository(db_session).create(name="P")
        repo = DashboardCardRepository(db_session)

        card = await repo.create_card(project_id=proj.id, type="chart", title="Gone")
        assert await repo.delete_card(card.id) is True
        assert await repo.delete_card(card.id) is False
