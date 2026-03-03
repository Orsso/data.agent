from pathlib import Path

_DIR = Path(__file__).resolve().parent


def _read(*parts: str) -> str:
    return (_DIR / Path(*parts)).with_suffix(".md").read_text(encoding="utf-8").strip()


IDENTITY = _read("chat", "identity")
DECISION_FRAMEWORK = _read("chat", "decision_framework")
CODE_RULES = _read("chat", "code_rules")
ERROR_RECOVERY = _read("chat", "error_recovery")
OUTPUT_FORMAT = _read("chat", "output_format")
TOOL_POLICY_CSV = _read("chat", "tool_policy_csv")
NO_DATA_POLICY = _read("chat", "no_data_policy")
MULTI_SOURCE_POLICY = _read("chat", "multi_source_policy")

DATA_QUERY = _read("context", "data_query")
CARD_CONTEXT = _read("context", "card_context")

DASHBOARD_SYSTEM = _read("dashboard", "dashboard_system")
AUTO_DASHBOARD = _read("dashboard", "auto_dashboard")

INSIGHT_SYSTEM = _read("insight", "insight_system")
INSIGHT_USER = _read("insight", "insight_user")


def build_chat_system(has_sources: bool = True, source_count: int = 1) -> str:
    parts = [IDENTITY]
    if has_sources:
        parts += [DECISION_FRAMEWORK, CODE_RULES, ERROR_RECOVERY]
        parts += [MULTI_SOURCE_POLICY if source_count > 1 else TOOL_POLICY_CSV]
    else:
        parts += [NO_DATA_POLICY]
    parts += [OUTPUT_FORMAT]
    return "\n\n".join(parts)
