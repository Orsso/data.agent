"""Tests for core/tools/todo.py — todo tool."""

import json

import pytest

from core.state import TodoItem
from core.tools.exceptions import ToolError
from core.tools.todo import _serialize_todos, todo

# ── _serialize_todos ─────────────────────────────────────────────────────


class TestSerializeTodos:
    def test_serializes_all_fields(self):
        # INTENTION: Verify _serialize_todos returns dicts with id, content, status
        # FALSIFIABILITÉ: Would fail if any key is missing
        todos = [
            TodoItem(id="1", content="Step 1", status="pending"),
            TodoItem(id="2", content="Step 2", status="completed"),
        ]
        result = _serialize_todos(todos)
        assert result == [
            {"id": "1", "content": "Step 1", "status": "pending"},
            {"id": "2", "content": "Step 2", "status": "completed"},
        ]

    def test_empty_list(self):
        # INTENTION: Verify empty list returns empty list
        # FALSIFIABILITÉ: Would fail if None is returned
        assert _serialize_todos([]) == []


# ── todo tool ────────────────────────────────────────────────────────────


class TestTodoTool:
    def test_read_empty(self, runnable_config):
        # INTENTION: Verify action="read" with no todos returns {"todos": [], "total": 0}
        # FALSIFIABILITÉ: Would fail if format differs
        result = todo.invoke({"action": "read"}, config=runnable_config)
        parsed = json.loads(result)
        assert parsed["todos"] == []
        assert parsed["total"] == 0

    def test_read_with_items(self, runnable_config, tool_context):
        # INTENTION: Verify read returns pre-populated todos
        # FALSIFIABILITÉ: Would fail if serialization is wrong
        tool_context.todos.append(TodoItem(id="1", content="Analyze", status="in_progress"))
        result = todo.invoke({"action": "read"}, config=runnable_config)
        parsed = json.loads(result)
        assert parsed["total"] == 1
        assert parsed["todos"][0]["content"] == "Analyze"
        assert parsed["todos"][0]["status"] == "in_progress"

    def test_write_creates_items(self, runnable_config, tool_context):
        # INTENTION: Verify action="write" creates TodoItem objects
        # FALSIFIABILITÉ: Would fail if count is wrong
        items = [
            {"id": "1", "content": "Step 1", "status": "pending"},
            {"id": "2", "content": "Step 2", "status": "pending"},
            {"id": "3", "content": "Step 3", "status": "pending"},
        ]
        result = todo.invoke({"action": "write", "todos": items}, config=runnable_config)
        parsed = json.loads(result)
        assert parsed["updated"] == 3
        assert len(tool_context.todos) == 3

    def test_write_clears_previous(self, runnable_config, tool_context):
        # INTENTION: Verify write replaces all existing items
        # FALSIFIABILITÉ: Would fail if old items persist
        tool_context.todos.append(TodoItem(id="old", content="Old task", status="completed"))
        items = [{"id": "new", "content": "New task", "status": "pending"}]
        todo.invoke({"action": "write", "todos": items}, config=runnable_config)
        assert len(tool_context.todos) == 1
        assert tool_context.todos[0].id == "new"

    def test_write_generates_id(self, runnable_config, tool_context):
        # INTENTION: Verify items without "id" get a generated ID
        # FALSIFIABILITÉ: Would fail if uuid.uuid4() call is missing
        items = [{"content": "No id task", "status": "pending"}]
        todo.invoke({"action": "write", "todos": items}, config=runnable_config)
        assert tool_context.todos[0].id != ""
        assert len(tool_context.todos[0].id) > 0

    def test_write_preserves_id(self, runnable_config, tool_context):
        # INTENTION: Verify items with "id" keep their original ID
        # FALSIFIABILITÉ: Would fail if ID is overwritten
        items = [{"id": "my-id", "content": "Task", "status": "pending"}]
        todo.invoke({"action": "write", "todos": items}, config=runnable_config)
        assert tool_context.todos[0].id == "my-id"

    def test_write_uses_task_fallback(self, runnable_config, tool_context):
        # INTENTION: Verify items with "task" key (no "content") use "task" as content
        # FALSIFIABILITÉ: Would fail if item.get("task", "") fallback is removed
        items = [{"id": "1", "task": "My task", "status": "pending"}]
        todo.invoke({"action": "write", "todos": items}, config=runnable_config)
        assert tool_context.todos[0].content == "My task"

    def test_write_none_todos_raises(self, runnable_config):
        # INTENTION: Verify action="write" without todos raises ToolError
        # FALSIFIABILITÉ: Would fail if error check is missing
        with pytest.raises(ToolError):
            todo.invoke({"action": "write"}, config=runnable_config)

    def test_unknown_action_raises(self, runnable_config):
        # INTENTION: Verify unknown action raises ToolError
        # FALSIFIABILITÉ: Would fail if fallthrough is silent
        with pytest.raises(ToolError):
            todo.invoke({"action": "invalid"}, config=runnable_config)
