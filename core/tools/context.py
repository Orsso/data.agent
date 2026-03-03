from dataclasses import dataclass

from langchain_core.runnables import RunnableConfig

from core.models.sources import SourceRegistry
from core.models.turn import TurnState
from core.sandbox.manager import SandboxManager
from core.state import TodoItem


@dataclass
class ToolContext:
    project_id: str
    sandbox: SandboxManager
    sources: SourceRegistry
    turn: TurnState
    todos: list[TodoItem]


def get_tool_context(config: RunnableConfig) -> ToolContext:
    return config["configurable"]["tool_context"]
