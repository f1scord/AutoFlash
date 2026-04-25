import json
import os
import re
from deck import FlashCard
from exceptions import ApiError

DEFAULT_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"

PROMPT_TEMPLATE = (
    "You generate study flashcards.\n"
    "Return ONLY a JSON array. No prose. No markdown fences.\n"
    'Each item: { "front": str, "back": str, "topic": str, "difficulty": "easy"|"medium"|"hard" }.\n'
    "Generate 8-12 cards from the following lecture text:\n"
)


class CardGenerator:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.api_url = os.environ.get("LLM_API_URL", DEFAULT_API_URL)
        self.model = os.environ.get("LLM_MODEL", DEFAULT_MODEL)

    MAX_CHARS = 6000

    def generate(self, text: str, source_file: str, on_progress=None) -> list:
        if not self.api_key:
            raise ApiError("No API key set. Click ⚙ to add your API key.")
        excerpt = text[:self.MAX_CHARS]
        return self._call_api(excerpt, source_file)

    def _call_api(self, text: str, source_file: str) -> list:
        try:
            import requests
        except ModuleNotFoundError as e:
            raise ApiError("Package 'requests' is not installed. Use offline mode or install dependencies.") from e

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": PROMPT_TEMPLATE + text}],
            "temperature": 0.7,
        }
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
        except requests.Timeout:
            raise ApiError("API request timed out (60s). Check your connection.")
        except requests.HTTPError as e:
            raise ApiError(f"API error {e.response.status_code}: {e.response.text[:200]}")
        except requests.RequestException as e:
            raise ApiError(f"Network error: {e}")

        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # strip markdown fences the model sometimes adds
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()

        if not raw:
            raise ApiError("API returned an empty response.")
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ApiError(f"API returned invalid JSON: {e}\n\nGot:\n{raw[:300]}")

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

