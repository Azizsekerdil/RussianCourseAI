# -*- coding: utf-8 -*-
"""Sinav Motoru sekmesi.

Soru tipleri: coktan secmeli, bosluk doldurma, dogru hali sec, fiili cek,
TR->RU / RU->TR ceviri, dinleme (TTS), kelime dikte.
Ceviride esdeger cevap toleransi vardir ama SON KARARI KULLANICI verir.
Yanlislar kelime bankasinda otomatik 'yanlis' olarak isaretlenir.
"""
from __future__ import annotations

import random
import time
import tkinter as tk
from tkinter import ttk

import rca_common as C
from rca import content as K
from rca.quiz_engine import (CASE_PICK, CONJUGATE, LISTEN, MCQ, TYPE_IN, Question,
                             accuracy, check_answer, equivalent)
from rca.srs import review
from rca.ui_util import LazyTab


KINDS = [
    ("mcq_ru2tr", "Coktan secmeli (RU->TR)"),
    ("mcq_tr2ru", "Coktan secmeli (TR->RU)"),
    ("gap", "Bosluk doldurma"),
    ("case", "Dogru hali sec"),
    ("conj", "Fiili cek"),
    ("tr2ru", "Ceviri TR->RU"),
    ("ru2tr", "Ceviri RU->TR"),
    ("listen", "Dinleme"),
    ("dictate", "Kelime dikte"),
]


