
from dataclasses import dataclass, field

from core.state import ChatMessage, TodoItem


@dataclass
class ChatState:
    messages: list[ChatMessage] = field(default_factory=list)
    todos: list[TodoItem] = field(default_factory=list)
    pending_msg_id: str | None = None
