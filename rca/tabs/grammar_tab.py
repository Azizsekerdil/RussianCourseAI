# -*- coding: utf-8 -*-
"""Dilbilgisi Laboratuvarlari.

Her lab ayni akista: kural -> tablo -> canli ornek -> alistirma.
Icerik gomulu paketten (rca.content) gelir; harici dosya gerekmez.
"""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk

import rca_common as C
from rca import content as K
from rca.ui_util import LazyTab, ScrollFrame, style_text


class GrammarTab(LazyTab):
    """Hal / Fiil / Hareket / Sayi / Soz dizimi laboratuvarlari."""

    def build(self) -> None:
        p = self.palette()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        self._build_cases(p)
        self._build_verbs(p)
        self._build_motion(p)
        self._build_numbers(p)
        self._build_syntax(p)
        self._build_notes(p)

    # ==================================================================
    # NOTLAR (grammar/*.md)
    # ==================================================================
    def _build_notes(self, p) -> None:
        """grammar/ klasorundeki markdown notlarini goruntule."""
        frame = ttk.Frame(self.nb, padding=10)
        self.nb.add(frame, text="Notlar (.md)")

        bar = ttk.Frame(frame)
        bar.pack(fill="x")
        ttk.Label(bar, text="Dosya:").pack(side="left")
        self.note_file = tk.StringVar()
        self.note_box_sel = ttk.Combobox(bar, textvariable=self.note_file,
                                         state="readonly", width=38)
        self.note_box_sel.pack(side="left", padx=6)
        self.note_box_sel.bind("<<ComboboxSelected>>", lambda _e: self._load_note())
        ttk.Button(bar, text=self.t("g.refresh"),
                   command=self._scan_notes).pack(side="left")
        ttk.Label(bar, text=str(C.GRAMMAR_DIR), style="Dim.TLabel").pack(side="right")

        self.note_view = tk.Text(frame, wrap="word", padx=16, pady=12)
        style_text(self.note_view, p)
        self.note_view.pack(fill="both", expand=True, pady=10)
        self.note_view.tag_configure("h1", font=("Segoe UI", 17, "bold"),
                                     foreground=p["accent"], spacing1=12, spacing3=6)
        self.note_view.tag_configure("h2", font=("Segoe UI", 13, "bold"),
                                     spacing1=10, spacing3=4)
        self.note_view.tag_configure("bullet", lmargin1=18, lmargin2=32)
        self.note_view.tag_configure("code", font=C.FONT_MONO, foreground=p["ok"])
        self.note_view.tag_configure("ru", font=C.FONT_RU)
        self.note_view.configure(state="disabled")
        self._scan_notes()

    def _scan_notes(self) -> None:
        """grammar/ klasorundeki .md dosyalarini listele."""
        try:
            C.GRAMMAR_DIR.mkdir(parents=True, exist_ok=True)
            files = sorted(f.name for f in C.GRAMMAR_DIR.glob("*.md"))
        except Exception:
            files = []
        self.note_box_sel["values"] = files
        if files:
            if self.note_file.get() not in files:
                self.note_file.set(files[0])
            self._load_note()
        else:
            self._render_note(f"# Not bulunamadi\n\n"
                              f"{C.GRAMMAR_DIR} klasorune .md dosyalari koyun; "
                              f"burada listelenir.")

    def _load_note(self) -> None:
        """Secili markdown dosyasini oku."""
        name = self.note_file.get()
        if not name:
            return
        try:
            text = (C.GRAMMAR_DIR / name).read_text(encoding="utf-8")
        except Exception as e:                          # noqa: BLE001
            text = f"# Okunamadi\n\n{e}"
        self._render_note(text)

    def _render_note(self, text: str) -> None:
        """Basit markdown bicimlendirme (baslik, madde, kod, Kiril)."""
        self.note_view.configure(state="normal")
        self.note_view.delete("1.0", "end")
        for line in text.splitlines():
            if line.startswith("## "):
                self.note_view.insert("end", line[3:] + "\n", "h2")
            elif line.startswith("# "):
                self.note_view.insert("end", line[2:] + "\n", "h1")
            elif line.strip().startswith(("- ", "* ")):
                tag = "ru" if C.has_cyrillic(line) else "bullet"
                self.note_view.insert("end", "  • " + line.strip()[2:] + "\n",
                                      (tag, "bullet"))
            elif line.strip().startswith("|") or line.strip().startswith("```"):
                self.note_view.insert("end", line + "\n", "code")
            else:
                tag = "ru" if C.has_cyrillic(line) else ""
                self.note_view.insert("end", line + "\n", tag)
        self.note_view.configure(state="disabled")

    # ==================================================================
    # HAL LAB
    # ==================================================================
    def _build_cases(self, p) -> None:
        sf = ScrollFrame(self.nb)
        sf.paint(p)
        self.nb.add(sf, text="Hal Lab (Падежи)")
        b = sf.body

        ttk.Label(b, text="6 hal - ne zaman kullanilir?",
                  style="Title.TLabel").pack(anchor="w", pady=(6, 10))
        for c in K.CASES:
            row = ttk.Frame(b, style="Card.TFrame", padding=12)
            row.pack(fill="x", pady=4)
            head = ttk.Frame(row, style="Card.TFrame")
            head.pack(fill="x")
            ttk.Label(head, text=c["ru"], style="Card.TLabel",
                      font=("Segoe UI", 13, "bold")).pack(side="left")
            ttk.Label(head, text=f"  {c['tr']}", style="CardDim.TLabel").pack(side="left")
            ttk.Label(head, text=c["q"], style="Card.TLabel",
                      foreground=p["accent"]).pack(side="right")
            ttk.Label(row, text=c["use"], style="Card.TLabel", wraplength=880,
                      justify="left").pack(anchor="w", pady=(4, 2))
            ttk.Label(row, text=f"{c['ex'][0]}   —   {c['ex'][1]}", style="Card.TLabel",
                      font=C.FONT_RU).pack(anchor="w")
            ttk.Label(row, style="CardDim.TLabel",
                      text="Ekler:  eril " + c["endings"]["m"] + "  ·  disil " +
                           c["endings"]["f"] + "  ·  notr " + c["endings"]["n"] +
                           "  ·  cogul " + c["endings"]["pl"]).pack(anchor="w", pady=(4, 0))

        ttk.Label(b, text="Isim cekim tablosu", style="Title.TLabel").pack(
            anchor="w", pady=(18, 6))
        self._decl_table(b, K.NOUN_DECLENSION)

        ttk.Label(b, text="Zamir cekimi", style="Title.TLabel").pack(anchor="w", pady=(18, 6))
        self._decl_table(b, K.PRONOUN_DECLENSION)

        ttk.Label(b, text="Edat - hal eslesmesi", style="Title.TLabel").pack(
            anchor="w", pady=(18, 6))
        tv = ttk.Treeview(b, columns=("p", "c", "e"), show="headings",
                          height=len(K.PREPOSITION_CASE))
        for col, w, t in (("p", 220, "Edat"), ("c", 180, "Hal"), ("e", 300, "Ornek")):
            tv.heading(col, text=t)
            tv.column(col, width=w, anchor="w")
        names = {c["code"]: f"{c['ru']} ({c['tr']})" for c in K.CASES}
        for prep, code, ex in K.PREPOSITION_CASE:
            tv.insert("", "end", values=(prep, names.get(code, code), ex))
        tv.pack(fill="x", pady=4)

        ttk.Label(b, text="Cumledeki halleri isaretle", style="Title.TLabel").pack(
            anchor="w", pady=(18, 6))
        row = ttk.Frame(b)
        row.pack(fill="x")
        self.case_sent = tk.StringVar(value="Я читаю новую книгу о России в большом доме.")
        ttk.Entry(row, textvariable=self.case_sent, font=C.FONT_RU).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row, text="Coz", style="Accent.TButton",
                   command=self._mark_cases).pack(side="left", padx=6)
        self.case_out = tk.Text(b, height=6, wrap="word")
        style_text(self.case_out, p)
        self.case_out.pack(fill="x", pady=6)

        self._drill_block(b, "case", "Hal alistirmasi")

    def _decl_table(self, master, table) -> None:
        """Cekim tablosunu Treeview olarak ciz."""
        codes = [c["code"] for c in K.CASES]
        tv = ttk.Treeview(master, columns=["w"] + codes, show="headings",
                          height=len(table))
        tv.heading("w", text="Kelime")
        tv.column("w", width=170, anchor="w")
        for c in K.CASES:
            tv.heading(c["code"], text=c["ru"][:4] + ".")
            tv.column(c["code"], width=110, anchor="w")
        for name, forms in table.items():
            tv.insert("", "end", values=[name] + [forms.get(c, "") for c in codes])
        tv.pack(fill="x", pady=4)

    def _mark_cases(self) -> None:
        """Cumleyi ayristirip kelime turlerini ve olasi halleri goster."""
        p = self.palette()
        self.case_out.configure(state="normal")
        self.case_out.delete("1.0", "end")
        for tag, color in (("noun", p["accent"]), ("verb", p["ok"]),
                           ("adj", p["warn"]), ("prep", p["err"]),
                           ("other", p["fg_dim"])):
            self.case_out.tag_configure(tag, foreground=color)
        pairs = K.parse_sentence(self.case_sent.get())
        for word, tag in pairs:
            t = tag if tag in ("noun", "verb", "adj", "prep") else "other"
            self.case_out.insert("end", word + " ", t)
        self.case_out.insert("end", "\n\n")
        self.case_out.insert("end",
                             "Renk kodu: isim · fiil · sifat · edat · diger\n", "other")
        ends = {"e": "Предложный/Дательный olabilir", "у": "Дательный/Винительный olabilir",
                "ой": "Творительный olabilir", "ы": "Родительный/cogul olabilir",
                "и": "Родительный/cogul olabilir", "ом": "Творительный olabilir",
                "а": "Родительный tekil olabilir", "у ": "Дательный olabilir"}
        for word, tag in pairs:
            if tag != "noun":
                continue
            for suf, note in ends.items():
                if word.lower().endswith(suf.strip()):
                    self.case_out.insert("end", f"{word}: -{suf.strip()} -> {note}\n", "noun")
                    break
        self.case_out.configure(state="disabled")

    # ==================================================================
    # FIIL LAB
    # ==================================================================
    def _build_verbs(self, p) -> None:
        sf = ScrollFrame(self.nb)
        sf.paint(p)
        self.nb.add(sf, text="Fiil Lab (Вид)")
        b = sf.body

        ttk.Label(b, text="Gorunus (вид): tamamlanmis / tamamlanmamis",
                  style="Title.TLabel").pack(anchor="w", pady=(6, 8))
        for name, desc, ex in K.ASPECT_RULES:
            row = ttk.Frame(b, style="Card.TFrame", padding=12)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=name, style="Card.TLabel",
                      font=C.FONT_UI_BOLD).pack(anchor="w")
            ttk.Label(row, text=desc, style="CardDim.TLabel").pack(anchor="w")
            ttk.Label(row, text=ex, style="Card.TLabel", font=C.FONT_RU).pack(anchor="w")

        ttk.Label(b, text="Gorunus ciftleri", style="Title.TLabel").pack(
            anchor="w", pady=(18, 6))
        from rca.seed_words import ASPECT_PAIRS
        tv = ttk.Treeview(b, columns=("i", "p"), show="headings", height=len(ASPECT_PAIRS))
        tv.heading("i", text="несовершенный (surec)")
        tv.heading("p", text="совершенный (sonuc)")
        tv.column("i", width=260)
        tv.column("p", width=260)
        for impf, perf, perf_tr in ASPECT_PAIRS:
            tv.insert("", "end", values=(impf, f"{perf}  ({perf_tr})"))
        tv.pack(fill="x", pady=4)

        ttk.Label(b, text="Cekim tablolari", style="Title.TLabel").pack(
            anchor="w", pady=(18, 6))
        for name, d in K.CONJUGATION.items():
            box = ttk.Frame(b, style="Card.TFrame", padding=12)
            box.pack(fill="x", pady=4)
            ttk.Label(box, text=f"{name}  ·  {d['aspect']}", style="Card.TLabel",
                      font=C.FONT_UI_BOLD).pack(anchor="w")
            line = "   ".join(f"{k}: {v}" for k, v in d["present"].items())
            ttk.Label(box, text="Simdiki:  " + line, style="Card.TLabel",
                      font=C.FONT_RU, wraplength=900, justify="left").pack(anchor="w")
            past = "   ".join(f"{k}: {v}" for k, v in d["past"].items())
            ttk.Label(box, text="Gecmis:   " + past, style="Card.TLabel",
                      font=C.FONT_RU, wraplength=900, justify="left").pack(anchor="w")
            ttk.Label(box, text=f"Gelecek: {d['future']}", style="CardDim.TLabel",
                      wraplength=900, justify="left").pack(anchor="w")
            ttk.Label(box, text=f"Emir:    {d['imper']}", style="CardDim.TLabel").pack(
                anchor="w")

        self._drill_block(b, "verb", "Cekim alistirmasi")

    # ==================================================================
    # HAREKET FIILLERI
    # ==================================================================
    def _build_motion(self, p) -> None:
        sf = ScrollFrame(self.nb)
        sf.paint(p)
        self.nb.add(sf, text="Hareket Fiilleri")
        b = sf.body

        ttk.Label(b, text="Tek yon (однонаправленные) / Tekrarli (разнонаправленные)",
                  style="Title.TLabel").pack(anchor="w", pady=(6, 8))

        cv = tk.Canvas(b, height=170, highlightthickness=0, background=p["bg_alt"])
        cv.pack(fill="x", pady=6)
        self._motion_diagram(cv, p)

        for v in K.MOTION_VERBS:
            row = ttk.Frame(b, style="Card.TFrame", padding=12)
            row.pack(fill="x", pady=3)
            head = ttk.Frame(row, style="Card.TFrame")
            head.pack(fill="x")
            ttk.Label(head, text=f"{v['uni']}  ↔  {v['multi']}", style="Card.TLabel",
                      font=("Segoe UI", 14, "bold")).pack(side="left")
            ttk.Label(head, text=v["mode"], style="CardDim.TLabel").pack(side="right")
            ttk.Label(row, text="→  " + v["uni_ex"], style="Card.TLabel",
                      font=C.FONT_RU).pack(anchor="w", pady=(6, 0))
            ttk.Label(row, text="⇄  " + v["multi_ex"], style="Card.TLabel",
                      font=C.FONT_RU).pack(anchor="w")

        ttk.Label(b, text="On ekler ve anlamlari", style="Title.TLabel").pack(
            anchor="w", pady=(18, 6))
        tv = ttk.Treeview(b, columns=("p", "m", "e"), show="headings",
                          height=len(K.MOTION_PREFIXES))
        for c, w, t in (("p", 110, "On ek"), ("m", 220, "Anlam"), ("e", 420, "Ornek")):
            tv.heading(c, text=t)
            tv.column(c, width=w, anchor="w")
        for pre, mean, ex in K.MOTION_PREFIXES:
            tv.insert("", "end", values=(pre, mean, ex))
        tv.pack(fill="x", pady=4)

        self._drill_block(b, "motion", "Hareket fiili alistirmasi")

    @staticmethod
    def _motion_diagram(cv, p) -> None:
        """Tek yon / gidip gelme semasi."""
        cv.create_text(20, 20, text="идти / ехать  (tek yon, su an)", anchor="w",
                       fill=p["fg"])
        cv.create_line(30, 55, 380, 55, fill=p["accent"], width=3, arrow="last")
        cv.create_oval(24, 49, 36, 61, fill=p["ok"], outline="")
        cv.create_text(30, 75, text="ev", fill=p["fg_dim"], anchor="w")
        cv.create_text(380, 75, text="okul", fill=p["fg_dim"], anchor="e")

        cv.create_text(20, 105, text="ходить / ездить  (gidip gelme, aliskanlik)",
                       anchor="w", fill=p["fg"])
        cv.create_line(30, 140, 380, 140, fill=p["warn"], width=3, arrow="both")
        cv.create_oval(24, 134, 36, 146, fill=p["ok"], outline="")

    # ==================================================================
    # SAYI & OLCU
    # ==================================================================
    def _build_numbers(self, p) -> None:
        sf = ScrollFrame(self.nb)
        sf.paint(p)
        self.nb.add(sf, text="Sayi & Olcu")
        b = sf.body

        ttk.Label(b, text="Sayi - isim uyumu", style="Title.TLabel").pack(
            anchor="w", pady=(6, 8))
        tv = ttk.Treeview(b, columns=("n", "f", "e"), show="headings",
                          height=len(K.NUMBER_AGREEMENT))
        for c, w, t in (("n", 210, "Sayi"), ("f", 200, "Isim bicimi"), ("e", 400, "Ornek")):
            tv.heading(c, text=t)
            tv.column(c, width=w, anchor="w")
        for num, form, ex in K.NUMBER_AGREEMENT:
            tv.insert("", "end", values=(num, form, ex))
        tv.pack(fill="x", pady=4)

        ttk.Label(b, text="Saat · tarih · yas · para kaliplari",
                  style="Title.TLabel").pack(anchor="w", pady=(18, 6))
        for label, pattern in K.TIME_PATTERNS:
            row = ttk.Frame(b, style="Card.TFrame", padding=10)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, style="CardDim.TLabel", width=20).pack(side="left")
            ttk.Label(row, text=pattern, style="Card.TLabel", font=C.FONT_RU,
                      wraplength=680, justify="left").pack(side="left")

        self._drill_block(b, "numbers", "Sayi uyumu alistirmasi")

    # ==================================================================
    # SOZ DIZIMI
    # ==================================================================
    def _build_syntax(self, p) -> None:
        frame = ttk.Frame(self.nb, padding=12)
        self.nb.add(frame, text="Soz Dizimi")

        ttk.Label(frame, text="Cumle ayristirici", style="Title.TLabel").pack(anchor="w")
        note = ("pymorphy3 kuruluysa kok ve cekim etiketleri kesin olur; "
                "kurulu degilse sonek tabanli yaklasik etiketleme kullanilir.")
        ttk.Label(frame, text=note, style="Dim.TLabel", wraplength=900,
                  justify="left").pack(anchor="w", pady=(2, 10))

        row = ttk.Frame(frame)
        row.pack(fill="x")
        self.syn_sent = tk.StringVar(value="Мой друг читает интересную книгу в библиотеке.")
        ttk.Entry(row, textvariable=self.syn_sent, font=C.FONT_RU).pack(
            side="left", fill="x", expand=True)
        ttk.Button(row, text="Ayristir", style="Accent.TButton",
                   command=self._parse).pack(side="left", padx=6)

        self.tree = ttk.Treeview(frame, columns=("w", "pos", "note"), show="tree headings")
        for c, w, t in (("w", 220, "Kelime"), ("pos", 150, "Tur"), ("note", 420, "Not")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        self.tree.column("#0", width=40)
        self.tree.pack(fill="both", expand=True, pady=10)

    def _parse(self) -> None:
        """Cumleyi ayristirip agac gorunumunde goster."""
        self.tree.delete(*self.tree.get_children())
        pairs = K.parse_sentence(self.syn_sent.get())
        if not pairs:
            return
        groups = {}
        for w, tag in pairs:
            groups.setdefault(tag, []).append(w)
        for tag, words in groups.items():
            label = K.POS_LABELS.get(tag, tag)
            parent = self.tree.insert("", "end", text="", values=(label.upper(), tag,
                                                                 f"{len(words)} kelime"))
            for w in words:
                self.tree.insert(parent, "end", text="", values=(w, label, ""))
            self.tree.item(parent, open=True)

    # ==================================================================
    # ORTAK ALISTIRMA BLOGU
    # ==================================================================
    def _drill_block(self, master, lab: str, title: str) -> None:
        """Bir lab icin alistirma alani olustur."""
        ttk.Label(master, text=title, style="Title.TLabel").pack(anchor="w", pady=(20, 6))
        holder = ttk.Frame(master, style="Card.TFrame", padding=16)
        holder.pack(fill="x", pady=(0, 20))
        state = {"items": [], "i": 0, "ok": 0}
        stage = ttk.Frame(holder, style="Card.TFrame")
        stage.pack(fill="x")
        score = ttk.Label(holder, text="", style="CardDim.TLabel")
        score.pack(anchor="w", pady=(8, 0))

        def render() -> None:
            for c in stage.winfo_children():
                c.destroy()
            items = state["items"]
            if not items:
                ttk.Button(stage, text="▶ 10 soruluk tur baslat", style="Accent.TButton",
                           command=start).pack(anchor="w")
                return
            if state["i"] >= len(items):
                n = len(items)
                self.repos.study.log(self.pid, f"grammar.{lab}", state["ok"], n - state["ok"])
                ttk.Label(stage, text=f"Bitti: {state['ok']} / {n}", style="Card.TLabel",
                          font=C.FONT_UI_BOLD).pack(anchor="w")
                ttk.Button(stage, text="Tekrar", command=start).pack(anchor="w", pady=6)
                state["items"] = []
                return
            it = items[state["i"]]
            ttk.Label(stage, text=f"{state['i'] + 1} / {len(items)}",
                      style="CardDim.TLabel").pack(anchor="w")
            ttk.Label(stage, text=it["prompt"], style="Card.TLabel", font=C.FONT_RU,
                      wraplength=860, justify="left").pack(anchor="w", pady=10)
            box = ttk.Frame(stage, style="Card.TFrame")
            box.pack(anchor="w")
            for i, o in enumerate(it["options"]):
                ttk.Button(box, text=o, width=24,
                           command=lambda v=o: answer(v)).grid(row=i // 2, column=i % 2,
                                                               padx=5, pady=4)
            fb = ttk.Label(stage, text="", style="Card.TLabel", wraplength=860,
                           justify="left")
            fb.pack(anchor="w", pady=8)
            state["fb"] = fb

        def answer(given: str) -> None:
            it = state["items"][state["i"]]
            p = self.palette()
            ok = given == it["answer"]
            topic = it.get("topic", lab)
            self.repos.topics.ensure(topic, topic.replace(".", " · "), lab)
            self.repos.topics.record(self.pid, topic, 1 if ok else 0, 0 if ok else 1)
            if ok:
                state["ok"] += 1
                state["fb"].configure(text="✓ " + it["explain"], foreground=p["ok"])
            else:
                state["fb"].configure(text=f"✗ Dogrusu: {it['answer']}\n{it['explain']}",
                                      foreground=p["err"])
            score.configure(text=f"Skor: {state['ok']} / {state['i'] + 1}")
            state["i"] += 1
            self.after(1100 if ok else 2200, render)

        def start() -> None:
            state["items"] = K.build(lab, 10, random.Random())
            state["i"] = 0
            state["ok"] = 0
            render()

        render()
