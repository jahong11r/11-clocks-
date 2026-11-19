#!/usr/bin/env python3
"""
Clock Widgets - ish stoli uchun soat vidjetlari
================================================

Turli xil chiroyli soat vidjetlari. Galereyadan birini tanlang va uni
ish stolining istalgan joyiga qo'ying.

Imkoniyatlar:
  * Shaffof, ramkasiz soat oynalari (Windows'da to'liq shaffof)
  * Sichqoncha bilan sudrab istalgan joyga qo'yish
  * Sichqoncha g'ildiragi bilan kattalashtirish / kichraytirish
  * O'ng tugma menyusi: soatni almashtirish, rang, doim tepada, o'chirish
  * Joylashuv va sozlamalar saqlanadi (~/.clock_widgets.json)

Ishga tushirish:
    python clock_widgets.py

Talablar: Python 3.8+ (faqat standart kutubxona, tkinter bilan birga keladi).
"""

import json
import math
import os
import sys
import tkinter as tk
from datetime import datetime
from tkinter import colorchooser

APP_TITLE = "Clock Widgets"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".clock_widgets.json")

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# Windows'da shu rang shaffof qilib ko'rsatiladi
TRANSPARENT_KEY = "#010101"
BG = "systemTransparent" if IS_MAC else TRANSPARENT_KEY


# --------------------------------------------------------------------------
# Yordamchi funksiyalar
# --------------------------------------------------------------------------

def shade(color, factor):
    """Rangni qoraytiradi (factor 0..1)."""
    c = color.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * factor), int(g * factor), int(b * factor))


def rounded_rect(c, x1, y1, x2, y2, r, **kw):
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return c.create_polygon(pts, smooth=True, **kw)


def hand(c, cx, cy, angle_deg, length, width, color):
    a = math.radians(angle_deg)
    c.create_line(
        cx, cy, cx + length * math.sin(a), cy - length * math.cos(a),
        fill=color, width=max(1, width), capstyle="round",
    )


# --------------------------------------------------------------------------
# Soat dizaynlari: draw(canvas, w, h, now, color)
# Shriftlar piksel (manfiy o'lcham) bilan beriladi, shuning uchun
# vidjet o'lchami o'zgarganda ham chiroyli masshtablanadi.
# --------------------------------------------------------------------------

def draw_vertical(c, w, h, now, color):
    """Rasmdagi kabi katta vertikal soat: soat tepada, daqiqa pastda."""
    font = ("Segoe UI", -int(h * 0.46), "bold")
    c.create_text(w / 2, h * 0.26, text=now.strftime("%H"), font=font, fill=color)
    c.create_text(w / 2, h * 0.74, text=now.strftime("%M"), font=font, fill=color)


def draw_horizontal(c, w, h, now, color):
    """Katta vaqt va pastida sana."""
    c.create_text(w / 2, h * 0.42, text=now.strftime("%H:%M"),
                  font=("Segoe UI", -int(h * 0.55), "bold"), fill=color)
    c.create_text(w / 2, h * 0.87, text=now.strftime("%A, %d %B").upper(),
                  font=("Segoe UI", -int(h * 0.11), "bold"), fill=shade(color, 0.7))


def draw_analog(c, w, h, now, color):
    """Klassik analog soat (color - soniya mili rangi)."""
    cx, cy = w / 2, h / 2
    r = min(w, h) / 2 - 4
    c.create_oval(cx - r, cy - r, cx + r, cy + r,
                  fill="#12161c", outline=color, width=max(2, r * 0.03))
    for i in range(60):
        a = math.radians(i * 6)
        major = i % 5 == 0
        r1 = r * (0.84 if major else 0.91)
        r2 = r * 0.96
        c.create_line(
            cx + r1 * math.sin(a), cy - r1 * math.cos(a),
            cx + r2 * math.sin(a), cy - r2 * math.cos(a),
            fill="#eeeeee" if major else "#6b7280",
            width=max(1, r * (0.025 if major else 0.01)),
        )
    sec = now.second
    minute = now.minute + sec / 60
    hour = (now.hour % 12) + minute / 60
    hand(c, cx, cy, hour * 30, r * 0.50, r * 0.07, "#f4f4f4")
    hand(c, cx, cy, minute * 6, r * 0.76, r * 0.045, "#f4f4f4")
    hand(c, cx, cy, sec * 6, r * 0.86, r * 0.018, color)
    c.create_oval(cx - r * 0.05, cy - r * 0.05, cx + r * 0.05, cy + r * 0.05,
                  fill=color, outline="")


