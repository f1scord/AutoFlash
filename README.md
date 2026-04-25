# AutoFlash

Native desktop flashcard app built with Tkinter. Drop in a PDF, DOCX, or TXT lecture — DeepSeek generates study cards. Study them in a windowed UI with smooth flip and slide animations.

No Flask. No browser. No npm.

## Install

```bash
pip install requests pdfplumber python-docx
```

## Run

```bash
python main.py
```

Set your API key first:

```bash
export DEEPSEEK_API_KEY=your_key   # Linux / macOS
set DEEPSEEK_API_KEY=your_key      # Windows CMD
$env:DEEPSEEK_API_KEY="your_key"   # Windows PowerShell
```

## Offline mode

No key? No WiFi? The app still works with a regex-based fallback generator:

```bash
AUTOFLASH_OFFLINE=true python main.py
```

## Supported formats

- PDF (`.pdf`) via `pdfplumber`
- Word documents (`.docx`) via `python-docx`
- Plain text (`.txt`)

## How it works

1. **Generate screen** — paste text directly or open a lecture file. Click Generate.
2. **Deck screen** — browse, search, and delete cards. Cards persist in `data/deck.json`.
3. **Study screen** — click a card to flip (horizontal scale animation), then mark Knew it or Forgot. Progress bar at the top. Stats fade in when the session ends.

## File structure

```
autoflash/
├── main.py         # entry point
├── app.py          # App class, window, screen switching
├── screens.py      # GenerateScreen, DeckScreen, StudyScreen
├── widgets.py      # FlipCard canvas widget, AnimatedProgress
├── agent.py        # CardGenerator (DeepSeek + offline fallback)
├── deck.py         # FlashCard, Deck data classes
├── parser.py       # PDF / DOCX / TXT readers
├── storage.py      # JSON load/save helpers
├── decorators.py   # @log_action, @handle_errors
├── exceptions.py   # custom exception hierarchy
└── data/
    └── deck.json   # auto-created on first save
```

## Notes

- `data/deck.json` and `logs.txt` are created automatically on first run.
- All animations run via `widget.after()` — no external animation library.
- API calls and file parsing happen on background threads so the UI stays responsive.
