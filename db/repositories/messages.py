import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import MessageRow


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        chat_id: uuid.UUID,
        role: str,
        content: str = "",
        code: str | None = None,
        tool_steps: list | None = None,
        todos: list | None = None,
        thinking: str | None = None,
        thinking_duration_s: float | None = None,
        figs: list | None = None,
        proposals: list | None = None,
        asked_questions: list | None = None,
        created_at: datetime | None = None,
    ) -> MessageRow:
        row = MessageRow(
            chat_id=chat_id,
            role=role,
            content=content,
            code=code,
            tool_steps=tool_steps,
            todos=todos,
            thinking=thinking,
            thinking_duration_s=thinking_duration_s,
            figs=figs,
            proposals=proposals,
            asked_questions=asked_questions,
        )
        if created_at is not None:
            row.created_at = created_at
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_chat(self, chat_id: uuid.UUID) -> list[MessageRow]:
        stmt = (
            select(MessageRow).where(MessageRow.chat_id == chat_id).order_by(MessageRow.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, message_id: uuid.UUID) -> MessageRow | None:
        stmt = select(MessageRow).where(MessageRow.id == message_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_proposal(self, chat_id: uuid.UUID, proposal_id: str) -> MessageRow | None:
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB

        stmt = (
            select(MessageRow)
            .where(
                MessageRow.chat_id == chat_id,
                MessageRow.proposals.op("@>")(cast([{"proposal_id": proposal_id}], JSONB)),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_figures(self, message_id: uuid.UUID) -> list | None:
        row = await self.get(message_id)
        if row is None:
            return None
        return row.figs
