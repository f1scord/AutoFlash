<aside>
⚡

нативный desktop app на Tkinter. кидаешь PDF или DOCX лекцию. DeepSeek генерит флеш-карты. учишь в окне с плавными flip/slide анимациями. ни Flask. ни браузера. ни npm.

</aside>

## TL;DR

AutoFlash is a native desktop app built with Tkinter. It turns lecture slides and notes (**PDF, DOCX, TXT**) into flashcards via the DeepSeek API and lets you study them in a windowed UI with smooth flip and slide animations driven by `after()`. Local JSON storage. Optional offline fallback. One window, three screens.

---

## Why Tkinter

- Ships with Python. Zero dependencies for the UI.
- Real native window. Not a browser tab.
- Animations via `widget.after(ms, callback)` are simple and predictable.
- `ttk` themes look decent on dark backgrounds with a few lines of style.
- Defense laptop already has it. Always.

External deps: `requests` (DeepSeek), `pdfplumber` (PDF), `python-docx` (DOCX). That's it.

---

## Stack

| Layer | Tool | UI | Tkinter + ttk (stdlib) |
| --- | --- | --- | --- |
| Animation | `Canvas`  • `after()` loops | LLM | DeepSeek API via `requests` |
| PDF parsing | `pdfplumber` | DOCX parsing | `python-docx` |
| Storage | JSON file via `json` (stdlib) | Threading | `threading.Thread` to keep UI responsive during API/parse calls |

---

## File structure

```
autoflash/
├── main.py             # entry point: builds App, starts mainloop
├── app.py              # App class: window, screens, navigation
├── screens.py          # GenerateScreen, DeckScreen, StudyScreen frames
├── widgets.py          # FlipCard canvas widget, AnimatedProgress
├── agent.py            # CardGenerator (DeepSeek + offline fallback)
├── deck.py             # FlashCard, Deck classes
├── parser.py           # PDF / DOCX / TXT readers + dispatcher
├── storage.py          # JSON load / save
├── decorators.py       # @log_action, @handle_errors
├── exceptions.py       # custom exception hierarchy
├── data/
│   └── deck.json       # auto-created
├── notes/
│   ├── sample_lecture.pdf  # demo PDF for defense
│   └── sample_lecture.docx # demo DOCX for defense
├── logs.txt            # auto-created
└── README.md
```

10 Python files, all small. Single responsibility each.

---

## Parser (`parser.py`)

Dispatches by extension. One small function per format.

```python
import re, pdfplumber, docx
from exceptions import FileNotSupportedError

SUPPORTED = {".pdf", ".docx", ".txt"}

def parse_file(path: str) -> str:
    # validates extension via regex, dispatches to the right reader.
    ext = _ext(path)
    if ext not in SUPPORTED:
        raise FileNotSupportedError(f"Unsupported file type: {ext}")
    return {
        ".pdf":  read_pdf,
        ".docx": read_docx,
        ".txt":  read_text,
    }[ext](path)

def read_pdf(path: str) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:        # context manager
        for page in pdf.pages:
            text = page.extract_text() or ""
            parts.append(text)
    return "\n\n".join(parts)

def read_docx(path: str) -> str:
    document = docx.Document(path)
    # list comprehension over paragraphs
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_chunks(text: str, size: int = 4000):
    # generator: yields chunks for very large lectures so we don't blow the prompt.
    for i in range(0, len(text), size):
        yield text[i:i + size]

def _ext(path: str) -> str:
    m = re.search(r"\.[A-Za-z0-9]+$", path)
    if not m:
        raise FileNotSupportedError("File has no extension")
    return m.group(0).lower()
```

File picker in the UI uses `tk.filedialog.askopenfilename` with the same extensions:

```python
filetypes = [("Lecture files", "*.pdf *.docx *.txt")]
```

---

## Classes (`deck.py`)

```python
class FlashCard:
    id: str            # uuid4
    front: str         # question
    back: str          # answer
    topic: str
    difficulty: str    # easy | medium | hard
    status: str        # new | known | review
    times_reviewed: int
    correct_answers: int
    source_file: str
    created_at: str

    def to_dict() -> dict
    @classmethod
    def from_dict(data: dict) -> FlashCard

class Deck:
    cards: dict        # id -> FlashCard

    def add(card: FlashCard) -> None
    def remove(card_id: str) -> None        # raises CardNotFoundError
    def search(query: str) -> list           # regex over front/back/topic
    def due_cards() -> generator             # yields cards with status != 'known'
    def mark(card_id: str, knew_it: bool) -> None
    def stats() -> dict                      # totals, accuracy, by topic
    def save(path: str) -> None
    def load(path: str) -> None
```

---

## Agent (`agent.py`)

