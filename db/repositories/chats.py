
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ChatRow


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, project_id: uuid.UUID, title: str | None = None) -> ChatRow:
        row = ChatRow(project_id=project_id, title=title)
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_project(self, project_id: uuid.UUID) -> list[ChatRow]:
        stmt = (
            select(ChatRow)
            .where(ChatRow.project_id == project_id)
            .order_by(ChatRow.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, chat_id: uuid.UUID) -> ChatRow | None:
        stmt = select(ChatRow).where(ChatRow.id == chat_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_title(self, chat_id: uuid.UUID, title: str) -> ChatRow | None:
        row = await self.get(chat_id)
        if row is None:
            return None
        row.title = title
        await self._session.flush()
        return row

    async def delete(self, chat_id: uuid.UUID) -> bool:
        row = await self.get(chat_id)
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True
