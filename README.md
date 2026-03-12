# data.agent

WIP - Agentic analytics assistant

## Setup

```bash
cp .env.example .env   # add your GOOGLE_API_KEY
docker compose up --build
```

Rebuild sandbox after pulling: `docker compose build sandbox-image`
Open http://localhost:3000.

## Overview 

<p align="center">
  <img src="docs/architecture.png" alt="Architecture" width="900">
</p>

## Architecture

```mermaid
graph LR
    subgraph "frontend/ · :3000"
        Next["Next.js 16 · React 18 · Tailwind"]
    end

    subgraph "api/ + core/ · :8000"
        Backend["FastAPI · LangGraph · Gemini"]
    end

    subgraph "sandbox/ · :8080 per project"
        Kernel["IPython kernel · Pandas · Plotly"]
    end

    subgraph "db/ · :5432"
        DB[("PostgreSQL 16")]
    end

    Next -- "REST + SSE" --> Backend
    Backend --- DB
    Backend -- "execute_python" --> Kernel
    Backend -. "docker.sock" .-> Kernel
```

## CDM

```mermaid
erDiagram
    projects ||--o{ sources : "has"
    projects ||--o{ chats : "has"
    projects ||--o{ dashboard_cards : "has"
    chats ||--o{ messages : "has"

    projects {
        UUID id PK
        VARCHAR name
        TEXT description
        VARCHAR status
        VARCHAR model
        JSONB suggested_questions
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    sources {
        UUID id PK
        UUID project_id FK
        VARCHAR name
        VARCHAR origin
        INTEGER row_count
        JSONB columns
        JSONB profile
        TIMESTAMPTZ created_at
    }

    chats {
        UUID id PK
        UUID project_id FK
        VARCHAR title
        JSONB pending_questions
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    messages {
        UUID id PK
        UUID chat_id FK
        VARCHAR role
        TEXT content
        TEXT code
        JSONB tool_steps
        JSONB todos
        TEXT thinking
        FLOAT thinking_duration_s
        JSONB figs
        JSONB proposals
        JSONB asked_questions
        TIMESTAMPTZ created_at
    }

    dashboard_cards {
        UUID id PK
        UUID project_id FK
        VARCHAR type
        VARCHAR title
        TEXT code
        TEXT value
        JSONB fig
        INTEGER position
    }
```

