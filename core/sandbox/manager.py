"""Host-side manager for sandbox Docker containers."""

import asyncio
import contextlib
import io
import logging
import os
import time
from dataclasses import dataclass, field

import docker
import docker.errors
import httpx
from docker.models.containers import Container

from core.constants import SANDBOX_CPU_QUOTA, SANDBOX_MEM_LIMIT, SANDBOX_PIDS_LIMIT
from core.sandbox.exceptions import SandboxError, SandboxTimeoutError

logger = logging.getLogger(__name__)

SANDBOX_NETWORK = "sandbox-net"
_SANDBOX_LABEL = {"managed-by": "data-agent-sandbox"}


def _running_in_docker() -> bool:
    """Detect if the current process is running inside a Docker container."""
    return os.path.exists("/.dockerenv") or os.environ.get("RUNNING_IN_DOCKER") == "1"


@dataclass
class _Handle:
    container: Container
    project_id: str
    base_url: str
    last_used_at: float = field(default_factory=time.monotonic)


class SandboxManager:
    SANDBOX_IMAGE = "data-agent-sandbox:latest"
    IDLE_TIMEOUT_S = 300  # 5 min
    CLEANUP_INTERVAL_S = 30
    EXECUTE_TIMEOUT_S = 60.0
    MAX_CONTAINERS = 20
    HEALTH_WAIT_S = 30.0
    HEALTH_POLL_S = 0.3

    def __init__(self) -> None:
        self._docker: docker.DockerClient | None = None
        self._http: httpx.AsyncClient | None = None
        self._handles: dict[str, _Handle] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._project_locks: dict[str, asyncio.Lock] = {}
        self._use_network: bool = False  # True when backend is in Docker

    @property
    def _client(self) -> docker.DockerClient:
        assert self._docker is not None, "SandboxManager not started"
        return self._docker

    @property
    def _api(self) -> httpx.AsyncClient:
        assert self._http is not None, "SandboxManager not started"
        return self._http

    def _get_project_lock(self, project_id: str) -> asyncio.Lock:
        return self._project_locks.setdefault(project_id, asyncio.Lock())

    async def start(self) -> None:
        self._docker = docker.from_env()
        self._use_network = _running_in_docker()
        if self._use_network:
            self._ensure_network()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._reap_orphaned_containers)
        logger.info(
            "SandboxManager started (mode=%s)",
            "network" if self._use_network else "published-ports",
        )
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(self.EXECUTE_TIMEOUT_S + 10))
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task

        async with self._lock:
            for project_id in list(self._handles):
                await self._destroy(project_id)

        if self._http:
            await self._http.aclose()
        logger.info("SandboxManager stopped")

    @staticmethod
    def _volume_name(project_id: str) -> str:
        return f"sandbox-data-{project_id}"

    def create_volume(self, project_id: str) -> str:
        vol_name = self._volume_name(project_id)
        try:
            self._client.volumes.get(vol_name)
            logger.debug("Volume %s already exists", vol_name)
        except docker.errors.NotFound:
            self._client.volumes.create(vol_name)
            logger.info("Created volume %s", vol_name)
        return vol_name

    def delete_volume(self, project_id: str) -> None:
        vol_name = self._volume_name(project_id)
        try:
            vol = self._client.volumes.get(vol_name)
        except docker.errors.NotFound:
            logger.debug("Volume %s not found (already deleted)", vol_name)
            return

        try:
            vol.remove(force=True)
            logger.info("Deleted volume %s", vol_name)
        except docker.errors.APIError as exc:
            logger.warning("Could not remove volume %s: %s", vol_name, exc)

    async def create(self, project_id: str) -> _Handle:
        """Create a new sandbox container. Caller must hold the project lock."""
        t0 = time.monotonic()
        logger.info("Creating sandbox container for project %s …", project_id)

        async with self._lock:
            await self._evict_if_needed()

        container_name = f"sandbox-{project_id}"
        loop = asyncio.get_running_loop()

        vol_name = await loop.run_in_executor(None, self.create_volume, project_id)

        run_kwargs: dict = {
            "image": self.SANDBOX_IMAGE,
            "name": container_name,
            "detach": True,
            "mem_limit": SANDBOX_MEM_LIMIT,
            "cpu_quota": SANDBOX_CPU_QUOTA,
            "pids_limit": SANDBOX_PIDS_LIMIT,
            "auto_remove": True,
            "security_opt": ["no-new-privileges"],
            "labels": _SANDBOX_LABEL,
            "volumes": {vol_name: {"bind": "/data", "mode": "rw"}},
        }

        if self._use_network:
            run_kwargs["network"] = SANDBOX_NETWORK
            base_url = f"http://{container_name}:8080"
        else:
            run_kwargs["ports"] = {"8080/tcp": None}
            base_url = ""  # Will be set after inspecting the port

        t_docker = time.monotonic()
        container = await loop.run_in_executor(
            None, lambda: self._client.containers.run(**run_kwargs)
        )
        logger.info(
            "Docker container started for %s (%dms)",
            project_id,
            int((time.monotonic() - t_docker) * 1000),
        )

        try:
            if not self._use_network:
                # Retrieve the dynamically assigned host port
                await loop.run_in_executor(None, container.reload)
                port_info = container.ports.get("8080/tcp")
                if port_info:
                    base_url = f"http://127.0.0.1:{port_info[0]['HostPort']}"
                else:
                    raise SandboxError(f"No published port for container {container_name}")

            handle = _Handle(
                container=container,
                project_id=project_id,
                base_url=base_url,
            )

            async with self._lock:
                self._handles[project_id] = handle

            await self._wait_healthy(handle)
        except BaseException:
            async with self._lock:
                self._handles.pop(project_id, None)
            with contextlib.suppress(docker.errors.APIError):
                await loop.run_in_executor(
                    None,
                    lambda: container.remove(force=True),
                )
            raise

        total_ms = int((time.monotonic() - t0) * 1000)
        logger.info(
            "Sandbox ready for project %s at %s (total %dms)",
            project_id,
            base_url,
            total_ms,
        )
        return handle

    async def destroy(self, project_id: str) -> None:
        async with self._lock:
            await self._destroy(project_id)

    async def _destroy(self, project_id: str) -> None:
        """Internal destroy — caller must hold ``self._lock``."""
        handle = self._handles.pop(project_id, None)
        if handle is None:
            return
        t0 = time.monotonic()
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: handle.container.stop(timeout=5))
        except docker.errors.NotFound:
            logger.debug("Container already removed for project %s", project_id)
        except docker.errors.APIError as exc:
            logger.warning(
                "Docker API error stopping container for project %s: %s", project_id, exc
            )
        self._project_locks.pop(project_id, None)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info("Container destroyed for project %s (%dms)", project_id, elapsed_ms)

    async def ensure_container(self, project_id: str) -> _Handle:
        """Get or create a container. Volume + _autoload_sources handles data."""
        project_lock = self._get_project_lock(project_id)
        async with project_lock:
            return await self._ensure_container_locked(project_id)

    async def _ensure_container_locked(self, project_id: str) -> _Handle:
        """Inner ensure_container — caller must hold the project lock."""
        async with self._lock:
            handle = self._handles.get(project_id)
            if handle is not None:
                try:
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, handle.container.reload)
                    if handle.container.status == "running":
                        handle.last_used_at = time.monotonic()
                        logger.debug("Reusing existing container for %s", project_id)
                        return handle
                except docker.errors.NotFound:
                    pass
                except docker.errors.APIError as exc:
                    logger.warning("Failed to check container for %s: %s", project_id, exc)
                self._handles.pop(project_id, None)

        return await self.create(project_id)

    async def delete_project_sandbox(self, project_id: str) -> None:
        """Destroy container AND volume for a project."""
        await self.destroy(project_id)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delete_volume, project_id)

    async def execute(self, project_id: str, code: str, timeout: float | None = None) -> dict:
        handle = self._handles.get(project_id)
        if handle is None:
            raise SandboxError(f"No container for project {project_id}")
        handle.last_used_at = time.monotonic()

        try:
            resp = await self._api.post(
                f"{handle.base_url}/execute",
                json={"code": code, "timeout_seconds": timeout or self.EXECUTE_TIMEOUT_S},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException as exc:
            raise SandboxTimeoutError(f"Execution timed out for project {project_id}") from exc
        except httpx.HTTPError as exc:
            raise SandboxError(f"Sandbox HTTP error: {exc}") from exc

    async def upload_source(self, project_id: str, name: str, data: bytes) -> dict:
        """Upload parquet bytes to the sandbox."""
        handle = self._handles.get(project_id)
        if handle is None:
            raise SandboxError(f"No container for project {project_id}")
        handle.last_used_at = time.monotonic()

        t0 = time.monotonic()
        buf = io.BytesIO(data)

        try:
            resp = await self._api.post(
                f"{handle.base_url}/upload",
                params={"name": name},
                files={"file": ("data.parquet", buf, "application/octet-stream")},
            )
            resp.raise_for_status()
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            logger.info(
                "Source '%s' uploaded to sandbox %s (%dms)",
                name,
                project_id,
                elapsed_ms,
            )
            return resp.json()
        except httpx.HTTPError as exc:
            raise SandboxError(f"Upload failed for source '{name}': {exc}") from exc

    async def remove_source(self, project_id: str, name: str) -> None:
        handle = self._handles.get(project_id)
        if handle is None:
            raise SandboxError(f"No container for project {project_id}")
        handle.last_used_at = time.monotonic()

        try:
            resp = await self._api.delete(f"{handle.base_url}/sources/{name}")
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise SandboxError(f"Remove source '{name}' failed: {exc}") from exc

    def _ensure_network(self) -> None:
        """Create the sandbox-net Docker network if it doesn't exist."""
        try:
            self._client.networks.get(SANDBOX_NETWORK)
        except docker.errors.NotFound:
            self._client.networks.create(SANDBOX_NETWORK, internal=True)
            logger.info("Created Docker network %s", SANDBOX_NETWORK)

    def _reap_orphaned_containers(self) -> None:
        """Remove sandbox containers left over from a previous backend run."""
        orphans = self._client.containers.list(
            all=True,
            filters={"label": [f"{k}={v}" for k, v in _SANDBOX_LABEL.items()]},
        )
        if not orphans:
            return
        removed = 0
        for ctr in orphans:
            try:
                ctr.remove(force=True)
                removed += 1
                logger.debug("Reaped orphaned container %s", ctr.name)
            except docker.errors.APIError as exc:
                logger.warning("Failed to reap container %s: %s", ctr.name, exc)
        logger.info(
            "Startup reap: removed %d/%d orphaned sandbox container(s)", removed, len(orphans)
        )

    async def _wait_healthy(self, handle: _Handle) -> None:
        """Poll /health until the container is ready."""
        deadline = time.monotonic() + self.HEALTH_WAIT_S
        t0 = time.monotonic()
        attempt = 0
        while time.monotonic() < deadline:
            attempt += 1
            try:
                resp = await self._api.get(f"{handle.base_url}/health")
                if resp.status_code == 200:
                    elapsed = (time.monotonic() - t0) * 1000
                    logger.info(
                        "Health check passed for %s (%dms)", handle.project_id, int(elapsed)
                    )
                    return
            except httpx.HTTPError:
                pass
            logger.debug("Health poll attempt %d for %s", attempt, handle.project_id)
            await asyncio.sleep(self.HEALTH_POLL_S)
        raise SandboxError(f"Container for {handle.project_id} did not become healthy in time")

    async def _evict_if_needed(self) -> None:
        """If at max capacity, destroy the least recently used container.
        Caller must hold ``self._lock``.
        """
        while len(self._handles) >= self.MAX_CONTAINERS:
            oldest = min(self._handles.values(), key=lambda h: h.last_used_at)
            logger.warning("Evicting idle container for project %s (LRU)", oldest.project_id)
            await self._destroy(oldest.project_id)

    async def _cleanup_loop(self) -> None:
        """Background task to destroy idle containers."""
        while True:
            await asyncio.sleep(self.CLEANUP_INTERVAL_S)
            async with self._lock:
                now = time.monotonic()
                to_destroy = [
                    project_id
                    for project_id, h in self._handles.items()
                    if now - h.last_used_at > self.IDLE_TIMEOUT_S
                ]
                for project_id in to_destroy:
                    logger.info("Destroying idle container for project %s", project_id)
                    await self._destroy(project_id)
