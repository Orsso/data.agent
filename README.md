# data.agent

WIP - AI data analysis agent.

```mermaid
graph LR
    subgraph Frontend[":3000"]
        Next["Next.js 16<br/>React 18<br/>Tailwind"]
    end

    subgraph Backend[":8000"]
        API["FastAPI<br/>LangGraph Agent<br/>Gemini LLM"]
    end

    subgraph Sandbox[":8080 per project"]
        Kernel["IPython kernel<br/>Pandas + Plotly"]
        Vol[("sandbox-data-{id}")]
        Kernel --- Vol
    end

    DB[(PostgreSQL)]

    Next -->|"api"| API
    API -->|"SSE stream"| Next
    API --- DB
    API -->|"upload parquet"| Vol
    API -->|"execute_python"| Kernel
    API -->|"docker.sock"| Sandbox
```

## Setup

```bash
cp .env.example .env   # add your GOOGLE_API_KEY
docker compose up --build
```

Open http://localhost:3000.
