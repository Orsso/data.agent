import logging

from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphInterrupt

from core.sandbox.exceptions import SandboxError
from core.tools.exceptions import ToolError

logger = logging.getLogger(__name__)


@wrap_tool_call
async def tool_error_handler(request, handler):
    try:
        return await handler(request)
    except GraphInterrupt:
        # interrupt() control-flow — must propagate to the LangGraph runtime
        logger.debug("Tool '%s' raised GraphInterrupt (propagating)", request.tool_call["name"])
        raise
    except (ToolError, SandboxError) as exc:
        logger.warning(
            "Tool '%s' error: %s", request.tool_call["name"], exc,
        )
        return ToolMessage(
            content=str(exc),
            name=request.tool_call["name"],
            tool_call_id=request.tool_call["id"],
            status="error",
        )
    except Exception as exc:
        logger.error(
            "Tool '%s' unexpected error: %s", request.tool_call["name"], exc, exc_info=True,
        )
        return ToolMessage(
            content=f"Unexpected error: {exc}",
            name=request.tool_call["name"],
            tool_call_id=request.tool_call["id"],
            status="error",
        )
