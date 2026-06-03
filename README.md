# QuizMaster

QuizMaster is a standalone desktop app that turns study material into **AI-generated
flashcards**. Paste your lecture notes — or open a `PDF`, `DOCX` or `TXT` file — and
the app calls a language model to produce a set of question/answer cards, files them
into a topic folder, and lets you study them with a spaced, "did I know it?" review
flow.

A small sample deck ships with the project, so you can browse, search and study cards
**straight away — no API key or internet connection required**. An API key is only
needed if you want to *generate* new cards from your own material.

---

## Features

- **AI card generation** — paste text or import a file; the model returns 8–12 cards
  with a question, an answer and a difficulty (easy / medium / hard).
- **File import** — reads `PDF`, `DOCX` and `TXT` and extracts plain text for you.
- **Topic folders** — cards are grouped into folders; the AI can name the folder
  automatically, or you can pick/create one yourself.
- **Study sessions** — flip cards, mark "knew it / didn't know", and see live progress
  plus a coverage summary at the end. Study the whole deck or a single folder.
- **Search** — regex-powered search across questions, answers and topics.
- **Manual editing** — add, edit and delete cards by hand.
- **Local persistence** — the deck is stored as JSON on disk and reloaded on startup.
- **Offline-friendly** — the bundled sample deck works with zero configuration.

---

## Setup

Requires **Python 3.10+**.

```bash
python -m venv .venv
# activate the virtual environment:
#   Windows:  .venv\Scripts\activate
#   macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Dependencies (`requirements.txt`): `customtkinter`, `requests`, `pdfplumber`,
`python-docx`.

---

## How to use

1. **Browse the deck** — the app opens on the **Decks** tab. Cards are grouped into
   topic folders; open a folder to see its cards, or search the whole deck from the
   search bar.
2. **Set an API key** (only needed for generation) — go to the **Generate** tab and
   click **Key**, then paste any OpenAI-compatible API key.
3. **Generate cards** — on the **Generate** tab, paste your notes or click **Open File**
   (PDF / TXT / DOCX), optionally choose a target folder, then click **Generate**. The
   AI creates the cards and files them into a topic.
4. **Study** — open the **Study** tab (whole deck) or hit **Study** inside a folder.
   Flip each card, mark whether you knew it, and review the summary at the end.
5. **Manage cards** — use **+ New card** / **+ New folder** to add content by hand, or
   **Edit** / **Del** on any card row.

Your deck is saved automatically after every change.

## Controls (Study screen)

- **Click the card** or **Space** — flip between question and answer
- **→** or **Enter** — mark the card as known
- **←** — mark the card as not known

---

## API compatibility

Generation works with any **OpenAI-compatible Chat Completions API**. By default it
targets [OpenRouter](https://openrouter.ai). To use a different provider or model, set
environment variables (e.g. in a `.env` file next to `main.py`):

```env
LLM_API_KEY=your-key-here
LLM_API_URL=https://your-provider/v1/chat/completions
LLM_MODEL=openai/gpt-4o-mini
```

The app also loads `LLM_API_KEY` / `API_KEY` from a `.env` file or your environment, so
you don't have to paste the key into the UI each time.

---

## Project structure

| File | Responsibility |
|------|----------------|
| `main.py` | Entry point — launches the app |
| `app.py` | Main window, navigation, app icon, shared data and API-key handling |
| `screens.py` | All UI screens (Generate, Decks, Study) and dialogs |
| `deck.py` | `FlashCard` and `Deck` classes — model, search, study queue, JSON I/O |
| `agent.py` | `CardGenerator` — calls the AI API and parses the response into cards |
| `parser.py` | Reads PDF / DOCX / TXT files into plain text |
| `storage.py` | Loads/saves the deck and config files |
| `decorators.py` | `log_action` decorator — audit-logs deck saves to `logs.txt` |
| `exceptions.py` | Custom exception hierarchy rooted at `FlashcardsError` |
| `requirements.txt` | Python dependencies |
| `data/deck.json` | Saved flashcards (sample deck included) |

---

## Python concepts demonstrated

This project is a course assignment; the required language elements are used naturally
throughout:

- **Modules & classes** — code split across 9 modules; `FlashCard`, `Deck`,
  `CardGenerator` and the UI screen classes.
- **Control flow & operators** — `if` / `for` / `while` (e.g. the `.env` line reader in
  `app.py`) and arithmetic/logical/comparison operators.
- **Functions & lambda** — button-builder helpers and lambdas in UI callbacks.
- **Custom decorator** — `log_action` (`decorators.py`) wraps `Deck.save` to log each
  save with a timestamp.
- **Collections** — `dict` (cards by id), `set` (supported extensions), `list`.
- **Comprehensions** — list, dict and set comprehensions in `deck.py`.
- **Generator** — `Deck.due_cards()` yields the cards still to be studied.
- **Files + context managers** — `with open(...)` for the deck, config, logs and files.
- **Serialization** — the deck is serialized to/from JSON.
- **Regular expressions** — file-extension parsing, markdown-fence stripping of API
  output, and deck search.
- **Exceptions** — a custom `FlashcardsError` hierarchy (`ApiError`, `StorageError`,
  `FileNotSupportedError`) with meaningful messages.

---

## Notes

- `logs.txt` is created at runtime to record deck saves (ignored by git).
- `data/config.json` stores your saved API key locally (ignored by git).
- No card data leaves your machine except the text you explicitly send for generation.
