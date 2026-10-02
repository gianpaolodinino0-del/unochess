from __future__ import annotations

from dataclasses import dataclass
import random

COLORS = ("red", "yellow", "green", "blue")
NUMBERS = tuple(range(0, 10))

@dataclass(frozen=True)
class Card:
    color: str | None
    value: str

    @property
    def label(self) -> str:
        return f"{self.color or 'wild'} {self.value}"


def build_deck() -> list[Card]:
    deck: list[Card] = []

    for color in COLORS:
        for n in range(1, 9):
            deck.extend((Card(color, str(n)), Card(color, str(n))))

        deck.extend((Card(color, "+2"), Card(color, "+2")))
        deck.extend((Card(color, "stop"), Card(color, "stop")))

    deck.extend(Card(None, "+4") for _ in range(4))
    deck.extend(Card(None, "wild") for _ in range(4))

    return deck


class Deck:
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.draw_pile: list[Card] = []
        self.discard_pile: list[Card] = []
        self.reset()

    def reset(self) -> None:
        self.draw_pile = build_deck()
        self.rng.shuffle(self.draw_pile)
        self.discard_pile = []

    def draw(self) -> Card:
        if not self.draw_pile:
            self._recycle_discards()
        if not self.draw_pile:
            raise RuntimeError("Il mazzo è vuoto.")
        return self.draw_pile.pop()

    def discard(self, card: Card) -> None:
        self.discard_pile.append(card)

    def _recycle_discards(self) -> None:
        if len(self.discard_pile) <= 1:
            top = self.discard_pile[-1] if self.discard_pile else None
            self.draw_pile = build_deck()
            if top is not None:
                self.draw_pile.remove(top)
                self.discard_pile = [top]
            self.rng.shuffle(self.draw_pile)
            return
        top = self.discard_pile[-1]
        self.draw_pile = self.discard_pile[:-1]
        self.discard_pile = [top]
        self.rng.shuffle(self.draw_pile)
