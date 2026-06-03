# screens module — all ui screens for the app
# uses tkinter for gui, customtkinter for modern look

import re
from tkinter import filedialog

import customtkinter as ctk

from deck import FlashCard
from exceptions import FileNotSupportedError

# ── color palette: black + mint ─────────────────────────────
BG = "#0a0a0a"
SURFACE = "#111111"
CARD = "#181818"
BORDER = "#252525"
MINT = "#3dd68c"
MINT_HOVER = "#2db46d"
TEXT = "#f0f0f0"
MUTED = "#aaaaaa"
RED = "#ff5555"
YELLOW = "#f0c040"
FONT = "Segoe UI"

# ── shared sizing scale ─────────────────────────────────────
PAD = 16  # outer spacing
GAP = 8  # inner spacing
BTN_H = 32  # standard button height


# ── helper functions ──────────────────────────────────────────


def _primary_btn(master, text, command):
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=MINT,
        hover_color=MINT_HOVER,
        text_color=BG,
        font=(FONT, 11, "bold"),
        corner_radius=8,
        height=BTN_H,
    )


def _secondary_btn(master, text, command):
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=CARD,
        hover_color=BORDER,
        text_color=TEXT,
        font=(FONT, 11),
        corner_radius=8,
        height=BTN_H,
    )


def _danger_btn(master, text, command):
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color="#2a1515",
        hover_color="#3d2020",
        text_color=RED,
        font=(FONT, 10),
        corner_radius=6,
        height=26,
        width=70,
        border_width=1,
        border_color="#3d2020",
    )


# ═══════════════════════════════════════════════════════════════
#  API KEY DIALOG
# ═══════════════════════════════════════════════════════════════


class ApiKeyDialog(ctk.CTkToplevel):
    """small popup to enter or update the api key"""

    def __init__(self, master, current_key: str = "", on_save=None):
        super().__init__(master)
        self.title("API Settings")
        self.geometry("400x160")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.on_save = on_save
        self._build(current_key)

    def _build(self, current_key):
        ctk.CTkLabel(self, text="API Key:", text_color=MUTED, font=(FONT, 10)).pack(
            anchor="w", padx=20, pady=(12, 2)
        )

        self.key_entry = ctk.CTkEntry(
            self,
            width=340,
            height=28,
            corner_radius=6,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            show="*",
        )
        self.key_entry.insert(0, current_key)
        self.key_entry.pack(pady=2)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=14)

        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save,
            fg_color=MINT,
            hover_color=MINT_HOVER,
            text_color=BG,
            font=(FONT, 10, "bold"),
            corner_radius=8,
            width=90,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=MUTED,
            font=(FONT, 10),
            corner_radius=8,
            width=90,
        ).pack(side="left", padx=6)

    def _save(self):
        key = self.key_entry.get().strip()
        if self.on_save:
            self.on_save(key)
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  CARD DIALOG
# ═══════════════════════════════════════════════════════════════


class CardDialog(ctk.CTkToplevel):
    """popup to add a new flashcard by hand"""

    def __init__(self, master, topics, default_topic="", on_save=None):
        super().__init__(master)
        self.title("New Card")
        self.geometry("420x380")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.on_save = on_save
        self._build(topics, default_topic)

    def _build(self, topics, default_topic):
        def field_label(text):
            ctk.CTkLabel(self, text=text, text_color=MUTED, font=(FONT, 10)).pack(
                anchor="w", padx=20, pady=(10, 2)
            )

        field_label("Question (front)")
        self.front = ctk.CTkTextbox(
            self,
            height=58,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            corner_radius=6,
            font=(FONT, 11),
            wrap="word",
        )
        self.front.pack(fill="x", padx=20)

        field_label("Answer (back)")
        self.back = ctk.CTkTextbox(
            self,
            height=58,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            corner_radius=6,
            font=(FONT, 11),
            wrap="word",
        )
        self.back.pack(fill="x", padx=20)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(12, 0))

        self.topic = ctk.CTkComboBox(
            row,
            values=topics or ["general"],
            width=210,
            height=28,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            button_color=BORDER,
            font=(FONT, 11),
        )
        self.topic.set(default_topic or (topics[0] if topics else "general"))
        self.topic.pack(side="left")

        self.difficulty = ctk.CTkOptionMenu(
            row,
            values=["easy", "medium", "hard"],
            width=110,
            height=28,
            fg_color=CARD,
            text_color=TEXT,
            button_color=BORDER,
            font=(FONT, 11),
        )
        self.difficulty.set("medium")
        self.difficulty.pack(side="right")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=12)
        _primary_btn(btns, "Add card", self._save).pack(side="left", padx=6)
        _secondary_btn(btns, "Cancel", self.destroy).pack(side="left", padx=6)

        self.error = ctk.CTkLabel(self, text="", text_color=RED, font=(FONT, 9))
        self.error.pack()

    def _save(self):
        front = self.front.get("1.0", "end").strip()
        back = self.back.get("1.0", "end").strip()
        topic = self.topic.get().strip() or "general"
        if not front or not back:
            self.error.configure(text="Both question and answer are required.")
            return
        if self.on_save:
            self.on_save(front, back, topic, self.difficulty.get())
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  EDIT CARD DIALOG
# ═══════════════════════════════════════════════════════════════


