from dataclasses import dataclass, field


@dataclass
class TurnState:
    figs: list[dict] = field(default_factory=list)
    cards: list[dict] = field(default_factory=list)
    code: str | None = None
    result: dict | None = None

    def reset(self) -> None:
        self.figs = []
        self.cards = []
        self.code = None
        self.result = None
