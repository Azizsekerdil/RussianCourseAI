# -*- coding: utf-8 -*-
"""Cevrimdisi seslendirme sarmalayicisi.

Sira: pyttsx3 (Windows SAPI5) -> PowerShell System.Speech (Windows)
-> `say` (macOS) -> sessiz. Hicbiri yoksa program COKMEZ; `available()`
False doner ve dugmeler gri kalir. Konusma her zaman ayri bir threadde
yapilir, arayuz kilitlenmez.

Not: pyttsx3 GPL-3.0 lisanslidir ve dagitilan `.exe` / `.app` paketlerine
BILEREK dahil edilmez (bkz. THIRD_PARTY_NOTICES.md). Bu yuzden isletim
sisteminin kendi motorlarina dusen yedek yollar birinci sinif yollardir,
yalnizca acil durum cikisi degildir.
"""
from __future__ import annotations

import queue
import shutil
import subprocess
import sys
import threading
from typing import Optional

import rca_common as C


class Speaker:
    """Rusca metni seslendirir. Motor yoksa sessizce devre disi kalir."""

    def __init__(self, rate: int = 150) -> None:
        self.rate = rate
        self.engine = None
        self.backend = "none"
        self.voice_name = ""
        self._q: "queue.Queue[Optional[str]]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._init_engine()
        if self.backend != "none":
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()

    # -- kurulum -----------------------------------------------------------
    def _init_engine(self) -> None:
        """Kullanilabilir ilk motoru sec."""
        try:
            import pyttsx3                      # type: ignore
            eng = pyttsx3.init()
            eng.setProperty("rate", self.rate)
            ru = self._pick_russian_voice(eng)
            if ru:
                eng.setProperty("voice", ru.id)
                self.voice_name = ru.name
            self.engine = eng
            self.backend = "pyttsx3"
            return
        except Exception:
            self.engine = None

        if sys.platform.startswith("win"):
            self.backend = "powershell"
            self.voice_name = "System.Speech"
        elif sys.platform == "darwin" and shutil.which("say"):
            self.backend = "say"
            self.voice_name = self._pick_macos_voice()

    @staticmethod
    def _pick_macos_voice() -> str:
        """`say -v ?` ciktisindan Rusca bir ses sec (yoksa bos dizge)."""
        try:
            done = subprocess.run(["say", "-v", "?"], capture_output=True,
                                  text=True, timeout=10)
        except Exception:
            return ""
        for line in (done.stdout or "").splitlines():
            # Bicim:  "Milena              ru_RU    # Zdravstvuyte!"
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower().startswith("ru"):
                return parts[0]
        return ""

    @staticmethod
    def _pick_russian_voice(eng) -> Optional[object]:
        """Kurulu sesler icinde Rusca olani bul."""
        try:
            for v in eng.getProperty("voices"):
                blob = f"{getattr(v, 'id', '')} {getattr(v, 'name', '')} " \
                       f"{getattr(v, 'languages', '')}".lower()
                if "ru" in blob.split() or "russ" in blob or "ru-ru" in blob or "0419" in blob:
                    return v
        except Exception:
            pass
        return None

    # -- kullanim ----------------------------------------------------------
    def available(self) -> bool:
        """Seslendirme yapilabiliyor mu?"""
        return self.backend != "none"

    def has_russian_voice(self) -> bool:
        """Sistemde Rusca ses var mi? (yoksa telaffuz yaklasik olur)"""
        return bool(self.voice_name) and self.backend in ("pyttsx3", "say")

    def say(self, text: str) -> None:
        """Metni kuyruga at (arayuzu bloklamaz)."""
        if not text or not self.available():
            return
        self._q.put(text)

    def stop(self) -> None:
        """Calisan konusmayi ve isciyi durdur."""
        try:
            while not self._q.empty():
                self._q.get_nowait()
        except Exception:
            pass
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass

    def set_rate(self, rate: int) -> None:
        """Konusma hizini degistir."""
        self.rate = int(rate)
        if self.engine is not None:
            try:
                self.engine.setProperty("rate", self.rate)
            except Exception:
                pass

    def status_text(self) -> str:
        """Ayarlar ekraninda gosterilecek durum satiri."""
        if self.backend == "none":
            return "Ses motoru bulunamadi - dinleme ozellikleri kapali."
        if self.backend == "pyttsx3" and self.voice_name:
            return f"pyttsx3 / SAPI5 - ses: {self.voice_name}"
        if self.backend == "pyttsx3":
            return "pyttsx3 / SAPI5 - Rusca ses bulunamadi, varsayilan ses kullanilacak."
        if self.backend == "say":
            if self.voice_name:
                return f"macOS `say` - ses: {self.voice_name}"
            return "macOS `say` - Rusca ses bulunamadi, varsayilan ses kullanilacak."
        return "Windows System.Speech (PowerShell) - Rusca ses varsa kullanilir."

    # -- ic dongu ----------------------------------------------------------
    def _run(self) -> None:
        """Kuyruktaki metinleri sirayla seslendiren isci thread."""
        while True:
            text = self._q.get()
            if text is None:
                break
            try:
                if self.backend == "pyttsx3" and self.engine is not None:
                    self.engine.say(text)
                    self.engine.runAndWait()
                elif self.backend == "powershell":
                    self._speak_powershell(text)
                elif self.backend == "say":
                    self._speak_say(text, self.voice_name, self.rate)
            except Exception:
                pass                        # seslendirme hatasi programi durdurmaz

    @staticmethod
    def _speak_powershell(text: str) -> None:
        """PowerShell System.Speech ile seslendir (pyttsx3 yoksa yedek yol)."""
        safe = text.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "try{$s.SelectVoiceByHints('NotSet','NotSet',0,"
            "(New-Object System.Globalization.CultureInfo('ru-RU')))}catch{};"
            f"$s.Speak('{safe}')")
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                       capture_output=True, timeout=60)

    @staticmethod
    def _speak_say(text: str, voice: str, rate: int) -> None:
        """macOS'un `say` komutuyla seslendir (pyttsx3 yoksa yedek yol).

        Metin argüman olarak degil `--` sonrasinda verilir; boylece tire ile
        baslayan bir kelime secenek sanilmaz.
        """
        cmd = ["say", "-r", str(int(rate))]
        if voice:
            cmd += ["-v", voice]
        cmd += ["--", text]
        subprocess.run(cmd, capture_output=True, timeout=60)


class ASR:
    """Cevrimdisi konusma tanima (Vosk). Model yoksa devre disi kalir."""

    def __init__(self) -> None:
        self.model = None
        self.reason = "Vosk modeli kurulu degil"
        try:
            import vosk                        # type: ignore
            model_dir = C.APP_HOME / "models" / "vosk-ru"
            if model_dir.exists():
                self.model = vosk.Model(str(model_dir))
                self.reason = ""
            else:
                self.reason = f"Vosk 'ru' modeli bulunamadi: {model_dir}"
        except ImportError:
            self.reason = "vosk paketi kurulu degil"
        except Exception as e:
            self.reason = f"Vosk yuklenemedi: {e}"

    def available(self) -> bool:
        """Tanima yapilabiliyor mu?"""
        return self.model is not None
