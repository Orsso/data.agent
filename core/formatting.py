import json
import re
from typing import Any

from core.state import LoopResult

MAX_SUMMARY_LINE = 80
MAX_SUMMARY_LENGTH = 100


def serialize_figure(fig: Any) -> dict | None:
    if fig is None:
        return None
    if hasattr(fig, "to_json"):
        return json.loads(fig.to_json())
    if isinstance(fig, dict):
        return fig
    return None


def summarize_args(tool_name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        return "(invalid JSON)"

    if tool_name == "execute_python":
        code = args.get("code", "")
        first_line = code.strip().split("\n")[0][:MAX_SUMMARY_LINE]
        return first_line + ("..." if len(code.strip()) > MAX_SUMMARY_LINE else "")
    elif tool_name == "ask_question":
        questions = args.get("questions", [])
        return questions[0].get("question", "")[:MAX_SUMMARY_LINE] if questions else ""
    elif tool_name == "todo":
        action = args.get("action", "")
        todos = args.get("todos", [])
        count = len(todos) if todos else 0
        return f"{action} ({count} items)" if todos else action
    return str(args)[:MAX_SUMMARY_LENGTH]


def extract_insights(loop: LoopResult) -> dict:
    result = loop.result
    if isinstance(result, dict) and "description" in result and "questions" in result:
        return result
    if isinstance(result, str):
        parsed = _try_parse_insights(result)
        if parsed:
            return parsed
    if loop.content:
        parsed = _try_parse_insights(loop.content)
        if parsed:
            return parsed
    return {"description": loop.content or "", "questions": []}


def _try_parse_insights(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict) and "description" in parsed and "questions" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass
    return None
