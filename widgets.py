import tkinter as tk


class FlipCard(tk.Canvas):
    FRONT_BG = "#1e2a3a"
    BACK_BG = "#1a3a2a"
    TEXT_COLOR = "#e8e8e8"
    BORDER_COLOR = "#3a4a5a"

    def __init__(self, master, width=520, height=300, **kwargs):
        super().__init__(master, width=width, height=height,
                         bg="#0d1117", highlightthickness=0, **kwargs)
        self._w = width
        self._h = height
        self._card = None
        self._showing_front = True
        self._animating = False
        self.bind("<Button-1>", self._on_click)

    def load(self, card) -> None:
        self._card = card
        self._showing_front = True
        self._animating = False
        self._redraw(scale_x=1.0)

    def flip(self) -> None:
        if self._animating or self._card is None:
            return
        self._animating = True
        self._animate_scale(1.0, 0.0, 12, on_done=self._swap_and_expand)

    def _swap_and_expand(self) -> None:
        self._showing_front = not self._showing_front
        self._animate_scale(0.0, 1.0, 12, on_done=self._done_animating)

    def _done_animating(self) -> None:
        self._animating = False

    def _animate_scale(self, start: float, end: float, steps: int, on_done) -> None:
        delta = (end - start) / steps

        def step(i: int, value: float) -> None:
            self._redraw(scale_x=max(0.0, value))
            if i < steps:
                self.after(20, step, i + 1, value + delta)
            else:
                on_done()

        step(0, start)

    def _redraw(self, scale_x: float = 1.0) -> None:
        self.delete("all")
        if self._card is None:
            return

        cx = self._w / 2
        card_w = int(self._w * 0.9 * scale_x)
        card_h = int(self._h * 0.88)
        x0 = cx - card_w // 2
        x1 = cx + card_w // 2
        y0 = int(self._h * 0.06)
        y1 = y0 + card_h

        bg = self.FRONT_BG if self._showing_front else self.BACK_BG
        self.create_rectangle(x0, y0, x1, y1, fill=bg, outline=self.BORDER_COLOR,
                               width=2, tags="card")

        if scale_x > 0.15:
            label = "QUESTION" if self._showing_front else "ANSWER"
            label_color = "#4a9eff" if self._showing_front else "#4aff9e"
            self.create_text(cx, y0 + 18, text=label, fill=label_color,
                             font=("Helvetica", 9, "bold"))

            text = self._card.front if self._showing_front else self._card.back
            wrap = max(1, int((card_w - 40) / (scale_x if scale_x > 0.3 else 0.3)))
            self.create_text(cx, (y0 + y1) // 2, text=text, fill=self.TEXT_COLOR,
                             font=("Helvetica", 13), width=wrap, justify="center")

            diff = self._card.difficulty
            diff_colors = {"easy": "#4aff9e", "medium": "#ffd700", "hard": "#ff6b6b"}
            self.create_text(x1 - 8, y1 - 10, text=diff.upper(),
                             fill=diff_colors.get(diff, "#aaa"),
                             font=("Helvetica", 8, "bold"), anchor="se")

    def _on_click(self, _event) -> None:
        self.flip()


class AnimatedProgress(tk.Canvas):
    def __init__(self, master, width=500, height=12, **kwargs):
        super().__init__(master, width=width, height=height,
                         bg="#0d1117", highlightthickness=0, **kwargs)
        self._w = width
        self._h = height
        self._current = 0.0
        self._target = 0.0
        self._draw(0.0)

    def set_progress(self, value: float) -> None:
        self._target = max(0.0, min(1.0, value))
        self._animate()

    def _animate(self) -> None:
        diff = self._target - self._current
        if abs(diff) < 0.005:
            self._current = self._target
            self._draw(self._current)
            return
        self._current += diff * 0.25
        self._draw(self._current)
        self.after(16, self._animate)

    def _draw(self, value: float) -> None:
        self.delete("all")
        self.create_rectangle(0, 0, self._w, self._h, fill="#1e2a3a", outline="")
        bar_w = int(self._w * value)
        if bar_w > 0:
            self.create_rectangle(0, 0, bar_w, self._h, fill="#4a9eff", outline="")
