import chess
import pytest
from game.cards import Card
from game.game_state import GameState
from game.uno_game import UnoChessGame

def test_numeric_card_filters_moves():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    card = Card("red", "1")
    game.player.hand.append(card)
    game.current_color = "red"
    game.last_played_card = card

    moves = game.legal_chess_moves_for_card(card)

    assert moves
    assert all(chess.square_rank(m.from_square) == 0 or chess.square_file(m.from_square) == 0 for m in moves)
    assert any(m.from_square == chess.A2 for m in moves)
    assert all(m.from_square != chess.E2 for m in moves)


def test_wild_color_selection_applies_after_move():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    wild = Card(None, "wild")
    game.player.hand.append(wild)

    game.play_card(wild)
    game.choose_color("blue")
    game.players[1].hand[:] = [Card("blue", "1")]
    hand_size_before = len(game.player.hand)
    game.play_move(chess.Move.from_uci("e2e4"))

    assert game.last_played_card == wild
    assert game.current_color == "blue"
    assert game.pending_color is None
    assert len(game.players[0].hand) == hand_size_before - 1
    assert all(card is not wild for card in game.players[0].hand)
    assert any(card is wild for card in game.deck.discard_pile)


def test_wild_color_selection_requires_valid_pending_wild():
    game = UnoChessGame()
    game.start()

    with pytest.raises(ValueError):
        game.choose_color("purple")
    with pytest.raises(ValueError):
        game.choose_color("blue")

    wild = Card(None, "wild")
    game.player.hand.append(wild)
    game.play_card(wild)
    with pytest.raises(ValueError):
        game.choose_color("purple")


def test_start_resets_pending_game_state():
    game = UnoChessGame()
    game.start()
    game.pending_draw = 6
    game.pending_draw_type = "+4"
    game.pending_color = "blue"
    game.has_drawn = True
    game.winner = 1
    game.finish_reason = "test"
    game.checked_player = 1
    game.checking_player = 0
    game.active_card = Card(None, "wild")

    game.start()

    assert game.pending_draw == 0
    assert game.pending_draw_type is None
    assert game.pending_color is None
    assert game.winner is None
    assert game.finish_reason is None
    assert game.checked_player is None
    assert game.checking_player is None
    assert game.active_card is None
    assert game.started is True
    assert game.chess.board.board_fen() == chess.Board().board_fen()


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 42, 99, 2025])
def test_start_leaves_game_over_or_current_player_with_an_action(seed):
    game = UnoChessGame()
    game.deck.rng.seed(seed)

    game.start()

    assert game.winner is not None or game._has_playable_action()


def test_plus_four_keeps_existing_penalty_and_stacking_rules():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    plus_four = Card(None, "+4")
    game.player.hand.append(plus_four)
    game.play_card(plus_four)
    game.choose_color("green")
    game.play_move(chess.Move.from_uci("e2e4"))

    assert game.pending_draw == 4
    assert game.pending_draw_type == "+4"
    assert game.current_color == "green"

    stacked_plus_two = Card("green", "+2")
    game.player.hand.append(stacked_plus_two)
    assert game.can_play_card(stacked_plus_two)

    different_color_plus_two = Card("blue", "+2")
    stackable_plus_four = Card(None, "+4")
    numeric_card = Card("green", "3")
    game.player.hand.extend((different_color_plus_two, stackable_plus_four, numeric_card))

    assert not game.can_play_card(different_color_plus_two)
    assert game.can_play_card(stackable_plus_four)
    assert not game.can_play_card(numeric_card)

    game.pending_draw = 2
    game.pending_draw_type = "+2"
    assert game.can_play_card(different_color_plus_two)


def test_stop_skips_opponent_and_keeps_turn_with_player_who_played_it():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    stop = Card("red", "stop")
    game.players[0].hand[:] = [stop, Card("red", "5"), Card("red", "1"), Card("red", "2")]
    game.players[1].hand[:] = [Card("red", "1")]
    game.current_color = "red"
    game.last_played_card = Card("red", "2")

    game.play_special_card(stop)

    assert game.current_player == 0
    assert game.chess.board.turn == chess.WHITE
    assert game.skip_turns == 1
    assert all(card is not stop for card in game.players[0].hand)
    assert any(card is stop for card in game.deck.discard_pile)

    game.play_move(chess.Move.from_uci("e2e4"))
    assert game.current_player == 0
    assert game.skip_turns == 0

    game.play_move(chess.Move.from_uci("a2a3"))
    assert game.current_player == 1


