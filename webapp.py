"""Small room-based web server for two-player UNO Chess."""
from __future__ import annotations

import secrets
import socket
import string
import threading
import chess
import chess.svg
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

from game.cards import Card, COLORS
from game.card_images import card_image_url
from game.uno_game import UnoChessGame

app = Flask(__name__, template_folder="web")
rooms: dict[str, dict] = {}
rooms_lock = threading.RLock()


def error(message: str, status: int = 400):
    return jsonify(error=message), status


def serialize_card(card: Card | None):
    return {"color": card.color, "value": card.value, "label": card.label,
            "image": card_image_url(card.color, card.value)} if card else None


def invite_base_url() -> str:
    host = request.host.split(":", 1)[0]
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        address = "127.0.0.1"
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("8.8.8.8", 80))
            address = probe.getsockname()[0]
        except OSError:
            pass
        finally:
            probe.close()
        return f"http://{address}:{request.environ.get('SERVER_PORT', '5000')}"
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme).split(",", 1)[0]
    return f"{scheme}://{request.host}"


def state_for(room: dict, token: str | None):
    game: UnoChessGame = room["game"]
    seat = room["tokens"].index(token) if token in room["tokens"] else None
    player = room["token_players"][seat] if seat is not None else None
    board = game.board_snapshot()
    legal = []
    hand = []
    if player is not None and player == game.current_player and game.winner is None:
        hand = [serialize_card(card) | {"index": i, "playable": game.can_play_card(card), "moves": [m.uci() for m in game.legal_chess_moves_for_card(card)]} for i, card in enumerate(game.players[player].hand)]
        legal = sorted({m.uci() for card in game.players[player].hand for m in game.legal_chess_moves_for_card(card)})
    return {
        "room": room["code"], "player": player, "players": [p.name for p in game.players],
        "connected": room["connected"], "started": game.started,
        "turn": game.current_player, "winner": game.winner,
        "finish_reason": game.finish_reason,
        "board": [[(board.piece_at(chess.square(file, rank)).symbol() if board.piece_at(chess.square(file, rank)) else None) for file in range(8)] for rank in range(7, -1, -1)],
        "fen": board.fen(), "hand": hand,
        "hand_sizes": list(game.hand_sizes), "last_card": serialize_card(game.last_played_card),
        "current_color": game.current_color, "pending_draw": game.pending_draw,
        "has_drawn": game.has_drawn, "checked": game.checked_player,
        "legal_moves": legal,
        "history": room.get("history", []),
    }


def get_room(code: str):
    room = rooms.get(code.upper())
    if room is None:
        return None, error("Stanza non trovata.", 404)
    token = request.headers.get("X-Player-Token")
    if token not in room["tokens"]:
        return None, error("Token giocatore non valido.", 403)
    return room, None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/manifest.webmanifest")
def manifest():
    return send_from_directory("web", "manifest.webmanifest", mimetype="application/manifest+json")


@app.get("/app-icon.svg")
def app_icon():
    return send_from_directory("web", "app-icon.svg", mimetype="image/svg+xml")


@app.get("/pieces/<symbol>.svg")
def chess_piece(symbol: str):
    try:
        piece = chess.Piece.from_symbol(symbol)
    except ValueError:
        return error("Pezzo non valido.", 404)
    response = Response(chess.svg.piece(piece, size=80), mimetype="image/svg+xml")
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


@app.get("/cards/<path:filename>")
def card_asset(filename: str):
    return send_from_directory(Path(__file__).parent / "cards" / "PineTools.com_files", filename)


@app.post("/api/rooms")
def create_room():
    name = str((request.json or {}).get("name", "Giocatore 1")).strip()[:24] or "Giocatore 1"
    code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    token = secrets.token_urlsafe(24)
    with rooms_lock:
        while code in rooms:
            code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5))
        rooms[code] = {"code": code, "game": UnoChessGame(), "tokens": [token], "token_players": [0], "names": [name, None], "connected": [True, False]}
    return jsonify(code=code, token=token, player=0, invite_base=invite_base_url())


@app.post("/api/rooms/<code>/join")
def join_room(code: str):
    name = str((request.json or {}).get("name", "Giocatore 2")).strip()[:24] or "Giocatore 2"
    with rooms_lock:
        room = rooms.get(code.upper())
        if room is None:
            return error("Stanza non trovata.", 404)
        if len(room["tokens"]) > 1:
            return error("La stanza è già piena.", 409)
        token = secrets.token_urlsafe(24)
        room["tokens"].append(token)
        room["names"][1] = name
        room["connected"][1] = True
        room["token_players"] = [0, 1]
        secrets.SystemRandom().shuffle(room["token_players"])
        for seat, game_player in enumerate(room["token_players"]):
            room["game"].players[game_player].name = room["names"][seat]
        room["game"].start()
        room["history"] = [{"player": None, "text": f"Inizio · {room['game'].last_card_text()}"}]
    return jsonify(code=room["code"], token=token, player=room["token_players"][1], invite_base=invite_base_url())


@app.get("/api/rooms/<code>")
def get_state(code: str):
    with rooms_lock:
        room, err = get_room(code)
        return err or jsonify(state_for(room, request.headers.get("X-Player-Token")))


@app.post("/api/rooms/<code>/action")
def action(code: str):
    with rooms_lock:
        room, err = get_room(code)
        if err:
            return err
        game: UnoChessGame = room["game"]
        seat = room["tokens"].index(request.headers.get("X-Player-Token"))
        player = room["token_players"][seat]
        if player != game.current_player or game.winner is not None:
            return error("Non è il tuo turno.", 409)
        data = request.json or {}
        try:
            kind = data.get("type")
            if kind == "start":
                if len(room["tokens"]) != 2:
                    return error("Serve un secondo giocatore.", 409)
                game.start()
            elif kind == "card":
                card = game.player.hand[int(data["index"])]
                if card.value in ("+2", "stop"):
                    game.play_special_card(card)
                    room.setdefault("history", []).append({"player": player, "text": card.label})
                else:
                    game.play_card(card)
            elif kind == "color":
                game.choose_color(str(data["color"]))
            elif kind == "move":
                move = chess.Move.from_uci(str(data["uci"]))
                if data.get("index") is not None:
                    chosen = game.player.hand[int(data["index"])]
                    if game.active_card is None:
                        game.play_card(chosen)
                    elif game.active_card is not chosen:
                        return error("La carta selezionata non corrisponde.")
                played = game.active_card or (game.player.hand[int(data["index"])] if data.get("index") is not None else None)
                san = game.play_move(move)
                played_text = played.label if played else "carta"
                if played and played.value in ("wild", "+4"):
                    played_text += f" → {game.current_color or ''}"
                room.setdefault("history", []).append({"player": player, "text": f"{san} [{played_text}]"})
            elif kind == "draw":
                penalty = game.pending_draw
                drawn = game.draw_card()
                room.setdefault("history", []).append({"player": player, "text": f"Pesca {penalty} carte" if penalty else (f"Pesca [{drawn.label}]" if drawn else "Pesca")})
            elif kind == "clear_card":
                game.clear_active_card()
            else:
                return error("Azione non riconosciuta.")
        except (ValueError, IndexError, KeyError, RuntimeError) as exc:
            return error(str(exc))
        return jsonify(state=state_for(room, request.headers.get("X-Player-Token")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