class ExamTab(LazyTab):
    """Otomatik puanlamali sinav oturumu."""

    def build(self) -> None:
        self.questions = []
        self.idx = 0
        self.exam_id = None
        self.results = []
        self.started = 0.0

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        setup = ttk.LabelFrame(root, text="Sinav kur", padding=10)
        setup.pack(fill="x")

        self.kind_vars = {}
        for i, (code, label) in enumerate(KINDS):
            v = tk.BooleanVar(value=code in ("mcq_ru2tr", "gap", "case", "tr2ru"))
            ttk.Checkbutton(setup, text=label, variable=v).grid(
                row=i // 3, column=i % 3, sticky="w", padx=8, pady=3)
            self.kind_vars[code] = v

        row = ttk.Frame(setup)
        row.grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 0))
        ttk.Label(row, text="Soru sayisi:").pack(side="left")
        self.count = tk.IntVar(value=15)
        ttk.Spinbox(row, from_=5, to=60, increment=5, width=5,
                    textvariable=self.count).pack(side="left", padx=6)
        ttk.Label(row, text="Kaynak:").pack(side="left", padx=(16, 4))
        self.source = tk.StringVar(value="Karisik")
        ttk.Combobox(row, textvariable=self.source, state="readonly", width=16,
                     values=["Karisik", "Vakti gelenler", "Yanlislar",
                             "Yeni kelimeler"]).pack(side="left")
        ttk.Button(row, text="▶ " + self.t("g.start"), style="Accent.TButton",
                   command=self.start).pack(side="left", padx=16)

        self.stage = ttk.Frame(root, style="Card.TFrame", padding=24)
        self.stage.pack(fill="both", expand=True, pady=12)
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x")

        self.history_box = ttk.Frame(root)
        self.history_box.pack(fill="x", pady=(10, 0))
        self._idle()
        self._refresh_history()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Gecmis sinav listesini tazele."""
        if getattr(self, "history_box", None) is not None and not self.questions:
            self._refresh_history()

    def _idle(self) -> None:
        for c in self.stage.winfo_children():
            c.destroy()
        ttk.Label(self.stage, text="Soru tiplerini secip Basla'ya tiklayin",
                  style="Card.TLabel", font=("Segoe UI", 14)).pack(pady=50)

    def _refresh_history(self) -> None:
        """Son sinavlarin puanlarini goster."""
        for c in self.history_box.winfo_children():
            c.destroy()
        rows = self.repos.exams.history(self.pid, 8)
        if not rows:
            ttk.Label(self.history_box, text="Henuz sinav yok.",
                      style="Dim.TLabel").pack(anchor="w")
            return
        ttk.Label(self.history_box, text="Son sinavlar:",
                  style="Dim.TLabel").pack(anchor="w")
        line = ttk.Frame(self.history_box)
        line.pack(anchor="w", pady=4)
        for r in reversed(rows):
            txt = f"{r['started_at'][5:10]}  %{r['score']:.0f}"
            ttk.Label(line, text=txt, style="Card.TLabel",
                      padding=(8, 4)).pack(side="left", padx=3)

    # ------------------------------------------------------------------
    def _pick_words(self, n: int):
        """Kaynaga gore kelime havuzu sec."""
        src = self.source.get()
        if src == "Vakti gelenler":
            rows = self.repos.progress.due_words(self.pid, n * 2)
        elif src == "Yanlislar":
            rows = self.repos.progress.wrong_words(self.pid, n * 2)
        elif src == "Yeni kelimeler":
            rows = self.repos.progress.new_words(self.pid, n * 2)
        else:
            rows = self.repos.words.all()
        rows = [dict(r) for r in rows]
        if not rows:
            rows = [dict(r) for r in self.repos.words.all()]
        return rows

    def start(self) -> None:
        """Secili tiplerden soru uret ve sinavi baslat."""
        kinds = [c for c, v in self.kind_vars.items() if v.get()]
        if not kinds:
            self._msg("En az bir soru tipi secin.")
            return
        n = int(self.count.get())
        rng = random.Random()
        pool = self._pick_words(n)
        all_words = [dict(r) for r in self.repos.words.all()]
        pool_tr = [w["tr"] for w in all_words if w["tr"]]
        pool_ru = [w["ru"] for w in all_words if w["ru"]]

        qs = []
        for i in range(n):
            kind = kinds[i % len(kinds)]
            q = self._make(kind, rng, pool, pool_tr, pool_ru)
            if q:
                qs.append(q)
        if not qs:
            self._msg("Soru uretilemedi - kelime bankasi bos olabilir.")
            return
        rng.shuffle(qs)
        self.questions = qs
        self.idx = 0
        self.results = []
        self.started = time.time()
        self.exam_id = self.repos.exams.start(self.pid, ",".join(kinds))
        self.progress.configure(maximum=len(qs), value=0)
        self.render()

    def _make(self, kind: str, rng, pool, pool_tr, pool_ru):
        """Tek bir soru uret (uretilemezse None)."""
        def rand_word():
            return rng.choice(pool) if pool else None

        if kind in ("mcq_ru2tr", "mcq_tr2ru"):
            w = rand_word()
            if not w:
                return None
            if kind == "mcq_ru2tr":
                opts = self._opts(w["tr"], pool_tr, rng)
                return Question(MCQ, w["ru"], w["tr"], opts, w["id"])
            opts = self._opts(w["ru"], pool_ru, rng)
            return Question(MCQ, w["tr"], w["ru"], opts, w["id"])

        if kind == "gap":
            cands = [w for w in pool if w.get("example_ru") and w["ru"] in w["example_ru"]]
            if not cands:
                cands = [w for w in pool if w.get("example_ru")]
            if not cands:
                return None
            w = rng.choice(cands)
            sentence = w["example_ru"]
            gapped = sentence.replace(w["ru"], "____", 1)
            if gapped == sentence:
                first = sentence.split()[0]
                gapped = sentence.replace(first, "____", 1)
                return Question(TYPE_IN, gapped, first.strip(".,!?"), [], w["id"],
                                hint=w.get("example_tr", ""))
            return Question(TYPE_IN, gapped, w["ru"], [], w["id"],
                            hint=w.get("example_tr", ""))

        if kind == "case":
            items = K.build("case", 1, rng)
            if not items:
                return None
            it = items[0]
            return Question(CASE_PICK, it["prompt"], it["answer"], it["options"],
                            None, hint=it["explain"], meta={"topic": it["topic"]})

        if kind == "conj":
            items = K.build("verb", 1, rng)
            if not items:
                return None
            it = items[0]
            return Question(CONJUGATE, it["prompt"], it["answer"], it["options"],
                            None, hint=it["explain"], meta={"topic": it["topic"]})

        if kind in ("tr2ru", "ru2tr"):
            w = rand_word()
            if not w:
                return None
            if kind == "tr2ru":
                return Question(TYPE_IN, f"Ceviri (TR->RU):  {w['tr']}", w["ru"], [],
                                w["id"], meta={"tolerant": True})
            return Question(TYPE_IN, f"Ceviri (RU->TR):  {w['ru']}", w["tr"], [],
                            w["id"], meta={"tolerant": True})

        if kind in ("listen", "dictate"):
            w = rand_word()
            if not w:
                return None
            label = "Duydugunuzu yazin" if kind == "listen" else "Dikte: kelimeyi yazin"
            return Question(LISTEN, label, w["ru"], [], w["id"],
                            hint=w["tr"], meta={"speak": w["ru"]})
        return None

    @staticmethod
    def _opts(correct, pool, rng, n=4):
        """Coktan secmeli secenekleri uret."""
        others = [x for x in pool if x and x != correct]
        rng.shuffle(others)
        opts = others[:n - 1] + [correct]
        rng.shuffle(opts)
        return opts

    # ------------------------------------------------------------------
    def _msg(self, text: str) -> None:
        for c in self.stage.winfo_children():
            c.destroy()
        ttk.Label(self.stage, text=text, style="Card.TLabel").pack(pady=50)

    def render(self) -> None:
        """Siradaki soruyu ciz."""
        for c in self.stage.winfo_children():
            c.destroy()
        if self.idx >= len(self.questions):
            self.finish()
            return
        q = self.questions[self.idx]
        self.progress.configure(value=self.idx)

        head = ttk.Frame(self.stage, style="Card.TFrame")
        head.pack(fill="x")
        ttk.Label(head, text=f"Soru {self.idx + 1} / {len(self.questions)}",
                  style="CardDim.TLabel").pack(side="left")
        ttk.Label(head, text=q.kind, style="CardDim.TLabel").pack(side="right")

        if q.kind == LISTEN:
            ttk.Label(self.stage, text=q.prompt, style="Card.TLabel",
                      font=("Segoe UI", 14)).pack(pady=(24, 10))
            btn = ttk.Button(self.stage, text="🔊 Dinle", style="Accent.TButton",
                             command=lambda: self.app.speak(q.meta.get("speak", "")))
            btn.pack()
            if not self.app.can_speak():
                btn.state(["disabled"])
                ttk.Label(self.stage, text=f"(Ses motoru yok - kelime: {q.answer})",
                          style="CardDim.TLabel").pack(pady=6)
            else:
                self.app.speak(q.meta.get("speak", ""))
        else:
            ttk.Label(self.stage, text=q.prompt, style="Card.TLabel",
                      font=C.FONT_RU, wraplength=760, justify="center").pack(pady=(26, 16))

        if q.options:
            box = ttk.Frame(self.stage, style="Card.TFrame")
            box.pack()
            for i, o in enumerate(q.options):
                ttk.Button(box, text=o, width=26,
                           command=lambda v=o: self.answer(v)).grid(
                    row=i // 2, column=i % 2, padx=6, pady=5)
        else:
            self.var = tk.StringVar()
            e = ttk.Entry(self.stage, textvariable=self.var, width=34,
                          font=C.FONT_RU, justify="center")
            e.pack(pady=10)
            e.focus_set()
            e.bind("<Return>", lambda _ev: self.answer(self.var.get()))
            ttk.Button(self.stage, text=self.t("g.check"), style="Accent.TButton",
                       command=lambda: self.answer(self.var.get())).pack()

        self.fb = ttk.Frame(self.stage, style="Card.TFrame")
        self.fb.pack(fill="x", pady=14)

    def answer(self, given: str) -> None:
        """Cevabi puanla. Ceviride tolerans varsa son karar kullanicinin."""
        q = self.questions[self.idx]
        ok = check_answer(q, given)
        tolerant = bool(q.meta.get("tolerant"))
        near = (not ok) and tolerant and equivalent(given, q.answer)

        for c in self.fb.winfo_children():
            c.destroy()

        if near:
            ttk.Label(self.fb, text=f"Beklenen: {q.answer}\nSizin: {given}",
                      style="Card.TLabel", justify="left").pack(anchor="w")
            ttk.Label(self.fb, text="Esdeger gorunuyor - dogru saymak ister misiniz?",
                      style="Card.TLabel", foreground=self.palette()["warn"]).pack(anchor="w")
            row = ttk.Frame(self.fb, style="Card.TFrame")
            row.pack(anchor="w", pady=6)
            ttk.Button(row, text="Dogru say", style="OK.TButton",
                       command=lambda: self._commit(q, given, True)).pack(side="left")
            ttk.Button(row, text="Yanlis say", style="Err.TButton",
                       command=lambda: self._commit(q, given, False)).pack(side="left", padx=6)
            return

        if not ok and tolerant:
            ttk.Label(self.fb, text=f"Beklenen: {q.answer}", style="Card.TLabel",
                      foreground=self.palette()["err"]).pack(anchor="w")
            row = ttk.Frame(self.fb, style="Card.TFrame")
            row.pack(anchor="w", pady=6)
            ttk.Button(row, text="Yine de dogru say",
                       command=lambda: self._commit(q, given, True)).pack(side="left")
            ttk.Button(row, text="Devam", style="Accent.TButton",
                       command=lambda: self._commit(q, given, False)).pack(side="left", padx=6)
            return

        self._commit(q, given, ok, delay=True)

    def _commit(self, q: Question, given: str, ok: bool, delay: bool = False) -> None:
        """Cevabi kaydet ve siradaki soruya gec."""
        self.repos.exams.answer(self.exam_id, q.word_id, q.kind, q.prompt,
                                q.answer, given, ok)
        if q.word_id:
            st = self.repos.progress.state(self.pid, int(q.word_id))
            self.repos.progress.save(self.pid, int(q.word_id),
                                     review(st, 5 if ok else 0),
                                     correct_inc=1 if ok else 0,
                                     wrong_inc=0 if ok else 1)
        topic = q.meta.get("topic")
        if topic:
            lab = topic.split(".")[0]
            self.repos.topics.ensure(topic, topic.replace(".", " · "), lab)
            self.repos.topics.record(self.pid, topic, 1 if ok else 0, 0 if ok else 1)
        self.results.append(ok)

        if delay:
            for c in self.fb.winfo_children():
                c.destroy()
            if ok:
                ttk.Label(self.fb, text="✓ " + self.t("g.correct"), style="Card.TLabel",
                          foreground=self.palette()["ok"], font=C.FONT_UI_BOLD).pack()
            else:
                ttk.Label(self.fb, text=f"✗ Dogrusu: {q.answer}", style="Card.TLabel",
                          foreground=self.palette()["err"], font=C.FONT_UI_BOLD).pack()
                if q.hint:
                    ttk.Label(self.fb, text=q.hint, style="CardDim.TLabel",
                              wraplength=700).pack()
            self.idx += 1
            self.after(800 if ok else 2000, self.render)
            return

        self.idx += 1
        self.render()

    # ------------------------------------------------------------------
    def finish(self) -> None:
        """Sinavi kapat ve sonuc ekranini goster."""
        summary = self.repos.exams.finish(self.exam_id)
        secs = int(time.time() - self.started)
        self.repos.study.log(self.pid, "exam", summary["correct"],
                             summary["total"] - summary["correct"], secs)
        wrongs = self.repos.exams.wrong_answers(self.exam_id)
        self.questions = []
        self.progress.configure(value=0)

        for c in self.stage.winfo_children():
            c.destroy()
        ttk.Label(self.stage, text=f"Puan: %{summary['score']:.0f}", style="Card.TLabel",
                  font=("Segoe UI", 26, "bold")).pack(pady=(20, 4))
        ttk.Label(self.stage, style="CardDim.TLabel",
                  text=f"{summary['correct']} / {summary['total']} dogru · "
                       f"{secs // 60} dk {secs % 60} sn").pack()

        if wrongs:
            ttk.Label(self.stage, text="Yanlislar (kelime bankasinda isaretlendi):",
                      style="Card.TLabel", font=C.FONT_UI_BOLD).pack(anchor="w", pady=(18, 6))
            tv = ttk.Treeview(self.stage, columns=("p", "e", "g"), show="headings", height=8)
            for c, w, t in (("p", 320, "Soru"), ("e", 200, "Dogru"), ("g", 200, "Sizin")):
                tv.heading(c, text=t)
                tv.column(c, width=w)
            for r in wrongs:
                tv.insert("", "end", values=(r["prompt"], r["expected"], r["given"]))
            tv.pack(fill="both", expand=True)
        else:
            ttk.Label(self.stage, text="Hic hata yok - tebrikler!",
                      style="Card.TLabel", foreground=self.palette()["ok"]).pack(pady=20)

        self._refresh_history()
        self.app.set_status(f"Sinav bitti - %{summary['score']:.0f}")