def test_stop_after_pending_plus_two_applies_penalty_then_skips_turns():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    plus_two = Card("red", "+2")
    game.players[0].hand[:] = [plus_two, Card("red", "5")]
    game.current_color = "red"
    game.last_played_card = Card("red", "1")

    game.play_special_card(plus_two)
    stop = Card("red", "stop")
    game.players[1].hand[:] = [stop, Card("red", "1")]
    game.deck.draw_pile[:] = [Card("green", "4"), Card("yellow", "3")]

    game.play_special_card(stop)

    assert game.pending_draw == 0
    assert game.pending_draw_type is None
    assert len(game.players[1].hand) == 3
    assert all(card is not stop for card in game.players[1].hand)
    assert any(card is stop for card in game.deck.discard_pile)
    assert game.current_player == 1
    assert game.chess.board.turn == chess.BLACK
    assert game.skip_turns == 1

    game.players[1].hand.append(Card("red", "1"))
    game.play_move(chess.Move.from_uci("a7a6"))
    assert game.current_player == 1
    assert game.chess.board.turn == chess.BLACK
    assert game.skip_turns == 0

    game.play_move(chess.Move.from_uci("a8a7"))
    assert game.current_player == 0
    assert game.chess.board.turn == chess.WHITE


def test_mandatory_non_wild_king_capture_rejects_other_move():
    game = UnoChessGame()
    game.start()
    game.debug_load_fen("7k/8/8/8/8/8/8/K6R w - - 0 1")
    capture_card = Card("red", "8")
    wild = Card(None, "wild")
    game.player.hand[:] = [capture_card, wild]
    game.current_color = "red"
    game.last_played_card = Card("red", "2")
    game.play_card(wild)
    game.choose_color("blue")
    before_fen = game.chess.board.fen()

    with pytest.raises(ValueError, match="catturare il Re"):
        game.play_move(chess.Move.from_uci("a1a2"))

    assert game.chess.board.fen() == before_fen
    assert game.winner is None


def test_auto_draw_loop_stops_at_its_safety_limit_without_an_action():
    game = UnoChessGame()
    game.start()
    game.chess.board.clear()
    game.chess.board.turn = chess.WHITE
    game.current_player = 0
    game.players[0].hand.clear()
    game.players[1].hand.clear()
    game.current_color = "purple"
    game.last_played_card = Card("black", "0")
    game.pending_draw = 0
    game.pending_draw_type = None
    game.deck.draw_pile.clear()
    game.deck.discard_pile.clear()
    game.has_drawn = False

    game._auto_draw_until_action()

    assert len(game.players[0].hand) + len(game.players[1].hand) == 176
    assert game.winner is None


def test_pending_draw_prevents_automatic_draw_until_stacking_choice():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.players[0].hand[:] = [Card("red", "1")]
    game.current_color = "red"
    game.last_played_card = Card("red", "+4")
    game.pending_draw = 4
    game.pending_draw_type = "+4"
    game.deck.draw_pile[:] = [Card("red", "2")]

    game._auto_draw_until_action()

    assert game.pending_draw == 4
    assert len(game.deck.draw_pile) == 1
    assert len(game.players[0].hand) == 1


@pytest.mark.parametrize("value", ["wild", "+4"])
def test_terminal_wild_card_leaves_consistent_state(value):
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    card = Card(None, value)
    game.player.hand[:] = [card]
    game.play_card(card)
    game.choose_color("yellow")

    game.play_move(chess.Move.from_uci("e2e4"))

    assert game.winner == 0
    assert game.finish_reason == "carte esaurite"
    assert game.last_played_card == card
    assert game.current_color == "yellow"
    assert game.pending_color is None
    assert game.active_card is None
    assert game.has_drawn is False
    assert game.pending_draw == (4 if value == "+4" else 0)


def test_playing_normal_card_clears_stale_pending_color():
    game = UnoChessGame()
    game.start()
    card = Card("red", "1")
    game.player.hand.append(card)
    game.current_color = "red"
    game.pending_color = "blue"

    game.play_card(card)

    assert game.pending_color is None


def test_game_state_is_canonical_and_legacy_attributes_remain_compatible():
    game = UnoChessGame()

    assert isinstance(game.state, GameState)
    assert game.state.current_player == game.current_player == 0
    game.current_player = 1
    assert game.state.current_player == 1
    game.state.pending_draw = 4
    assert game.pending_draw == 4


def test_clearing_selected_wild_card_clears_pending_color():
    game = UnoChessGame()
    game.start()
    wild = Card(None, "wild")
    game.player.hand.append(wild)

    game.play_card(wild)
    game.choose_color("blue")
    game.clear_active_card()

    assert game.active_card is None
    assert game.pending_color is None


