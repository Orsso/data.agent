# ---- Builder: install Python dependencies with uv ----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- Runtime ----
FROM python:3.13-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --create-home app

WORKDIR /app

# Virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Application code
COPY api/ api/
COPY core/ core/
COPY db/ db/
COPY alembic/ alembic/
COPY alembic.ini ./

# Entrypoint auto-detects Docker socket GID
COPY entrypoint.sh /entrypoint.sh

# Logs directory (writable by app user)
RUN mkdir -p /app/logs && chown app:app /app/logs

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
