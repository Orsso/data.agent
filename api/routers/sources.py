import io
import logging
import re

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_project_manager, require_project
from api.models import SourceResponse, source_response
from core.profiler import build_profile
from core.project_manager import ProjectManager
from core.sandbox.exceptions import SandboxError
from db import get_db
from db.repositories.sources import SourceRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/sources", tags=["sources"])


@router.post(
    "",
    response_model=SourceResponse,
    status_code=201,
)
async def add_project_source(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    project_row = await require_project(project_id, db)

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(400, "File must be a CSV")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        logger.warning("CSV parse failure for '%s' [project=%s]: %s", file.filename, project_id, exc)
        raise HTTPException(400, f"Failed to parse CSV: {exc}") from exc

    raw_name = file.filename.rsplit(".", 1)[0].lower()
    name = re.sub(r"[^a-z0-9_]", "_", raw_name)  # keep only identifier chars
    name = re.sub(r"_+", "_", name).strip("_")    # collapse & trim underscores
    if not name or name[0].isdigit():
        name = f"df_{name}" if name else "source"

    repo = SourceRepository(db)
    existing = await repo.get_by_name(project_row.id, name)
    if existing:
        i = 2
        while await repo.get_by_name(project_row.id, f"{name}_{i}"):
            i += 1
        name = f"{name}_{i}"

    profile = build_profile(df)
    sample_text = df.head(3).to_string()
    row_count = len(df)
    columns = df.columns.tolist()

    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    parquet_bytes = buf.getvalue()

    profile_dict = {
        "row_count": profile.row_count,
        "sample_text": sample_text,
        "columns": [
            {
                "name": c.name,
                "dtype": c.dtype,
                "format": c.format,
                "nulls_pct": c.nulls_pct,
                "cardinality": c.cardinality,
                "sample_values": c.sample_values,
            }
            for c in profile.columns
        ],
    }

    row = await repo.create(
        project_id=project_row.id,
        name=name,
        origin="upload",
        row_count=row_count,
        columns=columns,
        profile=profile_dict,
    )

    proj = pm.get_or_load(project_id, model=project_row.model)
    try:
        await proj.add_source(
            name, parquet_bytes,
            profile=profile, row_count=row_count,
            columns=columns, sample_text=sample_text,
        )
    except SandboxError as exc:
        logger.error("Sandbox error adding source '%s' [project=%s]: %s", name, project_id, exc)
        raise HTTPException(503, f"Sandbox unavailable: {exc}") from exc

    logger.info(
        "Source '%s' added (%d rows, %d cols) [project=%s]",
        name, row_count, len(columns), project_id,
    )
    return source_response(row)


@router.get(
    "",
    response_model=list[SourceResponse],
)
async def list_project_sources(
    project_id: str, db: AsyncSession = Depends(get_db)
):
    project_row = await require_project(project_id, db)
    rows = await SourceRepository(db).list_by_project(project_row.id)
    return [source_response(r) for r in rows]


@router.delete("/{name}")
async def remove_project_source(
    project_id: str,
    name: str,
    db: AsyncSession = Depends(get_db),
    pm: ProjectManager = Depends(get_project_manager),
):
    project_row = await require_project(project_id, db)
    deleted = await SourceRepository(db).delete(project_row.id, name)
    if not deleted:
        raise HTTPException(404, f"Source '{name}' not found")

    proj = pm.get_project(project_id)
    if proj:
        await proj.remove_source(name)

    logger.info("Source '%s' removed [project=%s]", name, project_id)
    return {"deleted": True}
