# -*- coding: utf-8 -*-
"""Kiril Laboratuvari: 33 harf, el yazisi formlari, karisan ciftler, alistirma."""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

import rca_common as C
from rca import content as K
from rca.ui_util import LazyTab, ScrollFrame


class CyrillicTab(LazyTab):
    """Alfabe tablosu + yazim sirasi animasyonu + harf/ses alistirmasi."""

    def build(self) -> None:
        p = self.palette()
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_alphabet(nb, p)
        self._build_writing(nb, p)
        self._build_confusable(nb, p)
        self._build_drill(nb, p)

    # -- 1) alfabe -----------------------------------------------------
    def _build_alphabet(self, nb, p) -> None:
        """33 harflik tablo."""
        frame = ttk.Frame(nb, padding=10)
        nb.add(frame, text="Alfabe (33 harf)")

        cols = ("harf", "ad", "ses", "tr", "elyazisi")
        tv = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        for c, w, t in (("harf", 90, "Harf"), ("ad", 130, "Adi"), ("ses", 90, "Ses"),
                        ("tr", 130, "TR karsilik"), ("elyazisi", 420, "El yazisi ipucu")):
            tv.heading(c, text=t)
            tv.column(c, width=w, anchor="w")
        for letter, name, sound, hint, tr in K.ALPHABET:
            tv.insert("", "end", values=(letter, name, sound, tr, hint))
        vs = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        tv.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        tv.bind("<Double-1>", lambda _e: self._speak_row(tv))

        self.alpha_tv = tv

    def _speak_row(self, tv) -> None:
        """Secili harfi seslendir."""
        sel = tv.selection()
        if sel and self.app.can_speak():
            self.app.speak(tv.item(sel[0], "values")[0][0])

    # -- 2) yazim sirasi -----------------------------------------------
    def _build_writing(self, nb, p) -> None:
        """Harfi buyuk gosterir, kullanici tabletle uzerine yazar."""
        frame = ttk.Frame(nb, padding=10)
        nb.add(frame, text="Yazim / El yazisi")

        bar = ttk.Frame(frame)
        bar.pack(fill="x")
        ttk.Label(bar, text="Harf:").pack(side="left")
        self.letter_var = tk.StringVar(value=K.ALPHABET[0][0])
        box = ttk.Combobox(bar, textvariable=self.letter_var, state="readonly", width=8,
                           values=[a[0] for a in K.ALPHABET])
        box.pack(side="left", padx=6)
        box.bind("<<ComboboxSelected>>", lambda _e: self._draw_guide())
        ttk.Button(bar, text="▶ Yazim sirasini oynat",
                   command=self._animate).pack(side="left", padx=6)
        ttk.Button(bar, text="Tuvali temizle",
                   command=lambda: self._clear_user()).pack(side="left")
        ttk.Button(bar, text="🔊", command=lambda: self.app.speak(
            self.letter_var.get()[0])).pack(side="left", padx=6)

        wrap = ttk.Frame(frame)
        wrap.pack(fill="both", expand=True, pady=10)

        self.guide = tk.Canvas(wrap, width=360, height=360, highlightthickness=1,
                               background=p["bg_alt"], highlightbackground=p["border"])
        self.guide.pack(side="left", padx=(0, 12))
        self.user_canvas = tk.Canvas(wrap, width=360, height=360, highlightthickness=1,
                                     background=p["bg_alt"], highlightbackground=p["border"])
        self.user_canvas.pack(side="left")
        self.user_canvas.bind("<B1-Motion>", self._draw)
        self.user_canvas.bind("<ButtonRelease-1>", lambda _e: setattr(self, "_last", None))
        self._last = None
        self._strokes = 0

        self.hint = ttk.Label(frame, text="", style="Dim.TLabel", wraplength=740,
                              justify="left")
        self.hint.pack(anchor="w")
        self.compare = ttk.Label(frame, text="", style="TLabel")
        self.compare.pack(anchor="w", pady=6)
        ttk.Button(frame, text="Karsilastir",
                   command=self._compare).pack(anchor="w")
        self._draw_guide()

    def _draw_guide(self) -> None:
        """Sol tuvale hedef harfi ve satir cizgilerini ciz."""
        p = self.palette()
        c = self.guide
        c.delete("all")
        for y in (90, 180, 270):
            c.create_line(20, y, 340, y, fill=p["border"], dash=(3, 5))
        c.create_line(20, 300, 340, 300, fill=p["border"])
        pair = self.letter_var.get()
        c.create_text(120, 180, text=pair[0], font=("Georgia", 120), fill=p["fg"])
        c.create_text(250, 180, text=pair[1] if len(pair) > 1 else "",
                      font=("Segoe Script", 110, "italic"), fill=p["accent"])
        c.create_text(180, 330, text="basili  /  el yazisi (курсив)",
                      fill=p["fg_dim"], font=C.FONT_UI)
        for letter, name, sound, hint, tr in K.ALPHABET:
            if letter == pair:
                self.hint.configure(text=f"{name}  ·  {sound}  ·  TR: {tr}\nEl yazisi: {hint}")
                break

    def _animate(self) -> None:
        """Harfi yavasca ortaya cikararak yazim sirasi hissi ver."""
        p = self.palette()
        c = self.guide
        c.delete("anim")
        pair = self.letter_var.get()
        steps = 24
        c.create_rectangle(20, 60, 340, 300, fill=p["bg_alt"], outline="", tags="anim")
        c.create_text(180, 180, text=pair[1] if len(pair) > 1 else pair[0],
                      font=("Segoe Script", 130, "italic"), fill=p["accent"], tags="anim")
        mask = c.create_rectangle(20, 60, 340, 300, fill=p["bg_alt"], outline="",
                                  tags="anim")

        def step(i: int) -> None:
            if i > steps:
                c.delete("anim")
                self._draw_guide()
                return
            x = 20 + (320 * i / steps)
            try:
                c.coords(mask, x, 60, 340, 300)
                self.after(45, lambda: step(i + 1))
            except tk.TclError:
                pass
        step(0)

    def _draw(self, evt) -> None:
        """Sag tuvale serbest cizim."""
        p = self.palette()
        if self._last is not None:
            self.user_canvas.create_line(self._last[0], self._last[1], evt.x, evt.y,
                                         fill=p["fg"], width=4, capstyle="round",
                                         smooth=True)
        else:
            self._strokes += 1
        self._last = (evt.x, evt.y)

    def _clear_user(self) -> None:
        """Kullanici tuvalini temizle."""
        self.user_canvas.delete("all")
        self._last = None
        self._strokes = 0
        self.compare.configure(text="")

    def _compare(self) -> None:
        """Cizilen sekli kaba olcutlerle degerlendir (mürekkep yogunlugu + kalem darbesi)."""
        items = self.user_canvas.find_all()
        if not items:
            self.compare.configure(text="Once sag tuvale harfi yazin.",
                                   foreground=self.palette()["warn"])
            return
        xs, ys = [], []
        for i in items:
            x0, y0, x1, y1 = self.user_canvas.bbox(i)
            xs += [x0, x1]
            ys += [y0, y1]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        ink = len(items)
        notes = []
        if h < 60:
            notes.append("harf cok kucuk - satir yuksekligini doldurun")
        if w > h * 1.6:
            notes.append("cok genis yazilmis")
        if ink < 8:
            notes.append("cizgi az - harfi tamamlamamis olabilirsiniz")
        if self._strokes > 4:
            notes.append(f"{self._strokes} kalem darbesi - el yazisinda genelde 1-2 yeterli")
        p = self.palette()
        if notes:
            self.compare.configure(text="· " + "  · ".join(notes), foreground=p["warn"])
        else:
            self.compare.configure(text=f"Olculer uygun ({w:.0f}x{h:.0f} px, "
                                        f"{self._strokes} darbe).", foreground=p["ok"])

    # -- 3) karisan ciftler --------------------------------------------
    def _build_confusable(self, nb, p) -> None:
        """Sik karistirilan harf ciftleri."""
        sf = ScrollFrame(nb)
        sf.paint(p)
        nb.add(sf, text="Karisan ciftler")
        ttk.Label(sf.body, text="Sik karistirilan harfler", style="Title.TLabel",
                  padding=(10, 10)).pack(anchor="w")
        for a, b, note in K.CONFUSABLE:
            row = ttk.Frame(sf.body, style="Card.TFrame", padding=12)
            row.pack(fill="x", padx=10, pady=4)
            ttk.Label(row, text=f"{a}  /  {b}", style="Card.TLabel",
                      font=("Segoe UI", 20, "bold")).pack(side="left", padx=(0, 18))
            ttk.Label(row, text=note, style="Card.TLabel", font=C.FONT_RU,
                      wraplength=620, justify="left").pack(side="left")

    # -- 4) alistirma ---------------------------------------------------
    def _build_drill(self, nb, p) -> None:
        """Harf -> ses degeri alistirmasi."""
        frame = ttk.Frame(nb, padding=16)
        nb.add(frame, text="Alistirma")
        self.drill_items = []
        self.drill_i = 0
        self.drill_ok = 0

        ttk.Button(frame, text="▶ 12 soruluk tur baslat", style="Accent.TButton",
                   command=self._drill_start).pack(anchor="w")
        self.drill_stage = ttk.Frame(frame, style="Card.TFrame", padding=24)
        self.drill_stage.pack(fill="both", expand=True, pady=12)
        self.drill_score = ttk.Label(frame, text="", style="Dim.TLabel")
        self.drill_score.pack(anchor="w")

    def _drill_start(self) -> None:
        self.drill_items = K.build_cyrillic_exercises(12, random.Random())
        self.drill_i = 0
        self.drill_ok = 0
        self._drill_render()

    def _drill_render(self) -> None:
        for c in self.drill_stage.winfo_children():
            c.destroy()
        if self.drill_i >= len(self.drill_items):
            n = len(self.drill_items)
            if n:
                self.repos.study.log(self.pid, "cyrillic", self.drill_ok, n - self.drill_ok)
                self.repos.topics.ensure("cyrillic", "Kiril alfabesi", "cyrillic")
                self.repos.topics.record(self.pid, "cyrillic", self.drill_ok,
                                         n - self.drill_ok)
            ttk.Label(self.drill_stage, text=f"Bitti: {self.drill_ok} / {n}",
                      style="Card.TLabel", font=("Segoe UI", 18, "bold")).pack(pady=40)
            return
        it = self.drill_items[self.drill_i]
        ttk.Label(self.drill_stage, text=f"{self.drill_i + 1} / {len(self.drill_items)}",
                  style="CardDim.TLabel").pack(anchor="w")
        ttk.Label(self.drill_stage, text=it["prompt"], style="Card.TLabel",
                  font=("Segoe UI", 34, "bold")).pack(pady=20)
        box = ttk.Frame(self.drill_stage, style="Card.TFrame")
        box.pack()
        for i, o in enumerate(it["options"]):
            ttk.Button(box, text=o, width=14,
                       command=lambda v=o: self._drill_answer(v)).grid(
                row=i // 2, column=i % 2, padx=6, pady=5)
        self.drill_fb = ttk.Label(self.drill_stage, text="", style="Card.TLabel",
                                  wraplength=620, justify="left")
        self.drill_fb.pack(pady=12)

    def _drill_answer(self, given: str) -> None:
        it = self.drill_items[self.drill_i]
        p = self.palette()
        ok = given == it["answer"]
        if ok:
            self.drill_ok += 1
            self.drill_fb.configure(text="✓ " + it["explain"], foreground=p["ok"])
        else:
            self.drill_fb.configure(text=f"✗ Dogrusu: {it['answer']}\n{it['explain']}",
                                    foreground=p["err"])
        self.drill_score.configure(
            text=f"Skor: {self.drill_ok} / {self.drill_i + 1}")
        self.drill_i += 1
        self.after(1000 if ok else 2000, self._drill_render)
