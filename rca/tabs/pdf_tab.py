# -*- coding: utf-8 -*-
"""PDF Okuyucu / Not Alma sekmesi.

PyMuPDF (fitz) kuruluysa tam ozellikli calisir. Kurulu degilse sekme acilir
ama kullaniciya nasil kuracagi soylenir - program COKMEZ.
"""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca.ui_util import LazyTab, style_text

TOOLS = [("pen", "✏ Kalem"), ("mark", "🖍 Isaretleme"), ("text", "🔤 Metin"),
         ("erase", "🧽 Silgi"), ("select", "⬚ Metin sec")]


class PdfTab(LazyTab):
    """Sayfa gezinme, zoom, isaretleme, Kiril metin secimi ve AI'a gonderme."""

    def build(self) -> None:
        p = self.palette()
        self.doc = None
        self.path = ""
        self.page_no = 0
        self.zoom = 1.25
        self.tool = tk.StringVar(value="select")
        self._draw_last = None
        self._img = None
        self._page_words = []
        self._sel_start = None
        self._sel_rect = None
        self.selected_text = ""

        root = ttk.Frame(self, padding=8)
        root.pack(fill="both", expand=True)

        bar = ttk.Frame(root)
        bar.pack(fill="x")
        ttk.Button(bar, text="📂 PDF ac", style="Accent.TButton",
                   command=self.open_dialog).pack(side="left")
        ttk.Button(bar, text="◀", width=3, command=lambda: self.go(-1)).pack(
            side="left", padx=(12, 2))
        self.page_var = tk.StringVar(value="0 / 0")
        ttk.Label(bar, textvariable=self.page_var, width=10,
                  anchor="center").pack(side="left")
        ttk.Button(bar, text="▶", width=3, command=lambda: self.go(1)).pack(side="left")
        ttk.Button(bar, text="Git...", command=self.goto_page).pack(side="left", padx=6)

        ttk.Button(bar, text="−", width=3,
                   command=lambda: self.set_zoom(self.zoom - 0.2)).pack(side="left", padx=(14, 2))
        self.zoom_var = tk.StringVar(value="125%")
        ttk.Label(bar, textvariable=self.zoom_var, width=6,
                  anchor="center").pack(side="left")
        ttk.Button(bar, text="+", width=3,
                   command=lambda: self.set_zoom(self.zoom + 0.2)).pack(side="left")
        ttk.Button(bar, text="Genislige sigdir",
                   command=self.fit_width).pack(side="left", padx=6)

        for code, label in TOOLS:
            ttk.Radiobutton(bar, text=label, value=code,
                            variable=self.tool).pack(side="left", padx=2)

        ttk.Button(bar, text="Notlari kaydet", command=self.save_notes).pack(side="right")
        ttk.Button(bar, text="Isaretli PDF disa aktar",
                   command=self.export_pdf).pack(side="right", padx=6)
        ttk.Button(bar, text="Sayfayi temizle",
                   command=self.clear_page).pack(side="right")

        pane = ttk.PanedWindow(root, orient="horizontal")
        pane.pack(fill="both", expand=True, pady=8)

        left = ttk.Frame(pane)
        self.canvas = tk.Canvas(left, background=p["bg_alt"], highlightthickness=0)
        hs = ttk.Scrollbar(left, orient="horizontal", command=self.canvas.xview)
        vs = ttk.Scrollbar(left, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hs.set, yscrollcommand=vs.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-e.delta / 120), "units"))
        pane.add(left, weight=4)

        right = ttk.Frame(pane, padding=(10, 0))
        ttk.Label(right, text="Secili metin", style="TLabel",
                  font=C.FONT_UI_BOLD).pack(anchor="w")
        self.sel_box = tk.Text(right, height=7, wrap="word")
        style_text(self.sel_box, p)
        self.sel_box.pack(fill="x")
        row = ttk.Frame(right)
        row.pack(fill="x", pady=6)
        ttk.Button(row, text="AI'a acikla", style="Accent.TButton",
                   command=self.ask_ai).pack(side="left")
        ttk.Button(row, text="Sozlukte ara", command=self.lookup).pack(side="left", padx=4)
        ttk.Button(row, text="🔊", command=self.speak_sel).pack(side="left")
        ttk.Button(row, text="Bankaya ekle", command=self.add_to_bank).pack(side="left", padx=4)

        ttk.Label(right, text="Sayfa notu", style="TLabel",
                  font=C.FONT_UI_BOLD).pack(anchor="w", pady=(10, 0))
        self.note_box = tk.Text(right, height=10, wrap="word")
        style_text(self.note_box, p)
        self.note_box.pack(fill="both", expand=True)

        ttk.Label(right, text="AI yaniti", style="TLabel",
                  font=C.FONT_UI_BOLD).pack(anchor="w", pady=(10, 0))
        self.ai_box = tk.Text(right, height=12, wrap="word")
        style_text(self.ai_box, p)
        self.ai_box.pack(fill="both", expand=True)
        self.ai_box.configure(state="disabled")
        pane.add(right, weight=2)

        self.status = ttk.Label(root, text="", style="Dim.TLabel")
        self.status.pack(anchor="w")

        if not self._fitz():
            self.status.configure(
                text="PyMuPDF kurulu degil - PDF goruntuleme kapali.  Kurmak icin: "
                     "pip install pymupdf",
                foreground=p["warn"])
        last = self.app.settings.get("last_pdf", "")
        if last and Path(last).exists():
            self.load_pdf(last)

    # ------------------------------------------------------------------
    @staticmethod
    def _fitz():
        """PyMuPDF modulunu dondur (yoksa None)."""
        try:
            import fitz                       # type: ignore
            return fitz
        except Exception:
            return None

    def open_dialog(self) -> None:
        """Dosya secme penceresi."""
        path = filedialog.askopenfilename(title="PDF ac",
                                          filetypes=[("PDF", "*.pdf")])
        if path:
            self.load_pdf(path)

    def load_pdf(self, path: str) -> None:
        """PDF'i ac ve ilk sayfayi goster."""
        fitz = self._fitz()
        if not fitz:
            messagebox.showinfo(C.APP_NAME,
                                "PDF goruntulemek icin PyMuPDF gerekli:\n\n"
                                "pip install pymupdf")
            return
        try:
            self.doc = fitz.open(path)
        except Exception as e:                       # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"PDF acilamadi:\n{e}")
            return
        self.path = path
        self.page_no = 0
        self.app.settings["last_pdf"] = path
        C.save_settings(self.app.settings)
        self.render()

    def go(self, delta: int) -> None:
        """Sayfa degistir."""
        if not self.doc:
            return
        new = max(0, min(len(self.doc) - 1, self.page_no + delta))
        if new != self.page_no:
            self.page_no = new
            self.render()

    def goto_page(self) -> None:
        """Sayfa numarasi sor."""
        if not self.doc:
            return
        from tkinter import simpledialog
        n = simpledialog.askinteger(C.APP_NAME, f"Sayfa (1-{len(self.doc)}):",
                                    parent=self, minvalue=1, maxvalue=len(self.doc))
        if n:
            self.page_no = n - 1
            self.render()

    def set_zoom(self, z: float) -> None:
        """Yakinlastirma orani."""
        self.zoom = max(0.4, min(4.0, round(z, 2)))
        self.zoom_var.set(f"{self.zoom * 100:.0f}%")
        self.render()

    def fit_width(self) -> None:
        """Sayfayi tuval genisligine sigdir."""
        if not self.doc:
            return
        page = self.doc[self.page_no]
        w = self.canvas.winfo_width() or 800
        self.set_zoom((w - 20) / page.rect.width)

    # ------------------------------------------------------------------
    def render(self) -> None:
        """Gecerli sayfayi ciz ve kayitli isaretlemeleri uygula."""
        if not self.doc:
            return
        fitz = self._fitz()
        page = self.doc[self.page_no]
        mat = fitz.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        self._img = tk.PhotoImage(data=pix.tobytes("ppm"))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self._img, anchor="nw", tags="page")
        self.canvas.configure(scrollregion=(0, 0, pix.width, pix.height))
        self.page_var.set(f"{self.page_no + 1} / {len(self.doc)}")
        self.zoom_var.set(f"{self.zoom * 100:.0f}%")

        try:
            self._page_words = page.get_text("words")
        except Exception:
            self._page_words = []

        self.note_box.delete("1.0", "end")
        for n in self.repos.notes.for_page(self.path, self.page_no):
            if n["kind"] == "note":
                self.note_box.insert("end", n["payload"])
            else:
                self._replay(n)
        self.status.configure(
            text=f"{Path(self.path).name} · sayfa {self.page_no + 1} · "
                 f"{len(self._page_words)} kelime · arac: {self.tool.get()}")

    def _replay(self, note) -> None:
        """Kayitli cizim/isaretlemeyi tuvale geri koy."""
        p = self.palette()
        try:
            data = json.loads(note["payload"])
        except Exception:
            return
        z = self.zoom
        if note["kind"] == "pen":
            pts = [c * z for c in data.get("points", [])]
            if len(pts) >= 4:
                self.canvas.create_line(*pts, fill=data.get("color", p["err"]),
                                        width=2, tags="ink", capstyle="round")
        elif note["kind"] == "mark":
            x0, y0, x1, y1 = [c * z for c in data.get("rect", [0, 0, 0, 0])]
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="",
                                         fill=data.get("color", "#ffe066"),
                                         stipple="gray50", tags="ink")
        elif note["kind"] == "text":
            x, y = data.get("x", 0) * z, data.get("y", 0) * z
            self.canvas.create_text(x, y, text=data.get("text", ""), anchor="nw",
                                    fill=p["err"], font=C.FONT_UI_BOLD, tags="ink")

    # ------------------------------------------------------------------
    def on_press(self, evt) -> None:
        """Fare basildi."""
        if not self.doc:
            return
        x, y = self.canvas.canvasx(evt.x), self.canvas.canvasy(evt.y)
        tool = self.tool.get()
        self._draw_last = (x, y)
        self._points = [x, y]
        if tool in ("select", "mark"):
            self._sel_start = (x, y)
            if self._sel_rect:
                self.canvas.delete(self._sel_rect)
            self._sel_rect = None
        elif tool == "text":
            from tkinter import simpledialog
            txt = simpledialog.askstring(C.APP_NAME, "Not metni:", parent=self)
            if txt:
                self.canvas.create_text(x, y, text=txt, anchor="nw",
                                        fill=self.palette()["err"],
                                        font=C.FONT_UI_BOLD, tags="ink")
                self.repos.notes.add(self.pid, self.path, self.page_no, "text",
                                     json.dumps({"x": x / self.zoom, "y": y / self.zoom,
                                                 "text": txt}, ensure_ascii=False))
        elif tool == "erase":
            for item in self.canvas.find_overlapping(x - 8, y - 8, x + 8, y + 8):
                if "ink" in self.canvas.gettags(item):
                    self.canvas.delete(item)

    def on_drag(self, evt) -> None:
        """Fare surukleniyor."""
        if not self.doc or self._draw_last is None:
            return
        x, y = self.canvas.canvasx(evt.x), self.canvas.canvasy(evt.y)
        tool = self.tool.get()
        p = self.palette()
        if tool == "pen":
            self.canvas.create_line(self._draw_last[0], self._draw_last[1], x, y,
                                    fill=p["err"], width=2, capstyle="round", tags="ink")
            self._points += [x, y]
        elif tool in ("select", "mark") and self._sel_start:
            if self._sel_rect:
                self.canvas.delete(self._sel_rect)
            color = p["accent"] if tool == "select" else "#ffe066"
            self._sel_rect = self.canvas.create_rectangle(
                self._sel_start[0], self._sel_start[1], x, y,
                outline=color, width=1,
                fill=color if tool == "mark" else "", stipple="gray50",
                tags="ink" if tool == "mark" else "sel")
        elif tool == "erase":
            for item in self.canvas.find_overlapping(x - 8, y - 8, x + 8, y + 8):
                if "ink" in self.canvas.gettags(item):
                    self.canvas.delete(item)
        self._draw_last = (x, y)

    def on_release(self, evt) -> None:
        """Fare birakildi - islemi kalicilastir."""
        if not self.doc:
            return
        tool = self.tool.get()
        x, y = self.canvas.canvasx(evt.x), self.canvas.canvasy(evt.y)
        z = self.zoom
        if tool == "pen" and len(getattr(self, "_points", [])) >= 4:
            self.repos.notes.add(
                self.pid, self.path, self.page_no, "pen",
                json.dumps({"points": [c / z for c in self._points],
                            "color": self.palette()["err"]}))
        elif tool == "mark" and self._sel_start:
            x0, y0 = self._sel_start
            self.repos.notes.add(
                self.pid, self.path, self.page_no, "mark",
                json.dumps({"rect": [min(x0, x) / z, min(y0, y) / z,
                                     max(x0, x) / z, max(y0, y) / z],
                            "color": "#ffe066"}))
        elif tool == "select" and self._sel_start:
            self._extract_text(self._sel_start, (x, y))
        self._draw_last = None
        self._sel_start = None

    def _extract_text(self, a, b) -> None:
        """Secim dikdortgeni icindeki Kiril metni topla."""
        if not self._page_words:
            return
        z = self.zoom
        x0, y0 = min(a[0], b[0]) / z, min(a[1], b[1]) / z
        x1, y1 = max(a[0], b[0]) / z, max(a[1], b[1]) / z
        picked = []
        for w in self._page_words:
            wx0, wy0, wx1, wy1, text = w[0], w[1], w[2], w[3], w[4]
            if wx1 >= x0 and wx0 <= x1 and wy1 >= y0 and wy0 <= y1:
                picked.append(text)
        self.selected_text = " ".join(picked).strip()
        self.sel_box.delete("1.0", "end")
        self.sel_box.insert("1.0", self.selected_text)
        self.status.configure(text=f"{len(picked)} kelime secildi")

    # ------------------------------------------------------------------
    def _sel(self) -> str:
        """Panelde duran secili metin."""
        return self.sel_box.get("1.0", "end").strip()

    def ask_ai(self) -> None:
        """Secili metni yerel modele acikla."""
        text = self._sel()
        if not text:
            return
        self._ai_write(self.t("ai.thinking"))

        def job():
            return self.app.ai.explain(text, self.app.ui_lang())
        self.app.worker.run(job, self._ai_write,
                            lambda e: self._ai_write(f"{self.t('ai.offline')}\n\n({e})"))

    def _ai_write(self, text: str) -> None:
        self.ai_box.configure(state="normal")
        self.ai_box.delete("1.0", "end")
        self.ai_box.insert("1.0", text)
        self.ai_box.configure(state="disabled")

    def lookup(self) -> None:
        """Secili metni kelime bankasinda ara."""
        text = self._sel()
        if not text:
            return
        widget = self.app.goto_tab("tab.vocab")
        if widget is not None and hasattr(widget, "q"):
            widget.q.set(text.split()[0])
            widget.do_search()

    def speak_sel(self) -> None:
        """Secili metni seslendir."""
        self.app.speak(self._sel())

    def add_to_bank(self) -> None:
        """Secili ilk kelimeyi bankaya ekle."""
        text = self._sel()
        if not text:
            return
        word = text.split()[0].strip(".,!?;:()")
        if not C.has_cyrillic(word):
            messagebox.showinfo(C.APP_NAME, "Secim Kiril harf icermiyor.")
            return
        from tkinter import simpledialog
        tr = simpledialog.askstring(C.APP_NAME, f"'{word}' kelimesinin Turkcesi:",
                                    parent=self)
        if tr:
            self.repos.words.add(word, tr.strip(), deck="PDF'ten",
                                 example_ru=text[:180])
            self.app.set_status(f"Bankaya eklendi: {word}")

    def save_notes(self) -> None:
        """Sayfa notunu kaydet."""
        if not self.path:
            return
        text = self.note_box.get("1.0", "end").strip()
        rows = self.repos.notes.for_page(self.path, self.page_no)
        for r in rows:
            if r["kind"] == "note":
                self.repos.db.execute("DELETE FROM pdf_notes WHERE id=?", (r["id"],))
        if text:
            self.repos.notes.add(self.pid, self.path, self.page_no, "note", text)
        self.app.set_status("Not kaydedildi")

    def clear_page(self) -> None:
        """Bu sayfadaki tum isaretlemeleri sil."""
        if not self.path:
            return
        if messagebox.askyesno(C.APP_NAME, "Bu sayfadaki tum notlar silinsin mi?"):
            self.repos.notes.clear_page(self.path, self.page_no)
            self.render()

    def export_pdf(self) -> None:
        """Isaretlemeleri gomulu yeni bir PDF yaz."""
        fitz = self._fitz()
        if not fitz or not self.doc:
            return
        out = filedialog.asksaveasfilename(
            title="Isaretli PDF", defaultextension=".pdf",
            initialdir=str(C.EXPORT_DIR),
            initialfile=Path(self.path).stem + "_notlu.pdf",
            filetypes=[("PDF", "*.pdf")])
        if not out:
            return
        try:
            doc = fitz.open(self.path)
            rows = self.repos.db.query(
                "SELECT * FROM pdf_notes WHERE pdf_path=? ORDER BY page, id", (self.path,))
            for r in rows:
                if r["page"] >= len(doc):
                    continue
                page = doc[r["page"]]
                try:
                    data = json.loads(r["payload"]) if r["kind"] != "note" else None
                except Exception:
                    continue
                if r["kind"] == "mark" and data:
                    x0, y0, x1, y1 = data["rect"]
                    page.draw_rect(fitz.Rect(x0, y0, x1, y1),
                                   color=None, fill=(1, 0.9, 0.4), fill_opacity=0.35)
                elif r["kind"] == "pen" and data:
                    pts = data["points"]
                    for i in range(0, len(pts) - 3, 2):
                        page.draw_line(fitz.Point(pts[i], pts[i + 1]),
                                       fitz.Point(pts[i + 2], pts[i + 3]),
                                       color=(0.85, 0.2, 0.2), width=1.5)
                elif r["kind"] == "text" and data:
                    page.insert_text(fitz.Point(data["x"], data["y"] + 10),
                                     data["text"], fontsize=10, color=(0.85, 0.2, 0.2))
                elif r["kind"] == "note":
                    page.insert_text(fitz.Point(30, 30), "[not] " + r["payload"][:120],
                                     fontsize=8, color=(0.2, 0.4, 0.8))
            doc.save(out)
            doc.close()
            self.app.set_status(f"Disa aktarildi: {out}")
        except Exception as e:                       # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Yazilamadi:\n{e}")
