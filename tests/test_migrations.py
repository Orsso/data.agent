"""Test that Alembic migrations apply cleanly on a fresh database."""

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://data_agent:data_agent@localhost:5432/data_agent_test",
)

# Derive a sync URL for Alembic (it runs its own async loop internally)
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")


@pytest.fixture
async def temp_database():
    """Create a temporary database, yield its async URL, then drop it."""
    db_name = f"test_migrations_{uuid.uuid4().hex[:8]}"
    # Use the database from DATABASE_URL itself as the admin connection
    admin_url = DATABASE_URL
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        await conn.execute(text(f"CREATE DATABASE {db_name}"))
    try:
        base_url = DATABASE_URL.rsplit("/", 1)[0]
        yield f"{base_url}/{db_name}"
    finally:
        async with engine.connect() as conn:
            # Terminate active connections before dropping
            await conn.execute(
                text(
                    f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid()"
                )
            )
            await conn.execute(text(f"DROP DATABASE {db_name}"))
        await engine.dispose()


async def test_alembic_upgrade_head(temp_database):
    """All migrations apply cleanly on a blank database."""
    import subprocess

    # Pass the asyncpg URL — db/engine.py and alembic/env.py both expect it
    env = {**os.environ, "DATABASE_URL": temp_database}
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stderr}"

    # Verify tables exist via introspection
    engine = create_async_engine(temp_database)
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        )
        tables = {r[0] for r in rows}
    await engine.dispose()

    expected = {"projects", "sources", "chats", "messages", "dashboard_cards", "alembic_version"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"
