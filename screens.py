import queue
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk

from agent import CardGenerator
from decorators import handle_errors, log_action
from parser import parse_file
from widgets import AnimatedProgress, FlipCard


BG = "#0d1117"
FG = "#e8e8e8"
ACCENT = "#4a9eff"
BTN_BG = "#1e2a3a"
ENTRY_BG = "#161b22"


def _style_btn(btn: tk.Button, primary: bool = False) -> None:
    btn.configure(
        bg=ACCENT if primary else BTN_BG,
        fg="#000" if primary else FG,
        relief="flat",
        padx=14, pady=6,
        cursor="hand2",
        font=("Helvetica", 11, "bold" if primary else "normal"),
        activebackground=ACCENT,
        activeforeground="#000",
    )


class ApiKeyDialog(tk.Toplevel):
    """Modal dialog for entering / changing the DeepSeek API key."""

    def __init__(self, master, current_key: str = "", on_save=None):
        super().__init__(master)
        self.title("API Key")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()  # modal
        self._on_save = on_save
        self._build(current_key)
        self.transient(master)
        self.wait_visibility()
        self.focus_force()

    def _build(self, current_key: str) -> None:
        pad = {"padx": 24, "pady": 8}

        tk.Label(self, text="DeepSeek API Key", bg=BG, fg=ACCENT,
                 font=("Helvetica", 14, "bold")).pack(**pad)
        tk.Label(self,
                 text="Get your key at platform.deepseek.com → API Keys",
                 bg=BG, fg="#888", font=("Helvetica", 10)).pack(padx=24, pady=(0, 8))

        self._entry = tk.Entry(self, width=52, bg=ENTRY_BG, fg=FG,
                               insertbackground=FG, font=("Helvetica", 11),
                               relief="flat", show="•")
        self._entry.pack(padx=24, pady=4)
        self._entry.insert(0, current_key)

        show_var = tk.BooleanVar(value=False)

        def _toggle():
            self._entry.configure(show="" if show_var.get() else "•")

        tk.Checkbutton(self, text="Show key", variable=show_var, command=_toggle,
                       bg=BG, fg="#888", selectcolor=BG,
                       activebackground=BG, font=("Helvetica", 10)).pack(padx=24, anchor="w")

        row = tk.Frame(self, bg=BG)
        row.pack(pady=12)

        cancel_btn = tk.Button(row, text="Cancel", command=self.destroy)
        _style_btn(cancel_btn)
        cancel_btn.pack(side="left", padx=6)

        save_btn = tk.Button(row, text="Save", command=self._save)
        _style_btn(save_btn, primary=True)
        save_btn.pack(side="left", padx=6)

        self._entry.bind("<Return>", lambda _: self._save())

    def _save(self) -> None:
        key = self._entry.get().strip()
        if self._on_save:
            self._on_save(key)
        self.destroy()


