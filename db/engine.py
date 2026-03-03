import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://data_agent:data_agent@localhost:5432/data_agent",
)

_engine = create_async_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_session_factory():
    return _session_factory


async def close_db() -> None:
    await _engine.dispose()


def get_checkpoint_url() -> str:
    """URL psycopg-compatible (without +asyncpg) for the LangGraph checkpointer."""
    return DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
