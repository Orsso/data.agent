import logging
import os
import uuid

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from core.chat_thread import ChatThread
from core.constants import DEFAULT_MODEL
from core.models.sources import DataSource
from core.project import Project
from core.sandbox import SandboxManager
from core.state import ColumnProfile, DataProfile
from db.repositories.sources import SourceRepository

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = os.environ.get("MODEL_NAME", DEFAULT_MODEL)
_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


def _reconstruct_profile(profile_dict: dict) -> DataProfile:
    columns = [
        ColumnProfile(
            name=c["name"],
            dtype=c["dtype"],
            format=c.get("format"),
            nulls_pct=c.get("nulls_pct", 0.0),
            cardinality=c.get("cardinality", 0),
            sample_values=c.get("sample_values", []),
        )
        for c in profile_dict.get("columns", [])
    ]
    return DataProfile(
        row_count=profile_dict.get("row_count", 0),
        columns=columns,
    )


class ProjectManager:
    def __init__(self, sandbox_manager: SandboxManager) -> None:
        self._projects: dict[str, Project] = {}
        self._chat_threads: dict[str, ChatThread] = {}
        self._checkpointer: AsyncPostgresSaver | None = None
        self._checkpointer_cm = None  # keep context manager alive
        self._sandbox = sandbox_manager

    async def init_checkpointer(self, checkpoint_url: str) -> None:
        self._checkpointer_cm = AsyncPostgresSaver.from_conn_string(checkpoint_url)
        self._checkpointer = await self._checkpointer_cm.__aenter__()
        await self._checkpointer.setup()
        logger.info("AsyncPostgresSaver initialized")

    async def close_checkpointer(self) -> None:
        if self._checkpointer_cm is not None:
            await self._checkpointer_cm.__aexit__(None, None, None)
            self._checkpointer_cm = None
            self._checkpointer = None

    def get_or_load(self, project_id: str, model: str | None = None) -> Project:
        if project_id in self._projects:
            return self._projects[project_id]

        project = Project(
            project_id=project_id,
            model=model or _DEFAULT_MODEL,
            api_key=_API_KEY,
            sandbox_manager=self._sandbox,
        )
        self._projects[project_id] = project
        logger.info("Project loaded into memory: %s", project_id)
        return project

    async def hydrate(self, project_id: str, db_session) -> Project:
        """Ensure a project's sources are loaded and its sandbox container is running."""
        proj = self._projects.get(project_id)
        if proj is None:
            raise ValueError(f"Project {project_id} not in memory — call get_or_load first")

        if proj.sources.is_empty:
            repo = SourceRepository(db_session)
            rows = await repo.list_by_project(uuid.UUID(project_id))
            if not rows:
                return proj

            hydrated = []
            for row in rows:
                try:
                    profile = _reconstruct_profile(row.profile)
                    source = DataSource(
                        name=row.name,
                        profile=profile,
                        origin=row.origin,
                        row_count=row.row_count,
                        columns=row.columns,
                        sample_text=row.profile.get("sample_text", ""),
                    )
                    proj.sources.add(row.name, source)
                    hydrated.append(row.name)
                except Exception as exc:
                    logger.warning("Failed to hydrate source '%s' [project=%s]: %s", row.name, project_id, exc)

            if hydrated:
                logger.info("Hydrated %d source(s) [project=%s]: %s", len(hydrated), project_id, ", ".join(hydrated))

        if not proj.sources.is_empty:
            await self._sandbox.ensure_container(project_id)

        return proj

    def get_project(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def get_chat_thread(self, project_id: str, chat_id: str) -> ChatThread:
        key = f"{project_id}:{chat_id}"
        if key in self._chat_threads:
            return self._chat_threads[key]

        project = self.get_or_load(project_id)
        thread = ChatThread(
            chat_id=chat_id,
            project=project,
            checkpointer=self._checkpointer,
        )
        self._chat_threads[key] = thread
        logger.info("ChatThread created: chat=%s [project=%s]", chat_id, project_id)
        return thread

    async def remove(self, project_id: str) -> None:
        """Evict project from cache and destroy its sandbox + volume."""
        keys_to_remove = [k for k in self._chat_threads if k.startswith(f"{project_id}:")]
        for k in keys_to_remove:
            del self._chat_threads[k]

        self._projects.pop(project_id, None)
        await self._sandbox.delete_project_sandbox(project_id)
        logger.info("Project removed from memory: %s", project_id)
