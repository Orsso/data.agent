"""Integration tests for the chats API router."""


class TestChatsRouter:
    async def _create_project(self, client) -> str:
        res = await client.post("/api/projects", json={"name": "Chat Project"})
        return res.json()["id"]

    async def test_create_chat(self, client):
        pid = await self._create_project(client)
        res = await client.post(f"/api/projects/{pid}/chats", json={"title": "My Chat"})
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "My Chat"
        assert data["project_id"] == pid

    async def test_create_chat_no_body(self, client):
        pid = await self._create_project(client)
        res = await client.post(f"/api/projects/{pid}/chats")
        assert res.status_code == 201
        assert res.json()["title"] is None

    async def test_list_chats(self, client):
        pid = await self._create_project(client)
        await client.post(f"/api/projects/{pid}/chats", json={"title": "A"})
        await client.post(f"/api/projects/{pid}/chats", json={"title": "B"})
        res = await client.get(f"/api/projects/{pid}/chats")
        assert res.status_code == 200
        titles = {c["title"] for c in res.json()}
        assert {"A", "B"}.issubset(titles)

    async def test_get_chat(self, client):
        pid = await self._create_project(client)
        create = await client.post(f"/api/projects/{pid}/chats", json={"title": "Fetch"})
        cid = create.json()["id"]
        res = await client.get(f"/api/projects/{pid}/chats/{cid}")
        assert res.status_code == 200
        assert res.json()["title"] == "Fetch"

    async def test_get_chat_not_found(self, client):
        pid = await self._create_project(client)
        res = await client.get(f"/api/projects/{pid}/chats/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404

    async def test_rename_chat(self, client):
        pid = await self._create_project(client)
        create = await client.post(f"/api/projects/{pid}/chats", json={"title": "Old"})
        cid = create.json()["id"]
        res = await client.patch(f"/api/projects/{pid}/chats/{cid}", json={"title": "New"})
        assert res.status_code == 200
        assert res.json()["title"] == "New"

    async def test_delete_chat(self, client):
        pid = await self._create_project(client)
        create = await client.post(f"/api/projects/{pid}/chats", json={"title": "Temp"})
        cid = create.json()["id"]
        res = await client.delete(f"/api/projects/{pid}/chats/{cid}")
        assert res.status_code == 200
        assert res.json()["deleted"] is True

        res = await client.get(f"/api/projects/{pid}/chats/{cid}")
        assert res.status_code == 404

    async def test_cross_project_chat_not_found(self, client):
        """A chat from project A should not be accessible from project B."""
        pid_a = await self._create_project(client)
        pid_b_res = await client.post("/api/projects", json={"name": "Other"})
        pid_b = pid_b_res.json()["id"]

        create = await client.post(f"/api/projects/{pid_a}/chats", json={"title": "Owned by A"})
        cid = create.json()["id"]

        res = await client.get(f"/api/projects/{pid_b}/chats/{cid}")
        assert res.status_code == 404
