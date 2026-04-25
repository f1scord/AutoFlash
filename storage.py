import os
from deck import Deck

DECK_PATH = os.path.join("data", "deck.json")


def load_deck() -> Deck:
    deck = Deck()
    deck.load(DECK_PATH)
    return deck


def save_deck(deck: Deck) -> None:
    deck.save(DECK_PATH)
