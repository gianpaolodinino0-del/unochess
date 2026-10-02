from __future__ import annotations

from dataclasses import dataclass

from .cards import Card


@dataclass
class GameState:
    """Mutable state belonging to one UNO Chess match."""

    current_player: int = 0
    active_card: Card | None = None
    started: bool = False
    has_drawn: bool = False
    last_played_card: Card | None = None
    current_color: str | None = None
    pending_color: str | None = None
    checked_player: int | None = None
    checking_player: int | None = None
    winner: int | None = None
    finish_reason: str | None = None
    pending_draw: int = 0
    pending_draw_type: str | None = None
    skip_turns: int = 0
