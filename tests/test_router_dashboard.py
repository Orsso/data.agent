"""Integration tests for the dashboard API router."""


class TestDashboardRouter:
    async def _create_project(self, client) -> str:
        res = await client.post("/api/projects", json={"name": "Dashboard Project"})
        return res.json()["id"]

    async def test_list_cards_empty(self, client):
        pid = await self._create_project(client)
        res = await client.get(f"/api/projects/{pid}/dashboard-cards")
        assert res.status_code == 200
        assert res.json() == []

    async def test_add_card(self, client):
        pid = await self._create_project(client)
        res = await client.post(
            f"/api/projects/{pid}/dashboard-cards",
            json={"type": "chart", "title": "Revenue", "code": "px.bar(df)"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["type"] == "chart"
        assert data["title"] == "Revenue"
        assert data["position"] == 0

    async def test_update_card(self, client):
        pid = await self._create_project(client)
        create = await client.post(
            f"/api/projects/{pid}/dashboard-cards",
            json={"type": "kpi", "title": "Old Title", "value": "42"},
        )
        card_id = create.json()["id"]
        res = await client.patch(
            f"/api/projects/{pid}/dashboard-cards/{card_id}",
            json={"title": "New Title"},
        )
        assert res.status_code == 200
        assert res.json()["title"] == "New Title"

    async def test_update_card_not_found(self, client):
        pid = await self._create_project(client)
        res = await client.patch(
            f"/api/projects/{pid}/dashboard-cards/00000000-0000-0000-0000-000000000000",
            json={"title": "X"},
        )
        assert res.status_code == 404

    async def test_update_card_no_fields(self, client):
        pid = await self._create_project(client)
        create = await client.post(
            f"/api/projects/{pid}/dashboard-cards",
            json={"type": "kpi", "title": "T"},
        )
        card_id = create.json()["id"]
        res = await client.patch(f"/api/projects/{pid}/dashboard-cards/{card_id}", json={})
        assert res.status_code == 400

    async def test_batch_update_layouts(self, client):
        pid = await self._create_project(client)
        c1 = await client.post(
            f"/api/projects/{pid}/dashboard-cards",
            json={"type": "chart", "title": "A"},
        )
        c2 = await client.post(
            f"/api/projects/{pid}/dashboard-cards",
            json={"type": "kpi", "title": "B"},
        )
        items = [
            {"id": c1.json()["id"], "layout": {"x": 0, "y": 0, "w": 6, "h": 4}},
            {"id": c2.json()["id"], "layout": {"x": 6, "y": 0, "w": 6, "h": 4}},
        ]
        res = await client.put(
            f"/api/projects/{pid}/dashboard-cards/layouts", json={"items": items}
        )
        assert res.status_code == 200

        cards = await client.get(f"/api/projects/{pid}/dashboard-cards")
        layouts = {c["id"]: c["layout"] for c in cards.json()}
        assert layouts[c1.json()["id"]] == {"x": 0, "y": 0, "w": 6, "h": 4}

    async def test_delete_card(self, client):
        pid = await self._create_project(client)
        create = await client.post(
            f"/api/projects/{pid}/dashboard-cards",
            json={"type": "chart", "title": "Doomed"},
        )
        card_id = create.json()["id"]
        res = await client.delete(f"/api/projects/{pid}/dashboard-cards/{card_id}")
        assert res.status_code == 200
        assert res.json()["deleted"] is True

        res = await client.delete(f"/api/projects/{pid}/dashboard-cards/{card_id}")
        assert res.status_code == 404

    async def test_dashboard_content_crud(self, client):
        pid = await self._create_project(client)

        # Initially null
        res = await client.get(f"/api/projects/{pid}/dashboard-content")
        assert res.status_code == 200

        # Save content
        content = [{"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]}]
        res = await client.put(f"/api/projects/{pid}/dashboard-content", json={"content": content})
        assert res.status_code == 200

        # Read it back
        res = await client.get(f"/api/projects/{pid}/dashboard-content")
        assert res.status_code == 200
        assert res.json() == content
