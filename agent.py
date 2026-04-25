import json
import os
import re
import requests
from deck import FlashCard
from exceptions import ApiError
from parser import read_chunks

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

PROMPT_TEMPLATE = (
    "You generate study flashcards.\n"
    "Return ONLY a JSON array. No prose. No markdown fences.\n"
    'Each item: { "front": str, "back": str, "topic": str, "difficulty": "easy"|"medium"|"hard" }.\n'
    "Generate 8-12 cards from the following lecture text:\n"
)


class CardGenerator:
    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.offline = os.environ.get("AUTOFLASH_OFFLINE", "").lower() == "true"

    def generate(self, text: str, source_file: str) -> list:
        if self.offline or not self.api_key:
            return self._offline_generate(text, source_file)

        all_cards = []
        for chunk in read_chunks(text):
            try:
                cards = self._call_api(chunk, source_file)
                all_cards.extend(cards)
            except (ApiError, Exception):
                all_cards.extend(self._offline_generate(chunk, source_file))
        return all_cards

    def _call_api(self, text: str, source_file: str) -> list:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": PROMPT_TEMPLATE + text}],
            "temperature": 0.7,
        }
        try:
            resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ApiError(f"DeepSeek request failed: {e}") from e

        content = resp.json()["choices"][0]["message"]["content"].strip()
        try:
            items = json.loads(content)
        except json.JSONDecodeError as e:
            raise ApiError(f"DeepSeek returned invalid JSON: {e}") from e

        return [
            FlashCard(
                front=item["front"],
                back=item["back"],
                topic=item.get("topic", "General"),
                difficulty=item.get("difficulty", "medium"),
                source_file=source_file,
            )
            for item in items
            if "front" in item and "back" in item
        ]

    def _offline_generate(self, text: str, source_file: str) -> list:
        trigger = re.compile(
            r"\b(is|are|means|defined as|refers to)\b", re.IGNORECASE
        )
        sentences = re.split(r"(?<=[.!?])\s+", text)
        cards = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            if trigger.search(sentence):
                cards.append(FlashCard(
                    front="What does this describe?",
                    back=sentence,
                    topic="General",
                    difficulty="medium",
                    source_file=source_file,
                ))
        return cards[:12]
