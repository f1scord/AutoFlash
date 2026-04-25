import json
import requests
from deck import FlashCard
from exceptions import ApiError

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

PROMPT_TEMPLATE = (
    "You generate study flashcards.\n"
    "Return ONLY a JSON array. No prose. No markdown fences.\n"
    'Each item: { "front": str, "back": str, "topic": str, "difficulty": "easy"|"medium"|"hard" }.\n'
    "Generate 8-12 cards from the following lecture text:\n"
)


class CardGenerator:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def generate(self, text: str, source_file: str) -> list:
        if not self.api_key:
            raise ApiError("No API key configured. Please enter your DeepSeek API key in Settings.")

        from parser import read_chunks
        all_cards = []
        for chunk in read_chunks(text):
            all_cards.extend(self._call_api(chunk, source_file))
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
