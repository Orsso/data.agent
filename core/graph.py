import httpx
from langchain.agents import create_agent
from langchain.agents.middleware.summarization import SummarizationMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI

from core.prompts import build_chat_system
from core.tools import ALL_TOOLS, PIPELINE_TOOLS
from core.tools.middleware import tool_error_handler


def _make_transport() -> httpx.AsyncHTTPTransport:
    """Fresh transport per LLM — avoids stale connection pool sharing."""
    return httpx.AsyncHTTPTransport(
        retries=3,
        limits=httpx.Limits(
            max_keepalive_connections=5,
            keepalive_expiry=30,
        ),
    )


def make_llm(model_name: str, api_key: str, **overrides) -> ChatGoogleGenerativeAI:
    defaults = {
        "model": model_name,
        "google_api_key": api_key,
        "temperature": 1.0,
        "include_thoughts": True,
        "client_args": {
            "transport": _make_transport(),
            "timeout": httpx.Timeout(120.0, connect=10.0),
        },
    }
    defaults.update(overrides)
    return ChatGoogleGenerativeAI(**defaults)


def build_chat_graph(
    model_name: str, api_key: str, checkpointer=None, system_prompt: str | None = None,
):
    llm = make_llm(model_name, api_key)
    return create_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=system_prompt or build_chat_system(),
        middleware=[tool_error_handler, SummarizationMiddleware(llm)],  # type: ignore[arg-type]
        checkpointer=checkpointer,
    )


def build_pipeline_graph(model_name: str, api_key: str, system_prompt: str):
    llm = make_llm(
        model_name,
        api_key,
        temperature=0.3,
        thinking_level="low",
    )
    return create_agent(
        model=llm,
        tools=PIPELINE_TOOLS,
        system_prompt=system_prompt,
        middleware=[tool_error_handler],  # type: ignore[arg-type]
    )
