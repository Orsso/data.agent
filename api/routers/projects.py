import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_project_manager, require_project
from api.models import (
    CreateProjectRequest,
    ProjectListItem,
    ProjectListResponse,
    ProjectResponse,
    UpdateProjectRequest,
    project_response,
)
from core.project_manager import ProjectManager
from db import get_db
from db.repositories.projects import ProjectRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(req: CreateProjectRequest, db: AsyncSession = Depends(get_db)):
    repo = ProjectRepository(db)
    row = await repo.create(name=req.name, model=req.model)
    logger.info("Project created: %s (%s)", row.id, row.name)
    return ProjectResponse(
        id=str(row.id),
        name=row.name,
        description=row.description,
        status=row.status,
        model=row.model,
        suggested_questions=row.suggested_questions or [],
        sources=[],
        chat_count=0,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(db: AsyncSession = Depends(get_db)):
    rows = await ProjectRepository(db).list_all()
    return ProjectListResponse(
        projects=[
            ProjectListItem(
                id=str(row.id),
                name=row.name,
                description=row.description,
                status=row.status,
                source_count=len(row.sources),
                source_names=[s.name for s in row.sources],
                chat_count=len(row.chats),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    row = await require_project(project_id, db)
    return project_response(row)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, req: UpdateProjectRequest, db: AsyncSession = Depends(get_db)
):
    row = await require_project(project_id, db)
    updates = req.model_dump(exclude_unset=True)
    if updates:
        repo = ProjectRepository(db)
        row = await repo.update(row.id, **updates)
    return project_response(row)


@router.delete("/{project_id}", status_code=200)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    row = await require_project(project_id, db)
    await ProjectRepository(db).delete(row.id)
    await pm.remove(project_id)
    logger.info("Project deleted: %s", project_id)
    return {"deleted": True}
