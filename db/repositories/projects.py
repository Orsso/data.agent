import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import ProjectRow

_UPDATABLE = {"name", "description", "status", "model", "suggested_questions", "dashboard_content"}


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, model: str | None = None) -> ProjectRow:
        row = ProjectRow(name=name)
        if model:
            row.model = model
        self._session.add(row)
        await self._session.flush()
        return row

    async def get(self, project_id: uuid.UUID) -> ProjectRow | None:
        stmt = (
            select(ProjectRow)
            .where(ProjectRow.id == project_id)
            .options(
                selectinload(ProjectRow.sources),
                selectinload(ProjectRow.chats),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ProjectRow]:
        stmt = (
            select(ProjectRow)
            .options(selectinload(ProjectRow.sources), selectinload(ProjectRow.chats))
            .order_by(ProjectRow.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, project_id: uuid.UUID, **kwargs) -> ProjectRow | None:
        row = await self.get(project_id)
        if row is None:
            return None
        for key, value in kwargs.items():
            if key in _UPDATABLE:
                setattr(row, key, value)
        await self._session.flush()
        return row

    async def get_dashboard_content(self, project_id: uuid.UUID) -> list | None:
        stmt = select(ProjectRow.dashboard_content).where(ProjectRow.id == project_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_dashboard_content(self, project_id: uuid.UUID, content: list) -> None:
        row = await self._session.get(ProjectRow, project_id)
        if row is not None:
            row.dashboard_content = content
            await self._session.flush()

    async def delete(self, project_id: uuid.UUID) -> bool:
        row = await self.get(project_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
