import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)-28s │ %(message)s",
    datefmt="%H:%M:%S",
)
for _name in ("httpx", "httpcore", "docker", "urllib3"):
    logging.getLogger(_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

from api.routers.chats import router as chats_router  # noqa: E402
from api.routers.dashboard import router as dashboard_router  # noqa: E402
from api.routers.messages import router as messages_router  # noqa: E402
from api.routers.pipelines import router as pipelines_router  # noqa: E402
from api.routers.projects import router as projects_router  # noqa: E402
from api.routers.sources import router as sources_router  # noqa: E402
from core.project_manager import ProjectManager  # noqa: E402
from core.sandbox import SandboxManager  # noqa: E402
from db import close_db, get_checkpoint_url  # noqa: E402

sandbox_manager = SandboxManager()
project_manager = ProjectManager(sandbox_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await project_manager.init_checkpointer(get_checkpoint_url())
    await sandbox_manager.start()
    logger.info("Application started")
    yield
    await project_manager.close_checkpointer()
    await sandbox_manager.stop()
    await close_db()
    logger.info("Application stopped")


app = FastAPI(
    title="Data Analysis Agent API",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.project_manager = project_manager


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    status = response.status_code
    msg = f"{request.method} {request.url.path} → {status} ({elapsed_ms}ms)"
    if status >= 500:
        logger.error(msg)
    elif status >= 400:
        logger.warning(msg)
    else:
        logger.info(msg)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(projects_router)
app.include_router(chats_router)
app.include_router(messages_router)
app.include_router(pipelines_router)
app.include_router(sources_router)
app.include_router(dashboard_router)
