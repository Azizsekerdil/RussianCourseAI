# -*- coding: utf-8 -*-
"""Whisper konusma tanima motoru (faster-whisper / CTranslate2).

Bu modul arayuzden bagimsizdir; sekmeler ve testler dogrudan kullanir.

Ozellikler
----------
* Butun Whisper modelleri: tiny, base, small, medium, large-v1/v2/v3,
  large-v3-turbo, distil-* ve `.en` cesitleri (faster_whisper.available_models()).
  Modeller ilk kullanimda `%APPDATA%/RussianCourseAI/models/whisper/<ad>`
  klasorune indirilir; sonra tamamen cevrimdisi calisir.
* Aygit secimi: auto / cuda / cpu; hesap turu: float16, int8_float16,
  bfloat16, int8, float32 (aygita gore otomatik).
* Gorevler: yaziya dokme (transcribe) ve Ingilizceye ceviri (translate).
* Dil algilama: en olasi diller ve olasiliklari.
* Kod cozme ayarlari: beam_size, best_of, patience, sicaklik geri dusmesi,
  sikistirma / log-olasilik / sessizlik esikleri, onceki metne kosullama,
  baslangic istemi, onek, hotwords, tekrar cezasi, n-gram engeli, kelime
  zaman damgalari, coklu dil, kirpma araliklari, halusinasyon sessizlik esigi.
* VAD (Silero) filtresi ve parametreleri.
* Toplu (batched) cikarim - uzun dosyalarda GPU'da cok daha hizli.
* Girdi: ses/video dosyasi (PyAV ile her bicim) ya da numpy dizisi.
* Cikti bicimleri: TXT, SRT, VTT, TSV, JSON, LRC.
* Mikrofon kaydi, canli dikte (kayan pencereli), telaffuz karsilastirmasi.

Hicbir paket kurulu degilse program COKMEZ: `status()` nedenini soyler ve
ilgili dugmeler gri kalir.
"""
from __future__ import annotations

import difflib
import inspect
import json
import os
import re
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import rca_common as C

SAMPLE_RATE = 16000
MODELS_DIR = C.APP_HOME / "models" / "whisper"

#: Arayuzde gosterilen model bilgisi: ad -> (yaklasik indirme boyutu MB, not)
MODEL_INFO: Dict[str, Tuple[int, str]] = {
    "tiny": (75, "en hizli, kaba"),
    "tiny.en": (75, "yalnizca Ingilizce"),
    "base": (145, "hizli"),
    "base.en": (145, "yalnizca Ingilizce"),
    "small": (485, "Rusca icin kabul edilebilir"),
    "small.en": (485, "yalnizca Ingilizce"),
    "distil-small.en": (335, "yalnizca Ingilizce, damitilmis"),
    "medium": (1530, "iyi denge"),
    "medium.en": (1530, "yalnizca Ingilizce"),
    "distil-medium.en": (790, "yalnizca Ingilizce, damitilmis"),
    "large-v1": (3090, "eski buyuk model"),
    "large-v2": (3090, "buyuk model"),
    "large-v3": (3090, "en dogru"),
    "large": (3090, "large-v3 ile ayni"),
    "distil-large-v2": (1510, "damitilmis, cok dilli zayif"),
    "distil-large-v3": (1510, "damitilmis, Ingilizce odakli"),
    "distil-large-v3.5": (1510, "damitilmis, Ingilizce odakli"),
    "large-v3-turbo": (1620, "large'a yakin dogruluk, cok hizli; Ingilizceye ceviri YAPMAZ"),
    "turbo": (1620, "large-v3-turbo ile ayni; Ingilizceye ceviri YAPMAZ"),
}


def translation_capable(model: str) -> bool:
    """Model Ingilizceye ceviri (task=translate) yapabilir mi?

    large-v3-turbo ceviri verisi olmadan ince ayarlanmistir; distil-* ve *.en
    modelleri de ceviri yapmaz. Bunlarda translate gorevi kaynak dili geri yazar.
    """
    m = (model or "").lower()
    return not ("turbo" in m or m.startswith("distil") or m.endswith(".en"))
DEFAULT_MODEL = "large-v3-turbo"

COMPUTE_TYPES = ("auto", "float16", "int8_float16", "bfloat16", "int8", "float32")
DEVICES = ("auto", "cuda", "cpu")
TASKS = ("transcribe", "translate")
EXPORT_FORMATS = ("txt", "srt", "vtt", "tsv", "json", "lrc")

