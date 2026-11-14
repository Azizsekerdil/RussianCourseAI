# -*- coding: utf-8 -*-
"""Kucuk ses calar: MP3/WAV calma, duraklatma, atlama, hiz (perde korunur), ses duzeyi.

PyAV ile cozer (hiz degisimi FFmpeg `atempo` filtresiyle, perde bozulmaz),
sounddevice ile calar. Arayuz thread'i `position()` / `finished` alanlarini
periyodik olarak okur; ses thread'i arayuz cagirmaz.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

RATE = 24000
SPEEDS = (0.5, 0.6, 0.75, 0.85, 1.0, 1.15, 1.25, 1.5, 1.75, 2.0)


def available() -> tuple:
    """(calinabilir mi, aciklama)"""
    try:
        import av  # noqa: F401
    except ImportError:
        return False, "PyAV (av) kurulu degil"
    try:
        import sounddevice as sd
        sd.query_devices(kind="output")
    except ImportError:
        return False, "sounddevice kurulu degil"
    except Exception as e:                                      # noqa: BLE001
        return False, f"ses cikis aygiti yok: {e}"
    return True, ""


def decode(path: str, speed: float = 1.0, rate: int = RATE):
    """Dosyayi mono float32 diziye coz; speed != 1 ise atempo uygula."""
    import av
    import numpy as np
    out = []
    with av.open(str(path)) as c:
        stream = c.streams.audio[0]
        if abs(speed - 1.0) < 1e-3:
            res = av.AudioResampler(format="flt", layout="mono", rate=rate)
            for frame in c.decode(stream):
                out += [f.to_ndarray().reshape(-1) for f in res.resample(frame)]
            out += [f.to_ndarray().reshape(-1) for f in res.resample(None)]
        else:
            g = av.filter.Graph()
            src = g.add_abuffer(template=stream)
            chain = [src]
            s = float(speed)
            # atempo tek basina 0.5..2.0; disindaysa zincirle
            while s < 0.5:
                chain.append(g.add("atempo", "0.5")); s /= 0.5
            while s > 2.0:
                chain.append(g.add("atempo", "2.0")); s /= 2.0
            chain.append(g.add("atempo", f"{s:.4f}"))
            chain.append(g.add("aresample", str(rate)))
            chain.append(g.add("aformat", "sample_fmts=flt:channel_layouts=mono"))
            sink = g.add("abuffersink")
            chain.append(sink)
            for a, b in zip(chain, chain[1:]):
                a.link_to(b)
            g.configure()

            def drain():
                while True:
                    try:
                        f = g.pull()
                    except (av.BlockingIOError, av.EOFError):
                        return
                    out.append(f.to_ndarray().reshape(-1))
            for frame in c.decode(stream):
                g.push(frame)
                drain()
            try:
                g.push(None)
            except Exception:
                pass
            drain()
    return np.concatenate(out).astype(np.float32) if out else np.zeros(0, dtype=np.float32)


class AudioPlayer:
    """Tek dosyalik calar. Zamanlar her zaman ORIJINAL hizdaki saniyedir.

    load() / set_speed() arka plan thread'lerinde calisir ve ust uste binebilir.
    Her istek bir nesil numarasi (gen) alir; yalnizca EN SON istegin sonucu
    uygulanir, bayat cozumler atilir. Sira cagiranin thread'inde belirlensin diye
    arayuz once request_load() / request_speed() ile numara alip ise verir.
    """

    def __init__(self) -> None:
        self._pcm = None
        self._pos = 0
        self._stream = None
        self._lock = threading.Lock()
        self._stream_lock = threading.RLock()   # akis ac/kapa (tek OutputStream)
        self.path: Optional[str] = None
        self.speed = 1.0                        # _pcm'in cozuldugu (uygulanmis) hiz
        self._want_speed: Optional[float] = None    # istenen hiz (None = self.speed)
        self.volume = 1.0
        self.playing = False
        self.finished = False
        self._orig_len = 0.0
        self._gen = 0
        self._load_pending = 0                  # bekleyen son yuklemenin nesli (0 = yok)

    # -- istek sirasi -------------------------------------------------------
    @property
    def target_speed(self) -> float:
        """Istenen hiz (henuz uygulanmamis olabilir)."""
        w = self._want_speed
        return self.speed if w is None else w

    def request_load(self) -> int:
        """Yeni yukleme istegi icin nesil numarasi al (onceki istekler bayatlar)."""
        with self._lock:
            self._gen += 1
            self._load_pending = self._gen
            return self._gen

    def request_speed(self, speed: float) -> int:
        """Hiz istegini kaydet. Bekleyen bir yukleme yeni hizla cozulecekse 0 doner
        (ayrica set_speed gerekmez); aksi halde set_speed icin nesil numarasi."""
        speed = max(0.25, min(4.0, float(speed)))
        with self._lock:
            self._want_speed = speed
            if self._load_pending and self._load_pending == self._gen:
                return 0
            self._gen += 1
            return self._gen

    def is_current(self, gen: int) -> bool:
        return gen == self._gen

    # -- yukleme ------------------------------------------------------------
    def load(self, path: str, start: float = 0.0, autoplay: bool = False,
             gen: Optional[int] = None) -> Optional[float]:
        """Dosyayi yukle; toplam sureyi (sn) dondur. Istek bayatladiysa None."""
        my = self.request_load() if gen is None else gen
        try:
            with self._stream_lock:
                if my != self._gen:
                    return None
                self.stop_stream()
            while True:
                speed = self.target_speed
                pcm = decode(path, speed)
                with self._lock:
                    if my != self._gen:
                        return None
                    if abs(speed - self.target_speed) > 1e-3:
                        continue                         # cozum sirasinda hiz degisti
                    self._pcm = pcm
                    self.path = str(path)
                    self.speed = speed
                    self._orig_len = len(pcm) / RATE * speed
                    self._pos = min(int(max(0.0, start) / speed * RATE), len(pcm))
                    self.finished = False
                    self.playing = False
                    dur = self._orig_len
                break
        finally:
            with self._lock:
                if self._load_pending == my:
                    self._load_pending = 0
        if autoplay:
            with self._stream_lock:
                if my == self._gen:
                    self.play()
        return dur

    @property
    def duration(self) -> float:
        return self._orig_len

    def position(self) -> float:
        with self._lock:
            return self._pos / RATE * self.speed

    # -- denetim ------------------------------------------------------------
    def _ensure_stream(self) -> None:
        with self._stream_lock:
            if self._stream is not None:
                return
            import sounddevice as sd

            def cb(outdata, frames, _time, _status):
                with self._lock:
                    pcm = self._pcm
                    if pcm is None or not self.playing:
                        outdata.fill(0)
                        return
                    a = self._pos
                    b = min(len(pcm), a + frames)
                    n = b - a
                    outdata[:n, 0] = pcm[a:b] * self.volume
                    if n < frames:
                        outdata[n:, 0] = 0
                        self.playing = False
                        self.finished = True
                    self._pos = b

            self._stream = sd.OutputStream(samplerate=RATE, channels=1, dtype="float32",
                                           callback=cb, blocksize=1024)
            self._stream.start()

    def play(self) -> None:
        with self._lock:
            if self._pcm is None:
                return
            if self._pos >= len(self._pcm):
                self._pos = 0
            self.finished = False
            self.playing = True
        self._ensure_stream()

    def pause(self) -> None:
        self.playing = False

    def toggle(self) -> None:
        if self.playing:
            self.pause()
        else:
            self.play()

    def seek(self, seconds: float) -> None:
        with self._lock:
            if self._pcm is None:
                return
            i = int(max(0.0, seconds) / self.speed * RATE)
            self._pos = min(i, len(self._pcm))
            self.finished = False

    def skip(self, delta: float) -> None:
        self.seek(self.position() + delta)

    def set_speed(self, speed: float, gen: Optional[int] = None) -> bool:
        """Hizi degistir (konum korunur, perde bozulmaz). Uygulandiysa True;
        istek bayatladiysa / bekleyen yuklemeye devredildiyse False."""
        speed = max(0.25, min(4.0, float(speed)))
        my = self.request_speed(speed) if gen is None else gen
        if not my:
            return False
        with self._lock:
            if my != self._gen:
                return False
            path = self.path
            if path is None or self._pcm is None:
                self.speed = speed                       # yuklu ses yok: yalnizca kaydet
                return True
            if abs(speed - self.speed) < 1e-3:
                return True
        try:
            pcm = decode(path, speed)
        except Exception:
            with self._lock:
                if my != self._gen:
                    return False
                self._want_speed = None                  # istenen hiz = uygulanmis hiz
            raise
        with self._lock:
            if my != self._gen or self.path != path:
                return False
            # konum uygulama aninda eski hizla hesaplanir (cozum sirasinda calma surer)
            pos = self._pos / RATE * self.speed
            self._pcm = pcm
            self.speed = speed
            self._orig_len = len(pcm) / RATE * speed
            self._pos = min(int(max(0.0, pos) / speed * RATE), len(pcm))
        return True

    def set_volume(self, v: float) -> None:
        self.volume = max(0.0, min(2.0, float(v)))

    def stop(self) -> None:
        self.playing = False
        self.seek(0)

    def stop_stream(self) -> None:
        self.playing = False
        with self._stream_lock:
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

    def unload(self) -> None:
        """Calari bosalt: bekleyen yuklemeler atilir, dosya / konum sifirlanir."""
        with self._lock:
            self._gen += 1
            self._load_pending = 0
        self.stop_stream()
        with self._lock:
            self._pcm = None
            self.path = None
            self._pos = 0
            self._orig_len = 0.0
            self.finished = False

    def close(self) -> None:
        with self._lock:
            self._gen += 1                               # bekleyen yuklemeler akis acmasin
            self._load_pending = 0
        self.stop_stream()
        self._pcm = None


def play_pcm_blocking(pcm_int16, rate: int) -> None:
    """Kisa bir sesi calip bitmesini bekle (kelime seslendirme icin)."""
    import numpy as np
    import sounddevice as sd
    sd.play(pcm_int16.astype(np.int16), rate, blocking=True)