class EditCardDialog(ctk.CTkToplevel):
    """popup to edit an existing flashcard"""

    def __init__(self, master, card, topics, on_save=None):
        super().__init__(master)
        self.title("Edit Card")
        self.geometry("420x380")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.card = card
        self.on_save = on_save
        self._build(topics)

    def _build(self, topics):
        def field_label(text):
            ctk.CTkLabel(self, text=text, text_color=MUTED, font=(FONT, 10)).pack(
                anchor="w", padx=20, pady=(10, 2)
            )

        field_label("Question (front)")
        self.front = ctk.CTkTextbox(
            self,
            height=58,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            corner_radius=6,
            font=(FONT, 11),
            wrap="word",
        )
        self.front.pack(fill="x", padx=20)
        self.front.insert("1.0", self.card.front)

        field_label("Answer (back)")
        self.back = ctk.CTkTextbox(
            self,
            height=58,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            corner_radius=6,
            font=(FONT, 11),
            wrap="word",
        )
        self.back.pack(fill="x", padx=20)
        self.back.insert("1.0", self.card.back)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(12, 0))

        self.topic = ctk.CTkComboBox(
            row,
            values=topics or ["general"],
            width=210,
            height=28,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            button_color=BORDER,
            font=(FONT, 11),
        )
        self.topic.set(self.card.topic)
        self.topic.pack(side="left")

        self.difficulty = ctk.CTkOptionMenu(
            row,
            values=["easy", "medium", "hard"],
            width=110,
            height=28,
            fg_color=CARD,
            text_color=TEXT,
            button_color=BORDER,
            font=(FONT, 11),
        )
        self.difficulty.set(self.card.difficulty)
        self.difficulty.pack(side="right")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=12)
        _primary_btn(btns, "Save", self._save).pack(side="left", padx=6)
        _secondary_btn(btns, "Cancel", self.destroy).pack(side="left", padx=6)

        self.error = ctk.CTkLabel(self, text="", text_color=RED, font=(FONT, 9))
        self.error.pack()

    def _save(self):
        front = self.front.get("1.0", "end").strip()
        back = self.back.get("1.0", "end").strip()
        topic = self.topic.get().strip() or "general"
        if not front or not back:
            self.error.configure(text="Both question and answer are required.")
            return
        if self.on_save:
            self.on_save(self.card.id, front, back, topic, self.difficulty.get())
        self.destroy()


# ═══════════════════════════════════════════════════════════════
#  GENERATE SCREEN
# ═══════════════════════════════════════════════════════════════


