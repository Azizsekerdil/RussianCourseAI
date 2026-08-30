# -*- coding: utf-8 -*-
"""Arayuz altyapisi: tema, kenar cubugu, yuvarlak kartlar, grafikler, thread kuyrugu."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Sequence

import rca_common as C


# ==========================================================================
# TEMA
# ==========================================================================
def apply_theme(root: tk.Misc, style: ttk.Style, name: str) -> Dict[str, str]:
    """Secili paleti ttk stiline uygula ve palet sozlugunu dondur."""
    p = C.THEME.get(name, C.THEME["dark"])
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # -- temel ------------------------------------------------------------
    style.configure(".", background=p["bg"], foreground=p["fg"], font=C.FONT_UI,
                    fieldbackground=p["bg_alt"], bordercolor=p["border"],
                    lightcolor=p["border"], darkcolor=p["border"], focuscolor=p["accent"])

    # -- cerceveler -------------------------------------------------------
    for sname, bg in (("TFrame", p["bg"]), ("Deep.TFrame", p["deep"]),
                      ("Panel.TFrame", p["panel"]), ("Card.TFrame", p["bg_alt"]),
                      ("Hover.TFrame", p["hover"]), ("Accent.TFrame", p["accent_soft"])):
        style.configure(sname, background=bg, relief="flat", borderwidth=0)

    # -- etiketler --------------------------------------------------------
    label_specs = {
        "TLabel": (p["bg"], p["fg"], C.FONT_UI),
        "Dim.TLabel": (p["bg"], p["fg_dim"], C.FONT_UI),
        "Mute.TLabel": (p["bg"], p["fg_mute"], C.FONT_UI_SM),
        "Title.TLabel": (p["bg"], p["fg"], C.FONT_TITLE),
        "Page.TLabel": (p["bg"], p["fg"], C.FONT_PAGE),
        "RU.TLabel": (p["bg"], p["fg"], C.FONT_RU),
        "OK.TLabel": (p["bg"], p["ok"], C.FONT_UI),
        "Err.TLabel": (p["bg"], p["err"], C.FONT_UI),
        "Warn.TLabel": (p["bg"], p["warn"], C.FONT_UI),
        "Deep.TLabel": (p["deep"], p["fg"], C.FONT_UI),
        "DeepDim.TLabel": (p["deep"], p["fg_mute"], C.FONT_UI_SM),
        "Panel.TLabel": (p["panel"], p["fg"], C.FONT_UI),
        "PanelDim.TLabel": (p["panel"], p["fg_dim"], C.FONT_UI),
        "Card.TLabel": (p["bg_alt"], p["fg"], C.FONT_UI),
        "CardDim.TLabel": (p["bg_alt"], p["fg_dim"], C.FONT_UI),
        "CardTitle.TLabel": (p["bg_alt"], p["fg"], C.FONT_TITLE),
        "CardNum.TLabel": (p["bg_alt"], p["fg"], C.FONT_NUM),
        "RUBig.TLabel": (p["bg_alt"], p["fg"], C.FONT_RU_BIG),
    }
    for sname, (bg, fg, font) in label_specs.items():
        style.configure(sname, background=bg, foreground=fg, font=font)

    # -- dugmeler ---------------------------------------------------------
    style.configure("TButton", background=p["panel"], foreground=p["fg"],
                    borderwidth=0, focusthickness=0, padding=(12, 7),
                    font=C.FONT_UI, relief="flat")
    style.map("TButton",
              background=[("pressed", p["sel"]), ("active", p["hover"]),
                          ("disabled", p["bg_alt"])],
              foreground=[("disabled", p["fg_mute"])])

    button_variants = {
        "Accent.TButton": (p["accent"], p["accent_fg"], p["sel"]),
        "OK.TButton": (p["ok"], "#08130d", p["ok_soft"]),
        "Warn.TButton": (p["warn"], "#1c1305", p["warn_soft"]),
        "Err.TButton": (p["err"], "#1c0808", p["err_soft"]),
    }
    for sname, (bg, fg, active) in button_variants.items():
        style.configure(sname, background=bg, foreground=fg, borderwidth=0,
                        focusthickness=0, padding=(12, 7), font=C.FONT_UI_BOLD,
                        relief="flat")
        style.map(sname, background=[("active", active), ("pressed", active),
                                     ("disabled", p["bg_alt"])],
                  foreground=[("disabled", p["fg_mute"])])

    style.configure("Ghost.TButton", background=p["bg_alt"], foreground=p["fg_dim"],
                    borderwidth=0, padding=(10, 6), relief="flat")
    style.map("Ghost.TButton", background=[("active", p["hover"])],
              foreground=[("active", p["fg"])])
    style.configure("Card.TButton", background=p["bg_alt"], foreground=p["fg"],
                    borderwidth=0, padding=(12, 7), relief="flat")
    style.map("Card.TButton", background=[("active", p["hover"])])
    style.configure("Panel.TButton", background=p["panel"], foreground=p["fg"],
                    borderwidth=0, padding=(10, 6), relief="flat")
    style.map("Panel.TButton", background=[("active", p["hover"])])
    style.configure("Deep.TButton", background=p["deep"], foreground=p["fg_dim"],
                    borderwidth=0, padding=(10, 6), relief="flat")
    style.map("Deep.TButton", background=[("active", p["hover"])],
              foreground=[("active", p["fg"])])

    # -- ic sekmeler (segment gorunumu) ------------------------------------
    style.configure("TNotebook", background=p["bg"], borderwidth=0,
                    tabmargins=(0, 6, 0, 10))
    style.configure("TNotebook.Tab", background=p["bg"], foreground=p["fg_dim"],
                    padding=(16, 8), borderwidth=0, font=C.FONT_UI)
    style.map("TNotebook.Tab",
              background=[("selected", p["accent_soft"]), ("active", p["hover"])],
              foreground=[("selected", p["accent"]), ("active", p["fg"])])

    # -- girdi ------------------------------------------------------------
    style.configure("TEntry", fieldbackground=p["bg_alt"], foreground=p["fg"],
                    insertcolor=p["accent"], borderwidth=1, relief="flat",
                    padding=6, bordercolor=p["border"])
    style.map("TEntry", bordercolor=[("focus", p["accent"])])
    style.configure("TCombobox", fieldbackground=p["bg_alt"], foreground=p["fg"],
                    background=p["panel"], arrowcolor=p["fg_dim"], borderwidth=1,
                    padding=5, relief="flat", bordercolor=p["border"])
    style.map("TCombobox", fieldbackground=[("readonly", p["bg_alt"])],
              bordercolor=[("focus", p["accent"])],
              arrowcolor=[("active", p["accent"])])
    style.configure("TSpinbox", fieldbackground=p["bg_alt"], foreground=p["fg"],
                    background=p["panel"], arrowcolor=p["fg_dim"], borderwidth=1,
                    padding=4, relief="flat")

    # -- tablolar ---------------------------------------------------------
    style.configure("Treeview", background=p["bg_alt"], fieldbackground=p["bg_alt"],
                    foreground=p["fg"], borderwidth=0, rowheight=30, relief="flat")
    style.configure("Treeview.Heading", background=p["panel"], foreground=p["fg_dim"],
                    borderwidth=0, relief="flat", padding=(8, 7), font=C.FONT_UI_SM)
    style.map("Treeview.Heading", background=[("active", p["hover"])])
    style.map("Treeview", background=[("selected", p["accent_soft"])],
              foreground=[("selected", p["fg"])])

    # -- diger ------------------------------------------------------------
    for sname, bg in (("TCheckbutton", p["bg"]), ("Card.TCheckbutton", p["bg_alt"]),
                      ("Panel.TCheckbutton", p["panel"])):
        style.configure(sname, background=bg, foreground=p["fg"], focuscolor=p["bg"])
        style.map(sname, background=[("active", bg)],
                  indicatorcolor=[("selected", p["accent"])])
    style.configure("TRadiobutton", background=p["bg"], foreground=p["fg"],
                    focuscolor=p["bg"])
    style.map("TRadiobutton", background=[("active", p["bg"])],
              indicatorcolor=[("selected", p["accent"])])
    style.configure("Card.TRadiobutton", background=p["bg_alt"], foreground=p["fg"],
                    focuscolor=p["bg_alt"])
    style.map("Card.TRadiobutton", background=[("active", p["bg_alt"])])

    style.configure("TLabelframe", background=p["bg"], foreground=p["fg"],
                    bordercolor=p["border"], borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=p["bg"], foreground=p["accent"],
                    font=C.FONT_UI_BOLD)
    style.configure("TScale", background=p["bg"], troughcolor=p["panel"],
                    bordercolor=p["border"])
    style.configure("Horizontal.TProgressbar", background=p["accent"],
                    troughcolor=p["panel"], borderwidth=0, thickness=6)
    style.configure("Thin.Horizontal.TProgressbar", background=p["accent"],
                    troughcolor=p["panel"], borderwidth=0, thickness=4)
    style.configure("TPanedwindow", background=p["bg"])
    style.configure("TSeparator", background=p["border"])
    style.configure("Vertical.TScrollbar", background=p["panel"],
                    troughcolor=p["bg"], bordercolor=p["bg"], arrowcolor=p["fg_mute"],
                    borderwidth=0, relief="flat")
    style.map("Vertical.TScrollbar", background=[("active", p["hover"])])
    style.configure("Horizontal.TScrollbar", background=p["panel"],
                    troughcolor=p["bg"], bordercolor=p["bg"], arrowcolor=p["fg_mute"],
                    borderwidth=0, relief="flat")

    try:
        root.configure(background=p["bg"])
    except tk.TclError:
        pass
    return p


def style_text(widget: tk.Text, p: Dict[str, str], mono: bool = False) -> None:
    """Duz tk.Text parcalarini palete uydur (ttk stili gecmez)."""
    widget.configure(background=p["bg_alt"], foreground=p["fg"],
                     insertbackground=p["accent"], selectbackground=p["sel"],
                     selectforeground=p["fg"], highlightthickness=1,
                     highlightbackground=p["border"], highlightcolor=p["accent"],
                     borderwidth=0, relief="flat", padx=10, pady=8,
                     font=C.FONT_MONO if mono else C.FONT_RU)


# ==========================================================================
# YUVARLAK KOSELI CIZIM
# ==========================================================================
def round_rect(canvas: tk.Canvas, x0: float, y0: float, x1: float, y1: float,
               r: int = C.RADIUS, **kw) -> int:
    """Tuvale yuvarlak koseli dikdortgen ciz ve oge kimligini dondur."""
    r = max(0, min(r, int(abs(x1 - x0) / 2), int(abs(y1 - y0) / 2)))
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
           x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return canvas.create_polygon(pts, smooth=True, splinesteps=24, **kw)


class Card(tk.Frame):
    """Yuvarlak koseli kart. Icerik `self.body` icine konur.

    Tkinter'da gercek yuvarlak cerceve yoktur; arka plan bir Canvas'a cizilir
    ve icerik onun uzerine yerlestirilir.
    """

    def __init__(self, master, p: Dict[str, str], padding: int = 16,
                 fill: str = None, outline: str = None, radius: int = C.RADIUS,
                 **kw) -> None:
        bg = kw.pop("background", None) or _parent_bg(master, p)
        super().__init__(master, background=bg, highlightthickness=0, bd=0, **kw)
        self.p = p
        self._fill = fill or p["bg_alt"]
        self._outline = outline or p["border"]
        self._radius = radius
        self.canvas = tk.Canvas(self, background=bg, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, background=self._fill, bd=0, highlightthickness=0)
        self.body.place(x=padding, y=padding,
                        width=-2 * padding, height=-2 * padding,
                        relwidth=1, relheight=1)
        self._shape = None
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _evt=None) -> None:
        """Kart arka planini yeniden ciz."""
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        self.canvas.delete("bgshape")
        round_rect(self.canvas, 1, 1, w - 1, h - 1, self._radius,
                   fill=self._fill, outline=self._outline, width=1, tags="bgshape")
        self.canvas.tag_lower("bgshape")


def _parent_bg(widget, p: Dict[str, str]) -> str:
    """Ust parcanin arka plan rengini bul (bulunamazsa tema bg)."""
    try:
        return widget.cget("background") or p["bg"]
    except Exception:
        try:
            style = ttk.Style()
            return style.lookup(widget.winfo_class(), "background") or p["bg"]
        except Exception:
            return p["bg"]


# ==========================================================================
# KENAR CUBUGU
# ==========================================================================
class Sidebar(tk.Frame):
    """Gruplu dikey gezinme cubugu.

    Ogeler `add_group()` ve `add_item()` ile eklenir; secim `on_select(key)`
    geri cagrimiyla bildirilir.
    """

    def __init__(self, master, p: Dict[str, str], on_select: Callable[[str], None],
                 width: int = 216) -> None:
        super().__init__(master, background=p["deep"], width=width)
        self.pack_propagate(False)
        self.p = p
        self.on_select = on_select
        self.items: Dict[str, Dict[str, Any]] = {}
        self.groups: Dict[str, tk.Label] = {}
        self.active: Optional[str] = None
        self._body = tk.Frame(self, background=p["deep"])
        self._body.pack(fill="both", expand=True, padx=0, pady=(4, 0))

    # -- kurulum ----------------------------------------------------------
    def add_brand(self, title: str, subtitle: str) -> None:
        """Ust kisma uygulama adini koy."""
        p = self.p
        box = tk.Frame(self._body, background=p["deep"])
        box.pack(fill="x", padx=16, pady=(14, 12))
        row = tk.Frame(box, background=p["deep"])
        row.pack(fill="x")
        mark = tk.Canvas(row, width=30, height=30, background=p["deep"],
                         highlightthickness=0)
        mark.pack(side="left")
        round_rect(mark, 1, 1, 29, 29, 8, fill=p["accent"], outline="")
        mark.create_text(15, 16, text="Я", fill=p["accent_fg"],
                         font=(C.FONT_FAMILY, 15, "bold"))
        text = tk.Frame(row, background=p["deep"])
        text.pack(side="left", padx=(10, 0))
        tk.Label(text, text=title, background=p["deep"], foreground=p["fg"],
                 font=(C.FONT_FAMILY, 11, "bold")).pack(anchor="w")
        tk.Label(text, text=subtitle, background=p["deep"], foreground=p["fg_mute"],
                 font=C.FONT_UI_SM).pack(anchor="w")

    def add_group(self, title: str, key: str = None) -> None:
        """Bolum basligi ekle."""
        label = tk.Label(self._body, text=title.upper(), background=self.p["deep"],
                         foreground=self.p["fg_mute"],
                         font=(C.FONT_FAMILY, 8, "bold"), anchor="w")
        label.pack(fill="x", padx=18, pady=(14, 4))
        if key:
            self.groups[key] = label

    def add_item(self, key: str, icon: str, label: str) -> None:
        """Gezinme ogesi ekle."""
        p = self.p
        row = tk.Frame(self._body, background=p["deep"], cursor="hand2")
        row.pack(fill="x", padx=8, pady=1)
        bar = tk.Frame(row, background=p["deep"], width=3)
        bar.pack(side="left", fill="y")
        icon_lbl = tk.Label(row, text=icon, background=p["deep"], foreground=p["fg_dim"],
                            font=(C.FONT_FAMILY, 12), width=3)
        icon_lbl.pack(side="left", pady=7)
        text_lbl = tk.Label(row, text=label, background=p["deep"], foreground=p["fg_dim"],
                            font=C.FONT_UI, anchor="w")
        text_lbl.pack(side="left", fill="x", expand=True, pady=7)
        badge = tk.Label(row, text="", background=p["deep"], foreground=p["accent"],
                         font=(C.FONT_FAMILY, 8, "bold"))
        badge.pack(side="right", padx=(0, 10))

        parts = (row, icon_lbl, text_lbl, badge)
        self.items[key] = {"row": row, "bar": bar, "icon": icon_lbl,
                           "text": text_lbl, "badge": badge, "label": label}
        for widget in parts:
            widget.bind("<Button-1>", lambda _e, k=key: self.select(k))
            widget.bind("<Enter>", lambda _e, k=key: self._hover(k, True))
            widget.bind("<Leave>", lambda _e, k=key: self._hover(k, False))

    def add_spacer(self) -> None:
        """Kalan bosluğu doldurur (alt ogeleri asagi iter)."""
        tk.Frame(self._body, background=self.p["deep"]).pack(fill="both", expand=True)

    # -- durum ------------------------------------------------------------
    def set_label(self, key: str, label: str) -> None:
        """Oge metnini degistir (dil degisiminde)."""
        item = self.items.get(key)
        if item:
            item["text"].configure(text=label)
            item["label"] = label

    def set_group_label(self, key: str, label: str) -> None:
        """Bolum basligini dil degisiminde guncelle."""
        widget = self.groups.get(key)
        if widget:
            widget.configure(text=label.upper())

    def set_badge(self, key: str, text: str) -> None:
        """Ogeye sayi rozeti koy (orn. bekleyen tekrar sayisi)."""
        item = self.items.get(key)
        if item:
            item["badge"].configure(text=text)

    def select(self, key: str) -> None:
        """Ogeyi sec ve geri cagrimi tetikle."""
        if key not in self.items or key == self.active:
            if key in self.items and key == self.active:
                return
            return
        previous, self.active = self.active, key
        if previous:
            self._paint(previous, False)
        self._paint(key, True)
        self.on_select(key)

    def _paint(self, key: str, active: bool) -> None:
        """Ogeyi etkin/etkisiz gorunume boya."""
        p = self.p
        item = self.items[key]
        bg = p["accent_soft"] if active else p["deep"]
        fg = p["accent"] if active else p["fg_dim"]
        item["row"].configure(background=bg)
        item["bar"].configure(background=p["accent"] if active else bg)
        item["icon"].configure(background=bg, foreground=fg)
        item["text"].configure(background=bg, foreground=p["fg"] if active else fg,
                               font=C.FONT_UI_BOLD if active else C.FONT_UI)
        item["badge"].configure(background=bg)

    def _hover(self, key: str, on: bool) -> None:
        """Fare uzerindeyken hafif vurgu."""
        if key == self.active:
            return
        p = self.p
        item = self.items[key]
        bg = p["hover"] if on else p["deep"]
        item["row"].configure(background=bg)
        item["bar"].configure(background=bg)
        item["icon"].configure(background=bg,
                               foreground=p["fg"] if on else p["fg_dim"])
        item["text"].configure(background=bg,
                               foreground=p["fg"] if on else p["fg_dim"])
        item["badge"].configure(background=bg)


class Pill(tk.Canvas):
    """Kucuk yuvarlak durum etiketi (orn. 'AI: cevrimici')."""

    def __init__(self, master, p: Dict[str, str], text: str = "", tone: str = "fg_dim",
                 width: int = 150, height: int = 26, bg: str = None) -> None:
        self.p = p
        self._bg = bg or p["panel"]
        super().__init__(master, width=width, height=height, background=self._bg,
                         highlightthickness=0, bd=0)
        self._tone = tone
        self._text = text
        self.bind("<Configure>", lambda _e: self.redraw())
        self.redraw()

    def set(self, text: str, tone: str = None) -> None:
        """Metni ve rengi guncelle."""
        self._text = text
        if tone:
            self._tone = tone
        self.redraw()

    def redraw(self) -> None:
        """Yeniden ciz."""
        p = self.p
        self.delete("all")
        w = max(self.winfo_width(), 40)
        h = max(self.winfo_height(), 20)
        color = p.get(self._tone, p["fg_dim"])
        soft = p.get(self._tone + "_soft", p["bg_alt"])
        round_rect(self, 1, 1, w - 1, h - 1, int(h / 2), fill=soft, outline="")
        self.create_oval(11, h / 2 - 3, 17, h / 2 + 3, fill=color, outline="")
        self.create_text(24, h / 2, text=self._text, anchor="w", fill=color,
                         font=C.FONT_UI_SM)


# ==========================================================================
# KAYDIRILABILIR CERCEVE
# ==========================================================================
class ScrollFrame(ttk.Frame):
    """Dikey kaydirilabilir cerceve. Icerik `self.body` icine konur."""

    def __init__(self, master, **kw) -> None:
        super().__init__(master, **kw)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.vs = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<Enter>", lambda e: self._bind_wheel(True))
        self.canvas.bind("<Leave>", lambda e: self._bind_wheel(False))
        self._bar_shown = False

    def paint(self, p: Dict[str, str]) -> None:
        """Tuval arka planini palete uydur."""
        self.canvas.configure(background=p["bg"])

    def _on_scroll(self, first, last) -> None:
        """Kaydirma cubugunu yalnizca gerektiginde goster."""
        need = not (float(first) <= 0.0 and float(last) >= 1.0)
        if need and not self._bar_shown:
            self.vs.pack(side="right", fill="y")
            self._bar_shown = True
        elif not need and self._bar_shown:
            self.vs.pack_forget()
            self._bar_shown = False
        self.vs.set(first, last)

    def _on_body(self, _evt) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, evt) -> None:
        self.canvas.itemconfigure(self._win, width=evt.width)

    def _bind_wheel(self, on: bool) -> None:
        if on:
            self.canvas.bind_all("<MouseWheel>", self._wheel)
        else:
            self.canvas.unbind_all("<MouseWheel>")

    def _wheel(self, evt) -> None:
        if self._bar_shown:
            self.canvas.yview_scroll(int(-evt.delta / 120), "units")


# ==========================================================================
# THREAD KUYRUGU
# ==========================================================================
class Worker:
    """Uzun islemleri arayuzu kilitlemeden calistirir."""

    def __init__(self, root: tk.Misc, poll_ms: int = 60) -> None:
        self.root = root
        self.q: "queue.Queue" = queue.Queue()
        self.poll_ms = poll_ms
        self._tick()

    def run(self, fn: Callable[[], Any], on_done: Callable[[Any], None] = None,
            on_error: Callable[[Exception], None] = None) -> None:
        """fn'i arka planda calistir; sonucu ana threadde geri ver."""
        def target() -> None:
            try:
                self.q.put(("ok", fn(), on_done))
            except Exception as e:                     # noqa: BLE001
                self.q.put(("err", e, on_error))
        threading.Thread(target=target, daemon=True).start()

    def post(self, fn: Callable[[], None]) -> None:
        """Arka plandan ana threade is gonder (ilerleme guncellemeleri icin)."""
        self.q.put(("ok", None, lambda _v: fn()))

    def _tick(self) -> None:
        try:
            while True:
                _kind, payload, cb = self.q.get_nowait()
                if cb is None:
                    continue
                try:
                    cb(payload)
                except Exception:
                    pass
        except queue.Empty:
            pass
        try:
            self.root.after(self.poll_ms, self._tick)
        except tk.TclError:
            pass                                        # pencere kapandi


