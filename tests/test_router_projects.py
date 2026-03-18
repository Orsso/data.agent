"""Integration tests for the projects API router."""

from unittest.mock import AsyncMock

from api.deps import get_project_manager


class TestProjectsRouter:
    async def test_create_project(self, client):
        res = await client.post("/api/projects", json={"name": "Test Project"})
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Test Project"
        assert data["status"] == "created"
        assert data["id"]

    async def test_list_projects(self, client):
        await client.post("/api/projects", json={"name": "P1"})
        await client.post("/api/projects", json={"name": "P2"})
        res = await client.get("/api/projects")
        assert res.status_code == 200
        names = {p["name"] for p in res.json()["projects"]}
        assert {"P1", "P2"}.issubset(names)

    async def test_get_project(self, client):
        create = await client.post("/api/projects", json={"name": "Fetch Me"})
        pid = create.json()["id"]
        res = await client.get(f"/api/projects/{pid}")
        assert res.status_code == 200
        assert res.json()["name"] == "Fetch Me"

    async def test_get_project_not_found(self, client):
        res = await client.get("/api/projects/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404

    async def test_get_project_invalid_uuid(self, client):
        res = await client.get("/api/projects/not-a-uuid")
        assert res.status_code == 400

    async def test_update_project(self, client):
        create = await client.post("/api/projects", json={"name": "Before"})
        pid = create.json()["id"]
        res = await client.patch(f"/api/projects/{pid}", json={"name": "After"})
        assert res.status_code == 200
        assert res.json()["name"] == "After"

    async def test_delete_project(self, client):
        from api.main import app

        mock_pm = AsyncMock()
        app.dependency_overrides[get_project_manager] = lambda: mock_pm
        try:
            create = await client.post("/api/projects", json={"name": "Doomed"})
            pid = create.json()["id"]
            res = await client.delete(f"/api/projects/{pid}")
            assert res.status_code == 200
            assert res.json()["deleted"] is True
            mock_pm.remove.assert_awaited_once_with(pid)

            res = await client.get(f"/api/projects/{pid}")
            assert res.status_code == 404
        finally:
            app.dependency_overrides.pop(get_project_manager, None)
