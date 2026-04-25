import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk

from agent import CardGenerator
from deck import FlashCard
from decorators import handle_errors, log_action
from parser import parse_file
from widgets import AnimatedProgress, FlipCard, FONT


BG      = "#111118"
SURFACE = "#1c1c28"
CARD_S  = "#252535"
BORDER  = "#38384f"
ACCENT  = "#7b7fff"
TEXT    = "#e6e6f0"
MUTED   = "#6a6a8a"
GREEN   = "#4ade80"
RED     = "#f87171"
YELLOW  = "#facc15"
ENTRY   = "#1c1c28"


def _btn(btn: tk.Button, primary: bool = False, danger: bool = False) -> None:
    if primary:
        bg, fg, abg = ACCENT, "#fff", "#9999ff"
    elif danger:
        bg, fg, abg = "#3a1a1a", RED, RED
    else:
        bg, fg, abg = SURFACE, TEXT, ACCENT
    btn.configure(bg=bg, fg=fg, activebackground=abg, activeforeground="#fff",
                  relief="flat", padx=16, pady=8, cursor="hand2",
                  font=(FONT, 10, "bold" if primary else "normal"),
                  bd=0, highlightthickness=0)


class ApiKeyDialog(tk.Toplevel):
    def __init__(self, master, current_key: str = "", on_save=None):
        super().__init__(master)
        self.title("API Key — DeepSeek")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._on_save = on_save
        self._build(current_key)
        self.transient(master)
        self.wait_visibility()
        self.focus_force()

    def _build(self, key: str) -> None:
        tk.Label(self, text="DeepSeek API Key", bg=BG, fg=ACCENT,
                 font=(FONT, 15, "bold")).pack(padx=30, pady=(22, 4))
        tk.Label(self, text="platform.deepseek.com → API Keys",
                 bg=BG, fg=MUTED, font=(FONT, 10)).pack(padx=30, pady=(0, 14))

        self._entry = tk.Entry(self, width=50, bg=SURFACE, fg=TEXT,
                               insertbackground=TEXT, font=(FONT, 11),
                               relief="flat", show="•", bd=0,
                               highlightthickness=1, highlightcolor=ACCENT,
                               highlightbackground=BORDER)
        self._entry.pack(padx=30, ipady=7)
        self._entry.insert(0, key)

        show = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Show key", variable=show, bg=BG, fg=MUTED,
                       selectcolor=SURFACE, activebackground=BG,
                       font=(FONT, 10),
                       command=lambda: self._entry.configure(
                           show="" if show.get() else "•")).pack(
            padx=30, pady=6, anchor="w")

        row = tk.Frame(self, bg=BG)
        row.pack(pady=(6, 22))
        cancel = tk.Button(row, text="Cancel", command=self.destroy)
        _btn(cancel)
        cancel.pack(side="left", padx=6)
        save = tk.Button(row, text="Save", command=self._save)
        _btn(save, primary=True)
        save.pack(side="left", padx=6)
        self._entry.bind("<Return>", lambda _: self._save())

    def _save(self) -> None:
        if self._on_save:
            self._on_save(self._entry.get().strip())
        self.destroy()


