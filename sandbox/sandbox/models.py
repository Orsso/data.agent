
from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    code: str
    timeout_seconds: float = Field(default=30.0, gt=0, le=120)


class ExecuteResponse(BaseModel):
    stdout: str = ""
    stderr: str = ""
    figures: list[dict] = Field(default_factory=list)
    result: dict | list | str | int | float | bool | None = None
    cards: list[dict] = Field(default_factory=list)
    card_updates: dict[str, dict] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


class UploadResponse(BaseModel):
    name: str
    rows: int
    columns: list[str]


class HealthResponse(BaseModel):
    status: str = "ok"
    uptime_seconds: float
    dataframes: list[str]
