"""Tests for core/models/turn.py — TurnState."""

from core.models.turn import TurnState


class TestTurnState:
    def test_initial_state(self):
        # INTENTION: Verify fresh TurnState has empty lists, None code/result
        # FALSIFIABILITÉ: Would fail if defaults change
        ts = TurnState()
        assert ts.figs == []
        assert ts.cards == []
        assert ts.card_updates == {}
        assert ts.code is None
        assert ts.result is None
        assert ts.selected_card_ids == []

    def test_accumulate_figs(self):
        # INTENTION: Verify appending to figs works
        # FALSIFIABILITÉ: Would fail if field is immutable
        ts = TurnState()
        ts.figs.append({"data": []})
        assert len(ts.figs) == 1

    def test_reset_clears_all(self):
        # INTENTION: Verify reset() returns all fields to defaults
        # FALSIFIABILITÉ: Would fail if any field is not reset
        ts = TurnState()
        ts.figs = [{"data": []}]
        ts.cards = [{"type": "metric"}]
        ts.card_updates = {"c1": {"data": []}}
        ts.code = "print('hi')"
        ts.result = {"key": "value"}
        ts.selected_card_ids = ["c1"]

        ts.reset()

        assert ts.figs == []
        assert ts.cards == []
        assert ts.card_updates == {}
        assert ts.code is None
        assert ts.result is None
        assert ts.selected_card_ids == []
