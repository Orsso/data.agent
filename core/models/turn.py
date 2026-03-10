from dataclasses import dataclass, field


@dataclass
class TurnState:
    figs: list[dict] = field(default_factory=list)
    cards: list[dict] = field(default_factory=list)
    card_updates: dict[str, dict] = field(default_factory=dict)
    code: str | None = None
    result: dict | None = None
    selected_card_ids: list[str] = field(default_factory=list)

    def reset(self) -> None:
        self.figs = []
        self.cards = []
        self.card_updates = {}
        self.code = None
        self.result = None
        self.selected_card_ids = []