class GenerateScreen(tk.Frame):
    def __init__(self, master, api_key, on_cards_added, on_study, on_key_change):
        super().__init__(master, bg=BG)
        self._on_cards_added = on_cards_added
        self._on_study = on_study
        self._on_key_change = on_key_change
        self._generator = CardGenerator(api_key)
        self._q: queue.Queue = queue.Queue()
        self._source = "pasted text"
        self._poll_start = 0.0
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="AutoFlash ⚡", bg=BG, fg=ACCENT,
                 font=(FONT, 24, "bold")).pack(pady=(24, 2))
        tk.Label(self, text="Paste lecture text or open a file",
                 bg=BG, fg=MUTED, font=(FONT, 11)).pack(pady=(0, 12))

        self._text = tk.Text(self, height=13, bg=SURFACE, fg=TEXT,
                             insertbackground=TEXT, font=(FONT, 11),
                             relief="flat", padx=12, pady=10,
                             wrap="word", bd=0,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=ACCENT)
        self._text.pack(fill="x", padx=28, pady=(0, 12))

        row = tk.Frame(self, bg=BG)
        row.pack()

        open_b = tk.Button(row, text="📂  Open lecture…", command=self._open_file)
        _btn(open_b)
        open_b.pack(side="left", padx=5)

        gen_b = tk.Button(row, text="⚡  Generate", command=self._generate)
        _btn(gen_b, primary=True)
        gen_b.pack(side="left", padx=5)

        key_b = tk.Button(row, text="⚙", command=self._open_key_dialog,
                          width=3)
        _btn(key_b)
        key_b.pack(side="left", padx=5)

        self._status = tk.Label(self, text="", bg=BG, fg=MUTED,
                                font=(FONT, 10))
        self._status.pack(pady=8)

        self._study_btn = tk.Button(self, text="Study cards  →",
                                    command=self._on_study)
        _btn(self._study_btn, primary=True)

        if not self._generator.api_key:
            self._status.configure(
                text="No API key — click ⚙", fg=YELLOW)

    def set_api_key(self, key: str) -> None:
        self._generator.api_key = key

    def _open_key_dialog(self) -> None:
        ApiKeyDialog(self, self._generator.api_key, on_save=self._key_saved)

    def _key_saved(self, key: str) -> None:
        self._generator.api_key = key
        self._on_key_change(key)
        self._status.configure(
            text="Key saved ✓" if key else "Key cleared", fg=GREEN if key else RED)

    @handle_errors
    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open lecture file",
            filetypes=[("Lecture files", "*.pdf *.docx *.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        self._status.configure(text="Parsing file…", fg=MUTED)
        pq: queue.Queue = queue.Queue()

        def worker():
            try:
                pq.put(("ok", parse_file(path)))
            except Exception as e:
                pq.put(("err", str(e)))

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                r, p = pq.get_nowait()
            except queue.Empty:
                self.after(80, poll)
                return
            if r == "ok":
                self._source = path
                self._text.delete("1.0", "end")
                self._text.insert("1.0", p)
                name = path.replace("\\", "/").split("/")[-1]
                self._status.configure(text=f"✓  {name}", fg=GREEN)
            else:
                self._status.configure(text=f"Error: {p}", fg=RED)

        poll()

    @handle_errors
    def _generate(self) -> None:
        if not self._generator.api_key:
            self._open_key_dialog()
            return
        text = self._text.get("1.0", "end").strip()
        if not text:
            self._status.configure(text="Paste or open a lecture first.", fg=YELLOW)
            return
        self._status.configure(text="Generating…  0s", fg=YELLOW)
        self.update_idletasks()
        self._run(text)

    @log_action
    def _run(self, text: str) -> None:
        src = self._source

        def worker():
            try:
                self._q.put(("ok", self._generator.generate(text, src)))
            except Exception as e:
                self._q.put(("err", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        import time
        self._poll_start = time.monotonic()
        self._poll()

    def _poll(self) -> None:
        import time
        try:
            r, p = self._q.get_nowait()
        except queue.Empty:
            s = int(time.monotonic() - self._poll_start)
            self._status.configure(text=f"Generating…  {s}s", fg=YELLOW)
            self.after(200, self._poll)
            return
        if r == "ok":
            self._on_cards_added(p)
            if p:
                self._status.configure(text=f"✓  {len(p)} cards added!", fg=GREEN)
                self._study_btn.pack(pady=4)
            else:
                self._status.configure(text="No cards returned. Try different text.", fg=RED)
        else:
            self._status.configure(text=f"Error: {p}", fg=RED)


class DeckScreen(tk.Frame):
    def __init__(self, master, deck, on_delete):
        super().__init__(master, bg=BG)
        self._deck = deck
        self._on_delete = on_delete
        self._sel_id = None
        self._build()

    def _build(self) -> None:
        tk.Label(self, text="Deck", bg=BG, fg=ACCENT,
                 font=(FONT, 20, "bold")).pack(pady=(18, 10))

        search_row = tk.Frame(self, bg=BG)
        search_row.pack(fill="x", padx=28, pady=(0, 8))

        tk.Label(search_row, text="🔍", bg=BG, fg=MUTED,
                 font=(FONT, 12)).pack(side="left")
        self._sv = tk.StringVar()
        self._sv.trace_add("write", lambda *_: self.refresh())
        e = tk.Entry(search_row, textvariable=self._sv,
                     bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                     font=(FONT, 11), relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT)
        e.pack(side="left", fill="x", expand=True, padx=(6, 0), ipady=5)

        lf = tk.Frame(self, bg=BG)
        lf.pack(fill="both", expand=True, padx=28, pady=(0, 4))

        sb = ttk.Scrollbar(lf, orient="vertical")
        sb.pack(side="right", fill="y")

        self._lb = tk.Listbox(lf, bg=SURFACE, fg=TEXT, selectbackground=ACCENT,
                              selectforeground="#fff", font=(FONT, 11),
                              relief="flat", bd=0, yscrollcommand=sb.set,
                              activestyle="none", highlightthickness=0)
        self._lb.pack(fill="both", expand=True)
        sb.configure(command=self._lb.yview)
        self._lb.bind("<<ListboxSelect>>", self._sel)

        bot = tk.Frame(self, bg=BG)
        bot.pack(fill="x", padx=28, pady=8)

        del_b = tk.Button(bot, text="🗑  Delete", command=self._delete)
        _btn(del_b, danger=True)
        del_b.pack(side="left")

        self._info = tk.Label(bot, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self._info.pack(side="right")

        self._ids = []
        self.refresh()

    def refresh(self) -> None:
        q = self._sv.get().strip()
        cards = self._deck.search(q) if q else list(self._deck.cards.values())
        self._ids = [c.id for c in cards]
        self._lb.delete(0, "end")
        diff_icons = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        for c in cards:
            icon = diff_icons.get(c.difficulty, "⚪")
            front = c.front[:58] + ("…" if len(c.front) > 58 else "")
            self._lb.insert("end", f"  {icon}  {front}")
        st = self._deck.stats()
        self._info.configure(
            text=f"Total: {st['total']}  •  Known: {st['known']}  •  {st['accuracy']}%")

    def _sel(self, _) -> None:
        s = self._lb.curselection()
        self._sel_id = self._ids[s[0]] if s else None

    @handle_errors
    def _delete(self) -> None:
        if not self._sel_id:
            return
        self._deck.remove(self._sel_id)
        self._on_delete()
        self._sel_id = None
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
        self._prog = AnimatedProgress(self, width=540, height=5)
        self._prog.pack(pady=(16, 2))

        self._counter = tk.Label(self, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self._counter.pack()

        self._card = FlipCard(self, width=540, height=300)
        self._card.pack(pady=(10, 4))

        tk.Label(self, text="Click card to flip  •  Space",
                 bg=BG, fg="#3a3a55", font=(FONT, 9)).pack()

        row = tk.Frame(self, bg=BG)
        row.pack(pady=14)

        self._forgot_b = tk.Button(row, text="✗  Forgot",
                                   command=lambda: self._ans(False))
        _btn(self._forgot_b, danger=True)
        self._forgot_b.pack(side="left", padx=10)

        self._knew_b = tk.Button(row, text="✓  Knew it",
                                 command=lambda: self._ans(True))
        _btn(self._knew_b, primary=True)
        self._knew_b.configure(bg="#1a3828", fg=GREEN,
                               activebackground=GREEN, activeforeground="#000")
        self._knew_b.pack(side="left", padx=10)

        self.bind_all("<space>", lambda _: self._card.flip())

    def start(self) -> None:
        self._cards = sorted(list(self._deck.due_cards()),
                             key=lambda c: c.times_reviewed)
        self._idx = 0
        if not self._cards:
            self._empty()
            return
        self._show()

    def _show(self) -> None:
        c = self._cards[self._idx]
        self._card.load(c)
        total = len(self._cards)
        self._counter.configure(text=f"{self._idx + 1} / {total}")
        self._prog.set_progress(self._idx / total)

    def _ans(self, knew: bool) -> None:
        if self._idx >= len(self._cards):
            return
        self._deck.mark(self._cards[self._idx].id, knew)
        self._idx += 1
        if self._idx >= len(self._cards):
            self._prog.set_progress(1.0)
            self.after(350, self._stats)
        else:
            self._show()

    def _empty(self) -> None:
        for w in self.winfo_children():
            w.pack_forget()
        tk.Label(self, text="Nothing to study", bg=BG, fg=ACCENT,
                 font=(FONT, 20, "bold")).pack(pady=(80, 8))
        tk.Label(self, text="Go to Generate and add flashcards first.",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack()
        if self._deck.stats()["total"] > 0:
            tk.Label(self, text="All cards already known — great job!",
                     bg=BG, fg=GREEN, font=(FONT, 11)).pack(pady=6)
        b = tk.Button(self, text="Back", command=self._on_done)
        _btn(b, primary=True)
        b.pack(pady=20)

    def _stats(self) -> None:
        for w in self.winfo_children():
            w.pack_forget()

        st = self._deck.stats()
        acc = st["accuracy"]

        outer = tk.Frame(self, bg=BG)
        outer.pack(expand=True, fill="both", padx=60, pady=30)

        tk.Label(outer, text="Session complete!", bg=BG, fg=ACCENT,
                 font=(FONT, 22, "bold")).pack(pady=(20, 16))

        rows = [
            (f"{len(self._cards)}", "cards studied"),
            (f"{st['known']}", "marked Known"),
            (f"{acc}%", "accuracy"),
        ]
        for val, lbl in rows:
            f = tk.Frame(outer, bg=SURFACE, padx=20, pady=12)
            f.pack(fill="x", pady=4)
            tk.Label(f, text=val, bg=SURFACE,
                     fg=GREEN if "%" not in val or acc >= 50 else RED,
                     font=(FONT, 20, "bold")).pack(side="left")
            tk.Label(f, text=f"  {lbl}", bg=SURFACE, fg=MUTED,
                     font=(FONT, 12)).pack(side="left", anchor="s", pady=4)

        by = "  •  ".join(f"{t}: {n}" for t, n in st["by_topic"].items())
        if by:
            tk.Label(outer, text=by, bg=BG, fg=MUTED, font=(FONT, 9),
                     wraplength=480, justify="center").pack(pady=8)

        b = tk.Button(outer, text="Back to deck", command=self._on_done)
        _btn(b, primary=True)
        b.pack(pady=12)
