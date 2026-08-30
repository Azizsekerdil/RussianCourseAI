# -*- coding: utf-8 -*-
"""Konusma Pratigi: yerel modelle CEFR seviyeli rol-yapma senaryolari."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import rca_common as C
from rca.ui_util import LazyTab, style_text

SCENARIOS = [
    ("Kafede siparis", "Ogrenci bir Moskova kafesinde; sen garsonsun."),
    ("Otel resepsiyonu", "Ogrenci otele giris yapiyor; sen resepsiyonistsin."),
    ("Doktorda", "Ogrenci poliklinige geldi; sen doktorsun."),
    ("Magazada alisveris", "Ogrenci kiyafet aliyor; sen satis danismanisin."),
    ("Yol sormak", "Ogrenci kaybolmus; sen yoldan gecen birisin."),
    ("Is gorusmesi", "Ogrenci bir is gorusmesinde; sen ise alim uzmanisin."),
    ("Tanisma", "Ogrenci yeni biriyle tanisiyor; sen o kisisin."),
    ("Telefonda randevu", "Ogrenci telefonla randevu aliyor; sen sekretersin."),
]


class SpeakingTab(LazyTab):
    """Diyalog oturumu + oturum sonu hata dokumu."""

    def build(self) -> None:
        p = self.palette()
        self.history = []

        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        bar = ttk.Frame(root)
        bar.pack(fill="x")
        ttk.Label(bar, text="Senaryo:").pack(side="left")
        self.scenario = tk.StringVar(value=SCENARIOS[0][0])
        ttk.Combobox(bar, textvariable=self.scenario, state="readonly", width=26,
                     values=[s[0] for s in SCENARIOS]).pack(side="left", padx=6)
        ttk.Label(bar, text="Seviye:").pack(side="left", padx=(16, 4))
        self.level = tk.StringVar(value=self.app.settings.get("cefr", "A1"))
        ttk.Combobox(bar, textvariable=self.level, state="readonly", width=6,
                     values=C.CEFR_LEVELS).pack(side="left")
        ttk.Button(bar, text="▶ Oturumu baslat", style="Accent.TButton",
                   command=self.start).pack(side="left", padx=12)
        ttk.Button(bar, text="⏹ Bitir ve rapor al",
                   command=self.report).pack(side="left")
        self.speak_on = tk.BooleanVar(value=self.app.can_speak())
        cb = ttk.Checkbutton(bar, text="Yanitlari seslendir", variable=self.speak_on)
        cb.pack(side="right")
        if not self.app.can_speak():
            cb.state(["disabled"])

        self.chat = tk.Text(root, wrap="word", height=20)
        style_text(self.chat, p)
        self.chat.pack(fill="both", expand=True, pady=10)
        self.chat.tag_configure("me", foreground=p["accent"], font=C.FONT_UI_BOLD)
        self.chat.tag_configure("bot", foreground=p["fg"], font=C.FONT_RU)
        self.chat.tag_configure("sys", foreground=p["fg_dim"])
        self.chat.configure(state="disabled")

        row = ttk.Frame(root)
        row.pack(fill="x")
        self.entry = ttk.Entry(row, font=C.FONT_RU)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda _e: self.send())
        ttk.Button(row, text="Gonder", style="Accent.TButton",
                   command=self.send).pack(side="left", padx=6)

        self._say("sys", "Bir senaryo secip 'Oturumu baslat'a tiklayin. "
                         "Model yerelde calisir; internet gerekmez.")

    # ------------------------------------------------------------------
    def _say(self, who: str, text: str) -> None:
        """Sohbet kutusuna satir ekle."""
        self.chat.configure(state="normal")
        prefix = {"me": "Sen: ", "bot": "🤖 ", "sys": "· "}.get(who, "")
        self.chat.insert("end", prefix + text + "\n\n", who)
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def start(self) -> None:
        """Yeni diyalog oturumu ac."""
        self.history = []
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        desc = next(d for n, d in SCENARIOS if n == self.scenario.get())
        self._say("sys", f"{self.scenario.get()} · {self.level.get()} · {desc}")
        self.history.append({"role": "user", "content": "Начнём."})
        self._ask()

    def send(self) -> None:
        """Kullanici cevabini gonder."""
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._say("me", text)
        self.history.append({"role": "user", "content": text})
        self._ask()

    def _ask(self) -> None:
        """Modelden siradaki repligi al."""
        scenario = next(d for n, d in SCENARIOS if n == self.scenario.get())
        level = self.level.get()
        lang = self.app.ui_lang()
        history = list(self.history)
        self._say("sys", self.t("ai.thinking"))

        def job():
            return self.app.ai.roleplay(scenario, level, history, lang)

        def done(reply: str):
            self._drop_last_sys()
            self._say("bot", reply)
            self.history.append({"role": "assistant", "content": reply})
            if self.speak_on.get():
                self.app.speak(reply)

        def fail(err: Exception):
            self._drop_last_sys()
            self._say("sys", f"{self.t('ai.offline')} ({err})")
        self.app.worker.run(job, done, fail)

    def _drop_last_sys(self) -> None:
        """'Dusunuyor...' satirini kaldir."""
        self.chat.configure(state="normal")
        ranges = self.chat.tag_ranges("sys")
        if ranges:
            self.chat.delete(ranges[-2], ranges[-1])
        self.chat.configure(state="disabled")

    def report(self) -> None:
        """Oturum sonu hata dokumu + 5 kelime."""
        if len(self.history) < 3:
            self._say("sys", "Rapor icin once birkac replik yazin.")
            return
        history = list(self.history)
        lang = self.app.ui_lang()
        self._say("sys", "Rapor hazirlaniyor...")

        def job():
            return self.app.ai.session_report(history, lang)

        def done(text: str):
            self._drop_last_sys()
            self._say("sys", "--- OTURUM RAPORU ---")
            self._say("bot", text)
            turns = sum(1 for m in history if m["role"] == "user") - 1
            self.repos.study.log(self.pid, "speaking", max(0, turns), 0)

        self.app.worker.run(job, done,
                            lambda e: self._say("sys", f"{self.t('ai.offline')} ({e})"))