# ==========================================================================
# SAYFA TABANI
# ==========================================================================
class LazyTab(ttk.Frame):
    """Icerigi ilk gorundugunde kurulan sayfa tabani."""

    title_key = ""

    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        self._built = False

    def ensure_built(self) -> None:
        """Sayfa ilk kez gorununce icerigi kur."""
        if self._built:
            return
        self._built = True
        try:
            self.build()
        except Exception as e:                          # noqa: BLE001
            for child in self.winfo_children():
                child.destroy()
            ttk.Label(self, text=f"Bu bolum yuklenemedi:\n{e}",
                      style="Err.TLabel", justify="left").pack(padx=20, pady=20, anchor="w")

    def build(self) -> None:
        """Alt sinif icerigi burada kurar."""
        raise NotImplementedError

    def on_show(self) -> None:
        """Sayfaya her geri donuste cagrilir (varsayilan: bir sey yapma)."""

    def is_current(self) -> bool:
        """Bu sayfa su anda goruntuleniyor mu?"""
        return self.app.current_page() is self

    # -- kisayollar --------------------------------------------------------
    @property
    def repos(self):
        """Repository kabina kisayol."""
        return self.app.repos

    @property
    def pid(self) -> int:
        """Aktif profil id'si."""
        return self.app.profile_id

    def t(self, key: str) -> str:
        """Secili arayuz diline gore metin."""
        return self.app.t(key)

    def u(self, text: str) -> str:
        """Eski, dogrudan yazilmis bir arayuz metnini cevir."""
        return self.app.u(text)

    def on_language_change(self) -> None:
        """Dil degisince ozel secenek listelerini yenilemek icin kanca."""

    def palette(self) -> Dict[str, str]:
        """Aktif renk paleti."""
        return self.app.palette