def draw_neon(c, w, h, now, color):
    """Neon yorug'lik effektli raqamli soat."""
    text = now.strftime("%H:%M:%S")
    font = ("Consolas", -int(h * 0.46), "bold")
    cx, cy = w / 2, h / 2
    for dist, f in ((max(2, int(h * 0.035)), 0.18), (max(1, int(h * 0.018)), 0.38)):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            c.create_text(cx + dx * dist, cy + dy * dist, text=text,
                          font=font, fill=shade(color, f))
    c.create_text(cx, cy, text=text, font=font, fill=color)


def draw_minimal(c, w, h, now, color):
    """Ingichka shriftli minimal soat va soniya chizig'i."""
    c.create_text(w / 2, h * 0.42, text=now.strftime("%H:%M"),
                  font=("Segoe UI Light", -int(h * 0.62)), fill=color)
    x1, x2, y = w * 0.12, w * 0.88, h * 0.86
    lw = max(2, h * 0.025)
    c.create_line(x1, y, x2, y, fill=shade(color, 0.35), width=lw, capstyle="round")
    prog = x1 + (x2 - x1) * (now.second + 1) / 60
    c.create_line(x1, y, prog, y, fill=color, width=lw, capstyle="round")


def draw_flip(c, w, h, now, color):
    """Flip-clock (varaqli soat) uslubi."""
    gap = w * 0.04
    cw = (w - gap) / 2
    font = ("Segoe UI", -int(h * 0.62), "bold")
    for i, txt in enumerate((now.strftime("%H"), now.strftime("%M"))):
        x1 = i * (cw + gap)
        rounded_rect(c, x1, 0, x1 + cw, h, h * 0.08, fill="#1c1f26", outline="")
        c.create_text(x1 + cw / 2, h / 2, text=txt, font=font, fill=color)
        c.create_line(x1, h / 2, x1 + cw, h / 2, fill="#0a0c10", width=max(2, h * 0.02))


# key -> ma'lumot
STYLES = {
    "vertical": dict(title="Vertikal", size=(240, 380), color="#111111",
                     preview_bg="#e9e9e9", draw=draw_vertical),
    "horizontal": dict(title="Gorizontal + sana", size=(420, 170), color="#111111",
                       preview_bg="#e9e9e9", draw=draw_horizontal),
    "analog": dict(title="Analog", size=(280, 280), color="#ff4d4d",
                   preview_bg="#e9e9e9", draw=draw_analog),
    "neon": dict(title="Neon", size=(440, 170), color="#00f5ff",
                 preview_bg="#14161b", draw=draw_neon),
    "minimal": dict(title="Minimal", size=(360, 150), color="#ffffff",
                    preview_bg="#2b2f36", draw=draw_minimal),
    "flip": dict(title="Flip", size=(380, 200), color="#f5f5f5",
                 preview_bg="#9aa3ad", draw=draw_flip),
}


# --------------------------------------------------------------------------
# Ish stoli vidjeti
# --------------------------------------------------------------------------

