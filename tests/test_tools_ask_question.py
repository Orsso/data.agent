"""Tests for core/tools/ask_question.py — ask_question tool."""

import json
from unittest.mock import patch

from core.tools.ask_question import QuestionSchema, ask_question


class TestAskQuestion:
    @patch("core.tools.ask_question.interrupt")
    def test_removes_other_option(self, mock_interrupt):
        # INTENTION: Verify options with label starting with "Other" are removed
        # FALSIFIABILITÉ: Would fail if filter is removed
        mock_interrupt.return_value = {"q1": "A"}

        questions = [
            QuestionSchema(
                question="Pick one",
                options=[
                    {"label": "A", "description": ""},
                    {"label": "Other", "description": "Free text"},
                    {"label": "B", "description": ""},
                ],
            )
        ]
        ask_question.invoke({"questions": questions})

        # Check what was passed to interrupt
        call_args = mock_interrupt.call_args[0][0]
        options = call_args["questions"][0]["options"]
        labels = [o["label"] for o in options]
        assert "Other" not in labels
        assert "A" in labels
        assert "B" in labels

    @patch("core.tools.ask_question.interrupt")
    def test_max_four_options(self, mock_interrupt):
        # INTENTION: Verify more than 4 options are truncated to 4
        # FALSIFIABILITÉ: Would fail if [:4] slice is removed
        mock_interrupt.return_value = {"q1": "A"}

        questions = [
            QuestionSchema(
                question="Pick one",
                options=[{"label": f"Option {i}", "description": ""} for i in range(6)],
            )
        ]
        ask_question.invoke({"questions": questions})

        call_args = mock_interrupt.call_args[0][0]
        options = call_args["questions"][0]["options"]
        assert len(options) == 4

    @patch("core.tools.ask_question.interrupt")
    def test_returns_user_answer(self, mock_interrupt):
        # INTENTION: Verify return format is "User answered: {json}"
        # FALSIFIABILITÉ: Would fail if format differs
        answers = {"q1": "Option A"}
        mock_interrupt.return_value = answers

        questions = [
            QuestionSchema(
                question="Pick one",
                options=[{"label": "A", "description": ""}],
            )
        ]
        result = ask_question.invoke({"questions": questions})
        assert result == f"User answered: {json.dumps(answers)}"
