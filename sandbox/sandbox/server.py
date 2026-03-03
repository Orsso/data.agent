"""FastAPI server for the sandbox container."""


import asyncio
import time
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from sandbox.kernel import SandboxKernel
from sandbox.models import ExecuteRequest, ExecuteResponse, HealthResponse, UploadResponse

app = FastAPI(title="Sandbox", docs_url=None, redoc_url=None)

_kernel = SandboxKernel()
_start_time = time.monotonic()

SOURCES_DIR = Path("/data/sources")

# Names that must not be overwritten in the IPython namespace.
_RESERVED_NAMES = frozenset({"pd", "px", "go", "np", "re", "fig", "result", "cards", "__builtins__"})


def _validate_df_name(name: str) -> None:
    if not name.isidentifier():
        raise HTTPException(400, f"Invalid DataFrame name: {name!r} (must be a Python identifier)")
    if name.startswith("_"):
        raise HTTPException(400, f"Invalid DataFrame name: {name!r} (must not start with _)")
    if name in _RESERVED_NAMES:
        raise HTTPException(400, f"Reserved name: {name!r}")


@app.post("/execute", response_model=ExecuteResponse)
async def execute(req: ExecuteRequest) -> ExecuteResponse:
    try:
        result = await asyncio.to_thread(_kernel.execute, req.code, req.timeout_seconds)
        return ExecuteResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            figures=result.figures,
            result=result.result,
            cards=result.cards,
            error=result.error,
            duration_ms=result.duration_ms,
        )
    except Exception as exc:
        return ExecuteResponse(error=f"Internal sandbox error: {exc}")


@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...), name: str = Query(...)) -> UploadResponse:
    _validate_df_name(name)
    parquet_bytes = await file.read()
    rows, columns = await asyncio.to_thread(_kernel.inject_dataframe, name, parquet_bytes)

    # Persist to volume so data survives container restart
    if SOURCES_DIR.exists():
        dest = SOURCES_DIR / f"{name}.parquet"
        dest.write_bytes(parquet_bytes)

    return UploadResponse(name=name, rows=rows, columns=columns)


@app.delete("/dataframes/{name}")
async def delete_dataframe(name: str) -> Response:
    _validate_df_name(name)
    removed = await asyncio.to_thread(_kernel.remove_dataframe, name)
    if not removed:
        raise HTTPException(404, f"DataFrame {name!r} not found")
    return Response(status_code=204)


@app.get("/sources/{name}")
async def download_source(name: str) -> Response:
    """Return the stored parquet file for a source."""
    _validate_df_name(name)
    parquet_path = SOURCES_DIR / f"{name}.parquet"
    if not parquet_path.exists():
        raise HTTPException(404, f"Source '{name}' not found on volume")
    return Response(content=parquet_path.read_bytes(), media_type="application/octet-stream")


@app.delete("/sources/{name}")
async def delete_source(name: str) -> Response:
    """Remove a source from namespace AND from the persistent volume."""
    _validate_df_name(name)
    await asyncio.to_thread(_kernel.remove_dataframe, name)

    parquet_path = SOURCES_DIR / f"{name}.parquet"
    if parquet_path.exists():
        parquet_path.unlink()

    return Response(status_code=204)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        uptime_seconds=round(time.monotonic() - _start_time, 1),
        dataframes=_kernel.list_dataframes(),
    )