```python
class CardGenerator:
    def generate(text: str, source_file: str) -> list[FlashCard]
    # Calls DeepSeek with strict JSON-only prompt.
    # On failure or missing key -> _offline_generate().
    # Runs inside a threading.Thread so the UI stays responsive.
    # Uses parser.read_chunks() if text is very long.

    def _offline_generate(text: str) -> list[FlashCard]
    # regex-based: split into sentences, build naive Q/A pairs
    # from sentences containing 'is', 'are', 'means', 'defined as'.
```

**Prompt (kept dumb on purpose):**

```
You generate study flashcards.
Return ONLY a JSON array. No prose. No markdown fences.
Each item: { "front": str, "back": str, "topic": str, "difficulty": "easy"|"medium"|"hard" }.
Generate 8–12 cards from the following lecture text:
<text>
```

---

## App architecture (`app.py`)

One `Tk` root window. A stack of `Frame` screens. Three screens:

1. **GenerateScreen** — a textarea where you can **paste text directly**, plus an "Open lecture…" button (PDF/DOCX/TXT picker) that fills the same textarea with extracted text. Then "Generate" + status label. Paste path and file path feed the same generator.
2. **DeckScreen** — scrollable list of cards, search entry, delete button.
3. **StudyScreen** — a single `FlipCard` canvas widget centered, two buttons below (Knew it / Forgot), animated progress bar on top.

The `App` class holds the `Deck` instance, switches between screens, and shares state via callbacks.

---

## Animations (the "красиво" part)

All done with `widget.after(ms, callback)` recursive loops. No external animation lib.

### Flip animation (`widgets.py`)

`FlipCard` is a `Canvas` that draws either the front or back text. Flip = horizontal scale animation:

```python
class FlipCard(tk.Canvas):
    def flip(self):
        # animate width scale from 1.0 -> 0.0 (squash to vertical line),
        # swap face, then 0.0 -> 1.0 (expand back).
        steps = 12
        self._animate_scale(1.0, 0.0, steps, on_done=self._swap_and_expand)

    def _animate_scale(self, start, end, steps, on_done):
        delta = (end - start) / steps
        def step(i, value):
            self._redraw(scale_x=value)
            if i < steps:
                self.after(20, step, i + 1, value + delta)
            else:
                on_done()
        step(0, start)
```

Result: card squashes to a line, flips, expands back showing the answer. ~250ms total. Looks legit.

### Slide-in for next card

When the user clicks Knew it / Forgot, the card slides off to the left while the next one slides in from the right:

```python
def slide_to_next(self, next_card):
    def step(offset):
        self.place_configure(x=offset)
        if offset > -window_width:
            self.after(15, step, offset - 30)
        else:
            self._render(next_card)
            self._slide_in_from_right()
    step(0)
```

### Progress bar

Custom `AnimatedProgress` widget that animates `width` from current to target value over ~200ms with `after()`.

### Fade for stats screen

Use `Canvas.itemconfigure(item, fill=...)` cycling through alpha-blended colors (manually computed) over a few frames. Cheap but effective.

---

## Threading for parsing + API calls

Both PDF parsing and DeepSeek calls happen on a background thread so the UI doesn't freeze:

```python
import threading, queue

def _generate_async(self, path):
    self._show_spinner()
    def worker():
        try:
            text = parse_file(path)
            cards = self.generator.generate(text, path)
            self.queue.put(("ok", cards))
        except AutoFlashError as e:
            self.queue.put(("err", str(e)))
    threading.Thread(target=worker, daemon=True).start()
    self._poll_queue()
```

`_poll_queue` is called via `after(100, ...)` and updates the UI when results arrive. Standard Tkinter pattern.

---

## Exceptions (`exceptions.py`)

```python
class AutoFlashError(Exception): ...
class FileNotSupportedError(AutoFlashError): ...
class ApiError(AutoFlashError): ...
class CardNotFoundError(AutoFlashError): ...
class StorageError(AutoFlashError): ...
```

---

## Decorators (`decorators.py`)

```python
def log_action(func):
    # writes timestamp + func name + args summary to logs.txt
    # using `with open(...) as f`

def handle_errors(func):
    # catches AutoFlashError -> shows tk.messagebox.showerror with friendly text
    # catches everything else -> generic error dialog, still logs traceback
```

Applied to every agent call and every UI button handler so a corrupt PDF or dead API never crashes the window.

---

## PPY1 requirements coverage

