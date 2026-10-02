from __future__ import annotations

import chess

from .cards import Card, Deck, COLORS
from .chess_game import ChessGame
from .game_state import GameState
from .player import Player


class _StateField:
    """Keep legacy game attributes backed by the canonical GameState."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance.state, self.name)

    def __set__(self, instance, value) -> None:
        setattr(instance.state, self.name, value)


class UnoChessGame:
    """Game state for UNO Chess."""

    current_player = _StateField("current_player")
    active_card = _StateField("active_card")
    started = _StateField("started")
    has_drawn = _StateField("has_drawn")
    last_played_card = _StateField("last_played_card")
    current_color = _StateField("current_color")
    pending_color = _StateField("pending_color")
    checked_player = _StateField("checked_player")
    checking_player = _StateField("checking_player")
    winner = _StateField("winner")
    finish_reason = _StateField("finish_reason")
    pending_draw = _StateField("pending_draw")
    pending_draw_type = _StateField("pending_draw_type")
    skip_turns = _StateField("skip_turns")

    def __init__(self) -> None:
        self.state = GameState()
        self.chess = ChessGame()
        self.deck = Deck()
        self.players = [Player("Bianco", chess.WHITE), Player("Nero", chess.BLACK)]
        self.winning_card = None
        self.winning_move = None

    @property
    def player(self) -> Player:
        return self.players[self.current_player]

    @property
    def current_hand(self) -> tuple[Card, ...]:
        return tuple(self.player.hand)

    @property
    def current_player_index(self) -> int:
        return self.current_player

    @property
    def current_player_name(self) -> str:
        return self.player.name

    @property
    def player_names(self) -> tuple[str, ...]:
        return tuple(player.name for player in self.players)

    @property
    def hand_sizes(self) -> tuple[int, ...]:
        return tuple(len(player.hand) for player in self.players)

    @property
    def winner_name(self) -> str | None:
        if self.winner is None:
            return None
        return self.players[self.winner].name

    def board_snapshot(self) -> chess.Board:
        """Return a detached board snapshot for read-only presentation."""
        return self.chess.board.copy(stack=False)

    def clear_active_card(self) -> None:
        self.active_card = None
        self.pending_color = None

    def start(self, cards_per_player: int = 7) -> None:
        self.chess.reset()
        self.deck.reset()
        self.current_player = 0
        self.active_card = None
        self.started = False
        self.has_drawn = False
        self.last_played_card = None
        self.current_color = None
        self.pending_color = None
        self.checked_player = None
        self.checking_player = None
        self.winner = None
        self.finish_reason = None
        self.winning_card = None
        self.winning_move = None
        self.pending_draw = 0
        self.pending_draw_type = None
        self.skip_turns = 0

        for player in self.players:
            player.hand.clear()
            player.hand.extend(
                self.deck.draw()
                for _ in range(cards_per_player)
            )

        first = self.deck.draw()

        while not first.value.isdigit():
            self.deck.draw_pile.append(first)
            self.deck.rng.shuffle(self.deck.draw_pile)
            first = self.deck.draw()

        self.deck.discard(first)
        self.last_played_card = first
        print(f"[START] {self.last_card_text()}")

        self.current_color = first.color
        self.started = True
        self._auto_draw_until_action()
        


    def playable_cards(self) -> list[Card]:
        return [
            card
            for card in self.player.hand
            if self.can_play_card(card)
        ]

    def can_play_card(self, card: Card) -> bool:
        return self._can_play_card_for_player(card, self.current_player)

    def _can_play_card_for_player(self, card: Card, player_index: int) -> bool:
        if card not in self.players[player_index].hand:
            return False

        if self.pending_draw > 0:

            if card.value == "+4":
                return True

            if card.value == "+2" and self.pending_draw_type == "+4" and card.color == self.current_color:
                return True

            if card.value == "+2" and self.pending_draw_type == "+2":
                return True

            return False

        if self.last_played_card is None:
            return True

        if card.value == "wild":
            return True

        if card.value == "+4":
            return True

        if card.color == self.current_color:
            return True

        return card.value == self.last_played_card.value
        
    def play_card(self, card: Card) -> None:
        if self.winner is not None:
            raise ValueError("La partita è terminata.")
        if card not in self.player.hand:
            raise ValueError("La carta non è nella mano del giocatore.")

        if not self.can_play_card(card):
            raise ValueError("La carta non è giocabile.")

        self.active_card = card
        self.pending_color = None

    def choose_color(self, color: str) -> None:
        """Set the color selected for the currently played Wild or +4 card."""
        if color not in COLORS:
            raise ValueError("Colore non valido.")
        if self.active_card is None or self.active_card.value not in ("wild", "+4"):
            raise ValueError("Non è in attesa la scelta di un colore.")
        self.pending_color = color

    def play_special_card(self, card: Card) -> None:
        if self.winner is not None:
            raise ValueError("La partita è terminata.")

        if card not in self.player.hand:
            raise ValueError("La carta non è nella mano del giocatore.")

        stop_on_plus_two = (
            card.value == "stop"
            and self.pending_draw > 0
            and self.pending_draw_type == "+2"
            and card.color == self.current_color
        )
        if not self.can_play_card(card) and not stop_on_plus_two:
            raise ValueError("La carta non è giocabile.")

        if card.value not in ("+2", "stop"):
            raise ValueError("Questa carta non è una speciale immediata.")

        player_index = self.current_player
        opponent_index = 1 - player_index

        if stop_on_plus_two:
            for _ in range(self.pending_draw):
                self.player.hand.append(self.deck.draw())
            self.pending_draw = 0
            self.pending_draw_type = None

        card_index = next(index for index, hand_card in enumerate(self.player.hand) if hand_card is card)
        self.player.hand.pop(card_index)
        self.deck.discard(card)
        self.last_played_card = card
        self.current_color = card.color
        self.pending_color = None
        self.active_card = None

        if card.value == "+2":
            self.pending_draw += 2
            self.pending_draw_type = "+2"

            print(f"Pesca {self.pending_draw}")

            self.current_player = opponent_index
            self.chess.board.turn = self.players[opponent_index].color

        elif card.value == "stop":
            self.skip_turns += 2
            self._advance_turn()

        print(f"[SPECIAL] {card.label} | "f"P1={len(self.players[0].hand)} | "f"P2={len(self.players[1].hand)}")        
        self.has_drawn = False
        self._auto_draw_until_action()


    def legal_chess_moves_for_card(self, card: Card) -> list[chess.Move]:
            if self.checked_player != self.current_player:
                return self._moves_for_card(card, resolve_check=False)

            resolving_moves = self._moves_for_card(card, resolve_check=True)
            if any(
                self._moves_for_card(hand_card, resolve_check=True)
                for hand_card in self.player.hand
            ):
                return resolving_moves

            # If no UNO-compatible card can answer check, pseudo-legal moves may
            # leave the king in check as the special rule permits.
            return self._moves_for_card(card, resolve_check=False)

    def _moves_for_card(self, card: Card, resolve_check: bool) -> list[chess.Move]:
        if not self.can_play_card(card) or card.value in ("+2", "stop"):
            return []

        moves = self.chess.pseudo_legal_moves()
        moves.extend(self._king_capture_moves())
        if resolve_check:
            moves = [move for move in moves if self._move_resolves_check(move)]

        if card.value in ("wild", "+4"):
            return moves

        n = int(card.value)
        target_rank = n - 1
        target_file = n - 1
        return [
            move
            for move in moves
            if chess.square_rank(move.from_square) == target_rank
            or chess.square_file(move.from_square) == target_file
        ]

    def card_has_move(self, card: Card) -> bool:
        if card.value in ("+2", "stop"):
            return self.can_play_card(card)

        return bool(self.legal_chess_moves_for_card(card))

    def legal_chess_moves_for_piece(self, square: int) -> set[chess.Move]:
        moves = set()

        for card in self.player.hand:
            for move in self.legal_chess_moves_for_card(card):
                if move.from_square == square:
                    moves.add(move)

        return moves

    def cards_for_move(self, move: chess.Move) -> list[Card]:
        cards = [
            card
            for card in self.player.hand
            if move in self.legal_chess_moves_for_card(card)
        ]
        mandatory_captures = {
            candidate_move
            for hand_card in self.player.hand
            if hand_card.value not in ("wild", "+4")
            for candidate_move in self.legal_chess_moves_for_card(hand_card)
            if (target_piece := self.chess.board.piece_at(candidate_move.to_square))
            and target_piece.piece_type == chess.KING
        }
        if mandatory_captures:
            if move not in mandatory_captures:
                return []
            cards = [card for card in cards if card.value not in ("wild", "+4")]
        return cards

    def _king_capture_moves(self) -> list[chess.Move]:
        board = self.chess.board
        king_square = board.king(not self.player.color)
        if king_square is None:
            return []

        moves = []
        for from_square in board.attackers(self.player.color, king_square):
            piece = board.piece_at(from_square)
            if piece is None or piece.piece_type == chess.KING:
                continue
            promotion = (
                chess.QUEEN
                if piece.piece_type == chess.PAWN
                and chess.square_rank(king_square) in (0, 7)
                else None
            )
            moves.append(chess.Move(from_square, king_square, promotion=promotion))
        return moves

    def play_move(self, move: chess.Move) -> str:
            if not self.started:
                raise RuntimeError("La partita non è iniziata.")

            if self.winner is not None:
                raise ValueError("La partita è terminata.")

            # Consentiamo le mosse pseudo-legali se siamo in scacco o per consentire la cattura diretta
            if self.checked_player == self.current_player or self.chess.board.is_check():
                available_moves = self.chess.pseudo_legal_moves()
            else:
                available_moves = self.chess.legal_moves()
                available_moves.extend(
                    candidate
                    for candidate in self.chess.pseudo_legal_moves()
                    if (target_piece := self.chess.board.piece_at(candidate.to_square))
                    and target_piece.piece_type == chess.KING
                )
            available_moves.extend(self._king_capture_moves())

            if move not in available_moves:
                raise ValueError("Mossa illegale.")

            card = self.active_card

            if card is None:
                cards = self.cards_for_move(move)
                if not cards:
                    raise ValueError("Nessuna carta permette questa mossa.")
                card = cards[0]

            if not any(hand_card is card for hand_card in self.player.hand):
                raise ValueError("La carta non è nella mano del giocatore.")

            if move not in self.legal_chess_moves_for_card(card):
                raise ValueError("La carta selezionata non permette questa mossa.")

            mover = self.current_player
            target = self.chess.board.piece_at(move.to_square)

            if card.value in ("wild", "+4") and self.pending_color not in COLORS:
                raise ValueError("Devi scegliere un colore.")

            mandatory_captures = {
                candidate_move
                for hand_card in self.player.hand
                if hand_card.value not in ("wild", "+4")
                for candidate_move in self.legal_chess_moves_for_card(hand_card)
                if (target_piece := self.chess.board.piece_at(candidate_move.to_square))
                and target_piece.piece_type == chess.KING
            }
            if mandatory_captures and (move not in mandatory_captures or card.value in ("wild", "+4")):
                raise ValueError("Devi catturare il Re quando è possibile.")

            # Esegui la mossa sulla scacchiera
            san = self.chess.push(move, ignore_check=True)

            card_index = next(index for index, hand_card in enumerate(self.player.hand) if hand_card is card)
            self.player.hand.pop(card_index)
            self.deck.discard(card)
            self.last_played_card = card

            if card.value == "+4":
                self.pending_draw += 4
                self.pending_draw_type = "+4"

            if card.value in ("wild", "+4"):
                self.current_color = self.pending_color
            else:
                self.current_color = card.color

            self.pending_color = None
            self.active_card = None
            self.has_drawn = False

            # CONDITTIONE DI VITTORIA 1: Cattura del Re!
            if target and target.piece_type == chess.KING:
                self.winner = mover
                self.finish_reason = "re catturato"
                return san

            # CONDIZIONE DI VITTORIA 2: Carte esaurite
            if len(self.players[mover].hand) == 0:
                self.winner = mover
                self.finish_reason = "carte esaurite"
                return san

            self._update_check_state(mover)

            self._advance_turn()
            self._auto_draw_until_action()

            return san

    def draw_card(self, defer_after_penalty: bool = False) -> Card | None:
        resolving_penalty = self.pending_draw > 0
        card = self._draw_card_once()
        if not (defer_after_penalty and resolving_penalty):
            self._auto_draw_until_action()
        return card

    def continue_after_penalty(self) -> None:
        """Resume automatic draws after the penalty and skipped turn are shown."""
        self._auto_draw_until_action()

    def _draw_card_once(self) -> Card | None:
        if not self.started:
            raise RuntimeError("La partita non è iniziata.")

        if self.winner is not None:
            raise ValueError("La partita è terminata.")

        if self.has_drawn:
            raise ValueError("Hai già pescato in questo turno.")
       
        if self.pending_draw > 0:

            for _ in range(self.pending_draw):
                self.player.hand.append(self.deck.draw())

            print(f"Pesca {self.pending_draw} eseguita")

            self.pending_draw = 0
            self.pending_draw_type = None

            self._advance_turn()

            self.has_drawn = False

            return None

        card = self.deck.draw()
        self.player.hand.append(card)
        self.has_drawn = True

        if not self.card_has_move(card):
            if self.checked_player == self.current_player:
                self._pass_after_failed_check()
            else:
                self._advance_turn()
                self.has_drawn = False

        return card

    def _has_playable_action(self) -> bool:
        if self.has_legal_move():
            return True

        if self.pending_draw > 0:
            return any(
                card.value in ("+2", "+4") and self.can_play_card(card)
                for card in self.player.hand
            )

        return any(
            card.value in ("+2", "stop") and self.can_play_card(card)
            for card in self.player.hand
        )

    def _advance_turn(self) -> None:
        self.current_player = 1 - self.current_player
        self.chess.board.turn = self.players[self.current_player].color

        if self.skip_turns > 0:
            self.skip_turns -= 1
            self.current_player = 1 - self.current_player
            self.chess.board.turn = self.players[self.current_player].color

    def _finish_if_king_capturable(self) -> bool:
        for card in self.player.hand:
            for move in self.legal_chess_moves_for_card(card):
                target = self.chess.board.piece_at(move.to_square)
                if target is not None and target.piece_type == chess.KING:
                    self.winner = self.current_player
                    self.finish_reason = "re catturabile"
                    self.winning_card = card
                    self.winning_move = move
                    self.active_card = None
                    self.pending_color = None
                    return True
        return False

    def _auto_draw_until_action(self) -> None:
        if not self.started or self.winner is not None:
            return

        # A pending +2/+4 remains available for the existing stacking choice.
        if self.pending_draw > 0:
            return

        # Bound automatic passes if the board has no move for either player.
        for _ in range(2 * len(self.deck.draw_pile) + 2 * len(self.deck.discard_pile) + 176):
            if self._finish_if_king_capturable() or self._has_playable_action():
                return
            self._draw_card_once()
            if self.winner is not None:
                return

    def has_legal_move(self) -> bool:
        return any(
            self.legal_chess_moves_for_card(card)
            for card in self.player.hand
        )

    def last_card_text(self) -> str:
        if self.last_played_card is None:
            return "Nessuna carta giocata"

        if self.last_played_card.value in ("wild", "+4"):
            return f"{self.last_played_card.value} → {self.current_color}"

        return self.last_played_card.label

    def _update_check_state(self, mover: int) -> None:
        if self.chess.board.is_check():
            self.checked_player = 1 - mover
            self.checking_player = mover
        else:
            self.checked_player = None
            self.checking_player = None

    def _pass_after_failed_check(self) -> None:
            # Pulisce lo stato dello scacco e passa il turno all'avversario.
            # Spetterà all'avversario catturare il Re nel suo turno se possiede la carta adatta!
            self.checked_player = None
            self.checking_player = None

            self._advance_turn()
            self.has_drawn = False

    def debug_draw(self, amount: int) -> None:
        for _ in range(amount):
            self.player.hand.append(self.deck.draw())

        print(f"[DEBUG] pescate {amount} carte")

    def _move_resolves_check(self, move: chess.Move) -> bool:
        board = self.chess.board.copy(stack=False)
        color = self.players[self.current_player].color
        board.turn = color
        board.push(move)
        king = board.king(color)
        return king is not None and not board.is_attacked_by(not color, king)

    def debug_load_fen(self, fen: str) -> None:
        board = self.chess.board
        board.set_fen(fen)

        self.current_player = 0 if board.turn == chess.WHITE else 1
        self.has_drawn = False
        self.active_card = None

        if board.is_check():
            self.checked_player = self.current_player
            self.checking_player = 1 - self.current_player
        else:
            self.checked_player = None
            self.checking_player = None

        print(f"[DEBUG] FEN caricata, turno {self.players[self.current_player].name}")
