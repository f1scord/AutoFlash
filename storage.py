import json
import os
from deck import Deck
from exceptions import StorageError

DECK_PATH = os.path.join("data", "deck.json")
CONFIG_PATH = os.path.join("data", "config.json")


def load_deck() -> Deck:
    deck = Deck()
    deck.load(DECK_PATH)
    return deck


def save_deck(deck: Deck) -> None:
    deck.save(DECK_PATH)


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as e:
        raise StorageError(f"Corrupt config file: {e}") from e


def save_config(config: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError as e:
        raise StorageError(f"Cannot save config: {e}") from e
