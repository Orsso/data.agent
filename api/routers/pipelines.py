import logging
import uuid as _uuid_mod

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_project_manager, require_project
from api.sse import pipeline_event_to_sse, stream_events
from core.formatting import serialize_figure
from core.project_manager import ProjectManager
from db import get_db, get_session_factory
from db.repositories.dashboard_cards import DashboardCardRepository
from db.repositories.projects import ProjectRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/pipelines", tags=["pipelines"])


@router.post("/{pipeline_type}")
async def run_project_pipeline(
    project_id: str,
    pipeline_type: str,
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    if pipeline_type not in ("insights", "dashboard"):
        raise HTTPException(400, f"Unknown pipeline type: {pipeline_type}")
    project_row = await require_project(project_id, db)
    proj = pm.get_or_load(project_id, model=project_row.model)
    await pm.hydrate(project_id, db)
    if proj.sources.is_empty:
        raise HTTPException(400, "No data sources loaded. Upload a CSV first.")

    from core.models.turn import TurnState

    turn = TurnState()

    event_gen = proj.run_pipeline(pipeline_type, turn)

    async def _wrapped():
        async for chunk in stream_events(event_gen, serializer=pipeline_event_to_sse):
            yield chunk

        try:
            factory = get_session_factory()
            async with factory() as session:
                repo = ProjectRepository(session)
                pid = _uuid_mod.UUID(project_id)

                if pipeline_type == "insights":
                    insights = proj.get_last_insights()
                    if insights:
                        description = insights.get("description")
                        questions = insights.get("questions", [])
                        await repo.update(
                            pid,
                            description=description,
                            suggested_questions=questions,
                            status="ready",
                        )
                        logger.info(
                            "Insights persisted [project=%s]: %d questions",
                            project_id,
                            len(questions),
                        )
                    else:
                        logger.warning("No insights to persist [project=%s]", project_id)
                elif pipeline_type == "dashboard":
                    cards = proj.dashboard_cards
                    if cards:
                        card_repo = DashboardCardRepository(session)
                        db_rows = await card_repo.replace_all(
                            pid,
                            [
                                {
                                    "type": c.type,
                                    "title": c.title,
                                    "code": c.code,
                                    "value": c.value,
                                    "fig": serialize_figure(c.fig),
                                    "position": i,
                                }
                                for i, c in enumerate(cards)
                            ],
                        )
                        # Update in-memory IDs to match DB UUIDs
                        for card, row in zip(cards, db_rows, strict=True):
                            card.id = str(row.id)
                        logger.info(
                            "Dashboard cards persisted [project=%s]: %d cards",
                            project_id,
                            len(cards),
                        )

                        # Generate default BlockNote document
                        def _bn_id() -> str:
                            return _uuid_mod.uuid4().hex[:8]

                        doc_blocks: list[dict] = [
                            {
                                "id": _bn_id(),
                                "type": "heading",
                                "props": {"level": 1},
                                "content": [
                                    {"type": "text", "text": project_row.name or "Dashboard"}
                                ],
                                "children": [],
                            }
                        ]
                        for row in db_rows:
                            block_type = "metric" if row.type == "metric" else "chart"
                            doc_blocks.append(
                                {
                                    "id": _bn_id(),
                                    "type": block_type,
                                    "props": {"cardId": str(row.id)},
                                    "content": [],
                                    "children": [],
                                }
                            )
                        await repo.update(pid, dashboard_content=doc_blocks)

                await session.commit()
        except Exception:
            logger.error(
                "Failed to persist %s results [project=%s]",
                pipeline_type,
                project_id,
                exc_info=True,
            )

    return StreamingResponse(
        _wrapped(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
