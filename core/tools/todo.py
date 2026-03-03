import json
import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from core.state import TodoItem
from core.tools.context import get_tool_context
from core.tools.exceptions import ToolError


def _serialize_todos(todos: list[TodoItem]) -> list[dict]:
    return [{"id": t.id, "content": t.content, "status": t.status} for t in todos]


@tool
def todo(action: str, config: RunnableConfig, todos: list[dict] | None = None) -> str:
    """Track multi-step analysis progress with a checklist.
    Use action='read' to get current todos.
    Use action='write' with the COMPLETE todo list to replace all items.

    EACH TODO ITEM MUST HAVE:
    - id: string (e.g. "1", "2", "3")
    - content: string describing the step
    - status: "pending", "in_progress", or "completed"

    Mark items in_progress before starting each step, completed after finishing.
    """
    ctx = get_tool_context(config)

    if action == "read":
        return json.dumps({"todos": _serialize_todos(ctx.todos), "total": len(ctx.todos)})

    if action == "write":
        if todos is None:
            raise ToolError("Error: 'write' action requires 'todos' list.")
        ctx.todos.clear()
        for item in todos:
            content = item.get("content") or item.get("task", "")
            item_id = str(item.get("id", "")) or uuid.uuid4().hex[:6]
            status = item.get("status", "pending")
            ctx.todos.append(TodoItem(id=item_id, content=content, status=status))
        return json.dumps({"updated": len(ctx.todos), "todos": _serialize_todos(ctx.todos)})

    raise ToolError(f"Error: Unknown action: {action}. Use 'read' or 'write'.")
