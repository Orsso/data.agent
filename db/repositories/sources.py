
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SourceRow


class SourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        project_id: uuid.UUID,
        name: str,
        origin: str,
        row_count: int,
        columns: list[str],
        profile: dict | None = None,
    ) -> SourceRow:
        row = SourceRow(
            project_id=project_id,
            name=name,
            origin=origin,
            row_count=row_count,
            columns=columns,
            profile=profile,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_project(self, project_id: uuid.UUID) -> list[SourceRow]:
        stmt = (
            select(SourceRow)
            .where(SourceRow.project_id == project_id)
            .order_by(SourceRow.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, project_id: uuid.UUID, name: str) -> SourceRow | None:
        stmt = select(SourceRow).where(
            and_(SourceRow.project_id == project_id, SourceRow.name == name)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, project_id: uuid.UUID, name: str) -> bool:
        row = await self.get_by_name(project_id, name)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
