import tkinter as tk

FONT = "Segoe UI"


def _ease(t: float) -> float:
    return t * t * (3 - 2 * t)  # smoothstep


class FlipCard(tk.Canvas):
    FRONT_BG = "#1e2048"
    FRONT_BORDER = "#4a4aff"
    BACK_BG = "#1a3828"
    BACK_BORDER = "#2dba6b"
    TEXT_COLOR = "#e8e8f4"
    LABEL_FRONT = "#7b7fff"
    LABEL_BACK = "#2dba6b"

    def __init__(self, master, width=560, height=300, **kwargs):
        super().__init__(master, width=width, height=height,
                         bg="#111118", highlightthickness=0, **kwargs)
        self._cw = width
        self._ch = height
        self._card = None
        self._showing_front = True
        self._animating = False
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

    def load(self, card) -> None:
        self._card = card
        self._showing_front = True
        self._animating = False
        self._redraw(1.0)

    def flip(self) -> None:
        if self._animating or self._card is None:
            return
        self._animating = True
        self._animate(0, going_back=False)

    def _animate(self, step: int, going_back: bool) -> None:
        steps = 10
        if not going_back:
            t = _ease(step / steps)
            scale = 1.0 - t
            self._redraw(scale)
            if step < steps:
                self.after(18, self._animate, step + 1, False)
            else:
                self._showing_front = not self._showing_front
                self._animate(0, going_back=True)
        else:
            t = _ease(step / steps)
            scale = t
            self._redraw(scale)
            if step < steps:
                self.after(18, self._animate, step + 1, True)
            else:
                self._animating = False

    def _redraw(self, scale_x: float = 1.0) -> None:
        self.delete("all")
        if self._card is None:
            return

        cx = self._cw // 2
        cw = max(2, int(self._cw * 0.92 * scale_x))
        ch = int(self._ch * 0.90)
        x0 = cx - cw // 2
        x1 = cx + cw // 2
        y0 = int(self._ch * 0.05)
        y1 = y0 + ch
        r = 12  # corner radius

        bg = self.FRONT_BG if self._showing_front else self.BACK_BG
        border = self.FRONT_BORDER if self._showing_front else self.BACK_BORDER

        # rounded rect via polygon approximation
        if cw > r * 2:
            pts = [
                x0 + r, y0,  x1 - r, y0,
                x1, y0 + r,  x1, y1 - r,
                x1 - r, y1,  x0 + r, y1,
                x0, y1 - r,  x0, y0 + r,
            ]
            self.create_polygon(pts, fill=bg, outline=border, width=2, smooth=True)
        else:
            self.create_rectangle(x0, y0, x1, y1, fill=bg, outline=border, width=2)

        if scale_x > 0.2:
            label = "QUESTION" if self._showing_front else "ANSWER"
            lc = self.LABEL_FRONT if self._showing_front else self.LABEL_BACK
            self.create_text(cx, y0 + 22, text=label, fill=lc,
                             font=(FONT, 9, "bold"))

            text = self._card.front if self._showing_front else self._card.back
            wrap = max(40, int((cw - 60) / max(0.3, scale_x)))
            self.create_text(cx, (y0 + y1) // 2 + 6, text=text,
                             fill=self.TEXT_COLOR,
                             font=(FONT, 13), width=wrap, justify="center")

            diff = self._card.difficulty
            colors = {"easy": "#4ade80", "medium": "#facc15", "hard": "#f87171"}
            self.create_text(x1 - 10, y1 - 12, text=diff.upper(),
                             fill=colors.get(diff, "#aaa"),
                             font=(FONT, 8, "bold"), anchor="se")

    def _on_click(self, _) -> None:
        self.flip()


class AnimatedProgress(tk.Canvas):
    def __init__(self, master, width=540, height=5, **kwargs):
        super().__init__(master, width=width, height=height,
                         bg="#111118", highlightthickness=0, **kwargs)
        self._cw = width
        self._ch = height
        self._current = 0.0
        self._target = 0.0
        self._draw(0.0)

    def set_progress(self, value: float) -> None:
        self._target = max(0.0, min(1.0, value))
        self._step()

    def _step(self) -> None:
        diff = self._target - self._current
        if abs(diff) < 0.004:
            self._current = self._target
            self._draw(self._current)
            return
        self._current += diff * 0.22
        self._draw(self._current)
        self.after(14, self._step)

    def _draw(self, value: float) -> None:
        self.delete("all")
        self.create_rectangle(0, 0, self._cw, self._ch, fill="#252535", outline="")
        w = int(self._cw * value)
        if w > 0:
            self.create_rectangle(0, 0, w, self._ch, fill="#7b7fff", outline="")