# ==========================================================================
# HAZIR PARCALAR
# ==========================================================================
def page_header(master, title: str, subtitle: str = "") -> ttk.Frame:
    """Sayfa basligi + aciklama satiri dondur (icine dugme eklenebilir)."""
    head = ttk.Frame(master)
    left = ttk.Frame(head)
    left.pack(side="left", fill="x", expand=True)
    ttk.Label(left, text=title, style="Page.TLabel").pack(anchor="w")
    if subtitle:
        ttk.Label(left, text=subtitle, style="Dim.TLabel").pack(anchor="w", pady=(2, 0))
    return head


def card(master, title: str, value: str, p: Dict[str, str],
         tone: str = None, hint: str = "") -> Card:
    """Yuvarlak koseli istatistik karti."""
    c = Card(master, p, padding=14)
    tk.Label(c.body, text=title, background=p["bg_alt"], foreground=p["fg_dim"],
             font=C.FONT_UI_SM, anchor="w").pack(anchor="w")
    tk.Label(c.body, text=value, background=p["bg_alt"],
             foreground=p.get(tone, p["fg"]) if tone else p["fg"],
             font=C.FONT_NUM, anchor="w").pack(anchor="w", pady=(2, 0))
    if hint:
        tk.Label(c.body, text=hint, background=p["bg_alt"], foreground=p["fg_mute"],
                 font=C.FONT_UI_SM, anchor="w").pack(anchor="w")
    c.configure(height=96)
    return c


