from game.cards import Card, Deck, build_deck

def test_deck_size():
    deck = build_deck()
    assert len(deck) == 88
    assert sum(card.value.isdigit() for card in deck) == 64
    assert sum(card.value == "+2" for card in deck) == 8
    assert sum(card.value == "stop" for card in deck) == 8
    assert sum(card.value == "wild" for card in deck) == 4
    assert sum(card.value == "+4" for card in deck) == 4


def test_empty_draw_pile_rebuilds_deck_when_discards_cannot_be_recycled():
    deck = Deck()
    top = Card("red", "1")
    deck.draw_pile.clear()
    deck.discard_pile[:] = [top]

    drawn = deck.draw()

    assert isinstance(drawn, Card)
    assert len(deck.draw_pile) == 86
    assert deck.discard_pile == [top]
