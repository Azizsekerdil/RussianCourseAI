# -*- coding: utf-8 -*-
"""Telaffuz & Vurgu Studyosu.

Vurgu (ударение) gosterimi, редукция kurallari, kaba IPA, cevrimdisi TTS,
ve Vosk varsa mikrofonla tekrar karsilastirmasi.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import rca_common as C
from rca import content as K
from rca.ui_util import LazyTab, ScrollFrame


class PronTab(LazyTab):
    """Kelimenin vurgusunu, indirgemesini ve okunusunu gosterir."""

    def build(self) -> None:
        p = self.palette()
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        bar = ttk.Frame(root)
        bar.pack(fill="x")
        ttk.Label(bar, text="Kelime:").pack(side="left")
        self.word = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.word, width=26, font=C.FONT_RU)
        e.pack(side="left", padx=6)
        e.bind("<Return>", lambda _ev: self.analyze())
        ttk.Button(bar, text="Coz", style="Accent.TButton",
                   command=self.analyze).pack(side="left")
        ttk.Button(bar, text="Bankadan sec", command=self.pick).pack(side="left", padx=6)
        self.btn_speak = ttk.Button(bar, text="🔊 " + self.t("g.listen"),
                                    command=self.speak)
        self.btn_speak.pack(side="left")
        if not self.app.can_speak():
            self.btn_speak.state(["disabled"])

        ttk.Label(bar, text="Vurgulu hece:").pack(side="left", padx=(20, 4))
        self.stress = tk.IntVar(value=-1)
        self.stress_box = ttk.Combobox(bar, state="readonly", width=16,
                                       textvariable=tk.StringVar())
        self.stress_box.pack(side="left")
        self.stress_box.bind("<<ComboboxSelected>>", lambda _e: self._on_stress_pick())

        # --- gosterim ------------------------------------------------------
        card = ttk.Frame(root, style="Card.TFrame", padding=20)
        card.pack(fill="x", pady=12)
        self.big = ttk.Label(card, text="—", style="Card.TLabel",
                             font=("Segoe UI", 40, "bold"))
        self.big.pack(anchor="w")
        self.ipa = ttk.Label(card, text="", style="CardDim.TLabel", font=("Consolas", 14))
        self.ipa.pack(anchor="w", pady=(4, 0))
        self.syl = ttk.Label(card, text="", style="Card.TLabel", font=C.FONT_RU)
        self.syl.pack(anchor="w", pady=(10, 0))
        self.reduction = ttk.Label(card, text="", style="Card.TLabel", wraplength=900,
                                   justify="left")
        self.reduction.pack(anchor="w", pady=(10, 0))

        # --- mikrofon ------------------------------------------------------
        self.mic = ttk.LabelFrame(root, text="Mikrofonla tekrar", padding=12)
        self.mic.pack(fill="x")
        self._build_mic()

        # --- kurallar ------------------------------------------------------
        rules = ScrollFrame(root)
        rules.paint(p)
        rules.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(rules.body, text="Редукция ve okuma kurallari",
                  style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        for name, desc, ex in K.REDUCTION_RULES:
            row = ttk.Frame(rules.body, style="Card.TFrame", padding=12)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=name, style="Card.TLabel",
                      font=C.FONT_UI_BOLD).pack(anchor="w")
            ttk.Label(row, text=desc, style="CardDim.TLabel").pack(anchor="w")
            ttk.Label(row, text=ex, style="Card.TLabel", font=C.FONT_RU).pack(anchor="w")

        self.current_stress = -1

    # -- mikrofon / tanima motoru ------------------------------------------
    def _asr_signature(self) -> tuple:
        """Tanima motoru secimini etkileyen durum: Whisper ayarlari + yerel modeller."""
        opts = self.app.settings.get("whisper") or {}
        try:
            from rca import whisper_engine as W
            have = tuple(W.downloaded_models()) if W.installed() else ()
        except Exception:
            have = ()
        vosk = (C.APP_HOME / "models" / "vosk-ru").exists()
        return (repr(sorted(opts.items())) if isinstance(opts, dict) else "", have, vosk)

    def _build_mic(self) -> None:
        """Mikrofon bolumunu (yeniden) kur; ASR guncel ayarlarla olusturulur."""
        for child in self.mic.winfo_children():
            child.destroy()
        self.mic_out = None
        self._mic_sig = self._asr_signature()
        from rca.tts import ASR
        self.asr = ASR(whisper_opts=self.app.settings.get("whisper") or {})
        if self.asr.available():
            ttk.Button(self.mic, text="● Kaydet ve karsilastir",
                       command=self.record).pack(side="left")
            self.mic_out = ttk.Label(self.mic, text="", style="TLabel")
            self.mic_out.pack(side="left", padx=12)
            ttk.Label(self.mic, text=f"({self.asr.backend})", style="Mute.TLabel").pack(side="right")
        else:
            ttk.Label(self.mic, style="Warn.TLabel", justify="left",
                      text=f"Konusma tanima devre disi: {self.asr.reason}\n"
                           f"Whisper icin 'Konusma Tanima (Whisper)' sayfasindan bir model indirin\n"
                           f"ya da Vosk 'ru' modelini su klasore acin: "
                           f"{C.APP_HOME / 'models' / 'vosk-ru'}").pack(anchor="w")

    def on_show(self) -> None:
        """Whisper ayari ya da indirilen modeller degistiyse mikrofon bolumunu yenile."""
        if getattr(self, "mic", None) is None:
            return
        if getattr(self, "_rec_busy", False):
            return                                     # kayit suruyor: etiket/ASR degismesin
        if self._asr_signature() != getattr(self, "_mic_sig", None):
            self._build_mic()

    # ------------------------------------------------------------------
    def pick(self) -> None:
        """Kelime bankasindan rastgele bir kelime getir."""
        import random
        rows = self.repos.words.all()
        if not rows:
            return
        w = random.choice(rows)
        self.word.set(w["ru"])
        self.current_stress = int(w.get("stress_pos") or -1)
        self.analyze(keep_stress=True)

    def analyze(self, keep_stress: bool = False) -> None:
        """Girilen kelimeyi coz: vurgu, IPA, hece, indirgeme."""
        raw = C.strip_stress(self.word.get().strip())
        if not raw:
            return
        if not keep_stress:
            row = self.repos.db.one("SELECT stress_pos FROM words WHERE ru_norm=?",
                                    (C.normalize_ru(raw),))
            self.current_stress = int(row["stress_pos"]) if row else -1

        vowels = [(i, ch) for i, ch in enumerate(raw.lower()) if ch in C.VOWELS]
        self.stress_box["values"] = [f"{n + 1}. hece: {ch}" for n, (i, ch) in enumerate(vowels)]
        self._vowel_index = [i for i, _ in vowels]
        if self.current_stress in self._vowel_index:
            self.stress_box.current(self._vowel_index.index(self.current_stress))
        elif len(vowels) == 1:
            self.current_stress = vowels[0][0]
            self.stress_box.current(0)

        self.big.configure(text=C.add_stress(raw, self.current_stress))
        self.ipa.configure(text=K.rough_ipa(raw, self.current_stress))
        n = C.syllables(raw)
        self.syl.configure(text=f"{n} hece" + (
            f"  ·  vurgu {self._vowel_index.index(self.current_stress) + 1}. hecede"
            if self.current_stress in self._vowel_index else "  ·  vurgu bilinmiyor"))

        notes = []
        low = raw.lower()
        for i, ch in enumerate(low):
            if ch == "о" and i != self.current_stress:
                notes.append(f"{i + 1}. harf 'о' vurgusuz -> [a]/[ə] okunur")
            if ch in ("е", "я") and i != self.current_stress:
                notes.append(f"{i + 1}. harf '{ch}' vurgusuz -> [i]'ye yaklasir")
        if low and low[-1] in "бвгдзж":
            notes.append(f"Son harf '{low[-1]}' sertlesir")
        if "ё" in low:
            notes.append("'ё' her zaman vurguludur")
        self.reduction.configure(text="\n".join(notes) if notes
                                 else "Bu kelimede belirgin indirgeme yok.")

    def _on_stress_pick(self) -> None:
        """Kullanici vurgulu heceyi degistirdi."""
        i = self.stress_box.current()
        if 0 <= i < len(getattr(self, "_vowel_index", [])):
            self.current_stress = self._vowel_index[i]
            self.analyze(keep_stress=True)

    def speak(self) -> None:
        """Kelimeyi seslendir."""
        self.app.speak(C.strip_stress(self.word.get()))

    def record(self) -> None:
        """Mikrofondan birkac saniye kaydet ve Whisper (yoksa Vosk) ile karsilastir."""
        target = C.normalize_ru(self.word.get())
        if not target or self.mic_out is None:
            return
        if self.asr.backend == "whisper":
            # Whisper sayfasinda model/cihaz degismis olabilir: guncel ayarlarla yeniden sec
            self.asr.whisper_opts = dict(self.app.settings.get("whisper") or {})
            if not self.asr._try_whisper():
                self._build_mic()                      # model kalmadi: bolumu durumuna gore kur
                localize = getattr(self.app, "localize_widgets", None)
                if localize is not None:
                    localize(self)
                return
        whisper = self.asr.backend == "whisper"
        self.mic_out.configure(text="Dinliyor... (3 sn)")
        self._rec_busy = True

        def job():
            if whisper:
                import re
                heard = self.asr.listen_whisper(3.0)
                return re.sub(r"[^\w\s\-]", "", heard).strip()
            return self._listen_once()

        def done(heard: str):
            self._rec_busy = False
            p = self.palette()
            if not heard:
                self.mic_out.configure(text="Ses alinamadi.", foreground=p["warn"])
                return
            if C.normalize_ru(heard) == target:
                self.mic_out.configure(text=f"✓ '{heard}' - dogru", foreground=p["ok"])
                self.repos.study.log(self.pid, "pron", 1, 0)
            else:
                self.mic_out.configure(
                    text=f"✗ duyulan: '{heard}'  ·  hedef: '{self.word.get()}'",
                    foreground=p["err"])
                self.repos.study.log(self.pid, "pron", 0, 1)

        def err(e):
            self._rec_busy = False
            self.mic_out.configure(text=f"Hata: {e}")

        self.app.worker.run(job, done, err)

    def _listen_once(self) -> str:
        """Vosk ile tek seferlik tanima (mikrofon yoksa bos metin)."""
        try:
            import json
            import sounddevice as sd            # type: ignore
            import vosk                          # type: ignore
        except Exception:
            return ""
        rec = vosk.KaldiRecognizer(self.asr.model, 16000)
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                               channels=1) as stream:
            for _ in range(6):
                data, _ = stream.read(8000)
                if rec.AcceptWaveform(bytes(data)):
                    break
        try:
            return json.loads(rec.FinalResult()).get("text", "")
        except Exception:
            return ""
