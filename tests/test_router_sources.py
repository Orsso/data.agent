"""Integration tests for the sources API router.

Note: upload tests are limited because the source router interacts with
ProjectManager/SandboxManager at runtime. We test the DB-facing paths
(list, delete) and validate error handling on the upload path.
"""


class TestSourcesRouter:
    async def _create_project(self, client) -> str:
        res = await client.post("/api/projects", json={"name": "Src Project"})
        return res.json()["id"]

    async def test_list_sources_empty(self, client):
        pid = await self._create_project(client)
        res = await client.get(f"/api/projects/{pid}/sources")
        assert res.status_code == 200
        assert res.json() == []

    async def test_upload_rejects_non_csv(self, client):
        pid = await self._create_project(client)
        res = await client.post(
            f"/api/projects/{pid}/sources",
            files={"file": ("data.txt", b"hello", "text/plain")},
        )
        assert res.status_code == 400

    async def test_upload_rejects_malformed_csv(self, client):
        pid = await self._create_project(client)
        # Non-UTF-8 binary that triggers UnicodeDecodeError in pd.read_csv
        res = await client.post(
            f"/api/projects/{pid}/sources",
            files={"file": ("bad.csv", b"\x80\x81\x82" * 100, "text/csv")},
        )
        assert res.status_code == 400

    async def test_delete_source_not_found(self, client):
        pid = await self._create_project(client)
        res = await client.delete(f"/api/projects/{pid}/sources/nonexistent")
        assert res.status_code == 404
