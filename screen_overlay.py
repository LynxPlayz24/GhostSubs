"""
Transparent, always-on-top subtitle overlay for your desktop.
Reads from translation.txt and displays subtitles over any window.

Controls:
  - Drag to reposition
  - Scroll wheel to resize text
  - Right-click to close
"""
import tkinter as tk
import os
import sys

TRANSLATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translation.txt")
POLL_MS = 50
MIN_FONT = 16
MAX_FONT = 48


class SubtitleOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Subtitles")
        self.root.overrideredirect(True)          # No title bar / borders
        self.root.attributes("-topmost", True)     # Always on top

        # Transparent background via chroma key
        self._chroma = "#010101"
        self.root.config(bg=self._chroma)
        self.root.attributes("-transparentcolor", self._chroma)

        # Screen geometry
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.w = int(sw * 0.50)
        self.h = 70
        x = (sw - self.w) // 2
        y = sh - self.h - 60
        self.root.geometry(f"{self.w}x{self.h}+{x}+{y}")

        # Dark rounded-ish bar (canvas)
        self.canvas = tk.Canvas(
            self.root, width=self.w, height=self.h,
            bg=self._chroma, highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Draw rounded rect background
        self._draw_bg()

        # Subtitle text on canvas
        self.font_size = 18
        self._text_id = self.canvas.create_text(
            self.w // 2, self.h // 2,
            text="Waiting for subtitles...",
            fill="white",
            font=("Arial", self.font_size, "bold"),
            width=self.w - 60,
            justify="center",
        )

        # --- Dragging ---
        self._dx = 0
        self._dy = 0
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        # --- Scroll to resize ---
        self.canvas.bind("<MouseWheel>", self._on_scroll)

        # --- Right-click to close ---
        self.canvas.bind("<ButtonPress-3>", lambda e: self.root.destroy())

        # Start polling
        self._last_text = ""
        self._poll()

    # ── drawing ──────────────────────────────────────────────
    def _draw_bg(self):
        self.canvas.delete("bg")
        r = 18  # corner radius
        x0, y0, x1, y1 = 6, 6, self.w - 6, self.h - 6
        # Rounded rectangle via arcs + rectangle fills
        self.canvas.create_arc(x0, y0, x0 + 2*r, y0 + 2*r, start=90,  extent=90,  fill="#111", outline="#111", tags="bg")
        self.canvas.create_arc(x1 - 2*r, y0, x1, y0 + 2*r, start=0,   extent=90,  fill="#111", outline="#111", tags="bg")
        self.canvas.create_arc(x0, y1 - 2*r, x0 + 2*r, y1, start=180, extent=90,  fill="#111", outline="#111", tags="bg")
        self.canvas.create_arc(x1 - 2*r, y1 - 2*r, x1, y1, start=270, extent=90,  fill="#111", outline="#111", tags="bg")
        self.canvas.create_rectangle(x0 + r, y0, x1 - r, y1, fill="#111", outline="#111", tags="bg")
        self.canvas.create_rectangle(x0, y0 + r, x1, y1 - r, fill="#111", outline="#111", tags="bg")
        self.canvas.tag_lower("bg")

    # ── drag ─────────────────────────────────────────────────
    def _start_drag(self, e):
        self._dx = e.x
        self._dy = e.y

    def _on_drag(self, e):
        nx = self.root.winfo_x() + e.x - self._dx
        ny = self.root.winfo_y() + e.y - self._dy
        self.root.geometry(f"+{nx}+{ny}")

    # ── scroll to resize text ────────────────────────────────
    def _on_scroll(self, e):
        if e.delta > 0:
            self.font_size = min(MAX_FONT, self.font_size + 2)
        else:
            self.font_size = max(MIN_FONT, self.font_size - 2)
        self.canvas.itemconfig(self._text_id, font=("Arial", self.font_size, "bold"))

    # ── poll translation.txt ─────────────────────────────────
    def _poll(self):
        try:
            if os.path.exists(TRANSLATION_FILE):
                with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if text and text != self._last_text:
                    self._last_text = text
                    self.canvas.itemconfig(self._text_id, text=text)
        except Exception:
            pass
        self.root.after(POLL_MS, self._poll)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    SubtitleOverlay().run()