def test_play_move_rejects_equal_card_instance_without_changing_state():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    hand_card = Card("red", "1")
    selected_card = Card("red", "1")
    game.player.hand.append(hand_card)
    game.current_color = "red"
    game.last_played_card = Card("red", "1")
    game.pending_color = "blue"
    game.active_card = selected_card

    before_fen = game.chess.board.fen()
    before_hand = tuple(game.player.hand)
    before_active_card = game.active_card
    before_current_color = game.current_color
    before_pending_color = game.pending_color

    with pytest.raises(ValueError):
        game.play_move(chess.Move.from_uci("a2a3"))

    assert game.chess.board.fen() == before_fen
    assert len(game.player.hand) == len(before_hand)
    assert all(current is previous for current, previous in zip(game.player.hand, before_hand))
    assert game.current_color == before_current_color
    assert game.pending_color == before_pending_color
    assert game.active_card is before_active_card


def test_check_priority_keeps_only_moves_that_resolve_check():
    game = UnoChessGame()
    game.start()
    game.debug_load_fen("k3r3/8/8/8/8/8/8/4K2R w - - 0 1")
    card = Card("red", "1")
    non_resolving_card = Card("red", "8")
    game.player.hand[:] = [card, non_resolving_card]
    game.current_color = "red"
    game.last_played_card = card

    moves = game.legal_chess_moves_for_card(card)

    assert moves
    assert all(game._move_resolves_check(move) for move in moves)
    assert game.legal_chess_moves_for_card(non_resolving_card) == []


def test_when_no_card_can_resolve_check_non_resolving_move_is_allowed():
    game = UnoChessGame()
    game.start()
    game.debug_load_fen("k3r3/8/8/8/8/8/8/4K2R w - - 0 1")
    card = Card("red", "8")
    game.player.hand[:] = [card]
    game.current_color = "red"
    game.last_played_card = card

    moves = game.legal_chess_moves_for_card(card)

    assert moves
    assert all(not game._move_resolves_check(move) for move in moves)


def test_drawn_playable_card_is_kept_for_immediate_play():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    game.players[0].hand[:] = [Card("blue", "8")]
    game.players[1].hand[:] = [Card("red", "1")]
    game.current_color = "red"
    game.last_played_card = Card("red", "2")
    drawn = Card("red", "1")
    game.deck.draw_pile[:] = [drawn]

    result = game.draw_card()

    assert result is drawn
    assert game.current_player == 0
    assert game.has_drawn is True
    assert any(card is drawn for card in game.players[0].hand)
    assert drawn in game.playable_cards()
    assert game.legal_chess_moves_for_card(drawn)


def test_nonplayable_draw_passes_turn_automatically():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    game.players[0].hand[:] = [Card("blue", "8")]
    game.players[1].hand[:] = [Card("red", "1")]
    game.current_color = "red"
    game.last_played_card = Card("red", "2")
    drawn = Card("blue", "8")
    game.deck.draw_pile[:] = [drawn]

    result = game.draw_card()

    assert result is drawn
    assert game.current_player == 1
    assert game.has_drawn is False
    assert drawn in game.players[0].hand


def test_turn_transition_automatically_draws_for_player_without_moves():
    game = UnoChessGame()
    game.start()
    game.current_player = 0
    game.chess.board.turn = chess.WHITE
    game.has_drawn = False
    white_card = Card("red", "5")
    game.players[0].hand[:] = [white_card, Card("red", "7")]
    game.players[1].hand[:] = [Card("blue", "8")]
    game.current_color = "red"
    game.last_played_card = Card("red", "2")
    drawn = Card("red", "8")
    game.deck.draw_pile[:] = [drawn]
    game.play_card(white_card)

    game.play_move(chess.Move.from_uci("e2e4"))

    assert game.current_player == 1
    assert game.has_drawn is True
    assert drawn in game.players[1].hand
    assert game.legal_chess_moves_for_card(drawn)


def test_capturable_king_ends_game_immediately():
    game = UnoChessGame()
    game.start()
    game.debug_load_fen("7k/8/8/8/8/8/8/K6R w - - 0 1")
    card = Card("red", "8")
    game.player.hand[:] = [card]
    game.current_color = "red"
    game.last_played_card = Card("red", "2")

    game._auto_draw_until_action()

    assert game.winner == 0
    assert game.finish_reason == "re catturabile"


def test_material_king_capture_wins_without_advancing_turn():
    game = UnoChessGame()
    game.start()
    game.debug_load_fen("7k/8/8/8/8/8/8/K6R w - - 0 1")
    card = Card("red", "8")
    game.player.hand[:] = [card, Card("red", "7")]
    game.current_color = "red"
    game.last_played_card = Card("red", "2")
    game.play_card(card)

    san = game.play_move(chess.Move.from_uci("h1h8"))

    assert san
    assert game.winner == 0
    assert game.finish_reason == "re catturato"
    assert game.current_player == 0