#: Whisper'in tanidigi diller (kod -> ad). Liste paket kurulu olmasa da gerekir.
LANGUAGES: Dict[str, str] = {
    "ru": "Русский", "tr": "Türkçe", "en": "English", "uk": "Українська",
    "be": "Беларуская", "kk": "Қазақша", "de": "Deutsch", "fr": "Français",
    "es": "Español", "it": "Italiano", "pt": "Português", "pl": "Polski",
    "cs": "Čeština", "bg": "Български", "sr": "Српски", "ar": "العربية",
    "fa": "فارسی", "az": "Azərbaycanca", "uz": "Oʻzbekcha", "ka": "ქართული",
    "hy": "Հայերեն", "el": "Ελληνικά", "nl": "Nederlands", "sv": "Svenska",
    "fi": "Suomi", "ja": "日本語", "zh": "中文", "ko": "한국어", "hi": "हिन्दी",
}


# ==========================================================================
# Kurulum / durum
# ==========================================================================
_DLL_DONE = False


def _setup_windows_cuda_dlls() -> None:
    """pip ile kurulan NVIDIA kutuphanelerini (cuBLAS / cuDNN) DLL yoluna ekle.

    `nvidia-cublas-cu12` ve `nvidia-cudnn-cu12` paketleri DLL'leri
    site-packages/nvidia/*/bin altina koyar; CTranslate2 bunlari PATH
    uzerinden arar. Sistemde CUDA Toolkit kurulu olmasi gerekmez.
    """
    global _DLL_DONE
    if _DLL_DONE or not sys.platform.startswith("win"):
        return
    _DLL_DONE = True
    try:
        import site
        roots = list(site.getsitepackages()) + [site.getusersitepackages()]
    except Exception:
        roots = []
    roots += [p for p in sys.path if p.endswith("site-packages")]
    seen = set()
    for root in roots:
        nv = Path(root) / "nvidia"
        if not nv.is_dir():
            continue
        for sub in nv.iterdir():
            for b in (sub / "bin", sub / "lib"):
                if b.is_dir() and str(b) not in seen:
                    seen.add(str(b))
                    try:
                        os.add_dll_directory(str(b))
                    except Exception:
                        pass
                    os.environ["PATH"] = str(b) + os.pathsep + os.environ.get("PATH", "")


def installed() -> bool:
    """faster-whisper kurulu mu?"""
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def cuda_device_count() -> int:
    """CTranslate2'nin gordugu CUDA aygiti sayisi (yoksa 0)."""
    _setup_windows_cuda_dlls()
    try:
        import ctranslate2
        return int(ctranslate2.get_cuda_device_count())
    except Exception:
        return 0


def gpu_name() -> str:
    """Ekran karti adi (nvidia-smi varsa)."""
    try:
        import subprocess
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total",
                              "--format=csv,noheader"], capture_output=True, text=True,
                             timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return (out.stdout or "").strip().splitlines()[0]
    except Exception:
        return ""


def available_models() -> List[str]:
    """Indirilebilir model adlari (paket yoksa bilinen liste)."""
    try:
        from faster_whisper import available_models as am
        names = list(am())
    except Exception:
        names = []
    for n in MODEL_INFO:
        if n not in names:
            names.append(n)
    order = list(MODEL_INFO)
    return sorted(names, key=lambda n: (order.index(n) if n in order else 99, n))


def model_dir(name: str) -> Path:
    """Modelin yerel klasoru."""
    return MODELS_DIR / name.replace("/", "__")


def is_downloaded(name: str) -> bool:
    """Model yerelde hazir mi? (model.bin + config.json)"""
    d = model_dir(name)
    return (d / "model.bin").exists() and (d / "config.json").exists()


def downloaded_models() -> List[str]:
    """Yerelde hazir olan modeller."""
    return [n for n in available_models() if is_downloaded(n)]


def download(name: str) -> Path:
    """Modeli indir (internet gerekir; bir kez yapilir)."""
    from faster_whisper.utils import download_model
    d = model_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    download_model(name, output_dir=str(d))
    return d


def delete_model(name: str) -> None:
    """Yerel model klasorunu sil."""
    import shutil
    d = model_dir(name)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def status() -> Tuple[bool, str]:
    """(kullanilabilir mi, aciklama)."""
    if not installed():
        return False, "faster-whisper kurulu degil: pip install -r requirements-audio.txt"
    n = cuda_device_count()
    have = downloaded_models()
    dev = f"GPU hazir ({gpu_name() or 'CUDA'})" if n else "GPU yok - CPU kullanilacak"
    mdl = f"indirilmis model: {', '.join(have)}" if have else "henuz model indirilmedi"
    return True, f"{dev} · {mdl}"


