# -*- coding: utf-8 -*-
"""Cevrimdisi seslendirme sarmalayicisi.

Sira: pyttsx3 (Windows SAPI5) -> PowerShell System.Speech (Windows)
-> `say` (macOS) -> sessiz. Hicbiri yoksa program COKMEZ; `available()`
False doner ve dugmeler gri kalir. Konusma her zaman ayri bir threadde
yapilir, arayuz kilitlenmez.

Istege bagli sinir agi sesleri (`engine` = "piper" | "edge"): Ayarlar'dan
secilirse kelime ve cumleler Piper (cevrimdisi) ya da Microsoft Edge
(cevrimici) sesiyle okunur. Motor ya da ses modeli yoksa sistem sesine
sessizce geri dusulur.

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
import time
from typing import Optional

import rca_common as C


class Speaker:
    """Rusca metni seslendirir. Motor yoksa sessizce devre disi kalir."""

    # Etkilesimli Edge okumasi: tek deneme + kisa zaman asimi (toplu uretimdeki
    # 4 denemelik dongu tek kelime icin ~15 sn bekletir). Hata olursa motor bir
    # sure "kapali" sayilir ve dogrudan sistem sesine gecilir.
    EDGE_TIMEOUT = 6.0
    NEURAL_COOLDOWN = 120.0

    def __init__(self, rate: int = 150, engine: str = "system",
                 voices: Optional[dict] = None) -> None:
        self.rate = rate
        self.engine = None
        self.backend = "none"
        self.voice_name = ""
        self.neural_name = "system"
        self.neural = None
        self._neural_down_until = 0.0
        self._neural_voices = voices or {}
        self._want_engine = engine
        self._q: "queue.Queue[Optional[str]]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._init_engine()
        if self.backend != "none":
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()
        self.set_engine(self._want_engine, self._neural_voices)

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

    # -- sinir agi sesleri ---------------------------------------------------
    def set_engine(self, engine: str, voices: Optional[dict] = None) -> None:
        """Konusma motorunu sec: system | piper | edge (yoksa sisteme duser)."""
        self.neural_name = engine if engine in ("piper", "edge") else "system"
        self._neural_voices = voices or {}
        self.neural = None
        self._neural_down_until = 0.0                  # yeni secim: bekleme suresi sifirlanir
        if self.neural_name == "system":
            return
        try:
            from rca import audiobook as A
            eng = A.make_engine(self.neural_name, self._neural_voices,
                                rate=max(0.5, min(2.0, self.rate / 150.0)))
            ok, _why = eng.status()
            self.neural = eng if ok else None
        except Exception:
            self.neural = None
        if self.neural is not None and self._worker is None:
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()

    def _synth_once(self, eng, text: str, lang: str):
        """Tek parca uret. Edge icin tek deneme + zaman asimi (yeniden deneme yok)."""
        from rca import audiobook as A
        if getattr(eng, "name", "") == "edge" and hasattr(eng, "_synth_async"):
            import asyncio
            data = asyncio.run(asyncio.wait_for(eng._synth_async(text, lang), self.EDGE_TIMEOUT))
            if not data:
                raise A.TTSError("bos ses dondu")
            return A.decode_to_pcm(data, eng.sample_rate)
        return eng.synth(text, lang)

    def _speak_neural(self, text: str) -> bool:
        """Sinir agi sesiyle oku. Basarisizsa False (sistem sesi devreye girer)."""
        eng = self.neural                              # set_engine baska threadden degistirebilir
        if eng is None or time.monotonic() < self._neural_down_until:
            return False
        try:
            import numpy as np
            import sounddevice as sd
            from rca import audiobook as A
        except Exception:
            return False
        try:
            parts = []
            for seg in A.split_languages(text) or [A.Seg("ru", "text", text)]:
                parts.append(self._synth_once(eng, A.speakable(seg.text), seg.lang))
                parts.append(A.silence(150, eng.sample_rate))
        except Exception:
            # Cevrimici motor ulasilamiyor: bir sure dogrudan sistem sesine gec
            if getattr(eng, "name", "") == "edge" and self.neural is eng:
                self._neural_down_until = time.monotonic() + self.NEURAL_COOLDOWN
            return False
        try:
            pcm = np.concatenate(parts) if parts else None
            if pcm is None or not len(pcm):
                return False
            sd.play(pcm, eng.sample_rate, blocking=True)
            return True
        except Exception:
            return False

    # -- kullanim ----------------------------------------------------------
    def available(self) -> bool:
        """Seslendirme yapilabiliyor mu?"""
        return self.backend != "none" or self.neural is not None

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
        if self.neural is not None:
            self.neural.rate = max(0.5, min(2.0, self.rate / 150.0))
        if self.engine is not None:
            try:
                self.engine.setProperty("rate", self.rate)
            except Exception:
                pass

    def status_text(self) -> str:
        """Ayarlar ekraninda gosterilecek durum satiri."""
        if self.neural is not None:
            v = getattr(self.neural, "voices", {}).get("ru", "")
            label = "Piper (cevrimdisi)" if self.neural_name == "piper" else "Microsoft Edge (cevrimici)"
            return f"{label} - Rusca ses: {v}"
        note = f"{self.neural_name} hazir degil, sistem sesi kullaniliyor. " \
            if self.neural_name != "system" else ""
        return note + self._system_status()

    def _system_status(self) -> str:
        """Isletim sistemi motorunun durum satiri."""
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
                if self._speak_neural(text):
                    continue
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
    """Cevrimdisi konusma tanima. Whisper (faster-whisper) varsa onu, yoksa Vosk'u kullanir.

    backend: "whisper" | "vosk" | "none"
    """

    def __init__(self, prefer: str = "whisper", whisper_opts: Optional[dict] = None) -> None:
        self.model = None
        self.backend = "none"
        self.reason = "Konusma tanima motoru yok"
        self.whisper_opts = dict(whisper_opts or {})
        if prefer == "whisper" and self._try_whisper():
            return
        self._try_vosk()
        if self.backend == "none" and prefer != "whisper":
            self._try_whisper()

    def _try_whisper(self) -> bool:
        try:
            from rca import whisper_engine as W
        except Exception:
            return False
        if not W.installed():
            self.reason = "faster-whisper kurulu degil"
            return False
        name = self.whisper_opts.get("model") or W.DEFAULT_MODEL
        have = W.downloaded_models()
        if not have:
            self.reason = "Whisper modeli indirilmedi (Konusma Tanima sayfasindan indirin)"
            return False
        if name not in have:
            name = have[0]
        self.whisper_opts["model"] = name
        self.backend = "whisper"
        self.reason = ""
        return True

    def _try_vosk(self) -> None:
        try:
            import vosk                        # type: ignore
            model_dir = C.APP_HOME / "models" / "vosk-ru"
            if model_dir.exists():
                self.model = vosk.Model(str(model_dir))
                self.backend = "vosk"
                self.reason = ""
            else:
                self.reason = f"Vosk 'ru' modeli bulunamadi: {model_dir}"
        except ImportError:
            self.reason = self.reason if "Whisper" in self.reason else "vosk paketi kurulu degil"
        except Exception as e:
            self.reason = f"Vosk yuklenemedi: {e}"

    def available(self) -> bool:
        """Tanima yapilabiliyor mu?"""
        return self.backend != "none"

    def listen_whisper(self, seconds: float = 4.0) -> str:
        """Mikrofondan `seconds` saniye kaydet ve Whisper ile Rusca yaziya dok.

        Model yerelde yoksa (silinmis / degismis) indirilen baska bir modele gecilir;
        hic yoksa acik bir hata verilir. WhisperEngine.load buradan ASLA indirme yapmaz.
        """
        from rca import whisper_engine as W
        name = self.whisper_opts.get("model") or W.DEFAULT_MODEL
        if not W.is_downloaded(name):
            have = W.downloaded_models()
            if not have:
                raise RuntimeError("Whisper modeli indirilmedi (Konusma Tanima sayfasindan indirin)")
            self.whisper_opts["model"] = have[0]
        rec = W.Recorder()
        rec.start()
        time.sleep(seconds)
        audio = rec.stop()
        opts = W.WhisperOptions.from_dict(dict(self.whisper_opts, language="ru", task="transcribe",
                                               batched=False, vad_filter=True,
                                               condition_on_previous_text=False))
        return W.shared_engine().transcribe(audio, opts).text
