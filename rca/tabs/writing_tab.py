# -*- coding: utf-8 -*-
"""El Yazisi Tahtasi: Kiril el yazisi calis, PNG kaydet, AI'a 'ne yazdim?' diye sor."""
from __future__ import annotations

import base64
import io
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca import content as K
from rca.ui_util import LazyTab, style_text


class WritingTab(LazyTab):
    """Tablet/fare ile serbest yazi tahtasi."""

    def build(self) -> None:
        p = self.palette()
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        bar = ttk.Frame(root)
        bar.pack(fill="x")
        ttk.Label(bar, text="Kalem:").pack(side="left")
        self.width = tk.IntVar(value=4)
        ttk.Scale(bar, from_=1, to=16, variable=self.width, length=120,
                  orient="horizontal").pack(side="left", padx=6)
        ttk.Label(bar, text="Renk:").pack(side="left", padx=(12, 4))
        self.color = tk.StringVar(value="fg")
        ttk.Combobox(bar, textvariable=self.color, state="readonly", width=10,
                     values=["fg", "accent", "err", "ok"]).pack(side="left")
        ttk.Label(bar, text="Kilavuz:").pack(side="left", padx=(12, 4))
        self.guide_var = tk.StringVar(value="")
        gb = ttk.Combobox(bar, textvariable=self.guide_var, state="readonly", width=10,
                          values=[""] + [a[0] for a in K.ALPHABET])
        gb.pack(side="left")
        gb.bind("<<ComboboxSelected>>", lambda _e: self.redraw_guides())

        ttk.Button(bar, text="Temizle", command=self.clear).pack(side="right")
        ttk.Button(bar, text="Geri al", command=self.undo).pack(side="right", padx=6)
        ttk.Button(bar, text="PNG kaydet", command=self.save_png).pack(side="right")
        ttk.Button(bar, text="🤖 Ne yazdim?", style="Accent.TButton",
                   command=self.ask_ai).pack(side="right", padx=6)

        self.canvas = tk.Canvas(root, background="#ffffff", highlightthickness=1,
                                highlightbackground=p["border"], height=420)
        self.canvas.pack(fill="both", expand=True, pady=10)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._draw)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Configure>", lambda _e: self.redraw_guides())

        ttk.Label(root, text="AI yaniti", style="TLabel",
                  font=C.FONT_UI_BOLD).pack(anchor="w")
        self.out = tk.Text(root, height=8, wrap="word")
        style_text(self.out, p)
        self.out.pack(fill="x")
        self.out.configure(state="disabled")

        self._last = None
        self._stroke = []
        self.strokes = []
        self.redraw_guides()

    # ------------------------------------------------------------------
    def _pen_color(self) -> str:
        """Secili kalem rengi (tuval beyaz oldugu icin koyu tonlar)."""
        table = {"fg": "#1a1a1a", "accent": "#2f6fe0", "err": "#c0332f", "ok": "#2f8f52"}
        return table.get(self.color.get(), "#1a1a1a")

    def redraw_guides(self) -> None:
        """Satir cizgilerini ve secili kilavuz harfi yeniden ciz."""
        self.canvas.delete("guide")
        h = self.canvas.winfo_height() or 420
        w = self.canvas.winfo_width() or 800
        rows = 3
        band = h / rows
        for r in range(rows):
            top = r * band
            for frac, dash in ((0.25, (2, 6)), (0.5, (4, 4)), (0.75, (2, 6))):
                y = top + band * frac
                self.canvas.create_line(10, y, w - 10, y, fill="#d8dbe2",
                                        dash=dash, tags="guide")
            self.canvas.create_line(10, top + band * 0.9, w - 10, top + band * 0.9,
                                    fill="#b9bec9", tags="guide")
        letter = self.guide_var.get()
        if letter:
            self.canvas.create_text(70, band * 0.55, text=letter[1],
                                    font=("Segoe Script", int(band * 0.5), "italic"),
                                    fill="#e3e6ec", tags="guide")
        self.canvas.tag_lower("guide")

    def _press(self, evt) -> None:
        self._last = (evt.x, evt.y)
        self._stroke = []

    def _draw(self, evt) -> None:
        """Serbest cizim."""
        if self._last is None:
            self._last = (evt.x, evt.y)
            return
        item = self.canvas.create_line(self._last[0], self._last[1], evt.x, evt.y,
                                       fill=self._pen_color(), width=int(self.width.get()),
                                       capstyle="round", smooth=True, tags="ink")
        self._stroke.append(item)
        self._last = (evt.x, evt.y)

    def _release(self, _evt) -> None:
        if self._stroke:
            self.strokes.append(self._stroke)
        self._stroke = []
        self._last = None

    def undo(self) -> None:
        """Son kalem darbesini geri al."""
        if not self.strokes:
            return
        for item in self.strokes.pop():
            self.canvas.delete(item)

    def clear(self) -> None:
        """Tuvali temizle."""
        self.canvas.delete("ink")
        self.strokes = []
        self._write("")

    # ------------------------------------------------------------------
    def _render_png(self):
        """Tuvali PNG baytlarina cevir (Pillow gerekir)."""
        try:
            from PIL import Image, ImageDraw       # type: ignore
        except Exception:
            return None
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 420
        img = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(img)
        for item in self.canvas.find_withtag("ink"):
            coords = self.canvas.coords(item)
            if len(coords) >= 4:
                color = self.canvas.itemcget(item, "fill") or "#000000"
                width = int(float(self.canvas.itemcget(item, "width") or 3))
                d.line(coords, fill=color, width=width, joint="curve")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def save_png(self) -> None:
        """Yaziyi PNG olarak kaydet."""
        data = self._render_png()
        if data is None:
            messagebox.showinfo(C.APP_NAME,
                                "PNG kaydetmek icin Pillow gerekli:\n\npip install pillow")
            return
        default = f"elyazisi_{datetime.now():%Y%m%d_%H%M%S}.png"
        path = filedialog.asksaveasfilename(
            title="PNG kaydet", defaultextension=".png",
            initialdir=str(C.EXPORT_DIR), initialfile=default,
            filetypes=[("PNG", "*.png")])
        if not path:
            return
        try:
            with open(path, "wb") as f:
                f.write(data)
            self.app.set_status(f"Kaydedildi: {path}")
        except Exception as e:                          # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Yazilamadi:\n{e}")

    def ask_ai(self) -> None:
        """Yazilani vision modeline okut."""
        data = self._render_png()
        if data is None:
            self._write("Bu ozellik icin Pillow gerekli:  pip install pillow")
            return
        if not self.canvas.find_withtag("ink"):
            self._write("Once tahtaya bir seyler yazin.")
            return
        self._write(self.t("ai.thinking"))
        b64 = base64.b64encode(data).decode("ascii")

        def job():
            return self.app.ai.describe_image(
                b64,
                "Bu goruntude Kiril el yazisiyla yazilmis metin var. "
                "Once ne yazdigini oku, sonra harflerin duzgun yazilip yazilmadigini "
                "kisaca degerlendir.",
                self.app.ui_lang())

        def fail(err: Exception):
            if "vision-model-yok" in str(err):
                self._write("Gorsel destekli model bulunamadi.\n"
                            "LM Studio'ya bir vision modeli yukleyin "
                            "(orn. qwen2-vl-7b-instruct).")
            else:
                self._write(f"{self.t('ai.offline')}\n\n{err}")
        self.app.worker.run(job, self._write, fail)

    def _write(self, text: str) -> None:
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text)
        self.out.configure(state="disabled")