class Widget:
    def __init__(self, app, style, x, y, scale=1.0, color=None, topmost=False):
        self.app = app
        self.style = style
        self.x, self.y = int(x), int(y)
        self.scale = scale
        self.color = color or STYLES[style]["color"]
        self.topmost = tk.BooleanVar(value=topmost)
        self.alive = True

        win = self.win = tk.Toplevel(app.root)
        win.overrideredirect(True)          # ramkasiz
        win.configure(bg=BG)
        if IS_WINDOWS:
            win.attributes("-transparentcolor", TRANSPARENT_KEY)
        elif IS_MAC:
            win.attributes("-transparent", True)
        win.attributes("-topmost", topmost)

        self.canvas = tk.Canvas(win, bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom(1.08))   # Linux
        self.canvas.bind("<Button-5>", lambda e: self._zoom(1 / 1.08))
        self.canvas.bind("<Button-3>", self._menu)
        if IS_MAC:
            self.canvas.bind("<Button-2>", self._menu)

        self._apply_geometry()
        self._tick()

    # -- o'lcham va chizish ------------------------------------------------
    @property
    def size(self):
        bw, bh = STYLES[self.style]["size"]
        return int(bw * self.scale), int(bh * self.scale)

    def _apply_geometry(self):
        w, h = self.size
        self.win.geometry(f"{w}x{h}+{self.x}+{self.y}")

    def _tick(self):
        if not self.alive:
            return
        w, h = self.size
        self.canvas.delete("all")
        STYLES[self.style]["draw"](self.canvas, w, h, datetime.now(), self.color)
        delay = 1000 - datetime.now().microsecond // 1000
        self.win.after(max(50, delay), self._tick)

    def _redraw_now(self):
        w, h = self.size
        self.canvas.delete("all")
        STYLES[self.style]["draw"](self.canvas, w, h, datetime.now(), self.color)

    # -- sichqoncha --------------------------------------------------------
    def _drag_start(self, e):
        self._dx = e.x_root - self.x
        self._dy = e.y_root - self.y

    def _drag_move(self, e):
        self.x = e.x_root - self._dx
        self.y = e.y_root - self._dy
        self.win.geometry(f"+{self.x}+{self.y}")

    def _drag_end(self, e):
        if not self.topmost.get():
            self.win.lower()                # boshqa oynalar tagida qoladi
        self.app.save()

    def _wheel(self, e):
        self._zoom(1.08 if e.delta > 0 else 1 / 1.08)

    def _zoom(self, factor):
        self.scale = max(0.4, min(4.0, self.scale * factor))
        self._apply_geometry()
        self._redraw_now()
        self.app.save()

    # -- o'ng tugma menyusi ------------------------------------------------
    def _menu(self, e):
        m = tk.Menu(self.win, tearoff=0)
        styles = tk.Menu(m, tearoff=0)
        for key, info in STYLES.items():
            styles.add_command(label=info["title"], command=lambda k=key: self.set_style(k))
        m.add_cascade(label="Soatni almashtirish", menu=styles)
        m.add_command(label="Rangni o'zgartirish...", command=self.pick_color)
        m.add_checkbutton(label="Doim tepada", variable=self.topmost,
                          command=self.toggle_topmost)
        m.add_command(label="Kattalashtirish (+)", command=lambda: self._zoom(1.15))
        m.add_command(label="Kichraytirish (-)", command=lambda: self._zoom(1 / 1.15))
        m.add_separator()
        m.add_command(label="Galereyani ochish", command=self.app.open_gallery)
        m.add_command(label="Bu vidjetni o'chirish", command=lambda: self.app.remove_widget(self))
        m.add_command(label="Dasturdan chiqish", command=self.app.quit)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def set_style(self, key):
        self.style = key
        self.color = STYLES[key]["color"]
        self._apply_geometry()
        self._redraw_now()
        self.app.save()

    def pick_color(self):
        picked = colorchooser.askcolor(color=self.color, parent=self.win,
                                       title="Soat rangi")[1]
        if picked:
            self.color = picked
            self._redraw_now()
            self.app.save()

    def toggle_topmost(self):
        self.win.attributes("-topmost", self.topmost.get())
        if not self.topmost.get():
            self.win.lower()
        self.app.save()

    def destroy(self):
        self.alive = False
        self.win.destroy()

    def to_dict(self):
        return dict(style=self.style, x=self.x, y=self.y, scale=round(self.scale, 3),
                    color=self.color, topmost=bool(self.topmost.get()))


# --------------------------------------------------------------------------
# Galereya (soat tanlash oynasi)
# --------------------------------------------------------------------------