# ==========================================================================
# Secenekler ve sonuclar
# ==========================================================================
@dataclass
class WhisperOptions:
    """Whisper'in TUM ayarlari. Bos/None alanlar paketin varsayilanina birakilir."""
    model: str = DEFAULT_MODEL
    device: str = "auto"
    compute_type: str = "auto"
    cpu_threads: int = 0
    task: str = "transcribe"
    language: Optional[str] = None           # None = otomatik algila
    multilingual: bool = False                # her bolumde dili yeniden algila
    beam_size: int = 5
    best_of: int = 5
    patience: float = 1.0
    length_penalty: float = 1.0
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0
    temperature: Sequence[float] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    compression_ratio_threshold: Optional[float] = 2.4
    log_prob_threshold: Optional[float] = -1.0
    no_speech_threshold: Optional[float] = 0.6
    condition_on_previous_text: bool = True
    prompt_reset_on_temperature: float = 0.5
    initial_prompt: Optional[str] = None
    prefix: Optional[str] = None
    hotwords: Optional[str] = None
    suppress_blank: bool = True
    without_timestamps: bool = False
    max_initial_timestamp: float = 1.0
    word_timestamps: bool = True
    hallucination_silence_threshold: Optional[float] = None
    clip_timestamps: str = "0"
    chunk_length: Optional[int] = None
    language_detection_threshold: float = 0.5
    language_detection_segments: int = 1
    vad_filter: bool = True
    vad_threshold: float = 0.5
    vad_min_speech_duration_ms: int = 250
    vad_max_speech_duration_s: float = float("inf")
    vad_min_silence_duration_ms: int = 1000
    vad_speech_pad_ms: int = 400
    batched: bool = False
    batch_size: int = 16

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["temperature"] = list(self.temperature)
        if d["vad_max_speech_duration_s"] == float("inf"):
            d["vad_max_speech_duration_s"] = None
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WhisperOptions":
        known = {f for f in cls.__dataclass_fields__}
        clean = {k: v for k, v in (data or {}).items() if k in known}
        if clean.get("vad_max_speech_duration_s") is None:
            clean.pop("vad_max_speech_duration_s", None)
        if "temperature" in clean:
            t = clean["temperature"]
            clean["temperature"] = tuple(t) if isinstance(t, (list, tuple)) else (float(t),)
        return cls(**clean)


@dataclass
class Word:
    start: float
    end: float
    word: str
    probability: float


@dataclass
class Segment:
    id: int
    start: float
    end: float
    text: str
    avg_logprob: float = 0.0
    no_speech_prob: float = 0.0
    compression_ratio: float = 0.0
    temperature: float = 0.0
    words: List[Word] = field(default_factory=list)


@dataclass
class Transcript:
    segments: List[Segment]
    language: str = ""
    language_probability: float = 0.0
    duration: float = 0.0
    duration_after_vad: float = 0.0
    all_language_probs: List[Tuple[str, float]] = field(default_factory=list)
    model: str = ""
    device: str = ""
    elapsed: float = 0.0
    task: str = "transcribe"

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments).strip()


