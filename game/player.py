from __future__ import annotations

from dataclasses import dataclass, field
from .cards import Card

@dataclass
class Player:
    name: str
    color: bool
    hand: list[Card] = field(default_factory=list)
