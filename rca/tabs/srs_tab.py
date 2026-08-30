# -*- coding: utf-8 -*-
"""Aralikli Tekrar sekmesi: 'Bugun' panosu + kelime karti oturumu.

Pano tamamen kural tabanlidir; AI cagrisi YAPILMAZ, aninda acilir.
"""
from __future__ import annotations

import random
import time
import tkinter as tk
from tkinter import ttk

import rca_common as C
from rca import i18n
from rca.quiz_engine import LISTEN, MATCH, MCQ, TYPE_IN, build_session, check_answer, diff_chars
from rca.srs import quality_from_button, review
from rca.ui_util import Card, LazyTab, card, page_header


MODE_KEYS = {
    "card": "srs.mode.card",
    "mcq": "srs.mode.mcq",
    "type": "srs.mode.type",
    "listen": "srs.mode.listen",
    "match": "srs.mode.match",
}


class SRSTab(LazyTab):
    """Leitner/SM-2 tekrar oturumu."""

    def build(self) -> None:
        self.session = []
        self.idx = 0
        self.flipped = False
        self.started = 0.0
        self.results = []

        p = self.palette()
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        head = page_header(root, self.t("srs.today"), self.t("srs.subtitle"))
        head.pack(fill="x")
        self.goal_lbl = ttk.Label(head, text="", style="Dim.TLabel")
        self.goal_lbl.pack(side="right", padx=(0, 10))

        # --- pano ---------------------------------------------------------
        self.dash = ttk.Frame(root)
        self.dash.pack(fill="x", pady=(12, 0))

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=(14, 0))
        ttk.Button(actions, text="▶  " + self.t("srs.review"), style="Accent.TButton",
                   command=lambda: self.start("due")).pack(side="left")
        ttk.Button(actions, text="✗  " + self.t("srs.wrong_drill"), style="Card.TButton",
                   command=lambda: self.start("wrong")).pack(side="left", padx=6)
        ttk.Button(actions, text="✚  " + self.t("srs.new_words"), style="Card.TButton",
                   command=lambda: self.start("new")).pack(side="left")
        ttk.Button(actions, text="★  " + self.t("srs.favorites"), style="Card.TButton",
                   command=lambda: self.start("star")).pack(side="left", padx=6)

        self.limit = tk.IntVar(value=int(self.app.settings.get("daily_goal", 20)))
        ttk.Spinbox(actions, from_=5, to=100, increment=5, width=5,
                    textvariable=self.limit).pack(side="right")
        ttk.Label(actions, text=self.t("srs.count"), style="Dim.TLabel").pack(
            side="right", padx=(12, 6))
        self.mode = tk.StringVar(value=self.t(MODE_KEYS["card"]))
        self.mode_box = ttk.Combobox(
            actions, textvariable=self.mode, state="readonly", width=17,
            values=[self.t(key) for key in MODE_KEYS.values()])
        self.mode_box.pack(side="right")
        ttk.Label(actions, text=self.t("srs.mode"), style="Dim.TLabel").pack(
            side="right", padx=(0, 6))

        # --- calisma alani ------------------------------------------------
        holder = Card(root, p, padding=26)
        holder.pack(fill="both", expand=True, pady=14)
        self.stage = tk.Frame(holder.body, background=p["bg_alt"])
        self.stage.pack(fill="both", expand=True)

        self.progress = ttk.Progressbar(root, mode="determinate",
                                        style="Thin.Horizontal.TProgressbar")
        self.progress.pack(fill="x")

        self.refresh_dash()
        self._idle_screen()
        self._bind()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Pano sayilarini tazele."""
        if getattr(self, "dash", None) is not None:
            self.refresh_dash()

    def on_language_change(self) -> None:
        """Mod adlarini yeni dile cevirirken secili modu koru."""
        if getattr(self, "mode_box", None) is None:
            return
        code = self._mode_code()
        self.mode_box["values"] = [self.t(key) for key in MODE_KEYS.values()]
        self.mode.set(self.t(MODE_KEYS[code]))

    def _mode_code(self) -> str:
        """Gorunen (herhangi bir dildeki) mod adini kararlı koda cevir."""
        value = self.mode.get()
        for code, key in MODE_KEYS.items():
            if value in {i18n.t(key, lang) for lang in i18n.LANGS}:
                return code
        return "card"

    def _bind(self) -> None:
        """Klavye kisayollari (yalnizca bu sekme odaktayken anlamli)."""
        self.app.bind("<space>", self._key_space, add="+")
        self.app.bind("<Key-1>", lambda e: self._key_grade("dontknow"), add="+")
        self.app.bind("<Key-2>", lambda e: self._key_grade("unsure"), add="+")
        self.app.bind("<Key-3>", lambda e: self._key_grade("know"), add="+")

    def _active(self) -> bool:
        """Bu sayfa gorunur ve oturum acik mi?"""
        try:
            return self.is_current() and bool(self.session)
        except Exception:
            return False

    def _key_space(self, _e=None) -> None:
        if self._active() and self._mode_code() == "card":
            self.flip()

    def _key_grade(self, name: str) -> None:
        if self._active() and self._mode_code() == "card" and self.flipped:
            self.grade(name)

    # ------------------------------------------------------------------
    def refresh_dash(self) -> None:
        """'Bugun' panosu - kural tabanli sayimlar."""
        for c in self.dash.winfo_children():
            c.destroy()
        p = self.palette()
        d = self.repos.progress.dashboard(self.pid)
        streak = self.repos.study.streak(self.pid)
        tot = self.repos.study.totals(self.pid)
        acc = (100.0 * tot["correct"] / (tot["correct"] + tot["wrong"])
               if (tot["correct"] + tot["wrong"]) else 0.0)

        cards = [
            (self.t("v.due"), str(d["due"]), "accent" if d["due"] else None,
             self.t("srs.word")),
            (self.t("srs.wrongs"), str(d["wrong"]), "err" if d["wrong"] else None,
             self.t("srs.drill_waiting")),
            (self.t("srs.untried"), str(d["new"]), None, self.t("srs.in_bank")),
            (self.t("srs.learned"), str(d["learned"]),
             "ok" if d["learned"] else None, self.t("srs.box3")),
            (self.t("srs.streak"), str(streak), "warn" if streak >= 3 else None,
             self.t("srs.day")),
            (self.t("srs.accuracy"),
             f"%{acc:.0f}" if (tot["correct"] + tot["wrong"]) else "-",
             None, f"{tot['correct'] + tot['wrong']} {self.t('srs.attempt')}"),
        ]
        for i, (title, value, tone, hint) in enumerate(cards):
            c = card(self.dash, title, value, p, tone=tone, hint=hint)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            self.dash.columnconfigure(i, weight=1)

        goal = int(self.app.settings.get("daily_goal", 20))
        today = self.repos.study.daily(self.pid, 1)
        done = (today[0]["correct"] + today[0]["wrong"]) if today else 0
        self.goal_lbl.configure(
            text=self.t("srs.goal").format(done=done, goal=goal) +
                 ("  ✓" if done >= goal else ""))

    # ------------------------------------------------------------------
    def start(self, source: str) -> None:
        """Oturum baslat. source: due | wrong | new | star"""
        limit = int(self.limit.get())
        if source == "due":
            words = self.repos.progress.due_words(self.pid, limit)
        elif source == "wrong":
            words = self.repos.progress.wrong_words(self.pid, limit)
        elif source == "star":
            words = self.repos.progress.starred(self.pid)[:limit]
        else:
            words = self.repos.progress.new_words(self.pid, limit)

        if not words:
            self._message(self.t("srs.no_category"))
            return

        mode = self._mode_code()
        if mode == "card":
            self.session = [dict(w) for w in words]
        else:
            kinds = {"mcq": [MCQ], "type": [TYPE_IN],
                     "listen": [LISTEN], "match": [MATCH]}[mode]
            pool = self.repos.words.all()
            self.session = build_session([dict(w) for w in words], kinds, limit,
                                         rng=random.Random())
            self._pool = pool
        self.idx = 0
        self.results = []
        self.started = time.time()
        self.progress.configure(maximum=len(self.session), value=0)
        self.render()

    def _idle_screen(self) -> None:
        """Oturum yokken gosterilen ekran - duruma gore farkli yonlendirir."""
        p = self.palette()
        for c in self.stage.winfo_children():
            c.destroy()
        d = self.repos.progress.dashboard(self.pid)
        if d["due"]:
            icon = "↻"
            title = self.t("srs.due_title").format(count=d["due"])
            detail = self.t("srs.due_detail")
        elif d["new"]:
            icon, title = "+", self.t("srs.new_title")
            detail = self.t("srs.new_detail")
        else:
            icon, title = "✓", self.t("srs.current")
            detail = self.t("srs.current_detail")
        tk.Label(self.stage, text=icon, background=p["bg_alt"], foreground=p["fg_dim"],
                 font=(C.FONT_FAMILY, 34)).pack(pady=(34, 8))
        tk.Label(self.stage, text=title, background=p["bg_alt"], foreground=p["fg"],
                 font=(C.FONT_FAMILY, 16, "bold")).pack()
        tk.Label(self.stage, text=detail, background=p["bg_alt"],
                 foreground=p["fg_dim"], font=C.FONT_UI, justify="center",
                 wraplength=520).pack(pady=(6, 20))
        tk.Label(self.stage, background=p["bg_alt"], foreground=p["fg_mute"],
                 font=C.FONT_UI_SM, justify="center",
                 text=self.t("srs.shortcuts")).pack()

    def _message(self, text: str) -> None:
        """Sahneye bilgi mesaji yaz."""
        p = self.palette()
        for c in self.stage.winfo_children():
            c.destroy()
        tk.Label(self.stage, text=text, background=p["bg_alt"], foreground=p["fg_dim"],
                 font=C.FONT_UI, justify="center", wraplength=520).pack(pady=60)

    # ------------------------------------------------------------------
    def render(self) -> None:
        """Siradaki ogeyi ciz."""
        for c in self.stage.winfo_children():
            c.destroy()
        if self.idx >= len(self.session):
            self.finish()
            return
        self.progress.configure(value=self.idx)
        if self._mode_code() == "card":
            self._render_card()
        else:
            self._render_question()

    # -- kart modu ------------------------------------------------------
    def _render_card(self) -> None:
        """Kelime karti on yuzu."""
        w = self.session[self.idx]
        self.flipped = False
        top = ttk.Frame(self.stage, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=f"{self.idx + 1} / {len(self.session)}",
                  style="CardDim.TLabel").pack(side="left")
        ttk.Label(top, text=w.get("tags", ""), style="CardDim.TLabel").pack(side="right")

        stress = int(w.get("stress_pos") or -1)
        ttk.Label(self.stage, text=C.add_stress(w["ru"], stress),
                  style="RUBig.TLabel").pack(pady=(30, 6))
        from rca.content import rough_ipa
        ttk.Label(self.stage, text=rough_ipa(w["ru"], stress),
                  style="CardDim.TLabel").pack()

        self.back = ttk.Frame(self.stage, style="Card.TFrame")
        self.back.pack(fill="x", pady=18)

        btns = ttk.Frame(self.stage, style="Card.TFrame")
        btns.pack(pady=6)
        self.flip_btn = ttk.Button(btns, text=self.t("v.flip"), style="Accent.TButton",
                                   command=self.flip)
        self.flip_btn.pack()
        if self.app.can_speak():
            ttk.Button(self.stage, text="🔊 " + self.t("g.listen"),
                       command=lambda: self.app.speak(w["ru"])).pack()
        self.grade_box = ttk.Frame(self.stage, style="Card.TFrame")
        self.grade_box.pack(pady=10)

    def flip(self) -> None:
        """Karti cevir ve degerlendirme butonlarini goster."""
        if self.flipped or self.idx >= len(self.session):
            return
        self.flipped = True
        w = self.session[self.idx]
        primary = w.get("en") if self.app.ui_lang() == "en" and w.get("en") else w["tr"]
        secondary = w["tr"] if self.app.ui_lang() == "en" else w.get("en")
        ttk.Label(self.back, text=primary, style="Card.TLabel",
                  font=("Segoe UI", 18, "bold")).pack()
        if secondary and secondary != primary:
            ttk.Label(self.back, text=secondary, style="CardDim.TLabel").pack()
        if w.get("example_ru"):
            ttk.Label(self.back, text=w["example_ru"], style="Card.TLabel",
                      font=C.FONT_RU).pack(pady=(12, 0))
            ttk.Label(self.back, text=w.get("example_tr", ""),
                      style="CardDim.TLabel").pack()
        self.flip_btn.state(["disabled"])
        for text, name, style in (("1 · " + self.t("v.dontknow"), "dontknow", "Err.TButton"),
                                  ("2 · " + self.t("v.unsure"), "unsure", "Warn.TButton"),
                                  ("3 · " + self.t("v.know"), "know", "OK.TButton")):
            ttk.Button(self.grade_box, text=text, style=style,
                       command=lambda n=name: self.grade(n)).pack(side="left", padx=6)

    def grade(self, name: str) -> None:
        """Kullanici degerlendirmesini SM-2'ye isle."""
        w = self.session[self.idx]
        q = quality_from_button(name)
        st = self.repos.progress.state(self.pid, int(w["id"]))
        new = review(st, q)
        ok = q >= 3
        self.repos.progress.save(self.pid, int(w["id"]), new,
                                 correct_inc=1 if ok else 0, wrong_inc=0 if ok else 1)
        self.results.append(ok)
        self.idx += 1
        self.render()

    # -- alistirma modlari ----------------------------------------------
    def _render_question(self) -> None:
        """Coktan secmeli / yazarak / dinleme / eslestirme sorusu."""
        q = self.session[self.idx]
        ttk.Label(self.stage, text=f"{self.idx + 1} / {len(self.session)}",
                  style="CardDim.TLabel").pack(anchor="w")

        if q.kind == LISTEN:
            ttk.Label(self.stage, text=self.t("srs.type_heard"),
                      style="Card.TLabel").pack(pady=(20, 8))
            ttk.Button(self.stage, text="🔊 " + self.t("srs.listen_again"),
                       style="Accent.TButton",
                       command=lambda: self.app.speak(q.meta.get("speak", q.prompt))).pack()
            self.app.speak(q.meta.get("speak", q.prompt))
        else:
            ttk.Label(self.stage, text=q.prompt, style="RUBig.TLabel").pack(pady=(24, 14))

        if q.kind == MCQ or q.kind == MATCH:
            box = ttk.Frame(self.stage, style="Card.TFrame")
            box.pack(pady=10)
            opts = q.options or [q.answer]
            for i, o in enumerate(opts):
                ttk.Button(box, text=o, width=28,
                           command=lambda v=o: self._answer(v)).grid(
                    row=i // 2, column=i % 2, padx=6, pady=5)
        else:
            self.entry_var = tk.StringVar()
            e = ttk.Entry(self.stage, textvariable=self.entry_var, width=30,
                          font=C.FONT_RU, justify="center")
            e.pack(pady=16)
            e.focus_set()
            e.bind("<Return>", lambda _ev: self._answer(self.entry_var.get()))
            ttk.Button(self.stage, text=self.t("g.check"), style="Accent.TButton",
                       command=lambda: self._answer(self.entry_var.get())).pack()
            if q.hint:
                ttk.Label(self.stage, text=f"{self.t('srs.hint')}: {q.hint}",
                          style="CardDim.TLabel").pack(pady=(8, 0))

        self.feedback = ttk.Frame(self.stage, style="Card.TFrame")
        self.feedback.pack(fill="x", pady=12)

    def _answer(self, given: str) -> None:
        """Cevabi degerlendir, geri bildirim goster ve SM-2'yi guncelle."""
        q = self.session[self.idx]
        ok = check_answer(q, given)
        for c in self.feedback.winfo_children():
            c.destroy()

        if ok:
            ttk.Label(self.feedback, text="✓ " + self.t("g.correct"),
                      style="Card.TLabel", foreground=self.palette()["ok"],
                      font=C.FONT_UI_BOLD).pack()
        else:
            ttk.Label(self.feedback, text=f"✗ {self.t('srs.correct_is')}: {q.answer}",
                      style="Card.TLabel", foreground=self.palette()["err"],
                      font=C.FONT_UI_BOLD).pack()
            if q.kind in (TYPE_IN, LISTEN):
                self._show_diff(given, q.answer)

        if q.word_id:
            st = self.repos.progress.state(self.pid, int(q.word_id))
            new = review(st, 5 if ok else 0)
            self.repos.progress.save(self.pid, int(q.word_id), new,
                                     correct_inc=1 if ok else 0,
                                     wrong_inc=0 if ok else 1)
        self.results.append(ok)
        self.idx += 1
        self.after(900 if ok else 2200, self.render)

    def _show_diff(self, given: str, correct: str) -> None:
        """Harf harf karsilastirmayi renkli goster."""
        p = self.palette()
        box = tk.Text(self.feedback, height=1, wrap="none", font=C.FONT_RU_BIG)
        box.configure(background=p["bg_alt"], foreground=p["fg"], borderwidth=0,
                      highlightthickness=0)
        box.pack()
        box.tag_configure("ok", foreground=p["ok"])
        box.tag_configure("bad", foreground=p["err"], underline=True)
        for ch, good in diff_chars(given, correct):
            box.insert("end", ch, "ok" if good else "bad")
        box.configure(state="disabled")

    # ------------------------------------------------------------------
    def finish(self) -> None:
        """Oturumu kapat, calisma gunlugune yaz, ozet goster."""
        n = len(self.results)
        correct = sum(1 for r in self.results if r)
        secs = int(time.time() - self.started) if self.started else 0
        if n:
            self.repos.study.log(self.pid, "srs", correct, n - correct, secs)
        self.session = []
        self.progress.configure(value=0)
        for c in self.stage.winfo_children():
            c.destroy()
        ttk.Label(self.stage, text=self.t("v.session_done"), style="Card.TLabel",
                  font=("Segoe UI", 18, "bold")).pack(pady=(40, 10))
        if n:
            ttk.Label(self.stage, style="Card.TLabel",
                      text=self.t("srs.result").format(
                          correct=correct, total=n, percent=100 * correct / n,
                          minutes=secs // 60, seconds=secs % 60)).pack()
        self.refresh_dash()
        self.app.set_status(self.t("srs.complete"))
