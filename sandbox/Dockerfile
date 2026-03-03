FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- Runtime ----
FROM python:3.13-slim-bookworm

RUN groupadd --gid 1000 sandbox && \
    useradd --uid 1000 --gid sandbox --create-home sandbox && \
    mkdir -p /data/sources && chown sandbox:sandbox /data /data/sources

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY sandbox/ sandbox/

ENV PATH="/app/.venv/bin:$PATH"

USER sandbox

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "sandbox.server:app", "--host", "0.0.0.0", "--port", "8080"]