| Requirement | Where | modules / files | 10 modules, single responsibility each |
| --- | --- | --- | --- |
| classes | `FlashCard`, `Deck`, `CardGenerator`, `App`, `FlipCard`, screen classes | control statements | parser dispatch, generate flow, study loop, screen routing, animation steps |
| operators | accuracy %, difficulty comparisons, status checks, animation math | functions + lambda | helpers everywhere; `sorted(cards, key=lambda c: c.times_reviewed)`; lambda for button commands |
| custom decorator | `@log_action`, `@handle_errors` | collections | `dict` of cards, `list` of generated cards, `set` of supported extensions, `queue.Queue` for thread results |
| comprehensions | DOCX paragraph join, search filter, topic dedup, stats by topic | generator | `Deck.due_cards()` yields cards lazily; `parser.read_chunks()` yields text chunks for big lectures |
| file handling + with | `pdfplumber.open(...)`, plain TXT reading, JSON save/load, log writing | serialization | `deck.json` via `json` module |
| regex | extension validation in parser, card search, offline fallback sentence extraction | exceptions | 5 custom classes, raised + caught with friendly messageboxes |
| UI | native Tkinter window with three screens and animations | README | description + run instructions |

Every item is natural. Nothing shoehorned.

---

## Offline fallback

If `DEEPSEEK_API_KEY` is missing OR the API call raises, `CardGenerator._offline_generate()` runs:

1. Split extracted text into sentences via regex.
2. Pick sentences containing trigger words (`is`, `are`, `means`, `defined as`, `refers to`).
3. For each pick: front = `"What does this describe?"`, back = the sentence.

Not smart. But guarantees the app works on defense day even if the wifi dies.

---

## Run

```bash
pip install requests pdfplumber python-docx
export DEEPSEEK_API_KEY=your_key
python main.py
```

Force offline mode:

```bash
AUTOFLASH_OFFLINE=true python main.py
```

No Flask. No browser. Just a window.

---

## Defense plan (3 minutes)

1. `python main.py` → native window opens.
2. Generate screen: paste a paragraph straight into the textarea → click Generate → spinner → cards appear.
3. Then click "Open lecture…" → pick `notes/sample_lecture.pdf` → extracted text shows in textarea → Generate again. Repeat with `.docx` to flex multi-format.
4. Deck screen: show the list, type in search to filter live, delete one card.
5. Study screen: click card → flip animation → click Knew it → next card slides in → finish set → stats fade in.
6. Open `data/deck.json` in a text editor to show serialization.
7. Open `logs.txt` to show decorator output.
8. Show README.

Done. Smile. Sit down.

---

## Defense Q&A cheatsheet

- **Why Tkinter, not Flask?** Native desktop app, no browser dependency, ships with Python, animations via `after()` are straightforward.
- **How do you read PDFs?** `pdfplumber.open(path)` inside a `with` block, iterate pages, call `page.extract_text()`, join the parts.
- **How do you read DOCX?** `python-docx` opens the document, iterate `document.paragraphs`, join non-empty text via a comprehension.
- **How does the parser dispatcher work?** Regex extracts the extension; a dict maps extension to reader function; unknown extensions raise `FileNotSupportedError`.
- **How does the flip animation work?** A `Canvas` widget redraws itself with shrinking horizontal scale via `after(20ms)` recursive calls; halfway through it swaps the face and expands back.
- **Why threading?** PDF parsing + DeepSeek can take several seconds; doing them on the main thread freezes the UI. A daemon thread does the work and pushes results into a `queue.Queue`, which the UI polls via `after()`.
- **What does the decorator do?** `@log_action` writes a timestamped entry per call; `@handle_errors` catches custom exceptions and shows friendly `messagebox` errors.
- **Where's the generator?** `Deck.due_cards()` and `parser.read_chunks()` — both yield items lazily.
- **Where's the lambda?** Sorting cards by `times_reviewed` in study mode and as Tk button `command` callbacks.
- **Why custom exceptions?** Separates expected app errors (unsupported file, corrupt PDF, missing card, dead API) from unexpected crashes.
- **Where's the regex?** Extension validation in parser, card search, sentence extraction in offline fallback.
- **Why JSON not DB?** Project is small, JSON is human-readable, easy to inspect during defense.

---

## Submission checklist

- [ ]  Zip is `s32618_projekt.zip`
- [ ]  Contains only `.py` and `.md` text files (sample PDF/DOCX go in `notes/` only if instructor allows binaries; otherwise leave the folder empty and note in README how to test)
- [ ]  No `.venv`, `.idea`, `.git`
- [ ]  `data/` and `logs.txt` are auto-created on first run, not pre-included
- [ ]  App starts with `python main.py` after one `pip install requests pdfplumber python-docx` line
- [ ]  README has description + run instructions + offline mode note + supported formats list

> **Note on binaries in zip.** PPY spec says zip should contain only text-like files. To stay safe: keep `notes/` empty in the submission and put 2–3 sample PDFs/DOCX on a USB stick or download them at defense time. Alternatively, ask the instructor explicitly. Don't gamble the 5-point deduction.
> 

---

<aside>
🎯

**главный завет.** один Tk рут. три фрейма-экрана. один Canvas с flip-анимацией. PDF + DOCX + TXT на входе. JSON на выходе. всё.

</aside>