class Gallery:
    COLUMNS = 3
    PREVIEW_BOX = (210, 130)

    def __init__(self, app):
        self.app = app
        top = self.top = tk.Toplevel(app.root)
        top.title(f"{APP_TITLE} - Soat tanlang")
        top.configure(bg="#f3f4f6")
        top.protocol("WM_DELETE_WINDOW", self.hide)

        tk.Label(top, text="Soat vidjetini tanlang", font=("Segoe UI", 15, "bold"),
                 bg="#f3f4f6").grid(row=0, column=0, columnspan=self.COLUMNS, pady=(14, 2))
        tk.Label(top, text="Tanlangach ish stolida paydo bo'ladi. Uni sudrab istalgan joyga qo'ying.",
                 font=("Segoe UI", 9), fg="#555", bg="#f3f4f6"
                 ).grid(row=1, column=0, columnspan=self.COLUMNS, pady=(0, 10))

        self.previews = []
        for i, (key, info) in enumerate(STYLES.items()):
            card = tk.Frame(top, bg="white", highlightbackground="#d1d5db", highlightthickness=1)
            card.grid(row=2 + i // self.COLUMNS, column=i % self.COLUMNS, padx=10, pady=8)

            bw, bh = info["size"]
            k = min(self.PREVIEW_BOX[0] / bw, self.PREVIEW_BOX[1] / bh)
            pw, ph = int(bw * k), int(bh * k)

            holder = tk.Frame(card, bg=info["preview_bg"],
                              width=self.PREVIEW_BOX[0] + 20, height=self.PREVIEW_BOX[1] + 20)
            holder.pack(padx=8, pady=8)
            holder.pack_propagate(False)
            cv = tk.Canvas(holder, width=pw, height=ph, bg=info["preview_bg"],
                           highlightthickness=0, bd=0)
            cv.place(relx=0.5, rely=0.5, anchor="center")
            self.previews.append((cv, key, pw, ph))

            tk.Label(card, text=info["title"], font=("Segoe UI", 10, "bold"),
                     bg="white").pack()
            tk.Button(card, text="Ish stoliga qo'yish", cursor="hand2",
                      command=lambda k=key: app.add_widget(k)).pack(pady=(4, 10), padx=10)

        bottom = tk.Frame(top, bg="#f3f4f6")
        bottom.grid(row=10, column=0, columnspan=self.COLUMNS, pady=(4, 14))
        tk.Button(bottom, text="Galereyani yashirish", command=self.hide).pack(side="left", padx=6)
        tk.Button(bottom, text="Dasturdan chiqish", command=app.quit).pack(side="left", padx=6)

        self._refresh()

    def _refresh(self):
        now = datetime.now()
        for cv, key, pw, ph in self.previews:
            cv.delete("all")
            STYLES[key]["draw"](cv, pw, ph, now, STYLES[key]["color"])
        self.top.after(1000, self._refresh)

    def show(self):
        self.top.deiconify()
        self.top.lift()

    def hide(self):
        self.top.withdraw()
        if not self.app.widgets:
            self.app.quit()

    def visible(self):
        return self.top.winfo_viewable()


# --------------------------------------------------------------------------
# Dastur
# --------------------------------------------------------------------------

class App:
    def __init__(self):
        if IS_WINDOWS:
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)   # aniq (blur'siz) ko'rinish
            except Exception:
                pass

        self.root = tk.Tk()
        self.root.withdraw()
        self.widgets = []
        self.gallery = Gallery(self)

        saved = self._load()
        for item in saved:
            if item.get("style") in STYLES:
                self.add_widget(**{k: item[k] for k in
                                   ("style", "x", "y", "scale", "color", "topmost") if k in item},
                                save=False)
        if self.widgets:
            self.gallery.top.withdraw()
        else:
            self.gallery.show()

    # -- vidjetlar ---------------------------------------------------------
    def add_widget(self, style, x=None, y=None, scale=1.0, color=None, topmost=False, save=True):
        n = len(self.widgets)
        if x is None:
            x = 120 + 40 * n
        if y is None:
            y = 120 + 40 * n
        self.widgets.append(Widget(self, style, x, y, scale, color, topmost))
        if save:
            self.save()

    def remove_widget(self, widget):
        widget.destroy()
        self.widgets.remove(widget)
        self.save()
        if not self.widgets:
            self.open_gallery()

    def open_gallery(self):
        self.gallery.show()

    # -- saqlash -----------------------------------------------------------
    def save(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump([w.to_dict() for w in self.widgets], f, indent=2)
        except OSError:
            pass

    @staticmethod
    def _load():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    # -- boshqaruv ---------------------------------------------------------
    def quit(self):
        self.save()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
