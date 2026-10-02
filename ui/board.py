from __future__ import annotations

import tkinter as tk
import chess
from pathlib import Path


PIECE_GLYPHS = {
    chess.PAWN: ("♙", "♟"),
    chess.KNIGHT: ("♘", "♞"),
    chess.BISHOP: ("♗", "♝"),
    chess.ROOK: ("♖", "♜"),
    chess.QUEEN: ("♕", "♛"),
    chess.KING: ("♔", "♚"),
}


class ChessBoardView:
    """Board renderer for UNO Chess."""

    def __init__(self, parent: tk.Misc, board: chess.Board, on_move_request, game):
        self.board = board
        self.on_move_request = on_move_request
        self.game = game
        self.orientation = chess.WHITE
        self.selected_square: int | None = None
        self.allowed_moves: set[chess.Move] = set()
        self.glow_image = tk.PhotoImage(
            file=str(Path(__file__).parent / "assets" / "soft_glow.png")
        )

        self.canvas = tk.Canvas(parent, width=640, height=640, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._on_click)

        self.draw()

    def draw(self, allowed_moves: set[chess.Move] | None = None) -> None:
        
        self.orientation = self.board.turn
        self.canvas.delete("all")

        if allowed_moves is not None:
            self.allowed_moves = allowed_moves

        indicators = self._get_move_indicators()
        movable_squares = self._get_movable_squares()
        king_capture_targets = {
            move.to_square
            for move in self.allowed_moves
            if (target := self.board.piece_at(move.to_square)) is not None
            and target.piece_type == chess.KING
        }

        for row in range(8):
            for col in range(8):
                self._draw_square(
                    row, col, indicators, movable_squares, king_capture_targets
                )

        self._draw_selected_square()
        self._draw_coordinates()

    def _get_move_indicators(self) -> dict[int, list[int]]:
        indicators: dict[int, list[int]] = {}

        for move in self.allowed_moves:
            piece = self.board.piece_at(move.from_square)

            if piece:
                indicators.setdefault(move.to_square, []).append(piece.piece_type)

        return indicators

    def _get_movable_squares(self) -> set[int]:
        if not self.game.started or self.game.winner is not None:
            return set()

        active_card = self.game.active_card
        if active_card is not None:
            moves = self.game.legal_chess_moves_for_card(active_card)
        else:
            moves = set()
            for card in self.game.current_hand:
                moves.update(self.game.legal_chess_moves_for_card(card))

        return {move.from_square for move in moves}

    def _draw_soft_glow(self, x0: int, y0: int) -> None:
        self.canvas.create_image(
            x0 + 40,
            y0 + 40,
            image=self.glow_image,
        )

    def _draw_square(
        self,
        row: int,
        col: int,
        indicators: dict[int, list[int]],
        movable_squares: set[int],
        king_capture_targets: set[int],
    ) -> None:
        sq = 80

        if self.orientation == chess.WHITE:
            file, rank = col, 7 - row
        else:
            file, rank = 7 - col, row

        square = chess.square(file, rank)
        x0, y0 = col * sq, row * sq
        color = "#f0d9b5" if (file + rank) % 2 == 0 else "#b58863"

        self.canvas.create_rectangle(
            x0,
            y0,
            x0 + sq,
            y0 + sq,
            fill=color,
            outline=""
        )

        piece_types = indicators.get(square, [])

        if len(set(piece_types)) > 1:
            self.canvas.create_oval(
                x0 + 35,
                y0 + 35,
                x0 + 44,
                y0 + 44,
                fill="#000000",
                outline=""
            )
        elif piece_types:
            piece_type = piece_types[0]
            glyph = PIECE_GLYPHS[piece_type][0]

            self.canvas.create_text(
                x0 + sq / 2,
                y0 + sq / 2,
                text=glyph,
                font=("Arial", 18, "bold"),
                fill="#000000"
            )

        piece = self.board.piece_at(square)

        if piece:
            if square in movable_squares:
                self._draw_soft_glow(x0, y0)

            glyph = PIECE_GLYPHS[piece.piece_type][0 if piece.color == chess.WHITE else 1]

            self.canvas.create_text(
                x0 + sq / 2,
                y0 + sq / 2,
                text=glyph,
                font=("Arial", 48)
            )

        if square in king_capture_targets:
            self.canvas.create_oval(
                x0 + 5, y0 + 5, x0 + sq - 5, y0 + sq - 5,
                outline="#c62828",
                width=5,
            )
            self.canvas.create_text(
                x0 + sq - 13,
                y0 + 13,
                text="×",
                font=("Arial", 20, "bold"),
                fill="#9b111e",
            )

    def _draw_selected_square(self) -> None:
        if self.selected_square is None:
            return

        sq = 80
        file = chess.square_file(self.selected_square)
        rank = chess.square_rank(self.selected_square)

        if self.orientation == chess.WHITE:
            col, row = file, 7 - rank
        else:
            col, row = 7 - file, rank

        self.canvas.create_rectangle(
            col * sq,
            row * sq,
            (col + 1) * sq,
            (row + 1) * sq,
            outline="#ffff00",
            width=3
        )

    def _draw_coordinates(self) -> None:
        sq = 80

        for i in range(8):
            if self.orientation == chess.WHITE:
                file_name = chr(ord("a") + i)
                rank_name = str(8 - i)
            else:
                file_name = chr(ord("h") - i)
                rank_name = str(i + 1)

            self.canvas.create_text(
                i * sq + 5,
                8 * sq - 5,
                text=file_name,
                anchor="sw",
                font=("Arial", 10))

            self.canvas.create_text(
                5,
                i * sq + 5,
                text=rank_name,
                anchor="nw",
                font=("Arial", 10))


    def reset_selection(self) -> None:
        self.selected_square = None
        self.allowed_moves.clear()
        self.draw()

    def update_board(self, board: chess.Board) -> None:
        self.board = board
        self.draw()

    def _square_from_xy(self, x: int, y: int) -> int | None:
        col = int(x // 80)
        row = int(y // 80)

        if not (0 <= col < 8 and 0 <= row < 8):
            return None

        if self.orientation == chess.WHITE:
            return chess.square(col, 7 - row)

        return chess.square(7 - col, row)

    def _on_click(self, event) -> None:
        square = self._square_from_xy(event.x, event.y)

        if square is None:
            return

        if self.selected_square is None:
            moves_to_square = [
                move
                for move in self.allowed_moves
                if move.to_square == square
            ]

            if moves_to_square:
                if len(moves_to_square) > 1:
                    # Don't guess which piece the player intended. Keep all
                    # candidates active so the player can select the source.
                    self.allowed_moves = set(moves_to_square)
                    self.draw()
                    return
                self.on_move_request(moves_to_square[0])
                return

            piece = self.board.piece_at(square)

            if piece and piece.color == self.board.turn:
                self.selected_square = square

                if self.game.active_card is None:
                    self.allowed_moves = self.game.legal_chess_moves_for_piece(square)
                else:
                    self.allowed_moves = {
                        move
                        for move in self.allowed_moves
                        if move.from_square == square
                    }

                self.draw()

            return

        selected_square = self.selected_square
        move = chess.Move(selected_square, square)
        piece = self.board.piece_at(selected_square)

        if piece and piece.piece_type == chess.PAWN and chess.square_rank(square) in (0, 7):
            move.promotion = chess.QUEEN

        if move in self.allowed_moves:
            self.selected_square = None
            self.on_move_request(move)
            return

        target = self.board.piece_at(square)

        if target and target.color == self.board.turn:
            self.selected_square = square
        else:
            self.selected_square = None

        self.draw()
