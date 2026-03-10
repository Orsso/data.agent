import json

from langchain_core.tools import tool
from langgraph.types import interrupt
from pydantic import BaseModel, Field


class OptionSchema(BaseModel):
    label: str = Field(description="Short button text (1-5 words), in the user's language")
    description: str = Field(default="", description="Tooltip explaining this option")


class QuestionSchema(BaseModel):
    question: str = Field(description="The question to ask the user")
    header: str = Field(default="", description="Short chip label (max 12 chars)")
    options: list[OptionSchema] = Field(
        description="2-4 clickable options. Do NOT include an 'Other' option, the UI adds one."
    )
    multi_select: bool = Field(default=False, description="Allow selecting multiple options")


@tool
def ask_question(questions: list[QuestionSchema]) -> str:
    """Ask the user clarifying questions with interactive buttons.
    MUST use this instead of asking in plain text, the UI only renders buttons via this tool.

    You can pass multiple questions in the `questions` list when several dimensions
    need clarification. The user answers all questions before execution resumes.

    USE WHEN:
    - The query is open-ended or has unclear dimensions (metric, grouping, time range, chart type).
    - Multiple valid analysis approaches exist (e.g., 'trends' could be by month, quarter, or year).
    - You want to confirm before an expensive operation.

    DO NOT USE WHEN:
    - The intent is clear on all dimensions. Just do it.
    - The question has an obvious best answer.

    Write option labels in the USER'S LANGUAGE. Keep labels short (1-5 words).
    """
    cleaned = []
    for q in questions:
        q_dict = q.model_dump()
        opts = q_dict.get("options", [])
        opts = [o for o in opts if not o.get("label", "").lower().startswith("other")][:4]
        cleaned.append({**q_dict, "options": opts})

    answers = interrupt({"questions": cleaned})
    return f"User answered: {json.dumps(answers)}"
