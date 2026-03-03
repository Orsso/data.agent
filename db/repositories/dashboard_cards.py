
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DashboardCardRow


class DashboardCardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_all(
        self, project_id: uuid.UUID, cards: list[dict]
    ) -> list[DashboardCardRow]:
        """Delete all existing cards for the project and insert new ones."""
        await self._session.execute(
            delete(DashboardCardRow).where(DashboardCardRow.project_id == project_id)
        )
        rows = []
        for i, card in enumerate(cards):
            row = DashboardCardRow(
                project_id=project_id,
                type=card["type"],
                title=card["title"],
                code=card.get("code"),
                value=card.get("value"),
                fig=card.get("fig"),
                position=i,
            )
            self._session.add(row)
            rows.append(row)
        await self._session.flush()
        return rows

    async def list_by_project(self, project_id: uuid.UUID) -> list[DashboardCardRow]:
        stmt = (
            select(DashboardCardRow)
            .where(DashboardCardRow.project_id == project_id)
            .order_by(DashboardCardRow.position)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_card(
        self,
        project_id: uuid.UUID,
        type: str,
        title: str,
        code: str | None = None,
        value: str | None = None,
        fig: dict | None = None,
        position: int | None = None,
    ) -> DashboardCardRow:
        # Auto-position: append after last card
        if position is None:
            existing = await self.list_by_project(project_id)
            position = len(existing)
        row = DashboardCardRow(
            project_id=project_id,
            type=type,
            title=title,
            code=code,
            value=value,
            fig=fig,
            position=position,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def delete_card(self, card_id: uuid.UUID) -> bool:
        stmt = select(DashboardCardRow).where(DashboardCardRow.id == card_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