class GenerateScreen(ctk.CTkFrame):
    """screen where user pastes text and generates flashcards with ai"""

    PLACEHOLDER = "Paste your lecture notes here..."

    def __init__(
        self,
        master,
        api_key: str = "",
        on_cards_added=None,
        on_key_change=None,
        on_back=None,
        topics=None,
    ):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.api_key = api_key
        self.on_cards_added = on_cards_added
        self.on_key_change = on_key_change
        self.on_back = on_back
        self.topics = topics or []
        self._build()

    def set_api_key(self, key: str):
        self.api_key = key

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=PAD, pady=(PAD, GAP))

        if self.on_back:
            _secondary_btn(header, "\u2190 Back", self.on_back).pack(
                side="left", padx=(0, GAP)
            )
        ctk.CTkLabel(
            header, text="Generate Flashcards", text_color=TEXT, font=(FONT, 16, "bold")
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Key",
            width=50,
            height=26,
            command=self._open_key_dialog,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=MUTED,
            font=(FONT, 10),
            corner_radius=6,
        ).pack(side="right")

        self.folder_menu = ctk.CTkComboBox(
            header,
            values=["Auto (AI decides)"] + self.topics,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            button_color=BORDER,
            font=(FONT, 10),
            height=28,
            width=180,
        )
        self.folder_menu.set("Auto (AI decides)")
        self.folder_menu.pack(side="right", padx=(0, GAP))

        ctk.CTkLabel(
            self,
            text="Paste your notes or open a file, then Generate.  ·  Supported formats: PDF, TXT, DOCX",
            text_color=MUTED,
            font=(FONT, 11),
        ).pack(anchor="w", padx=PAD)

        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=SURFACE,
            text_color=MUTED,
            border_color=BORDER,
            corner_radius=10,
            font=(FONT, 11),
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True, padx=PAD, pady=GAP)
        self.textbox.insert("1.0", self.PLACEHOLDER)
        self.textbox.bind("<FocusIn>", self._clear_placeholder)
        self.textbox.bind("<FocusOut>", self._restore_placeholder)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=PAD, pady=(0, GAP))
        _secondary_btn(btn_row, "Open File", self._open_file).pack(
            side="left", padx=(0, GAP)
        )
        self.gen_btn = _primary_btn(btn_row, "Generate", self._generate)
        self.gen_btn.pack(side="left")

        self.status = ctk.CTkLabel(self, text="", text_color=MUTED, font=(FONT, 13))
        self.status.pack(anchor="w", padx=PAD, pady=(0, GAP))
        self._dot_job = None  # handle for the animated dots after-loop

    def _clear_placeholder(self, _=None):
        if self.textbox.get("1.0", "end").strip() == self.PLACEHOLDER:
            self.textbox.delete("1.0", "end")
            self.textbox.configure(text_color=TEXT)

    def _restore_placeholder(self, _=None):
        if not self.textbox.get("1.0", "end").strip():
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", self.PLACEHOLDER)
            self.textbox.configure(text_color=MUTED)

    def _current_text(self) -> str:
        text = self.textbox.get("1.0", "end").strip()
        return "" if text == self.PLACEHOLDER else text

    def _open_key_dialog(self):
        ApiKeyDialog(
            self,
            current_key=self.api_key,
            on_save=self.on_key_change,
        )

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Select file",
            filetypes=[("Supported files", "*.pdf *.docx *.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            from parser import parse_file

            text = parse_file(path)
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", text)
            self.textbox.configure(text_color=TEXT)
            self.status.configure(text=f"Loaded: {path.split('/')[-1]}")
        except FileNotSupportedError as e:
            self.status.configure(text=str(e), text_color=RED)

    def _generate(self):
        text = self._current_text()
        if not text:
            self._stop_dots()
            self.status.configure(text="Paste some text first!", text_color=RED)
            return

        self._stop_dots()
        self.status.configure(text="Generating", text_color=YELLOW)
        self._animate_dots("Generating")
        self.gen_btn.configure(state="disabled")

        import threading

        def worker():
            try:
                from agent import CardGenerator

                gen = CardGenerator(self.api_key)
                cards = gen.generate(text)
                self.after(0, lambda: self._done(cards))
            except Exception as exc:
                message = str(exc)
                self.after(0, lambda: self._error(message))

        threading.Thread(target=worker, daemon=True).start()

    def _animate_dots(self, base, n=1):
        """cycle base. -> base.. -> base... then repeat"""
        self.status.configure(text=base + "." * n)
        self._dot_job = self.after(500, lambda: self._animate_dots(base, n % 3 + 1))

    def _stop_dots(self):
        if self._dot_job is not None:
            self.after_cancel(self._dot_job)
            self._dot_job = None

    def _done(self, cards: list[FlashCard]):
        self._stop_dots()
        self.gen_btn.configure(state="normal")
        if not cards:
            self.status.configure(text="No cards generated. Try again.", text_color=RED)
            return
        topic = cards[0].topic
        folder = self.folder_menu.get()
        if folder and folder != "Auto (AI decides)":
            for card in cards:
                card.topic = folder
            topic = folder
        self.status.configure(
            text=f"Added {len(cards)} cards to '{topic}'.", text_color=MINT
        )
        self.textbox.delete("1.0", "end")
        self._restore_placeholder()
        if self.on_cards_added:
            self.on_cards_added(cards)

    def _error(self, msg: str):
        self._stop_dots()
        self.gen_btn.configure(state="normal")
        self.status.configure(text=msg, text_color=RED)


# ═══════════════════════════════════════════════════════════════
#  DECK SCREEN
# ═══════════════════════════════════════════════════════════════


class DeckScreen(ctk.CTkFrame):
    """topic folders; open a folder to browse and manage its cards"""

    def __init__(self, master, deck, on_change=None, on_study_topic=None):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.deck = deck
        self.on_change = on_change
        self.on_study_topic = on_study_topic
        self.current_topic = None  # None = folder list, otherwise an open folder
        self._build()

    def _build(self):
        self.search_text = ""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=PAD, pady=(PAD, GAP))

        # persistent search bar — always below the header
        self.search_entry = ctk.CTkEntry(
            self,
            height=BTN_H,
            corner_radius=8,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            placeholder_text="Search cards...",
        )
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.pack(fill="x", padx=PAD, pady=(0, GAP))

        self.body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=BG,
            scrollbar_button_hover_color=BG,
            scrollbar_fg_color=BG,
        )
        self.body.pack(fill="both", expand=True, padx=PAD, pady=(0, GAP))

        self.refresh()

    def refresh(self):
        self._render_header()
        self._render_body()

    def _render_header(self):
        for w in self.header.winfo_children():
            w.destroy()
        if self.current_topic is None:
            self._folder_list_header()
        else:
            self._folder_header()

    def _render_body(self):
        for w in self.body.winfo_children():
            w.destroy()
        # search always wins — works from both folder list and inside a folder
        if self.search_text:
            if self.current_topic is None:
                self._show_search(self.search_text)
            else:
                # filter within the open folder
                try:
                    pattern = re.compile(self.search_text, re.IGNORECASE)
                except re.error:
                    pattern = None
                cards = self.deck.cards_in_topic(self.current_topic)
                if pattern:
                    cards = [
                        c
                        for c in cards
                        if pattern.search(c.front) or pattern.search(c.back)
                    ]
                if cards:
                    self._show_cards(cards)
                else:
                    self._empty("No matching cards.")
        elif self.current_topic is None:
            self._show_folders()
        else:
            self._show_cards(self.deck.cards_in_topic(self.current_topic))

    # ── folder list ──────────────────────────────────────────

    def _folder_list_header(self):
        ctk.CTkLabel(
            self.header, text="Your Decks", text_color=TEXT, font=(FONT, 16, "bold")
        ).pack(side="left")

        _primary_btn(self.header, "+ New card", self._add_card).pack(side="right")
        _secondary_btn(self.header, "+ New folder", self._new_folder).pack(
            side="right", padx=(0, GAP)
        )

    def _show_folders(self):
        topics = self.deck.topics()
        if not topics:
            self._empty("No cards yet — add one with + New card.")
            return
        for topic in topics:
            self._folder_row(topic)

    def _folder_row(self, topic):
        cards = self.deck.cards_in_topic(topic)
        known = sum(1 for c in cards if c.status == "known")
        pct = known / len(cards) if cards else 0

        row = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=10)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)
        row.configure(height=68)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        arrow = ctk.CTkLabel(
            left,
            text="\u25b8",
            text_color=TEXT,
            font=(FONT, 20, "bold"),
            anchor="center",
        )
        arrow.pack(side="left", anchor="center")

        name = ctk.CTkLabel(
            left,
            text=f"  {topic}",
            text_color=TEXT,
            font=(FONT, 13, "bold"),
            anchor="w",
        )
        name.pack(side="left", anchor="center")

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right", padx=14)

        bar_bg = ctk.CTkFrame(
            right, fg_color="#3a3a3a", corner_radius=3, height=5, width=70
        )
        bar_bg.pack(side="left", anchor="center")
        bar_bg.pack_propagate(False)
        if pct > 0:
            bar_fg = ctk.CTkFrame(bar_bg, fg_color=MINT, corner_radius=3)
            bar_fg.place(relx=0, rely=0, relwidth=pct, relheight=1.0)

        pct_label = ctk.CTkLabel(
            right, text=f"{round(pct * 100)}%", text_color=MUTED, font=(FONT, 9)
        )
        pct_label.pack(side="left", padx=(5, 0), anchor="center")

        for widget in (row, left, arrow, name, right, pct_label, bar_bg):
            widget.bind("<Button-1>", lambda _e, t=topic: self._open_topic(t))

    def _show_search(self, query):
        try:
            cards = self.deck.search(query)
        except re.error:
            cards = []
        if not cards:
            self._empty("No matching cards.")
            return
        for card in cards:
            self._card_row(card)

    # ── inside one folder ─────────────────────────────────────

    def _folder_header(self):
        _primary_btn(
            self.header,
            "\u25b6  Study",
            lambda: (
                self.on_study_topic(self.current_topic) if self.on_study_topic else None
            ),
        ).pack(side="right")
        ctk.CTkButton(
            self.header,
            text="+",
            command=self._add_card,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=TEXT,
            font=(FONT, 14),
            corner_radius=8,
            height=BTN_H,
            width=36,
        ).pack(side="right", padx=(0, GAP))
        ctk.CTkButton(
            self.header,
            text="\u2190",
            command=self._close_topic,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=TEXT,
            font=(FONT, 14),
            corner_radius=8,
            height=BTN_H,
            width=36,
        ).pack(side="left")
        ctk.CTkLabel(
            self.header,
            text=self.current_topic,
            text_color=TEXT,
            font=(FONT, 12, "bold"),
        ).pack(side="left", padx=GAP)

    def _show_cards(self, cards):
        if not cards:
            self._empty("This folder is empty.")
            return
        cards = sorted(cards, key=lambda c: (c.status != "new", c.status != "review"))
        for card in cards:
            self._card_row(card)

    def _card_row(self, card):
        row = ctk.CTkFrame(self.body, fg_color=SURFACE, corner_radius=8)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)
        row.configure(height=56)

        diff_colors = {"easy": MINT, "medium": YELLOW, "hard": RED}
        dot_color = diff_colors.get(card.difficulty, MUTED)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=6)

        ctk.CTkLabel(
            left,
            text=card.front[:60] + ("..." if len(card.front) > 60 else ""),
            text_color=TEXT,
            font=(FONT, 11, "bold"),
            anchor="w",
        ).pack(anchor="w")

        meta = f"{card.topic}  \u00b7  {card.difficulty}  \u00b7  {card.status}"
        ctk.CTkLabel(
            left, text=meta, text_color=MUTED, font=(FONT, 9), anchor="w"
        ).pack(anchor="w")

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right", padx=8, pady=6)

        ctk.CTkLabel(right, text="\u25cf", text_color=dot_color, font=(FONT, 12)).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(
            right,
            text="Edit",
            command=lambda cid=card.id: self._edit(cid),
            fg_color=CARD,
            hover_color=BORDER,
            text_color=TEXT,
            font=(FONT, 10),
            corner_radius=6,
            height=26,
            width=50,
            border_width=1,
            border_color=BORDER,
        ).pack(side="left", padx=(0, 4))
        _danger_btn(right, "Del", lambda cid=card.id: self._delete(cid)).pack(
            side="left"
        )

    # ── actions ───────────────────────────────────────────────

    def _edit(self, card_id):
        card = self.deck.cards.get(card_id)
        if not card:
            return
        EditCardDialog(
            self, card=card, topics=self.deck.topics(), on_save=self._save_edit
        )

    def _save_edit(self, card_id, front, back, topic, difficulty):
        card = self.deck.cards.get(card_id)
        if not card:
            return
        card.front = front
        card.back = back
        card.topic = topic
        card.difficulty = difficulty
        if self.on_change:
            self.on_change()
        self.refresh()

    def _empty(self, text):
        ctk.CTkLabel(self.body, text=text, text_color=MUTED, font=(FONT, 11)).pack(
            pady=30
        )

    def _on_search(self, _=None):
        self.search_text = self.search_entry.get().strip()
        self._render_body()

    def _open_topic(self, topic):
        self.current_topic = topic
        self.search_text = ""
        self.search_entry.delete(0, "end")
        self.search_entry.configure(placeholder_text=f"Search in {topic}...")
        self.refresh()

    def _close_topic(self):
        self.current_topic = None
        self.search_text = ""
        self.search_entry.configure(placeholder_text="Search cards...")
        self.refresh()

    def _add_card(self):
        CardDialog(
            self,
            topics=self.deck.topics(),
            default_topic=self.current_topic or "",
            on_save=self._save_new_card,
        )

    def _save_new_card(self, front, back, topic, difficulty):
        self.deck.add(
            FlashCard(front=front, back=back, topic=topic, difficulty=difficulty)
        )
        if self.on_change:
            self.on_change()
        self.refresh()

    def _new_folder(self):
        """small dialog to name a new folder, then open it"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Folder")
        dialog.geometry("320x170")
        dialog.resizable(False, False)
        dialog.configure(fg_color=BG)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()

        ctk.CTkLabel(
            dialog, text="Folder name", text_color=TEXT, font=(FONT, 12, "bold")
        ).pack(padx=24, pady=(20, 6), anchor="w")

        entry = ctk.CTkEntry(
            dialog,
            fg_color=CARD,
            text_color=TEXT,
            border_color=BORDER,
            placeholder_text="e.g. Biology",
            height=BTN_H,
            corner_radius=8,
        )
        entry.pack(fill="x", padx=24)
        entry.focus()

        def _create(_e=None):
            name = entry.get().strip()
            if not name:
                return
            dialog.destroy()
            self._open_topic(name)

        entry.bind("<Return>", _create)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=14)
        _secondary_btn(btn_row, "Cancel", dialog.destroy).pack(side="left")
        _primary_btn(btn_row, "Create", _create).pack(side="right")

    def _delete(self, card_id):
        self.deck.remove(card_id)
        if self.on_change:
            self.on_change()
        if self.current_topic and not self.deck.cards_in_topic(self.current_topic):
            self.current_topic = None
        self.refresh()


# ═══════════════════════════════════════════════════════════════
#  STUDY PICKER SCREEN
# ═══════════════════════════════════════════════════════════════


class StudyPickerScreen(ctk.CTkFrame):
    """study tab — topic selector at top, flashcard shown immediately below"""

    def __init__(self, master, deck, on_save=None):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.deck = deck
        self.on_save = on_save
        # session state
        self.queue = []
        self.index = 0
        self.knew_count = 0
        self.forgot_count = 0
        self.showing_back = False
        self.finished = False
        self._selected = None  # None = All
        self._toplevel = None
        self._build()

    def start(self):
        """bind keys and load the default (All) queue — call after packing"""
        self._load_topic(None)

    def _build(self):
        # ── top bar: topic selector (left) + live stats (right) ────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=PAD, pady=(PAD, GAP))

        ctk.CTkLabel(top, text="Topic:", text_color=MUTED, font=(FONT, 10)).pack(
            side="left", padx=(0, GAP)
        )
        self.sel_menu = ctk.CTkOptionMenu(
            top,
            values=["All"],
            command=lambda v: self._load_topic(
                None if v.startswith("All") else v.split("  (")[0]
            ),
            fg_color=CARD,
            button_color=BORDER,
            button_hover_color=BORDER,
            text_color=TEXT,
            font=(FONT, 10),
            height=28,
            width=180,
            corner_radius=6,
            dynamic_resizing=False,
        )
        self.sel_menu.pack(side="left")

        self.count_label = ctk.CTkLabel(top, text="", text_color=MUTED, font=(FONT, 10))
        self.count_label.pack(side="right")

        # ── card (fills remaining space) ────────────────────────────────
        self.card_frame = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=14,
            border_color=BORDER,
            border_width=1,
        )
        self.card_frame.pack(fill="both", expand=True, padx=PAD, pady=GAP)

        self.card_label = ctk.CTkLabel(
            self.card_frame,
            text="",
            text_color=TEXT,
            font=(FONT, 16, "bold"),
            wraplength=460,
            justify="center",
        )
        self.card_label.pack(expand=True, padx=20)

        self.card_frame.bind("<Button-1>", lambda _: self._flip())
        self.card_label.bind("<Button-1>", lambda _: self._flip())

        # ── progress bar ──────────────────────────────────────────────
        self.progress = ctk.CTkProgressBar(
            self, height=4, corner_radius=2, fg_color=SURFACE, progress_color=MINT
        )
        self.progress.pack(fill="x", padx=PAD, pady=(0, GAP))
        self.progress.set(0)

        # ── answer buttons ────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        bar.grid_columnconfigure(0, weight=1, uniform="ans")
        bar.grid_columnconfigure(1, weight=1, uniform="ans")

        self.forgot_btn = ctk.CTkButton(
            bar,
            text="\u2190  Didn't know",
            command=self._forgot,
            fg_color="#2a1515",
            hover_color="#3d2020",
            text_color=RED,
            font=(FONT, 11, "bold"),
            corner_radius=8,
            height=40,
            border_width=1,
            border_color="#3d2020",
        )
        self.forgot_btn.grid(row=0, column=0, sticky="ew", padx=(0, GAP // 2))

        self.knew_btn = ctk.CTkButton(
            bar,
            text="Knew it  \u2192",
            command=self._knew,
            fg_color=MINT,
            hover_color=MINT_HOVER,
            text_color=BG,
            font=(FONT, 11, "bold"),
            corner_radius=8,
            height=40,
        )
        self.knew_btn.grid(row=0, column=1, sticky="ew", padx=(GAP // 2, 0))

        self._set_buttons(False)

    # ── topic selector ────────────────────────────────────────

    def _refresh_selector(self):
        topics = self.deck.topics()
        all_n = sum(1 for _ in self.deck.due_cards())
        values = [f"All  ({all_n})"]
        for topic in topics:
            due_n = sum(
                1 for c in self.deck.cards_in_topic(topic) if c.status != "known"
            )
            values.append(f"{topic}  ({due_n})")
        self.sel_menu.configure(values=values)
        # keep current selection label in sync
        if self._selected is None:
            self.sel_menu.set(values[0])
        else:
            for v in values:
                if v.startswith(self._selected):
                    self.sel_menu.set(v)
                    break

    # ── session control ───────────────────────────────────────

    def _load_topic(self, topic):
        self._selected = topic
        self._refresh_selector()
        if topic is None:
            self.queue = list(self.deck.due_cards())
        else:
            cards = self.deck.cards_in_topic(topic)
            due = [c for c in cards if c.status != "known"]
            self.queue = due if due else cards
        self.index = 0
        self.knew_count = 0
        self.forgot_count = 0
        self.finished = False
        self._bind_keys()
        if not self.queue:
            self._show_empty()
            return
        self._show()

    def _show_empty(self):
        self.card_label.configure(
            text="Nothing to study here!\nAll cards are already known."
        )
        self.progress.set(1.0)
        self.count_label.configure(text="")
        self._set_buttons(False)

    def _show(self):
        if self.index >= len(self.queue):
            self._finish()
            return
        card = self.queue[self.index]
        self.showing_back = False
        self.card_label.configure(text=card.front)
        self.progress.set(self.index / len(self.queue))
        remaining = len(self.queue) - self.index
        self.count_label.configure(
            text=f"\u2713 {self.knew_count}   \u2717 {self.forgot_count}   \u00b7   {remaining} left"
        )
        self._set_buttons(True)
        if self._toplevel:
            self._toplevel.focus_set()

    def _finish(self):
        self.finished = True
        self.progress.set(1.0)
        total = len(self.queue)
        known_now = sum(1 for c in self.queue if c.status == "known")
        coverage = round(known_now / total * 100) if total else 0
        self.count_label.configure(
            text=f"\u2713 {self.knew_count}   \u2717 {self.forgot_count}   \u00b7   done"
        )
        self.card_label.configure(
            text=f"Session complete\n\n{coverage}% of these cards are now known"
        )
        self._set_buttons(False)
        self._refresh_selector()
        if self.on_save:
            self.on_save()

    def _set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        self.forgot_btn.configure(state=state)
        self.knew_btn.configure(state=state)

    # ── card interaction ──────────────────────────────────────

    def _flip(self):
        if self.finished or self.index >= len(self.queue):
            return
        card = self.queue[self.index]
        self.showing_back = not self.showing_back
        if self.showing_back:
            self.card_label.configure(text=card.back)
        else:
            self.card_label.configure(text=card.front)

    def _knew(self):
        self._answer(True)

    def _forgot(self):
        self._answer(False)

    def _answer(self, knew):
        if self.finished or self.index >= len(self.queue):
            return
        card = self.queue[self.index]
        self.deck.mark(card.id, knew_it=knew)
        if knew:
            self.knew_count += 1
        else:
            self.forgot_count += 1
        self.index += 1
        self._show()

    # ── keyboard shortcuts ────────────────────────────────────

    def _bind_keys(self):
        self._toplevel = self.winfo_toplevel()
        self._toplevel.bind("<space>", lambda _: self._flip())
        self._toplevel.bind("<Right>", lambda _: self._knew())
        self._toplevel.bind("<Return>", lambda _: self._knew())
        self._toplevel.bind("<Left>", lambda _: self._forgot())
        self._toplevel.focus_set()

    def _unbind_keys(self):
        if self._toplevel is None:
            return
        for seq in ("<space>", "<Right>", "<Return>", "<Left>"):
            self._toplevel.unbind(seq)
        self._toplevel = None

    def pack_forget(self):
        self._unbind_keys()
        if self.on_save:
            self.on_save()
        super().pack_forget()

    def destroy(self):
        self._unbind_keys()
        super().destroy()


# ═══════════════════════════════════════════════════════════════
#  STUDY SCREEN
# ═══════════════════════════════════════════════════════════════


class StudyScreen(ctk.CTkFrame):
    """study a set of flashcards one by one (used for folder-specific study)"""

    def __init__(self, master, deck, cards=None, title="Study", on_done=None):
        super().__init__(master, fg_color=BG, corner_radius=0)
        self.deck = deck
        self.title_text = title
        self.queue = list(cards) if cards else []
        self.on_done = on_done
        self.index = 0
        self.showing_back = False
        self.knew_count = 0
        self.forgot_count = 0
        self.finished = False
        self._toplevel = None
        self._build()

    def _build(self):
        # session title — use the nav bar to leave
        ctk.CTkLabel(
            self,
            text=self.title_text,
            text_color=TEXT,
            font=(FONT, 14, "bold"),
            anchor="w",
        ).pack(fill="x", padx=PAD, pady=(PAD, GAP))

        self.progress = ctk.CTkProgressBar(
            self, height=4, corner_radius=2, fg_color=SURFACE, progress_color=MINT
        )
        self.progress.pack(fill="x", padx=PAD, pady=(GAP, 2))
        self.progress.set(0)

        self.count_label = ctk.CTkLabel(
            self, text="", text_color=MUTED, font=(FONT, 10)
        )
        self.count_label.pack(pady=(0, GAP))

        self.card_frame = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=14,
            border_color=BORDER,
            border_width=1,
        )
        self.card_frame.pack(fill="both", expand=True, padx=PAD, pady=GAP)
        self.card_frame.pack_propagate(False)

        self.card_label = ctk.CTkLabel(
            self.card_frame,
            text="",
            text_color=TEXT,
            font=(FONT, 16, "bold"),
            wraplength=460,
            justify="center",
        )
        self.card_label.pack(expand=True, padx=20)

        self.card_frame.bind("<Button-1>", lambda _: self._flip())
        self.card_label.bind("<Button-1>", lambda _: self._flip())

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=PAD, pady=(0, PAD))
        bar.grid_columnconfigure(0, weight=1, uniform="ans")
        bar.grid_columnconfigure(1, weight=1, uniform="ans")

        self.forgot_btn = ctk.CTkButton(
            bar,
            text="\u2190   Didn't know",
            command=self._forgot,
            fg_color="#2a1515",
            hover_color="#3d2020",
            text_color=RED,
            font=(FONT, 12, "bold"),
            corner_radius=8,
            height=40,
            border_width=1,
            border_color="#3d2020",
        )
        self.forgot_btn.grid(row=0, column=0, sticky="ew", padx=(0, GAP // 2))

        self.knew_btn = ctk.CTkButton(
            bar,
            text="Knew it   \u2192",
            command=self._knew,
            fg_color=MINT,
            hover_color=MINT_HOVER,
            text_color=BG,
            font=(FONT, 12, "bold"),
            corner_radius=8,
            height=40,
        )
        self.knew_btn.grid(row=0, column=1, sticky="ew", padx=(GAP // 2, 0))

        self._set_buttons(False)
        self.answer_bar = bar

        # shown only when the session ends
        self.done_btn = _primary_btn(self, "Back to Decks  \u2192", self._back)

    # ── session control ───────────────────────────────────────

    def start(self):
        self._bind_keys()
        if not self.queue:
            self._set_buttons(False)
            self.count_label.configure(text="")
            self.card_label.configure(
                text="Nothing to study here!\nEverything is already known."
            )
            return
        self.index = 0
        self.knew_count = 0
        self.forgot_count = 0
        self.finished = False
        self._show()

    def _show(self):
        if self.index >= len(self.queue):
            self._finish()
            return
        card = self.queue[self.index]
        self.showing_back = False
        self.card_label.configure(text=card.front)
        self.progress.set(self.index / len(self.queue))
        remaining = len(self.queue) - self.index
        self.count_label.configure(
            text=f"\u2713 {self.knew_count}   \u2717 {self.forgot_count}   \u00b7   {remaining} left"
        )
        self._set_buttons(True)
        if self._toplevel is not None:
            self._toplevel.focus_set()

    def _finish(self):
        self.finished = True
        self.progress.set(1.0)
        total = len(self.queue)
        known_now = sum(1 for c in self.queue if c.status == "known")
        coverage = round(known_now / total * 100) if total else 0
        self.count_label.configure(
            text=f"\u2713 {self.knew_count}   \u2717 {self.forgot_count}   \u00b7   done"
        )
        self.card_label.configure(
            text=f"Session complete\n\n{coverage}% of these cards are now known"
        )
        self._set_buttons(False)
        self.answer_bar.pack_forget()
        self.done_btn.pack(fill="x", padx=PAD, pady=(0, PAD))

    def _set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        self.forgot_btn.configure(state=state)
        self.knew_btn.configure(state=state)

    def _flip(self):
        if self.finished or self.index >= len(self.queue):
            return
        card = self.queue[self.index]
        self.showing_back = not self.showing_back
        if self.showing_back:
            self.card_label.configure(text=card.back)
        else:
            self.card_label.configure(text=card.front)

    def _knew(self):
        self._answer(True)

    def _forgot(self):
        self._answer(False)

    def _answer(self, knew):
        if self.finished or self.index >= len(self.queue):
            return
        card = self.queue[self.index]
        self.deck.mark(card.id, knew_it=knew)
        if knew:
            self.knew_count += 1
        else:
            self.forgot_count += 1
        self.index += 1
        self._show()

    def _bind_keys(self):
        self._toplevel = self.winfo_toplevel()
        self._toplevel.bind("<space>", lambda _: self._flip())
        self._toplevel.bind("<Right>", lambda _: self._knew())
        self._toplevel.bind("<Return>", lambda _: self._knew())
        self._toplevel.bind("<Left>", lambda _: self._forgot())
        self._toplevel.focus_set()

    def _unbind_keys(self):
        if self._toplevel is None:
            return
        for seq in ("<space>", "<Right>", "<Return>", "<Left>"):
            self._toplevel.unbind(seq)
        self._toplevel = None

    def _back(self):
        self._unbind_keys()
        if self.on_done:
            self.on_done()

    def pack_forget(self):
        self._unbind_keys()
        super().pack_forget()

    def destroy(self):
        self._unbind_keys()
        super().destroy()