def empty_state(master, p: Dict[str, str], icon: str, title: str,
                detail: str = "") -> ttk.Frame:
    """Veri yokken gosterilen sakin bilgi bloku."""
    box = ttk.Frame(master)
    ttk.Label(box, text=icon, style="Dim.TLabel",
              font=(C.FONT_FAMILY, 30)).pack(pady=(30, 6))
    ttk.Label(box, text=title, style="Title.TLabel").pack()
    if detail:
        ttk.Label(box, text=detail, style="Dim.TLabel", justify="center",
                  wraplength=520).pack(pady=(6, 30))
    return box


def bar_chart(canvas: tk.Canvas, data: List[Dict[str, Any]], p: Dict[str, str],
              key: str = "correct", label_every: int = 5) -> None:
    """Cubuk grafik ciz. Veri yoksa 'veri yok' yazar (bos grafik cizmez)."""
    canvas.delete("all")
    w = max(canvas.winfo_width(), 200)
    h = max(canvas.winfo_height(), 120)
    canvas.configure(background=p["bg_alt"])
    values = [int(d.get(key, 0)) for d in data]
    if not values or max(values) == 0:
        canvas.create_text(w // 2, h // 2, text="Bu donemde veri yok",
                           fill=p["fg_mute"], font=C.FONT_UI)
        return
    pad = 26
    top = max(values)
    n = len(values)
    bw = max(3.0, (w - 2 * pad) / n * 0.66)
    step = (w - 2 * pad) / n
    base = h - pad
    for frac in (0.5, 1.0):
        y = base - (base - pad) * frac
        canvas.create_line(pad, y, w - pad, y, fill=p["border"], dash=(2, 5))
    canvas.create_line(pad - 4, base, w - pad + 4, base, fill=p["border_hi"])
    for i, v in enumerate(values):
        x = pad + i * step + (step - bw) / 2
        bh = max(2, (base - pad) * (v / top))
        round_rect(canvas, x, base - bh, x + bw, base, min(4, int(bw / 2)),
                   fill=p["accent"], outline="")
        if i % label_every == 0 or i == n - 1:
            canvas.create_text(x + bw / 2, base + 11, text=data[i]["day"][5:],
                               fill=p["fg_mute"], font=(C.FONT_FAMILY, 7))
    canvas.create_text(pad, pad - 12, text=f"en yuksek {top}", fill=p["fg_mute"],
                       anchor="w", font=(C.FONT_FAMILY, 8))


