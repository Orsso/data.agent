import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import require_project
from api.models import AddDashboardCardRequest, DashboardCardResponse, card_response
from db import get_db
from db.repositories.dashboard_cards import DashboardCardRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/dashboard-cards", tags=["dashboard"])


@router.get("", response_model=list[DashboardCardResponse])
async def get_project_dashboard_cards(
    project_id: str, db: AsyncSession = Depends(get_db)
):
    project_row = await require_project(project_id, db)
    rows = await DashboardCardRepository(db).list_by_project(project_row.id)
    return [card_response(r) for r in rows]


@router.post(
    "",
    response_model=DashboardCardResponse,
    status_code=201,
)
async def add_dashboard_card(
    project_id: str,
    req: AddDashboardCardRequest,
    db: AsyncSession = Depends(get_db),
):
    project_row = await require_project(project_id, db)
    repo = DashboardCardRepository(db)
    row = await repo.create_card(
        project_id=project_row.id,
        type=req.type,
        title=req.title,
        code=req.code,
        value=req.value,
        fig=req.fig,
    )
    logger.info("Dashboard card added [project=%s]: %s", project_id, row.id)
    return card_response(row)


@router.delete("/{card_id}", status_code=200)
async def delete_dashboard_card(
    project_id: str,
    card_id: str,
    db: AsyncSession = Depends(get_db),
):
    await require_project(project_id, db)
    try:
        cid = uuid.UUID(card_id)
    except ValueError as exc:
        raise HTTPException(400, "Invalid card ID") from exc
    deleted = await DashboardCardRepository(db).delete_card(cid)
    if not deleted:
        raise HTTPException(404, "Dashboard card not found")
    logger.info("Dashboard card deleted [project=%s]: %s", project_id, card_id)
    return {"deleted": True}