# ==========================================================================
# Motor
# ==========================================================================
class WhisperEngine:
    """Tek bir yuklu modeli tutar; ayni ayarla tekrar yukleme yapmaz.

    Thread guvenligi: `transcribe`, `detect_language`, `load` ve `unload` ayni
    kilidi kullanir (RLock: transcribe kilit altindayken load'u cagirabilir).
    """

    def __init__(self) -> None:
        self._model = None
        # _key: gercekte yuklenen (model, aygit, hesap, cekirdek);
        # _req_key: istenen ayar. GPU -> CPU dususunde ikisi farkli olur; onbellek
        # istenen anahtara bakar ki dusmus CPU modeli her cagrida yeniden yuklenmesin.
        self._key: Optional[Tuple[str, str, str, int]] = None
        self._req_key: Optional[Tuple[str, str, str, int]] = None
        self._lock = threading.RLock()
        self.device = ""
        self.compute_type = ""

    # -- yukleme -------------------------------------------------------------
    @staticmethod
    def resolve_device(device: str) -> str:
        if device == "auto":
            return "cuda" if cuda_device_count() > 0 else "cpu"
        return device

    @staticmethod
    def resolve_compute(device: str, compute: str) -> str:
        if compute != "auto":
            return compute
        return "float16" if device == "cuda" else "int8"

    def loaded_name(self) -> str:
        return self._key[0] if self._key else ""

    def load(self, opts: WhisperOptions, on_status: Callable[[str], None] = None):
        """Modeli (gerekirse indirip) yukle ve dondur."""
        with self._lock:
            return self._load_locked(opts, on_status)

    def _load_locked(self, opts: WhisperOptions, on_status: Callable[[str], None] = None):
        _setup_windows_cuda_dlls()
        from faster_whisper import WhisperModel
        device = self.resolve_device(opts.device)
        compute = self.resolve_compute(device, opts.compute_type)
        key = (opts.model, device, compute, int(opts.cpu_threads or 0))
        req_key = key
        if self._model is not None and self._req_key == req_key:
            return self._model
        self.unload()
        if not is_downloaded(opts.model):
            if on_status:
                on_status(f"'{opts.model}' modeli indiriliyor (~{MODEL_INFO.get(opts.model, (0, ''))[0]} MB)...")
            download(opts.model)
        if on_status:
            on_status(f"'{opts.model}' yukleniyor ({device}, {compute})...")
        try:
            model = WhisperModel(str(model_dir(opts.model)), device=device,
                                 compute_type=compute, cpu_threads=int(opts.cpu_threads or 0))
        except Exception:
            if device != "cuda":
                raise
            # GPU basarisizsa (surucu / DLL) CPU'ya dus - program durmasin.
            device, compute = "cpu", self.resolve_compute("cpu", "auto")
            if on_status:
                on_status("GPU yuklenemedi, CPU'ya geciliyor...")
            model = WhisperModel(str(model_dir(opts.model)), device=device,
                                 compute_type=compute, cpu_threads=int(opts.cpu_threads or 0))
            key = (opts.model, device, compute, int(opts.cpu_threads or 0))
        self._model, self._key, self._req_key = model, key, req_key
        self.device, self.compute_type = device, compute
        return model

    def unload(self) -> None:
        """Modeli bellekten (VRAM) bosalt."""
        with self._lock:
            self._model = None
            self._key = None
            self._req_key = None
            try:
                import gc
                gc.collect()
            except Exception:
                pass

    # -- yardimcilar ---------------------------------------------------------
    @staticmethod
    def _vad_params(opts: WhisperOptions) -> Dict[str, Any]:
        p = {"threshold": opts.vad_threshold,
             "min_speech_duration_ms": int(opts.vad_min_speech_duration_ms),
             "min_silence_duration_ms": int(opts.vad_min_silence_duration_ms),
             "speech_pad_ms": int(opts.vad_speech_pad_ms)}
        if opts.vad_max_speech_duration_s not in (None, float("inf")):
            p["max_speech_duration_s"] = float(opts.vad_max_speech_duration_s)
        return p

    @staticmethod
    def _filter_kwargs(fn, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Kurulu faster-whisper surumunun tanimadigi argumanlari ayikla."""
        try:
            params = inspect.signature(fn).parameters
        except (TypeError, ValueError):
            return kwargs
        if any(p.kind == p.VAR_KEYWORD for p in params.values()):
            return kwargs
        return {k: v for k, v in kwargs.items() if k in params}

    def build_kwargs(self, opts: WhisperOptions) -> Dict[str, Any]:
        """WhisperOptions -> model.transcribe(...) argumanlari."""
        kw: Dict[str, Any] = dict(
            language=opts.language or None,
            task=opts.task,
            beam_size=int(opts.beam_size),
            best_of=int(opts.best_of),
            patience=float(opts.patience),
            length_penalty=float(opts.length_penalty),
            repetition_penalty=float(opts.repetition_penalty),
            no_repeat_ngram_size=int(opts.no_repeat_ngram_size),
            temperature=list(opts.temperature) if len(opts.temperature) > 1 else float(opts.temperature[0]),
            compression_ratio_threshold=opts.compression_ratio_threshold,
            log_prob_threshold=opts.log_prob_threshold,
            no_speech_threshold=opts.no_speech_threshold,
            condition_on_previous_text=bool(opts.condition_on_previous_text),
            prompt_reset_on_temperature=float(opts.prompt_reset_on_temperature),
            initial_prompt=opts.initial_prompt or None,
            prefix=opts.prefix or None,
            hotwords=opts.hotwords or None,
            suppress_blank=bool(opts.suppress_blank),
            without_timestamps=bool(opts.without_timestamps),
            max_initial_timestamp=float(opts.max_initial_timestamp),
            word_timestamps=bool(opts.word_timestamps),
            multilingual=bool(opts.multilingual),
            vad_filter=bool(opts.vad_filter),
            vad_parameters=self._vad_params(opts) if opts.vad_filter else None,
            hallucination_silence_threshold=opts.hallucination_silence_threshold,
            clip_timestamps=opts.clip_timestamps or "0",
            chunk_length=opts.chunk_length,
            language_detection_threshold=float(opts.language_detection_threshold),
            language_detection_segments=int(opts.language_detection_segments),
        )
        return kw

    # -- ana isler -----------------------------------------------------------
    def transcribe(self, audio, opts: WhisperOptions,
                   on_segment: Callable[[Segment, float], None] = None,
                   on_status: Callable[[str], None] = None,
                   cancel: Optional[threading.Event] = None) -> Transcript:
        """Dosya yolu ya da 16 kHz mono float32 numpy dizisini yaziya dok.

        on_segment(segment, ilerleme_0_1) her bolum tamamlandikca cagrilir.
        cancel ayarlanirsa o ana kadarki bolumlerle doner.
        """
        with self._lock:
            model = self.load(opts, on_status)
            if isinstance(audio, (str, Path)):
                audio = str(audio)
            kwargs = self.build_kwargs(opts)
            t0 = time.time()
            if opts.batched:
                from faster_whisper import BatchedInferencePipeline
                pipe = BatchedInferencePipeline(model=model)
                kw = self._filter_kwargs(pipe.transcribe, dict(kwargs, batch_size=int(opts.batch_size)))
                # Toplu hatta clip_timestamps bir [{"start","end"}] listesi olmalidir;
                # normal hattin "0" / "10,20" metin bicimi burada gecersizdir.
                if isinstance(kw.get("clip_timestamps"), str):
                    kw.pop("clip_timestamps")
                # Toplu cikarim VAD ile bolumler; vad_filter kapaliysa clip_timestamps gerekir.
                if not opts.vad_filter and "vad_filter" in kw:
                    kw["vad_filter"] = True
                    kw["vad_parameters"] = self._vad_params(opts)
                segs_iter, info = pipe.transcribe(audio, **kw)
            else:
                kw = self._filter_kwargs(model.transcribe, kwargs)
                segs_iter, info = model.transcribe(audio, **kw)
            if on_status:
                on_status(f"Dil: {info.language} (%{info.language_probability * 100:.0f}) · "
                          f"sure {fmt_clock(info.duration)}")
            out: List[Segment] = []
            total = max(0.001, float(info.duration or 0.001))
            for s in segs_iter:
                seg = Segment(
                    id=len(out), start=float(s.start), end=float(s.end), text=s.text,
                    avg_logprob=float(getattr(s, "avg_logprob", 0.0) or 0.0),
                    no_speech_prob=float(getattr(s, "no_speech_prob", 0.0) or 0.0),
                    compression_ratio=float(getattr(s, "compression_ratio", 0.0) or 0.0),
                    temperature=float(getattr(s, "temperature", 0.0) or 0.0),
                    words=[Word(float(w.start), float(w.end), w.word, float(w.probability))
                           for w in (getattr(s, "words", None) or [])])
                out.append(seg)
                if on_segment:
                    on_segment(seg, min(1.0, seg.end / total))
                if cancel is not None and cancel.is_set():
                    break
            probs = list(getattr(info, "all_language_probs", None) or [])
            return Transcript(
                segments=out, language=info.language,
                language_probability=float(info.language_probability or 0.0),
                duration=float(info.duration or 0.0),
                duration_after_vad=float(getattr(info, "duration_after_vad", 0.0) or 0.0),
                all_language_probs=[(str(a), float(b)) for a, b in probs[:10]],
                model=opts.model, device=f"{self.device}/{self.compute_type}",
                elapsed=time.time() - t0, task=opts.task)

    def detect_language(self, audio, opts: WhisperOptions,
                        on_status: Callable[[str], None] = None) -> List[Tuple[str, float]]:
        """En olasi diller (kod, olasilik) - azalan sirada."""
        with self._lock:
            model = self.load(opts, on_status)
            if isinstance(audio, (str, Path)):
                from faster_whisper.audio import decode_audio
                audio = decode_audio(str(audio), sampling_rate=SAMPLE_RATE)
            if hasattr(model, "detect_language"):
                vad = None
                if opts.vad_filter:
                    # transcribe() sozluk kabul eder, detect_language() ise VadOptions nesnesi ister.
                    try:
                        from faster_whisper.vad import VadOptions
                        vad = VadOptions(**self._vad_params(opts))
                    except Exception:
                        vad = None
                kw = self._filter_kwargs(model.detect_language, dict(
                    audio=audio, vad_filter=bool(opts.vad_filter and vad is not None),
                    vad_parameters=vad,
                    language_detection_segments=int(opts.language_detection_segments),
                    language_detection_threshold=float(opts.language_detection_threshold)))
                _lang, _p, probs = model.detect_language(**kw)
            else:                                   # eski surumler
                _segs, info = model.transcribe(audio[: SAMPLE_RATE * 30], beam_size=1)
                probs = info.all_language_probs or [(info.language, info.language_probability)]
            return [(str(a), float(b)) for a, b in list(probs)[:10]]


# ==========================================================================
# Ses girdisi
# ==========================================================================
def load_audio(path: str):
    """Herhangi bir ses/video dosyasini 16 kHz mono float32 diziye cevir (PyAV)."""
    from faster_whisper.audio import decode_audio
    return decode_audio(str(path), sampling_rate=SAMPLE_RATE)


def mic_available() -> Tuple[bool, str]:
    """Mikrofon kaydi yapilabilir mi?"""
    try:
        import sounddevice as sd
        dev = sd.query_devices(kind="input")
        return True, str(dev.get("name", "mikrofon"))
    except ImportError:
        return False, "sounddevice kurulu degil"
    except Exception as e:                                  # noqa: BLE001
        return False, f"mikrofon bulunamadi: {e}"


class Recorder:
    """Basla/durdur mantigiyla mikrofon kaydi (16 kHz mono float32).

    `level` son blogun RMS seviyesidir (0..1) - arayuzde VU gostergesi icin.
    """

    def __init__(self, samplerate: int = SAMPLE_RATE) -> None:
        self.samplerate = samplerate
        self._chunks: List[Any] = []
        self._stream = None
        self._lock = threading.Lock()
        self.level = 0.0
        self.started_at = 0.0

    @property
    def recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        import numpy as np
        import sounddevice as sd
        if self._stream is not None:
            return
        self._chunks = []

        def cb(indata, _frames, _time, _status):
            block = indata[:, 0].copy()
            with self._lock:
                self._chunks.append(block)
            self.level = float(min(1.0, np.sqrt(np.mean(block ** 2)) * 6))

        self._stream = sd.InputStream(samplerate=self.samplerate, channels=1,
                                      dtype="float32", callback=cb, blocksize=1600)
        self._stream.start()
        self.started_at = time.time()

    def snapshot(self, last_seconds: Optional[float] = None):
        """Su ana kadar kaydedilen sesi (istege bagli son N saniye) dondur."""
        import numpy as np
        with self._lock:
            data = np.concatenate(self._chunks) if self._chunks else np.zeros(0, dtype="float32")
        if last_seconds:
            data = data[-int(last_seconds * self.samplerate):]
        return data

    def snapshot_from(self, start: int):
        """`start` orneginden sonraki sesi dondur; yalnizca gereken bloklari birlestirir.

        Canli dikte her adimda bunu cagirir: tum kaydi her seferinde kopyalamak
        uzun oturumlarda bellek/CPU yukunu surekli buyutur.
        """
        import numpy as np
        start = max(0, int(start))
        with self._lock:
            chunks = list(self._chunks)
        total = sum(len(c) for c in chunks)
        if start >= total:
            return np.zeros(0, dtype="float32")
        pos, i = total, len(chunks)
        while i > 0 and pos > start:            # sondan geriye: start'i kapsayan ilk blok
            i -= 1
            pos -= len(chunks[i])
        data = np.concatenate(chunks[i:])
        return data[start - pos:]

    def stop(self):
        """Kaydi bitir ve tum sesi dondur."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        self.level = 0.0
        return self.snapshot()

    def elapsed(self) -> float:
        return time.time() - self.started_at if self.recording else 0.0


def save_wav(path: str, audio, samplerate: int = SAMPLE_RATE) -> None:
    """float32 diziyi 16 bit WAV olarak kaydet (yalnizca stdlib)."""
    import wave
    import numpy as np
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(pcm)


class LiveDictation:
    """Canli dikte: mikrofon acikken her `step` saniyede son pencereyi yaziya doker.

    Pencere `window` saniyedir; bir cumle sessizlikle bittiginde metin
    "kesinlesir" ve pencere sifirlanir. Sonuclar on_text(kesin, gecici) ile
    bildirilir. Hafif bir yaklasimdir; gercek akis (streaming) modeli degildir.
    """

    def __init__(self, engine: WhisperEngine, opts: WhisperOptions,
                 on_text: Callable[[str, str], None],
                 on_error: Callable[[Exception], None] = None,
                 step: float = 1.2, window: float = 20.0) -> None:
        self.engine, self.opts = engine, opts
        self.on_text, self.on_error = on_text, on_error
        self.step, self.window = step, window
        self.rec = Recorder()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.committed = ""
        self._offset = 0

    def start(self) -> None:
        self.rec.start()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.rec.stop()

    def _loop(self) -> None:
        import numpy as np
        live = WhisperOptions.from_dict(dict(self.opts.to_dict(), word_timestamps=False,
                                             batched=False, condition_on_previous_text=False,
                                             beam_size=min(int(self.opts.beam_size), 3)))
        while not self._stop.wait(self.step):
            try:
                audio = self.rec.snapshot_from(self._offset)
                if len(audio) < SAMPLE_RATE * 0.6:
                    continue
                tr = self.engine.transcribe(audio.astype(np.float32), live)
                # Durdurulduysa (ornegin motor kilidinde beklerken) eski sonucu yazma:
                # metin kutusundaki daha yeni icerigi silebilir.
                if self._stop.is_set():
                    return
                text = tr.text
                tail_silent = float(np.sqrt(np.mean(audio[-SAMPLE_RATE // 2:] ** 2))) < 0.01
                too_long = len(audio) > SAMPLE_RATE * self.window
                if text and (tail_silent or too_long):
                    self.committed = (self.committed + " " + text).strip()
                    self._offset += len(audio)
                    self.on_text(self.committed, "")
                else:
                    if not text and (tail_silent or too_long):
                        # Sessizlik: pencereyi ilerlet (baslayan kelime kesilmesin diye
                        # ~0.3 sn birak); yoksa her adim buyuyen tamponu yeniden cozer.
                        self._offset += max(0, len(audio) - int(0.3 * SAMPLE_RATE))
                    self.on_text(self.committed, text)
            except Exception as e:                          # noqa: BLE001
                if self.on_error:
                    self.on_error(e)
                return


# ==========================================================================
# Telaffuz karsilastirmasi
# ==========================================================================
@dataclass
class WordScore:
    target: str              # hedef kelime ("" => fazladan soylendi)
    heard: str               # duyulan kelime ("" => atlandi)
    status: str              # ok | wrong | missing | extra
    probability: float = 0.0  # Whisper'in kelimeye guveni (0..1)


def _norm_word(w: str) -> str:
    return C.normalize_ru(w).replace(" ", "")


def compare_pronunciation(target: str, transcript: Transcript) -> Tuple[List[WordScore], float]:
    """Hedef metni duyulanla kelime kelime hizala; (kelime puanlari, %skor) dondur.

    Dogru kelimelerde Whisper'in olasiligi dusukse (<0.5) telaffuzun belirsiz
    oldugu anlasilir; arayuz bunlari sari gosterir.
    """
    # Kenardaki tire/kesme isaretleri (diyalog tiresi "- Привет") kelimeye ait degil;
    # hedef ve duyulan taraf ayni sekilde temizlenir. Ic tire ("кто-то") korunur.
    tgt = [w.strip("-'") for w in re.findall(r"[\ẃ'-]+", C.strip_stress(target or ""))]
    tgt = [w for w in tgt if w]
    heard_words: List[Tuple[str, float]] = []
    for s in transcript.segments:
        if s.words:
            heard_words += [(w.word.strip(), w.probability) for w in s.words if w.word.strip()]
        else:
            heard_words += [(w, 0.0) for w in s.text.split()]
    heard_clean = [(re.sub(r"[^\w'-]", "", w).strip("-'"), p) for w, p in heard_words]
    heard_clean = [(w, p) for w, p in heard_clean if w]
    a = [_norm_word(w) for w in tgt]
    b = [_norm_word(w) for w, _ in heard_clean]
    out: List[WordScore] = []
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                out.append(WordScore(tgt[i1 + k], heard_clean[j1 + k][0], "ok", heard_clean[j1 + k][1]))
        elif op == "replace":
            n = max(i2 - i1, j2 - j1)
            for k in range(n):
                t = tgt[i1 + k] if i1 + k < i2 else ""
                h, p = heard_clean[j1 + k] if j1 + k < j2 else ("", 0.0)
                out.append(WordScore(t, h, "wrong" if t and h else ("missing" if t else "extra"), p))
        elif op == "delete":
            out += [WordScore(tgt[k], "", "missing") for k in range(i1, i2)]
        elif op == "insert":
            out += [WordScore("", heard_clean[k][0], "extra", heard_clean[k][1]) for k in range(j1, j2)]
    n_target = max(1, len(tgt))
    good = sum(1 for w in out if w.status == "ok")
    # Benzer ama ayni olmayan kelimelere kismi puan (or. tek harf hatasi)
    partial = sum(difflib.SequenceMatcher(a=_norm_word(w.target), b=_norm_word(w.heard)).ratio()
                  for w in out if w.status == "wrong")
    extra = sum(1 for w in out if w.status == "extra")
    score = max(0.0, (good + 0.5 * partial - 0.25 * extra) / n_target) * 100
    return out, round(min(100.0, score), 1)


# ==========================================================================
# Disa aktarim
# ==========================================================================
def fmt_clock(t: float) -> str:
    t = max(0.0, float(t or 0))
    h, rem = divmod(int(t), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _ts(t: float, sep: str = ",") -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_txt(tr: Transcript) -> str:
    return "\n".join(s.text.strip() for s in tr.segments) + "\n"


def to_srt(tr: Transcript) -> str:
    out = []
    for i, s in enumerate(tr.segments, 1):
        out.append(f"{i}\n{_ts(s.start)} --> {_ts(s.end)}\n{s.text.strip()}\n")
    return "\n".join(out)


def to_vtt(tr: Transcript) -> str:
    out = ["WEBVTT", ""]
    for s in tr.segments:
        out.append(f"{_ts(s.start, '.')} --> {_ts(s.end, '.')}\n{s.text.strip()}\n")
    return "\n".join(out)


def to_tsv(tr: Transcript) -> str:
    rows = ["start\tend\ttext"]
    rows += [f"{int(s.start * 1000)}\t{int(s.end * 1000)}\t{s.text.strip()}" for s in tr.segments]
    return "\n".join(rows) + "\n"


def to_lrc(tr: Transcript) -> str:
    def lt(t: float) -> str:
        # Once santisaniyeye yuvarla, sonra bol: 119.999 -> [02:00.00] (asla [01:60.00]).
        cs = int(round(max(0.0, t) * 100))
        m, cs = divmod(cs, 6000)
        return f"[{m:02d}:{cs // 100:02d}.{cs % 100:02d}]"
    return "\n".join(f"{lt(s.start)}{s.text.strip()}" for s in tr.segments) + "\n"


def to_json(tr: Transcript) -> str:
    data = asdict(tr)
    data["text"] = tr.text
    return json.dumps(data, ensure_ascii=False, indent=2)


EXPORTERS: Dict[str, Callable[[Transcript], str]] = {
    "txt": to_txt, "srt": to_srt, "vtt": to_vtt, "tsv": to_tsv, "json": to_json, "lrc": to_lrc,
}


def export(tr: Transcript, fmt: str, path: str) -> None:
    """Transkripti istenen bicimde dosyaya yaz."""
    Path(path).write_text(EXPORTERS[fmt](tr), encoding="utf-8")


def transcript_from_json(text: str) -> Transcript:
    """to_json ciktisini geri oku (testler ve yeniden acma icin)."""
    d = json.loads(text)
    segs = [Segment(**{k: v for k, v in s.items() if k != "words"},
                    words=[Word(**w) for w in s.get("words", [])]) for s in d.get("segments", [])]
    d = {k: v for k, v in d.items() if k not in ("segments", "text")}
    d["all_language_probs"] = [tuple(x) for x in d.get("all_language_probs", [])]
    return Transcript(segments=segs, **d)


# Uygulama genelinde tek motor (VRAM'de tek model)
_ENGINE: Optional[WhisperEngine] = None


def shared_engine() -> WhisperEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = WhisperEngine()
    return _ENGINE
