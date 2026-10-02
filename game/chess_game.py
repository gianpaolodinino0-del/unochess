from __future__ import annotations

import chess


class ChessGame:
    """Thin wrapper around python-chess; UNO rules live elsewhere."""

    def __init__(self) -> None:
        self.board = chess.Board()

    def legal_moves(self) -> list[chess.Move]:
        return list(self.board.legal_moves)

    def pseudo_legal_moves(self) -> list[chess.Move]:
        return list(self.board.generate_pseudo_legal_moves())

    def push(self, move: chess.Move, ignore_check: bool = False) -> str:
        allowed_moves = self.pseudo_legal_moves() if ignore_check else self.legal_moves()

        if move not in allowed_moves:
            target = self.board.piece_at(move.to_square)
            moving = self.board.piece_at(move.from_square)
            is_king_capture = (
                target is not None
                and target.piece_type == chess.KING
                and moving is not None
                and moving.piece_type != chess.KING
                and moving.color == self.board.turn
                and move.from_square in self.board.attackers(self.board.turn, move.to_square)
            )
            if not is_king_capture:
                raise ValueError("Mossa illegale.")

            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            if moving.piece_type == chess.PAWN:
                san = f"{from_square[0]}x{to_square}"
                if move.promotion:
                    san += f"={chess.piece_symbol(move.promotion).upper()}"
            else:
                san = f"{moving.symbol().upper()}x{to_square}"
            self.board.push(move)
            return san + "#"

        san = self.board.san(move)
        self.board.push(move)
        return san

    def reset(self) -> None:
        self.board.reset()
