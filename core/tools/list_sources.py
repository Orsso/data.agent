import json

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from core.tools.context import get_tool_context


@tool
def list_sources(config: RunnableConfig) -> str:
    """List all loaded data sources with their names, row counts, and column names.
    Use this to discover available DataFrames before writing analysis code.
    """
    ctx = get_tool_context(config)

    if ctx.sources.is_empty:
        return "No data sources loaded."

    sources = []
    for name, src in ctx.sources.get_all().items():
        sources.append({
            "name": name,
            "rows": src.row_count,
            "columns": src.columns,
        })

    return json.dumps({"sources": sources}, ensure_ascii=False)
