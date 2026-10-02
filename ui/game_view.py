from __future__ import annotations
import tkinter as tk
from tkinter import colorchooser
import json
from pathlib import Path

from game.uno_game import UnoChessGame
from .board import ChessBoardView
from .cards_view import CardsView, LastCardView
from .history_view import HistoryView


COLOR_NAMES_IT = {"red": "rosso", "yellow": "giallo", "green": "verde", "blue": "blu"}
COLOR_LETTER = {"red": "R", "yellow": "Y", "green": "G", "blue": "B"}
VALUE_TAG = {"stop": "S", "wild": "W"}
POSITION_STEP = 2


class GameView:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.game = UnoChessGame()
        self._wild_color: str | None = None

        self.root.title("UNO Chess")
        self.root.state("zoomed")

        self.settings_file = Path("ui_settings.json")
        self.hand_scale = 1.25
        self.table_scale = 1.8
        self.board_pad = 60
        self.board_x_gap = 30
        # Padding below the hand moves it upward; unlike top padding on a
        # bottom-packed widget, this changes its actual screen position.
        self.hand_pad = 10
        self.table_x_pad = 40
        self.table_y_pad = 5
        self.background_color = "#f0f0f0"

        if self.settings_file.exists():
            try:
                data = json.loads(self.settings_file.read_text())
                self.hand_scale = float(data.get("hand_scale", 1.25))
                self.table_scale = float(data.get("table_scale", 1.8))
                self.board_pad = int(data.get("board_pad", 60))
                self.board_x_gap = int(data.get("board_x_gap", 30))
                self.hand_pad = int(data.get("hand_pad", 10))
                self.table_x_pad = int(data.get("table_x_pad", 40))
                self.table_y_pad = int(data.get("table_y_pad", 5))
                self.background_color = data.get("background_color", "#f0f0f0")
            except (OSError, ValueError, TypeError):
                pass

        self.hand_scale = max(0.7, self.hand_scale)
        self.table_scale = max(0.8, self.table_scale)
        self.board_pad = max(0, self.board_pad)
        self.board_x_gap = max(0, self.board_x_gap)
        self.hand_pad = max(0, self.hand_pad)
        self.table_x_pad = max(0, self.table_x_pad)
        self.table_y_pad = max(0, self.table_y_pad)

        main_container = tk.Frame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.history = HistoryView(main_container, width=20, height=22)
        self.history.pack(side="left", fill="y", padx=(0, self.board_x_gap))

        self.board_frame = tk.Frame(main_container)
        self.board_frame.pack(
            side="left",
            anchor="n",
            padx=(0, 10),
            pady=(self.board_pad, 0),
        )
        self.board = ChessBoardView(
            self.board_frame,
            self.game.board_snapshot(),
            self.on_move_request,
            self.game,
        )

        right_panel = tk.Frame(main_container)
        right_panel.pack(side="left", fill="both", expand=True)

        # Controlli compatti sulla destra, disposti orizzontalmente
        controls_frame = tk.Frame(right_panel)
        controls_frame.pack(side="top", anchor="ne", fill="x", pady=(10, 6))

        tk.Button(
            controls_frame,
            text="Nuova partita",
            command=self.new_game,
            font=("Arial", 10, "bold"),
            bg="#2b5c8f",
            fg="white",
            padx=8,
            pady=4,
        ).pack(side="left", padx=(0, 8))

        settings_frame = tk.Frame(controls_frame)
        settings_frame.pack(side="right")

        for index, (text, command) in enumerate((
            ("Mano −", self.decrease_hand),
            ("Mano +", self.increase_hand),
            ("Tavolo −", self.decrease_table),
            ("Tavolo +", self.increase_table),
            ("Board ↑", self.board_up),
            ("Board ↓", self.board_down),
            ("Board ←", self.board_left),
            ("Board →", self.board_right),
            ("Mano ↑", self.hand_up),
            ("Mano ↓", self.hand_down),
            ("Carta ↔ −", self.table_left),
            ("Carta ↔ +", self.table_right),
            ("Carta ↕ −", self.table_up),
            ("Carta ↕ +", self.table_down),
        )):
            tk.Button(
                settings_frame,
                text=text,
                command=command,
                padx=5,
                pady=2,
            ).grid(row=index // 6, column=index % 6, padx=2, pady=1)

        tk.Button(
            settings_frame,
            text="Sfondo…",
            command=self.choose_background_color,
            padx=5,
            pady=2,
        ).grid(row=2, column=2, padx=2, pady=1)

        last_card_container = tk.Frame(right_panel)
        last_card_container.pack(
            # The board is to the left of this panel, so left anchoring makes
            # the horizontal gap control move the card away from/toward it.
            anchor="nw",
            padx=(self.table_x_pad, 0),
            pady=self.table_y_pad,
        )

        self.last_card = LastCardView(
            last_card_container,
            scale=self.table_scale,
        )
        self.last_card.pack(anchor="w")

        self.draw_button = tk.Button(
            last_card_container,
            text="Pesca",
            command=self.on_draw_card,
            font=("Arial", 11, "bold"),
            width=18,
        )
        self.draw_button.pack(anchor="center", padx=(0, 0), pady=10)
        self.draw_button.pack_forget()

        cards_container = tk.Frame(right_panel)
        cards_container.pack(
            side="bottom",
            anchor="sw",
            fill="x",
            pady=(0, self.hand_pad),
        )

        self.cards = CardsView(cards_container, self.on_card_selected)
        self.cards.scale = self.hand_scale
        self.cards.pack(side="left", anchor="w")

        self.root.bind("<Button-1>", self._reset_if_outside_board, add="+")
        self._apply_background_color()

    def refresh_layout(self) -> None:
        """Apply current UI size/position settings immediately."""
        self.cards.scale = self.hand_scale
        self.cards.show(list(self.game.current_hand))

        self.last_card.scale = self.table_scale
        self._update_last_card()

        self.board_frame.pack_configure(
            pady=(self.board_pad, 0)
        )
        self.history.pack_configure(padx=(0, self.board_x_gap))
        self.cards.master.pack_configure(pady=(0, self.hand_pad))
        self.last_card.master.pack_configure(
            padx=(self.table_x_pad, 0),
            pady=self.table_y_pad,
        )

        self.root.update_idletasks()

    def _update_last_card(self) -> None:
        self.last_card.title_label.config(text="Carta sul tavolo")
        card = self.game.last_played_card
        note = ""

        if card is not None and card.value in ("wild", "+4"):
            text = self.game.last_card_text()
            color = text.split("→")[-1].strip() if "→" in text else ""
            note = f"Colore: {COLOR_NAMES_IT.get(color, color)}"

        self.last_card.show(card, note)

    def _card_tag(self, card, chosen_color: str | None = None) -> str:
        letter = COLOR_LETTER.get(card.color or chosen_color, "")
        value = VALUE_TAG.get(str(card.value), str(card.value))
        return f"[{letter}{value}]"

    def _log_hand_deltas(self, before, played_by=None, manual_draw_by=None) -> None:
        after = self.game.hand_sizes

        for i in range(len(after)):
            delta = after[i] - before[i]

            if i == played_by:
                delta += 1

            if i == manual_draw_by:
                delta -= 1

            if delta > 0:
                self.history.add_token(i, f"(+{delta})")

    def new_game(self) -> None:
        self.game.start()
        self._wild_color = None
        self._sync_draw_button_label()
        self.history.clear()
        self.history.set_header(
            f"Inizio: {self._card_tag(self.game.last_played_card)}"
        )

        self.draw_button.pack(anchor="center", padx=(0, 0), pady=10)
        self.draw_button.config(state="normal")
        self.cards.show(list(self.game.current_hand))
        self.board.reset_selection()
        self.board.update_board(self.game.board_snapshot())
        self._update_last_card()
        self._show_finished_game()

    def on_card_selected(self, card) -> None:
        if self.game.winner is not None:
            return

        if self.game.active_card == card:
            self.game.clear_active_card()
            self.board.reset_selection()
            return

        if card not in self.game.current_hand:
            return

        if not self.game.can_play_card(card):
            return

        if card.value in ("+2", "stop"):
            player_index = self.game.current_player_index
            before = self.game.hand_sizes

            try:
                self.game.play_special_card(card)
            except ValueError:
                return

            self.history.add_token(player_index, self._card_tag(card))
            self._log_hand_deltas(before, played_by=player_index)
            self.history.sync_turn(self.game.current_player_index)

            self.cards.show(list(self.game.current_hand))
            self.board.reset_selection()
            self.board.update_board(self.game.board_snapshot())
            self.draw_button.config(state="normal")
            self._update_last_card()
            self._sync_draw_button_label()
            if self._show_finished_game():
                return
            return

        if card.value in ("wild", "+4"):
            try:
                self.game.play_card(card)
            except ValueError:
                return

            self.choose_wild_color(card)
            return

        try:
            self.game.play_card(card)
        except ValueError:
            return

        allowed = set(self.game.legal_chess_moves_for_card(card))
        self.board.selected_square = None
        self.board.draw(allowed)

    def choose_wild_color(self, card, move=None) -> None:
        window = tk.Toplevel(self.root)
        window.title("Scegli il colore")
        window.transient(self.root)
        window.grab_set()

        for color in ("red", "yellow", "green", "blue"):
            tk.Button(
                window,
                text=color.capitalize(),
                width=12,
                command=lambda c=color: self.set_wild_color(window, card, c, move),
            ).pack(padx=10, pady=5)

    def set_wild_color(self, window, card, color, move=None) -> None:
        window.destroy()

        try:
            self.game.choose_color(color)
        except ValueError:
            return

        self._wild_color = color
        allowed = set(self.game.legal_chess_moves_for_card(card))
        self.board.selected_square = None
        self.board.draw(allowed)
        if move is not None:
            self.on_move_request(move)

    def on_move_request(self, move) -> None:
        if self.game.winner is not None:
            return

        if self.game.active_card is None:
            cards = self.game.cards_for_move(move)
            unique_cards = {}
            for card in cards:
                unique_cards.setdefault((card.color, card.value), card)
            cards = list(unique_cards.values())
            if not cards:
                return
            if len(cards) > 1:
                self.choose_card_for_move(move, cards)
                return

            card = cards[0]
            try:
                self.game.play_card(card)
            except ValueError:
                return
            if card.value in ("wild", "+4"):
                self.choose_wild_color(card, move)
                return

        self._execute_move(move)

    def choose_card_for_move(self, move, cards) -> None:
        window = tk.Toplevel(self.root)
        window.title("Scegli la carta")
        window.transient(self.root)
        window.grab_set()

        tk.Label(
            window,
            text="Più carte consentono questa mossa. Quale vuoi giocare?",
            font=("Arial", 10, "bold"),
        ).pack(padx=12, pady=(12, 8))

        for card in cards:
            tk.Button(
                window,
                text=self._card_tag(card),
                width=12,
                command=lambda c=card: self._select_card_for_move(window, move, c),
            ).pack(padx=12, pady=4)

    def _select_card_for_move(self, window, move, card) -> None:
        window.destroy()
        try:
            self.game.play_card(card)
        except ValueError:
            return

        if card.value in ("wild", "+4"):
            self.choose_wild_color(card, move)
        else:
            self.on_move_request(move)

    def _execute_move(self, move) -> None:
        mover_index = self.game.current_player_index
        before = self.game.hand_sizes

        try:
            san = self.game.play_move(move)
        except ValueError:
            return

        self._sync_draw_button_label()

        tag = self._card_tag(self.game.last_played_card, self._wild_color)
        self._wild_color = None

        self.history.add_token(mover_index, f"{san}{tag}")
        self.history.end_turn()
        self._log_hand_deltas(before, played_by=mover_index)

        self.cards.show(list(self.game.current_hand))
        self.board.reset_selection()
        self.board.update_board(self.game.board_snapshot())
        self._update_last_card()

        if self._show_finished_game():
            return

        self.history.sync_turn(self.game.current_player_index)
        self.draw_button.config(state="normal")

    def on_draw_card(self) -> None:
        if not self.game.started:
            return

        try:
            old_player = self.game.current_player_index
            before = self.game.hand_sizes
            penalty_to_draw = self.game.pending_draw
            card = self.game.draw_card(defer_after_penalty=penalty_to_draw > 0)
        except (ValueError, RuntimeError):
            return

        if card is not None:
            self.history.add_token(
                old_player,
                f"pesca{self._card_tag(card)}",
            )

        self._log_hand_deltas(
            before,
            manual_draw_by=old_player if card is not None else None,
        )

        self.cards.show(list(self.game.current_hand))
        self.board.reset_selection()
        self.board.update_board(self.game.board_snapshot())

        if self._show_finished_game():
            return

        if penalty_to_draw > 0:
            self.history.add_token(old_player, "(salta turno)")
            self._sync_draw_button_label()
            self.draw_button.config(state="disabled")
            self.history.sync_turn(self.game.current_player_index)
            self.root.after(350, self._continue_after_penalty)
            return

        self.history.sync_turn(self.game.current_player_index)

        if self.game.current_player_index != old_player:
            self.draw_button.config(state="normal")
        else:
            self.draw_button.config(state="disabled")

    def _continue_after_penalty(self) -> None:
        if self.game.winner is not None:
            return

        before = self.game.hand_sizes
        self.game.continue_after_penalty()
        self._log_hand_deltas(before)
        self.cards.show(list(self.game.current_hand))
        self.board.reset_selection()
        self.board.update_board(self.game.board_snapshot())
        if self._show_finished_game():
            return
        self.history.sync_turn(self.game.current_player_index)
        self.draw_button.config(state="normal")

    def _sync_draw_button_label(self) -> None:
        pending = self.game.pending_draw
        if pending > 0:
            self.draw_button.config(text=f"Avv. pesca {pending}")
        else:
            self.draw_button.config(text="Pesca")

    def _show_finished_game(self) -> bool:
        if self.game.winner is None:
            return False

        self.draw_button.pack_forget()
        reason = self.game.finish_reason
        if reason == "re catturabile" and self.game.winning_card is not None:
            card = self.game.winning_card
            move = self.game.winning_move
            move_text = f"{move.uci()[:2]}→{move.uci()[2:4]}" if move else ""
            self.history.set_footer(
                f"Vince {self.game.winner_name}: Re catturabile con {self._card_tag(card)}"
            )
            self.last_card.title_label.config(text="Carta che cattura il Re")
            self.last_card.show(card, f"Mossa: {move_text}")
            if move is not None:
                self.board.draw({move})
        else:
            message = {
                "re catturato": "Re catturato",
                "carte esaurite": "Carte esaurite",
            }.get(reason, "Partita terminata")
            self.history.set_footer(f"Vince {self.game.winner_name}: {message}")
        return True

    def _reset_if_outside_board(self, event) -> None:
        if event.widget is not self.board.canvas:
            self.game.clear_active_card()
            self.board.reset_selection()

    def save_ui_settings(self):
        self.settings_file.write_text(
            json.dumps(
                {
                    "hand_scale": self.hand_scale,
                    "table_scale": self.table_scale,
                    "board_pad": self.board_pad,
                    "board_x_gap": self.board_x_gap,
                    "hand_pad": self.hand_pad,
                    "table_x_pad": self.table_x_pad,
                    "table_y_pad": self.table_y_pad,
                    "background_color": self.background_color,
                }
            )
        )

    def increase_hand(self):
        self.hand_scale = min(3.0, self.hand_scale + 0.02)
        self.refresh_layout()
        self.save_ui_settings()

    def decrease_hand(self):
        self.hand_scale = max(0.7, self.hand_scale - 0.02)
        self.refresh_layout()
        self.save_ui_settings()

    def increase_table(self):
        self.table_scale = min(3.0, self.table_scale + 0.05)
        self.refresh_layout()
        self.save_ui_settings()

    def decrease_table(self):
        self.table_scale = max(0.8, self.table_scale - 0.05)
        self.refresh_layout()
        self.save_ui_settings()

    def board_down(self):
        self.board_pad += POSITION_STEP
        self.refresh_layout()
        self.save_ui_settings()

    def board_up(self):
        self.board_pad = max(0, self.board_pad - POSITION_STEP)
        self.refresh_layout()
        self.save_ui_settings()

    def board_left(self):
        self.board_x_gap = max(0, self.board_x_gap - POSITION_STEP)
        self.refresh_layout()
        self.save_ui_settings()

    def board_right(self):
        self.board_x_gap += POSITION_STEP
        self.refresh_layout()
        self.save_ui_settings()

    def hand_up(self):
        self.hand_pad += POSITION_STEP
        self.refresh_layout()
        self.save_ui_settings()

    def hand_down(self):
        self.hand_pad = max(0, self.hand_pad - POSITION_STEP)
        self.refresh_layout()
        self.save_ui_settings()

    def table_left(self):
        self.table_x_pad = max(0, self.table_x_pad - POSITION_STEP)
        self.refresh_layout()
        self.save_ui_settings()

    def table_right(self):
        self.table_x_pad += POSITION_STEP
        self.refresh_layout()
        self.save_ui_settings()

    def table_up(self):
        self.table_y_pad = max(0, self.table_y_pad - POSITION_STEP)
        self.refresh_layout()
        self.save_ui_settings()

    def table_down(self):
        self.table_y_pad += POSITION_STEP
        self.refresh_layout()
        self.save_ui_settings()

    def choose_background_color(self):
        _rgb, color = colorchooser.askcolor(
            color=self.background_color,
            title="Scegli il colore dello sfondo",
            parent=self.root,
        )
        if color:
            self.background_color = color
            self._apply_background_color()
            self.save_ui_settings()

    def _apply_background_color(self):
        supported_widgets = (tk.Frame, tk.Label, tk.Canvas, tk.Text)

        def apply_to(widget):
            if isinstance(widget, supported_widgets):
                try:
                    widget.configure(background=self.background_color)
                except tk.TclError:
                    pass
            for child in widget.winfo_children():
                apply_to(child)

        self.root.configure(background=self.background_color)
        apply_to(self.root)
