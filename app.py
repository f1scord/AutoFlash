import os
import tkinter as tk
from tkinter import ttk

from deck import Deck
from screens import ApiKeyDialog, DeckScreen, GenerateScreen, StudyScreen
from storage import load_config, load_deck, save_config, save_deck

BG = "#0d1117"
FG = "#e8e8e8"
ACCENT = "#4a9eff"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AutoFlash")
        self.root.geometry("640x580")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._apply_theme()
        self.deck: Deck = load_deck()
        self._api_key: str = self._load_api_key()
        self._current_screen = None
        self._build_nav()
        self._show_generate()

        if not self._api_key:
            ApiKeyDialog(self.root, current_key="", on_save=self._handle_key_save)

    def _load_api_key(self) -> str:
        env_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if env_key:
            return env_key
        config = load_config()
        return config.get("api_key", "")

    def _handle_key_save(self, key: str) -> None:
        self._api_key = key
        config = load_config()
        config["api_key"] = key
        save_config(config)
        if self._current_screen and hasattr(self._current_screen, "set_api_key"):
            self._current_screen.set_api_key(key)

    def _apply_theme(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Vertical.TScrollbar", background="#1e2a3a",
                        troughcolor=BG, arrowcolor=FG)

    def _build_nav(self) -> None:
        nav = tk.Frame(self.root, bg="#161b22", height=40)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        for label, cmd in [
            ("Generate", self._show_generate),
            ("Deck", self._show_deck),
            ("Study", self._show_study),
        ]:
            btn = tk.Button(nav, text=label, command=cmd,
                            bg="#161b22", fg=FG, relief="flat",
                            font=("Helvetica", 11), padx=18, pady=6,
                            cursor="hand2", activebackground="#1e2a3a",
                            activeforeground=ACCENT)
            btn.pack(side="left")

    def _switch(self, screen: tk.Frame) -> None:
        if self._current_screen is not None:
            self._current_screen.pack_forget()
        self._current_screen = screen
        screen.pack(fill="both", expand=True)

    def _show_generate(self) -> None:
        screen = GenerateScreen(
            self.root,
            api_key=self._api_key,
            on_cards_added=self._on_cards_added,
            on_study=self._show_study,
            on_key_change=self._handle_key_save,
        )
        self._switch(screen)

    def _show_deck(self) -> None:
        screen = DeckScreen(self.root, self.deck, on_delete=self._save)
        self._switch(screen)

    def _show_study(self) -> None:
        screen = StudyScreen(self.root, self.deck, on_done=self._show_deck)
        self._switch(screen)
        screen.start()

    def _on_cards_added(self, cards: list) -> None:
        for card in cards:
            self.deck.add(card)
        self._save()

    def _save(self) -> None:
        save_deck(self.deck)

    def run(self) -> None:
        self.root.mainloop()
