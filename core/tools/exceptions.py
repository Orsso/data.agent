class ToolError(Exception):
    """Tool-level error, caught by middleware -> ToolMessage(status='error')."""


class CodeExecutionError(ToolError):
    """Python code error in sandbox (HTTP 200 with error field)."""