def line_chart(canvas: tk.Canvas, points: Sequence[float], p: Dict[str, str],
               labels: List[str] = None) -> None:
    """Cizgi grafik (sinav puan trendi). Veri yoksa uyari yazar."""
    canvas.delete("all")
    w = max(canvas.winfo_width(), 200)
    h = max(canvas.winfo_height(), 120)
    canvas.configure(background=p["bg_alt"])
    if len(points) < 2:
        canvas.create_text(w // 2, h // 2, text="Trend icin en az 2 sinav gerekir",
                           fill=p["fg_mute"], font=C.FONT_UI)
        return
    pad = 28
    n = len(points)
    step = (w - 2 * pad) / (n - 1)
    coords = []
    for i, v in enumerate(points):
        x = pad + i * step
        y = h - pad - (h - 2 * pad) * (max(0.0, min(100.0, v)) / 100.0)
        coords += [x, y]
    for frac in (0.0, 0.5, 1.0):
        y = h - pad - (h - 2 * pad) * frac
        canvas.create_line(pad, y, w - pad, y, fill=p["border"], dash=(2, 5))
        canvas.create_text(pad - 6, y, text=str(int(frac * 100)), anchor="e",
                           fill=p["fg_mute"], font=(C.FONT_FAMILY, 7))
    area = list(coords) + [coords[-2], h - pad, coords[0], h - pad]
    canvas.create_polygon(area, fill=p["accent_soft"], outline="")
    canvas.create_line(*coords, fill=p["accent"], width=2, smooth=True)
    for i in range(0, len(coords), 2):
        canvas.create_oval(coords[i] - 3.5, coords[i + 1] - 3.5,
                           coords[i] + 3.5, coords[i + 1] + 3.5,
                           fill=p["bg_alt"], outline=p["accent"], width=2)


def hsep(master) -> ttk.Separator:
    """Yatay ayirici."""
    s = ttk.Separator(master, orient="horizontal")
    s.pack(fill="x", pady=10)
    return s
