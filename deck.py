import json
import re
import uuid
from datetime import datetime
from exceptions import CardNotFoundError, StorageError


class FlashCard:
    def __init__(self, front: str, back: str, topic: str, difficulty: str,
                 source_file: str = "", card_id: str = None):
        self.id = card_id or str(uuid.uuid4())
        self.front = front
        self.back = back
        self.topic = topic
        self.difficulty = difficulty  # easy | medium | hard
        self.status = "new"           # new | known | review
        self.times_reviewed = 0
        self.correct_answers = 0
        self.source_file = source_file
        self.created_at = datetime.now().isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "front": self.front,
            "back": self.back,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "status": self.status,
            "times_reviewed": self.times_reviewed,
            "correct_answers": self.correct_answers,
            "source_file": self.source_file,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlashCard":
        card = cls(
            front=data["front"],
            back=data["back"],
            topic=data.get("topic", ""),
            difficulty=data.get("difficulty", "medium"),
            source_file=data.get("source_file", ""),
            card_id=data.get("id"),
        )
        card.status = data.get("status", "new")
        card.times_reviewed = data.get("times_reviewed", 0)
        card.correct_answers = data.get("correct_answers", 0)
        card.created_at = data.get("created_at", card.created_at)
        return card


class Deck:
    def __init__(self):
        self.cards: dict[str, FlashCard] = {}

    def add(self, card: FlashCard) -> None:
        self.cards[card.id] = card

    def remove(self, card_id: str) -> None:
        if card_id not in self.cards:
            raise CardNotFoundError(f"Card {card_id} not found")
        del self.cards[card_id]

    def search(self, query: str) -> list:
        pattern = re.compile(query, re.IGNORECASE)
        return [
            c for c in self.cards.values()
            if pattern.search(c.front) or pattern.search(c.back) or pattern.search(c.topic)
        ]

    def due_cards(self):
        for card in self.cards.values():
            if card.status != "known":
                yield card

    def mark(self, card_id: str, knew_it: bool) -> None:
        if card_id not in self.cards:
            raise CardNotFoundError(f"Card {card_id} not found")
        card = self.cards[card_id]
        card.times_reviewed += 1
        if knew_it:
            card.correct_answers += 1
            card.status = "known"
        else:
            card.status = "review"

    def stats(self) -> dict:
        total = len(self.cards)
        known = sum(1 for c in self.cards.values() if c.status == "known")
        reviewed = sum(c.times_reviewed for c in self.cards.values())
        correct = sum(c.correct_answers for c in self.cards.values())
        accuracy = round(correct / reviewed * 100, 1) if reviewed else 0.0
        by_topic: dict[str, int] = {}
        for c in self.cards.values():
            by_topic[c.topic] = by_topic.get(c.topic, 0) + 1
        return {
            "total": total,
            "known": known,
            "review": sum(1 for c in self.cards.values() if c.status == "review"),
            "new": sum(1 for c in self.cards.values() if c.status == "new"),
            "accuracy": accuracy,
            "by_topic": by_topic,
        }

    def save(self, path: str) -> None:
        try:
            import os
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in self.cards.values()], f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise StorageError(f"Cannot save deck: {e}") from e

    def load(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.cards = {d["id"]: FlashCard.from_dict(d) for d in data}
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, KeyError) as e:
            raise StorageError(f"Corrupt deck file: {e}") from e
