# app module - main application with navigation
# ties everything together: generate, deck, study

import os
import tkinter

import customtkinter as ctk

from deck import Deck
from screens import (
    ApiKeyDialog,
    DeckScreen,
    GenerateScreen,
    StudyPickerScreen,
    StudyScreen,
)
from storage import load_config, load_deck, save_config, save_deck

# ── theme setup ───────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── colors: black + mint ──────────────────────────────────────
BG = "#0a0a0a"
SURFACE = "#111111"
CARD = "#181818"
BORDER = "#252525"
MINT = "#3dd68c"
MUTED = "#8a8a8a"
FONT = "Segoe UI"
NAV_H = 44


class App:
    """main app class — manages window, navigation and data"""

    def __init__(self):
        # create main window
        self.root = ctk.CTk()
        self.root.title("QuizMaster")
        self.root.geometry("560x480")
        self.root.minsize(480, 400)
        self.root.maxsize(760, 1100)
        self.root.configure(fg_color=BG)
        self.root.resizable(True, True)
        self._set_icon()

        # load data
        self.deck: Deck = load_deck()
        self._api_key = self._load_api_key()
        self._current_screen = None
        self._nav_btns: dict = {}

        # build ui
        self._build_nav()
        self._frame = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        self._frame.pack(fill="both", expand=True)

        # decks screen is the landing page
        self._show_deck()

        # prompt for api key if missing
        if not self._api_key:
            ApiKeyDialog(
                self.root,
                current_key="",
                on_save=self._save_key,
            )

    # ── window icon ───────────────────────────────────────────

    def _set_icon(self) -> None:
        """draw a small mint-diamond app icon in memory — no external file needed"""
        try:
            size = 64
            icon = tkinter.PhotoImage(width=size, height=size)
            center = size / 2
            radius = size * 0.42
            rows = []
            for y in range(size):
                # a pixel is "inside" the diamond by manhattan distance from center
                row = [
                    MINT if abs(x - center) + abs(y - center) <= radius else BG
                    for x in range(size)
                ]
                rows.append("{" + " ".join(row) + "}")
            icon.put(" ".join(rows))
            self._icon = icon  # keep a reference so it isn't garbage-collected
            self.root.iconphoto(True, icon)
        except Exception:
            pass  # icon is cosmetic — never let it block startup

    # ── api key handling ──────────────────────────────────────

    def _load_api_key(self) -> str:
        # try .env file first, then env vars, then config file
        self._load_dotenv()
        env = os.environ.get("LLM_API_KEY", "") or os.environ.get("API_KEY", "")
        return env if env else load_config().get("api_key", "")

    def _load_dotenv(self) -> None:
        # load key=value pairs from .env file into os.environ
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.isfile(env_path):
            return
        with open(env_path, "r", encoding="utf-8") as f:
            # read the file line by line until we hit EOF (empty string)
            line = f.readline()
            while line:
                stripped = line.strip()
                # only handle real KEY=VALUE lines, skip blanks and comments
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key, _, val = stripped.partition("=")
                    key, val = key.strip(), val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
                line = f.readline()

    def _save_key(self, key: str) -> None:
        self._api_key = key
        cfg = load_config()
        cfg["api_key"] = key
        save_config(cfg)
        # update current screen if it needs the key
        if self._current_screen and hasattr(self._current_screen, "set_api_key"):
            self._current_screen.set_api_key(key)

    # ── navigation bar ────────────────────────────────────────

    def _build_nav(self) -> None:
        nav = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=0, height=NAV_H)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        # separator line
        ctk.CTkFrame(self.root, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x"
        )

        # logo
        ctk.CTkLabel(
            nav,
            text="◆",
            font=(FONT, 16),
            text_color=MINT,
            fg_color=CARD,
            corner_radius=6,
            width=30,
            height=30,
        ).pack(side="left", padx=(12, 4), pady=6)

        for name, cmd in [
            ("Decks", self._show_deck),
            ("Study", self._show_study),
            ("Generate", self._show_generate),
        ]:
            b = ctk.CTkButton(
                nav,
                text=name,
                command=cmd,
                width=80,
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color=CARD,
                text_color=MUTED,
                font=(FONT, 11),
                border_width=0,
            )
            b.pack(side="left", padx=2, pady=8)
            self._nav_btns[name] = b

    def _set_active(self, name: str) -> None:
        for n, b in self._nav_btns.items():
            if n == name:
                b.configure(fg_color=CARD, text_color=MINT, font=(FONT, 11, "bold"))
            else:
                b.configure(fg_color="transparent", text_color=MUTED, font=(FONT, 11))

    # ── screen switching ──────────────────────────────────────

    def navigate(self, screen) -> None:
        if self._current_screen is not None:
            self._current_screen.pack_forget()
        self._current_screen = screen
        screen.pack(in_=self._frame, fill="both", expand=True)

    def _show_generate(self) -> None:
        s = GenerateScreen(
            self._frame,
            api_key=self._api_key,
            on_cards_added=self._cards_added,
            on_key_change=self._save_key,
            topics=self.deck.topics(),
        )
        self.navigate(s)
        self._set_active("Generate")

    def _show_deck(self, open_topic=None) -> None:
        s = DeckScreen(
            self._frame,
            self.deck,
            on_change=self._save,
            on_study_topic=self._study_topic,
        )
        if open_topic:
            s._open_topic(open_topic)
        self.navigate(s)
        self._set_active("Decks")

    def _study_topic(self, topic: str) -> None:
        """launch a focused study session for one folder, then return to it"""
        cards = self.deck.cards_in_topic(topic)
        due = [c for c in cards if c.status != "known"]
        study_cards = due if due else cards

        def _done():
            self._save()
            self._show_deck(open_topic=topic)

        s = StudyScreen(
            self._frame,
            self.deck,
            cards=study_cards,
            title=topic,
            on_done=_done,
        )
        self.navigate(s)
        self._set_active("Decks")
        s.start()

    def _show_study(self) -> None:
        s = StudyPickerScreen(
            self._frame,
            self.deck,
            on_save=self._save,
        )
        self.navigate(s)
        self._set_active("Study")
        s.start()

    # ── data handling ─────────────────────────────────────────

    def _cards_added(self, cards: list) -> None:
        for c in cards:
            self.deck.add(c)
        self._save()
        self._show_deck()

    def _save(self) -> None:
        save_deck(self.deck)

    def run(self) -> None:
        self.root.mainloop()