class GenerateScreen(tk.Frame):
    def __init__(self, master, api_key: str, on_cards_added, on_study, on_key_change):
        super().__init__(master, bg=BG)
        self._on_cards_added = on_cards_added
        self._on_study = on_study
        self._on_key_change = on_key_change
        self._generator = CardGenerator(api_key)
        self._queue: queue.Queue = queue.Queue()
        self._source_path = "pasted text"
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="AutoFlash", bg=BG, fg=ACCENT,
                 font=("Helvetica", 22, "bold")).pack(pady=(24, 4))
        tk.Label(self, text="Paste lecture text or open a file to generate flashcards",
                 bg=BG, fg="#888", font=("Helvetica", 11)).pack(pady=(0, 14))

        self._text = tk.Text(self, height=13, bg=ENTRY_BG, fg=FG, insertbackground=FG,
                             font=("Helvetica", 11), relief="flat", padx=10, pady=8,
                             wrap="word")
        self._text.pack(fill="x", padx=30, pady=(0, 10))

        row = tk.Frame(self, bg=BG)
        row.pack(pady=4)

        open_btn = tk.Button(row, text="Open lecture…", command=self._open_file)
        _style_btn(open_btn)
        open_btn.pack(side="left", padx=6)

        gen_btn = tk.Button(row, text="Generate  ⚡", command=self._generate)
        _style_btn(gen_btn, primary=True)
        gen_btn.pack(side="left", padx=6)

        key_btn = tk.Button(row, text="⚙ API Key", command=self._open_key_dialog)
        _style_btn(key_btn)
        key_btn.pack(side="left", padx=6)

        self._status = tk.Label(self, text="", bg=BG, fg="#888", font=("Helvetica", 10))
        self._status.pack(pady=6)

        self._study_btn = tk.Button(self, text="Study now  →", command=self._on_study)
        _style_btn(self._study_btn, primary=True)
        # hidden until cards are generated

        if not self._generator.api_key:
            self._status.configure(
                text="No API key set. Click ⚙ API Key to configure.",
                fg="#ff6b6b")

    def set_api_key(self, key: str) -> None:
        self._generator.api_key = key

    def _open_key_dialog(self) -> None:
        ApiKeyDialog(self, current_key=self._generator.api_key,
                     on_save=self._handle_key_save)

    def _handle_key_save(self, key: str) -> None:
        self._generator.api_key = key
        self._on_key_change(key)
        if key:
            self._status.configure(text="API key saved.", fg="#4aff9e")
        else:
            self._status.configure(text="API key cleared.", fg="#ff6b6b")

    @handle_errors
    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open lecture file",
            filetypes=[("Lecture files", "*.pdf *.docx *.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        self._status.configure(text="Parsing file…", fg="#888")
        self._parse_queue: queue.Queue = queue.Queue()

        def worker():
            try:
                text = parse_file(path)
                self._parse_queue.put(("ok", text))
            except Exception as e:
                self._parse_queue.put(("err", str(e)))

        threading.Thread(target=worker, daemon=True).start()

        def poll_parse():
            try:
                result, payload = self._parse_queue.get_nowait()
            except queue.Empty:
                self.after(100, poll_parse)
                return
            if result == "ok":
                self._source_path = path
                self._text.delete("1.0", "end")
                self._text.insert("1.0", payload)
                name = path.replace("\\", "/").split("/")[-1]
                self._status.configure(text=f"Loaded: {name}", fg=ACCENT)
            else:
                self._status.configure(text=f"Error parsing file: {payload}", fg="#ff6b6b")

        poll_parse()

    @handle_errors
    def _generate(self) -> None:
        if not self._generator.api_key:
            self._open_key_dialog()
            return
        text = self._text.get("1.0", "end").strip()
        if not text:
            self._status.configure(text="Paste or open a lecture first.", fg="#ff6b6b")
            return
        self._status.configure(text="Generating… (this may take a moment)", fg="#ffd700")
        self.update_idletasks()
        self._run_async(text)

    @log_action
    def _run_async(self, text: str) -> None:
        source = self._source_path

        def on_progress(msg: str) -> None:
            self._queue.put(("progress", msg))

        def worker():
            try:
                cards = self._generator.generate(text, source_file=source,
                                                  on_progress=on_progress)
                self._queue.put(("ok", cards))
            except Exception as e:
                self._queue.put(("err", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        self._poll_start = __import__("time").monotonic()
        self._poll()

    def _poll(self) -> None:
        import time
        try:
            result, payload = self._queue.get_nowait()
        except queue.Empty:
            elapsed = int(time.monotonic() - self._poll_start)
            self._status.configure(
                text=f"Generating… {elapsed}s", fg="#ffd700")
            self.after(200, self._poll)
            return

        if result == "progress":
            self._status.configure(text=f"Generating… {payload}", fg="#ffd700")
            self.after(200, self._poll)
        elif result == "ok":
            self._on_cards_added(payload)
            if payload:
                self._status.configure(
                    text=f"{len(payload)} cards added to your deck!", fg="#4aff9e")
                self._study_btn.pack(pady=4)
            else:
                self._status.configure(
                    text="No cards extracted. Try more detailed text.", fg="#ff6b6b")
        else:
            self._status.configure(text=f"Error: {payload}", fg="#ff6b6b")


class DeckScreen(tk.Frame):
    def __init__(self, master, deck, on_delete):
        super().__init__(master, bg=BG)
        self._deck = deck
        self._on_delete = on_delete
        self._selected_id = None
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Deck", bg=BG, fg=ACCENT,
                 font=("Helvetica", 20, "bold")).pack(pady=(18, 6))

        search_row = tk.Frame(self, bg=BG)
        search_row.pack(fill="x", padx=30, pady=(0, 8))
        tk.Label(search_row, text="Search:", bg=BG, fg=FG,
                 font=("Helvetica", 11)).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh())
        entry = tk.Entry(search_row, textvariable=self._search_var,
                         bg=ENTRY_BG, fg=FG, insertbackground=FG,
                         font=("Helvetica", 11), relief="flat")
        entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=30)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self._listbox = tk.Listbox(
            list_frame, bg=ENTRY_BG, fg=FG, selectbackground=ACCENT,
            selectforeground="#000", font=("Helvetica", 11),
            relief="flat", yscrollcommand=scrollbar.set, activestyle="none",
        )
        self._listbox.pack(fill="both", expand=True)
        scrollbar.configure(command=self._listbox.yview)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        del_btn = tk.Button(self, text="Delete selected", command=self._delete)
        _style_btn(del_btn)
        del_btn.pack(pady=10)

        self._info = tk.Label(self, text="", bg=BG, fg="#888", font=("Helvetica", 10))
        self._info.pack()

        self._ids = []
        self.refresh()

    def refresh(self) -> None:
        query = self._search_var.get().strip()
        cards = self._deck.search(query) if query else list(self._deck.cards.values())
        self._ids = [c.id for c in cards]
        self._listbox.delete(0, "end")
        for card in cards:
            label = f"[{card.difficulty}] {card.front[:60]}{'…' if len(card.front) > 60 else ''}"
            self._listbox.insert("end", label)
        stats = self._deck.stats()
        self._info.configure(
            text=f"Total: {stats['total']}  |  Known: {stats['known']}  "
                 f"|  Accuracy: {stats['accuracy']}%")

    def _on_select(self, _event) -> None:
        sel = self._listbox.curselection()
        self._selected_id = self._ids[sel[0]] if sel else None

    @handle_errors
    def _delete(self) -> None:
        if not self._selected_id:
            return
        self._deck.remove(self._selected_id)
        self._on_delete()
        self._selected_id = None
        self.refresh()


class StudyScreen(tk.Frame):
    def __init__(self, master, deck, on_done):
        super().__init__(master, bg=BG)
        self._deck = deck
        self._on_done = on_done
        self._cards = []
        self._idx = 0
        self._build()

    def _build(self) -> None:
        self._progress = AnimatedProgress(self, width=560)
        self._progress.pack(pady=(18, 4))

        self._counter = tk.Label(self, text="", bg=BG, fg="#888",
                                 font=("Helvetica", 10))
        self._counter.pack()

        self._flip_card = FlipCard(self, width=560, height=320)
        self._flip_card.pack(pady=14)

        hint = tk.Label(self, text="Click card to flip  •  keyboard: Space",
                        bg=BG, fg="#555", font=("Helvetica", 9))
        hint.pack()

        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(pady=12)

        forgot_btn = tk.Button(btn_row, text="✗  Forgot",
                               command=lambda: self._answer(False))
        _style_btn(forgot_btn)
        forgot_btn.configure(bg="#3a1a1a", fg="#ff6b6b",
                              activebackground="#ff6b6b", activeforeground="#000")
        forgot_btn.pack(side="left", padx=10)

        knew_btn = tk.Button(btn_row, text="✓  Knew it",
                             command=lambda: self._answer(True))
        _style_btn(knew_btn, primary=True)
        knew_btn.configure(bg="#1a3a1a", fg="#4aff9e",
                           activebackground="#4aff9e", activeforeground="#000")
        knew_btn.pack(side="left", padx=10)

        self.bind_all("<space>", lambda _: self._flip_card.flip())

    def start(self) -> None:
        self._cards = sorted(list(self._deck.due_cards()),
                             key=lambda c: c.times_reviewed)
        self._idx = 0
        if not self._cards:
            self._show_empty()
            return
        self._show_current()

    def _show_current(self) -> None:
        card = self._cards[self._idx]
        self._flip_card.load(card)
        total = len(self._cards)
        self._counter.configure(text=f"{self._idx + 1} / {total}")
        self._progress.set_progress(self._idx / total)

    def _answer(self, knew_it: bool) -> None:
        if self._idx >= len(self._cards):
            return
        card = self._cards[self._idx]
        self._deck.mark(card.id, knew_it)
        self._idx += 1
        if self._idx >= len(self._cards):
            self._progress.set_progress(1.0)
            self.after(300, self._show_stats)
        else:
            self._show_current()

    def _show_empty(self) -> None:
        for widget in self.winfo_children():
            widget.pack_forget()

        tk.Label(self, text="No cards to study yet.", bg=BG, fg=ACCENT,
                 font=("Helvetica", 18, "bold")).pack(pady=(80, 10))
        tk.Label(self, text="Go to Generate and add some flashcards first.",
                 bg=BG, fg="#888", font=("Helvetica", 12)).pack()

        if self._deck.stats()["total"] > 0:
            tk.Label(self, text="(All cards are marked as Known — great job!)",
                     bg=BG, fg="#4aff9e", font=("Helvetica", 11)).pack(pady=6)

        back_btn = tk.Button(self, text="Back to deck", command=self._on_done)
        _style_btn(back_btn, primary=True)
        back_btn.pack(pady=20)

    def _show_stats(self) -> None:
        for widget in self.winfo_children():
            widget.pack_forget()

        canvas = tk.Canvas(self, bg=BG, highlightthickness=0, width=560, height=340)
        canvas.pack(pady=20)

        stats = self._deck.stats()
        lines = [
            ("Session complete!", "#4a9eff", 22, "bold"),
            (f"Cards studied: {len(self._cards)}", FG, 14, "normal"),
            (f"Known: {stats['known']}  |  Review: {stats['review']}", "#4aff9e", 13, "normal"),
            (f"Overall accuracy: {stats['accuracy']}%", "#ffd700", 16, "bold"),
        ]
        target_fills = [l[1] for l in lines]

        items = []
        for i, (text, color, size, weight) in enumerate(lines):
            item = canvas.create_text(
                280, 60 + i * 60, text=text, fill="#0d1117",
                font=("Helvetica", size, weight), justify="center")
            items.append(item)

        def fade(step: int) -> None:
            t = min(1.0, step / 20)
            for idx2, item in enumerate(items):
                r0, g0, b0 = 0x0d, 0x11, 0x17
                tr = int(target_fills[idx2][1:3], 16)
                tg = int(target_fills[idx2][3:5], 16)
                tb = int(target_fills[idx2][5:7], 16)
                r = int(r0 + (tr - r0) * t)
                g = int(g0 + (tg - g0) * t)
                b = int(b0 + (tb - b0) * t)
                canvas.itemconfigure(item, fill=f"#{r:02x}{g:02x}{b:02x}")
            if step < 20:
                self.after(30, fade, step + 1)

        fade(0)

        by_topic_text = "  •  ".join(
            f"{topic}: {count}" for topic, count in stats["by_topic"].items()
        )
        if by_topic_text:
            canvas.create_text(280, 300, text=by_topic_text, fill="#555",
                                font=("Helvetica", 10), width=520, justify="center")

        back_btn = tk.Button(self, text="Back to deck", command=self._on_done)
        _style_btn(back_btn, primary=True)
        back_btn.pack(pady=8)
