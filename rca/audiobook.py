# -*- coding: utf-8 -*-
"""Sesli kitap motoru: PDF / seslendirme betigi -> sayfa sayfa MP3.

Kavramlar
---------
* **Kitap** (`Book`): `%APPDATA%/RussianCourseAI/audiobooks/<kimlik>/` klasoru.
  `book.json` (baslik, kaynak PDF, icindekiler, sayfa sayisi) ve
  `script/pNNN.json` seslendirme betigi burada durur.
* **Betik**: her sayfa icin dil etiketli parcalar
  `{"lang": "ru|tr|en", "kind": "heading|text|term|gloss|example|note", "text": "..."}`.
  Elle hazirlanmis bir betik ice aktarilabilir; yoksa PDF'in metin katmanindan
  sezgisel olarak uretilir (Kiril -> ru, Turkce harf/kelime -> tr, digeri -> en).
* **Motorlar**: Piper (cevrimdisi, varsayilan) ve Microsoft Edge sinir aglari
  (cevrimici). Her parca kendi dilinin sesiyle okunur.
* **Ses**: `<kitap>/<motor>/pages/pNNN.mp3` + `pNNN.json` (parca zaman cizelgesi).
  Ayni betik + ayni ses + ayni hiz icin tekrar uretim yapilmaz (karma kontrolu).
* **Disa aktarim**: bolum bolum MP3 (ID3 etiketli) + M3U8 calma listesi.

Arayuzden bagimsizdir; uzun isler `cancel` olayi ve ilerleme geri cagrisi alir.
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import json
import re
import shutil
import threading
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import rca_common as C

AUDIOBOOK_DIR = C.APP_HOME / "audiobooks"
PIPER_DIR = C.APP_HOME / "models" / "piper"
_DOWNLOAD_LOCK = threading.Lock()  # ayni surecteki es zamanli ses indirmelerini sirala
SR = 24000                       # varsayilan ornekleme (Edge); Piper 22050 Hz kullanir
ENGINE_RATE = {"piper": 22050, "edge": 24000}
LANGS = ("ru", "tr", "en")
KINDS = ("heading", "text", "term", "gloss", "example", "note")
ENGINES = ("piper", "edge")

#: parca turune gore parcadan SONRA birakilan sessizlik (ms)
PAUSE_AFTER = {"heading": 750, "text": 420, "term": 300, "gloss": 650,
               "example": 520, "note": 480}
LANG_SWITCH_PAD = 120            # dil degisiminde ek sessizlik (ms)
PAGE_LEAD = 250                  # sayfa basinda sessizlik (ms)

LANG_NAMES = {"ru": "Rusça", "tr": "Türkçe", "en": "İngilizce"}

# --------------------------------------------------------------------------
# Ses kataloglari
# --------------------------------------------------------------------------
#: Piper sesleri (Hugging Face rhasspy/piper-voices). Ilk eleman varsayilandir.
PIPER_VOICES: Dict[str, List[str]] = {
    "ru": ["ru_RU-irina-medium", "ru_RU-dmitri-medium", "ru_RU-denis-medium", "ru_RU-ruslan-medium"],
    "tr": ["tr_TR-dfki-medium"],
    "en": ["en_US-lessac-medium", "en_US-ryan-high", "en_US-amy-medium", "en_GB-alba-medium"],
}
#: Microsoft Edge sinir agi sesleri. Ilk eleman varsayilandir.
EDGE_VOICES: Dict[str, List[str]] = {
    "ru": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"],
    "tr": ["tr-TR-EmelNeural", "tr-TR-AhmetNeural"],
    "en": ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural", "en-GB-SoniaNeural",
           "en-GB-RyanNeural"],
}


def default_voices(engine: str) -> Dict[str, str]:
    cat = PIPER_VOICES if engine == "piper" else EDGE_VOICES
    return {lang: voices[0] for lang, voices in cat.items()}


# ==========================================================================
# Betik
# ==========================================================================
@dataclass
class Seg:
    lang: str
    kind: str
    text: str

    def to_dict(self) -> Dict[str, str]:
        return {"lang": self.lang, "kind": self.kind, "text": self.text}


@dataclass
class TocEntry:
    level: int
    title: str
    page: int                                   # 1 tabanli


@dataclass
class Section:
    """Icindekilerden turetilen calinabilir parca: [first, last] sayfa araligi."""
    index: int
    level: int
    title: str
    first: int
    last: int
    children: List["Section"] = field(default_factory=list)

    @property
    def pages(self) -> List[int]:
        return list(range(self.first, self.last + 1))


TR_CHARS = set("çğıöşüÇĞİÖŞÜâîûÂÎÛ")
TR_WORDS = set("""ve bir bu da de ile için gibi çok daha ama veya ya ne kim nasıl neden nerede hangi
olarak olan sayfa kelime cümle önce sonra her şey çalış oku yaz dinle bölüm alıştırma cevap örnek
not hâl isim fiil sıfat sayı zaman türkçe rusça ingilizce kitap kaynak""".split())
EN_WORDS = set("""the and of to a in is for on with as by an be are this that it or from at you
your not have has can will which their they we he she his her its was were been there what how
when where who why to""".split())


def guess_latin_lang(text: str) -> str:
    """Latin harfli metin Turkce mi Ingilizce mi?"""
    if any(ch in TR_CHARS for ch in text):
        return "tr"
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return "en"
    tr = sum(w in TR_WORDS for w in words)
    en = sum(w in EN_WORDS for w in words)
    return "tr" if tr > en else "en"


_RUN = re.compile(r"([Ѐ-ӿ́][Ѐ-ӿ́\s\-–—,.;:!?«»\"'()0-9]*)")


def split_languages(text: str, kind: str = "text") -> List[Seg]:
    """Karisik metni dil parcalarina bol (Kiril kosulari ru, gerisi tr/en)."""
    out: List[Seg] = []
    pos = 0
    text = re.sub(r"\s+", " ", text).strip()
    for m in _RUN.finditer(text):
        before = text[pos:m.start()].strip(" ,;:-–—")
        if re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", before):
            out.append(Seg(guess_latin_lang(before), kind, before))
        ru = m.group(1).strip(" ,;:-–—(")
        if ru:
            out.append(Seg("ru", kind, ru))
        pos = m.end()
    tail = text[pos:].strip(" ,;:-–—")
    if re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]", tail):
        out.append(Seg(guess_latin_lang(tail), kind, tail))
    # Ayni dildeki komsu kucuk parcalari birlestir
    merged: List[Seg] = []
    for s in out:
        if merged and merged[-1].lang == s.lang and len(merged[-1].text) + len(s.text) < 380:
            merged[-1].text += " " + s.text
        else:
            merged.append(s)
    return merged


_FURNITURE = re.compile(r"^\s*(\d+\s*/\s*\d+|\d+|.{0,60}\s\d+\s*/\s*\d+)\s*$")


def heuristic_page_script(text: str) -> List[Seg]:
    """PDF metin katmanindan kaba bir betik uret (elle hazirlanmis betik yoksa)."""
    segs: List[Seg] = []
    para: List[str] = []

    def flush():
        if para:
            joined = " ".join(para)
            joined = re.sub(r"\[[^\]]{1,24}\]", " ", joined)          # transkripsiyonlar
            segs.extend(split_languages(joined))
            para.clear()

    for line in (text or "").splitlines():
        line = line.strip()
        if not line or _FURNITURE.match(line):
            flush()
            continue
        para.append(line)
        if re.search(r"[.!?:]$", line):
            flush()
    flush()
    for s in segs:
        if s.text.isupper() and len(s.text) > 3:
            s.text = s.text.capitalize() if s.lang != "tr" else s.text.replace("I", "ı").replace("İ", "i").capitalize()
    return [s for s in segs if s.text.strip()]


# ==========================================================================
# Kitap deposu
# ==========================================================================
_TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")


#: Kiril -> Latin (kimlikler okunur kalsin; yoksa her Kiril baslik "kitap" olurdu)
_RU_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh",
    "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}
_RU_LATIN.update({k.upper(): v.capitalize() for k, v in _RU_LATIN.items()})
_RU_ASCII = str.maketrans(_RU_LATIN)


def _slug_ascii(name: str, translit: bool) -> str:
    if translit:
        name = name.translate(_RU_ASCII)
    s = unicodedata.normalize("NFKD", name.translate(_TR_ASCII)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "kitap"


def slugify(name: str) -> str:
    return _slug_ascii(name, True)


def _same_path(a: str, b: str) -> bool:
    if not a or not b:
        return False
    import os
    norm = lambda p: os.path.normcase(os.path.abspath(str(p)))     # noqa: E731
    return norm(a) == norm(b)


def _book_root(title: str, pdf_path: str) -> Path:
    """Kitap klasorunu sec: ayni PDF'in var olan klasoru yeniden kullanilir; baska bir
    PDF'e ait klasor asla ezilmez (cakismada -2, -3 ... eki)."""
    bases = []
    for b in (slugify(title), _slug_ascii(title, False)):    # eski (Kirilsiz) kimlik de denenir
        if b not in bases:
            bases.append(b)

    def chain(base):
        yield AUDIOBOOK_DIR / base
        for n in range(2, 1000):
            yield AUDIOBOOK_DIR / f"{base}-{n}"

    def owner(root: Path) -> Optional[str]:
        """Klasordeki kitabin kaynak PDF'i; kitap yoksa None."""
        if not (root / "book.json").exists():
            return None
        try:
            return str(json.loads((root / "book.json").read_text(encoding="utf-8")).get("source_pdf") or "")
        except Exception:
            return ""
    # 1) ayni PDF'ten olusturulmus kitap varsa onu kullan
    if AUDIOBOOK_DIR.exists():
        pats = [re.compile(re.escape(b) + r"(-\d+)?") for b in bases]
        for root in sorted(AUDIOBOOK_DIR.iterdir()):
            if any(p.fullmatch(root.name) for p in pats):
                src = owner(root)
                if src is not None and _same_path(src, pdf_path):
                    return root
    # 2) yoksa ilk bos klasor (book.json'u olmayan)
    for root in chain(bases[0]):
        if owner(root) is None:
            return root
    raise RuntimeError("kitap klasoru secilemedi")


class Book:
    """Diskteki bir sesli kitap."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.meta: Dict[str, Any] = json.loads((self.root / "book.json").read_text(encoding="utf-8"))
        self._scripts: Dict[int, List[Seg]] = {}

    # -- kimlik --------------------------------------------------------------
    @property
    def id(self) -> str:
        return self.root.name

    @property
    def title(self) -> str:
        return self.meta.get("title", self.id)

    @property
    def page_count(self) -> int:
        return int(self.meta.get("pages", 0))

    @property
    def source_pdf(self) -> str:
        return self.meta.get("source_pdf", "")

    @property
    def toc(self) -> List[TocEntry]:
        return [TocEntry(int(t["level"]), t["title"], int(t["page"])) for t in self.meta.get("toc", [])]

    # -- betik ---------------------------------------------------------------
    def script_path(self, page: int) -> Path:
        return self.root / "script" / f"p{page:03d}.json"

    def script(self, page: int) -> List[Seg]:
        if page not in self._scripts:
            p = self.script_path(page)
            segs: List[Seg] = []
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                for s in data.get("segments", []):
                    lang = s.get("lang") if s.get("lang") in LANGS else "tr"
                    kind = s.get("kind") if s.get("kind") in KINDS else "text"
                    text = (s.get("text") or "").strip()
                    if text:
                        segs.append(Seg(lang, kind, text))
            self._scripts[page] = segs
        return self._scripts[page]

    def script_source(self) -> str:
        return self.meta.get("script_source", "heuristic")

    # -- bolumler ------------------------------------------------------------
    def sections(self) -> List[Section]:
        """Icindekilerden agac: her girdi bir sonraki ayni/ust seviye girdiye kadar surer."""
        # Yalnizca sayfaya gore KARARLI siralama: PDF anahat sirasi zaten belge sirasidir.
        # (page, level) ile siralamak ayni sayfada baslayan yeni bolumu, onceki bolumun
        # son dersinin onune alip dersi yanlis bolume ve yanlis araliga koyuyordu.
        toc = sorted(self.toc, key=lambda t: t.page)
        n = self.page_count
        flat: List[Section] = []
        for i, t in enumerate(toc):
            end = n
            for u in toc[i + 1:]:
                if u.level <= t.level and u.page > t.page:
                    end = u.page - 1
                    break
                if u.level <= t.level and u.page == t.page:
                    end = u.page
                    break
            flat.append(Section(i, t.level, t.title, t.page, max(t.page, end)))
        if not flat:
            return [Section(0, 0, self.title, 1, n)]
        # Ilk girdiden onceki sayfalar (kapak vb.)
        if flat[0].first > 1:
            flat.insert(0, Section(-1, flat[0].level, "Kapak ve içindekiler", 1, flat[0].first - 1))
        roots: List[Section] = []
        stack: List[Section] = []
        for s in flat:
            while stack and stack[-1].level >= s.level:
                stack.pop()
            (stack[-1].children if stack else roots).append(s)
            stack.append(s)
        return roots

    def flat_sections(self) -> List[Section]:
        out: List[Section] = []

        def walk(items):
            for s in items:
                out.append(s)
                walk(s.children)
        walk(self.sections())
        return out

    def section_of(self, page: int) -> str:
        """Sayfanin ait oldugu en derin bolum basligi."""
        best = ""
        for s in self.flat_sections():
            if s.first <= page <= s.last:
                best = s.title
        return best

    def top_sections(self) -> List[Section]:
        """Disa aktarim icin ust seviye bolumler (sayfalari ortusmez).

        Ayni sayfada baslayan kardes kokler (A [3,3] ve B [3,5] gibi) tek bolumde
        birlestirilir ("A / B", [3,5]); aksi halde ortak sayfa iki dosyaya yazilirdi.
        """
        out: List[Section] = []
        for s in self.sections():
            if out and s.first <= out[-1].last:
                prev = out[-1]
                out[-1] = Section(prev.index, prev.level, f"{prev.title} / {s.title}",
                                  prev.first, max(prev.last, s.last), prev.children + s.children)
            else:
                out.append(s)
        return out

    # -- ses yollari ---------------------------------------------------------
    def audio_dir(self, engine: str) -> Path:
        return self.root / engine / "pages"

    def page_audio(self, engine: str, page: int) -> Path:
        return self.audio_dir(engine) / f"p{page:03d}.mp3"

    def page_timing(self, engine: str, page: int) -> Path:
        return self.audio_dir(engine) / f"p{page:03d}.json"

    def has_audio(self, engine: str, page: int) -> bool:
        return self.page_audio(engine, page).exists() and self.page_timing(engine, page).exists()

    def timings(self, engine: str, page: int) -> List[Dict[str, Any]]:
        p = self.page_timing(engine, page)
        if not p.exists():
            return []
        return json.loads(p.read_text(encoding="utf-8")).get("segments", [])

    def export_dir(self, engine: str) -> Path:
        return self.root / engine / "bolumler"


def list_books() -> List[Book]:
    out = []
    if AUDIOBOOK_DIR.exists():
        for d in sorted(AUDIOBOOK_DIR.iterdir()):
            if (d / "book.json").exists():
                try:
                    out.append(Book(d))
                except Exception:
                    pass
    return out


def create_book(pdf_path: str, title: str = "", script_dir: Optional[str] = None,
                on_progress: Callable[[str, float], None] = None) -> Book:
    """PDF'ten kitap olustur. `script_dir` verilirse hazir betik (pNNN.json) kopyalanir,
    eksik sayfalar PDF metninden sezgisel olarak doldurulur."""
    import pypdfium2 as pdfium
    pdf_path = str(pdf_path)
    doc = pdfium.PdfDocument(pdf_path)
    try:
        title = title or Path(pdf_path).stem.replace("_", " ")
        root = _book_root(title, pdf_path)
        (root / "script").mkdir(parents=True, exist_ok=True)
        toc = []
        try:
            for t in doc.get_toc():
                dest = t.get_dest()
                if dest is not None and dest.get_index() is not None:
                    # ic satir sonu / sekme gibi kontrol karakterleri tek bosluga iner
                    toc.append({"level": int(t.level), "title": " ".join(t.get_title().split()),
                                "page": int(dest.get_index()) + 1})
        except Exception:
            toc = []
        n = len(doc)
        src_dir = Path(script_dir) if script_dir else None
        imported = 0
        for i in range(n):
            page = i + 1
            target = root / "script" / f"p{page:03d}.json"
            src = src_dir / f"p{page:03d}.json" if src_dir else None
            if src is not None and src.exists():
                shutil.copyfile(src, target)
                imported += 1
            elif not target.exists():
                text = doc[i].get_textpage().get_text_range()
                segs = heuristic_page_script(text)
                target.write_text(json.dumps({"page": page, "segments": [s.to_dict() for s in segs]},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
            if on_progress:
                on_progress(f"Sayfa {page}/{n}", page / n)
        meta = {"title": title, "source_pdf": pdf_path, "pages": n, "toc": toc,
                "script_source": "curated" if imported == n else ("mixed" if imported else "heuristic")}
        (root / "book.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        return Book(root)
    finally:
        doc.close()


# ==========================================================================
# Ses yardimcilari (PyAV + numpy)
# ==========================================================================
def _np():
    import numpy as np
    return np


def silence(ms: int, sr: int = SR):
    np = _np()
    return np.zeros(int(sr * ms / 1000), dtype=np.int16)


def decode_to_pcm(data_or_path, rate: int = SR):
    """MP3/WAV bayt ya da dosya -> mono int16 numpy (rate Hz).

    Kaynak zaten istenen orneklemede ve monoysa yeniden ornekleyici kurulmaz
    (PyAV'in AudioResampler'i kisa parcalarda pahalidir).
    """
    import av
    np = _np()
    src = io.BytesIO(data_or_path) if isinstance(data_or_path, (bytes, bytearray)) else str(data_or_path)
    chunks = []
    with av.open(src) as c:
        stream = c.streams.audio[0]
        direct = int(stream.rate or 0) == rate and int(getattr(stream, "channels", 1) or 1) == 1
        res = None if direct else av.AudioResampler(format="s16", layout="mono", rate=rate)
        for frame in c.decode(stream):
            if res is None:
                arr = frame.to_ndarray().reshape(-1)
                if arr.dtype.kind == "f":
                    arr = np.clip(arr * 32767.0, -32768, 32767)
                chunks.append(arr.astype(np.int16))
            else:
                for f in res.resample(frame):
                    chunks.append(f.to_ndarray().reshape(-1))
        if res is not None:
            for f in res.resample(None):
                chunks.append(f.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.int16) if chunks else np.zeros(0, dtype=np.int16)


def resample_int16(pcm, src_rate: int, dst_rate: int = SR):
    """Hizli dogrusal yeniden ornekleme (yalnizca nadiren, ses hizi farkliysa kullanilir).

    Not: PyAV'in AudioResampler'i her cagrida filtre kurdugu icin kisa parcalarda
    cok yavastir; motorlar bu yuzden kendi dogal orneklemesinde calisir.
    """
    np = _np()
    if src_rate == dst_rate or len(pcm) == 0:
        return pcm
    n = int(round(len(pcm) * dst_rate / src_rate))
    x = np.linspace(0, len(pcm) - 1, n)
    return np.interp(x, np.arange(len(pcm)), pcm.astype(np.float32)).astype(np.int16)


def trim_silence(pcm, threshold: int = 300, keep_ms: int = 40, sr: int = SR):
    """Bas/son sessizligi kirp (TTS motorlari farkli bosluk birakir)."""
    np = _np()
    if len(pcm) == 0:
        return pcm
    idx = np.where(np.abs(pcm) > threshold)[0]
    if len(idx) == 0:
        return pcm[:0]
    keep = int(sr * keep_ms / 1000)
    return pcm[max(0, idx[0] - keep): min(len(pcm), idx[-1] + keep)]


def encode_mp3(pcm, path: Path, bitrate: int = 64000, tags: Dict[str, str] = None,
               sr: int = SR) -> None:
    import av
    np = _np()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.mp3")
    with av.open(str(tmp), "w") as out:
        for k, v in (tags or {}).items():
            out.metadata[k] = str(v)
        st = out.add_stream("libmp3lame", rate=sr)
        st.layout = "mono"
        st.bit_rate = bitrate
        step = sr * 10
        for i in range(0, max(1, len(pcm)), step):
            block = pcm[i:i + step]
            if len(block) == 0:
                break
            fr = av.AudioFrame.from_ndarray(block.reshape(1, -1).astype(np.int16), format="s16", layout="mono")
            fr.sample_rate = sr
            for p in st.encode(fr):
                out.mux(p)
        for p in st.encode(None):
            out.mux(p)
    tmp.replace(path)


def speakable(text: str) -> str:
    """TTS icin son temizlik: vurgu isareti, gereksiz semboller."""
    t = unicodedata.normalize("NFC", text).replace(C.STRESS_MARK, "")
    t = t.replace("…", "...").replace("___", "...").replace("•", " ")
    return re.sub(r"\s+", " ", t).strip()


# ==========================================================================
# TTS motorlari
# ==========================================================================
class TTSError(RuntimeError):
    pass


class PiperTTS:
    """Cevrimdisi Piper motoru. Ses modelleri PIPER_DIR altinda (*.onnx + *.onnx.json)."""

    name = "piper"
    sample_rate = ENGINE_RATE["piper"]

    def __init__(self, voices: Dict[str, str] = None, rate: float = 1.0, use_cuda: bool = False,
                 threads: int = 0) -> None:
        self.voices = dict(default_voices("piper"), **(voices or {}))
        self.rate = float(rate or 1.0)
        self.use_cuda = use_cuda
        self.threads = int(threads or 0)             # 0 = onnxruntime varsayilani (tum cekirdekler)
        self._loaded: Dict[str, Any] = {}

    @staticmethod
    def installed() -> bool:
        try:
            import piper  # noqa: F401
            return True
        except Exception:
            return False

    @staticmethod
    def installed_voices() -> List[str]:
        if not PIPER_DIR.exists():
            return []
        return sorted(p.name[:-5] for p in PIPER_DIR.glob("*.onnx") if (PIPER_DIR / (p.name + ".json")).exists())

    @staticmethod
    def download_voice(voice: str) -> None:
        """Hugging Face'ten ses modelini indir (internet gerekir).

        Atomik: once PIPER_DIR altinda gecici klasore indirilir, sonra once .onnx.json,
        en son .onnx yerine tasinir. Yarim kalan indirme (kapatma, ag kopmasi) asla
        PIPER_DIR'de "var" gorunen bozuk bir model birakmaz.
        """
        import os
        import tempfile
        voice = voice.strip()
        PIPER_DIR.mkdir(parents=True, exist_ok=True)
        with _DOWNLOAD_LOCK:
            tmp = Path(tempfile.mkdtemp(prefix=".indir-", dir=str(PIPER_DIR)))
            try:
                try:
                    from piper.download_voices import download_voice
                    download_voice(voice, tmp)
                except ImportError:
                    import subprocess
                    import sys
                    subprocess.run([sys.executable, "-m", "piper.download_voices", voice,
                                    "--data-dir", str(tmp)], check=True, capture_output=True,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                model, cfg = tmp / f"{voice}.onnx", tmp / f"{voice}.onnx.json"
                if not (model.exists() and model.stat().st_size and cfg.exists() and cfg.stat().st_size):
                    raise TTSError(f"ses modeli indirilemedi: {voice}")
                os.replace(cfg, PIPER_DIR / cfg.name)
                os.replace(model, PIPER_DIR / model.name)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def missing_voices(self) -> List[str]:
        have = set(self.installed_voices())
        return [v for v in self.voices.values() if v not in have]

    def status(self) -> Tuple[bool, str]:
        if not self.installed():
            return False, "piper-tts kurulu degil: pip install piper-tts (GPL-3.0, istege bagli)"
        miss = self.missing_voices()
        if miss:
            return False, "eksik ses modelleri: " + ", ".join(miss)
        return True, "Piper hazir: " + ", ".join(f"{k}={v}" for k, v in self.voices.items())

    def _voice(self, lang: str):
        name = self.voices.get(lang) or default_voices("piper")[lang]
        if name not in self._loaded:
            from piper import PiperVoice
            model = PIPER_DIR / f"{name}.onnx"
            # Model ancak .onnx ve .onnx.json birlikte varsa kurulu sayilir
            if not (model.exists() and Path(f"{model}.json").exists()):
                self.download_voice(name)
            try:
                voice = self._load_voice(PiperVoice, model)
            except Exception as load_err:
                # Eski (atomik olmayan) indirmeden kalmis yarim dosya olabilir: bir kez
                # yeniden indir (atomik; basarisizsa dosyalara dokunulmaz) ve tekrar dene.
                try:
                    self.download_voice(name)
                except Exception:
                    raise load_err
                voice = self._load_voice(PiperVoice, model)
            self._loaded[name] = voice
        return self._loaded[name]

    def _load_voice(self, PiperVoice, model: Path):
        """Sesi yukle; paralel uretimde ONNX is parcacigi sayisini sinirla."""
        if self.threads:
            try:
                import importlib

                import onnxruntime
                from piper.config import PiperConfig
                # Modul adi bilerek parcali: lisans kapisi pakette "piper" + ".voice"
                # izini arar; kendi kaynagimiz o izi tasimamali (bkz. test_licenses).
                ESPEAK_DATA_DIR = importlib.import_module("piper" + "." + "voice").ESPEAK_DATA_DIR
                so = onnxruntime.SessionOptions()
                so.intra_op_num_threads = int(self.threads)
                so.inter_op_num_threads = 1
                cfg = json.loads(Path(f"{model}.json").read_text(encoding="utf-8"))
                return PiperVoice(config=PiperConfig.from_dict(cfg),
                                  session=onnxruntime.InferenceSession(
                                      str(model), sess_options=so, providers=["CPUExecutionProvider"]),
                                  espeak_data_dir=Path(ESPEAK_DATA_DIR), download_dir=PIPER_DIR)
            except Exception:
                pass                                         # API degistiyse standart yukleme
        return PiperVoice.load(str(model), use_cuda=self.use_cuda)

    def synth(self, text: str, lang: str):
        np = _np()
        voice = self._voice(lang)
        try:
            from piper import SynthesisConfig
            cfg = SynthesisConfig(length_scale=1.0 / max(0.3, self.rate))
            chunks = list(voice.synthesize(text, syn_config=cfg))
        except ImportError:                                 # eski API
            chunks = list(voice.synthesize(text))
        if not chunks:
            return np.zeros(0, dtype=np.int16)
        sr = int(getattr(chunks[0], "sample_rate", 22050))
        pcm = np.concatenate([np.frombuffer(c.audio_int16_bytes, dtype=np.int16) for c in chunks])
        return resample_int16(pcm, sr, self.sample_rate)


class EdgeTTS:
    """Microsoft Edge cevrimici sinir agi sesleri (edge-tts paketi; internet gerekir)."""

    name = "edge"
    sample_rate = ENGINE_RATE["edge"]

    def __init__(self, voices: Dict[str, str] = None, rate: float = 1.0) -> None:
        self.voices = dict(default_voices("edge"), **(voices or {}))
        self.rate = float(rate or 1.0)

    @staticmethod
    def installed() -> bool:
        try:
            import edge_tts  # noqa: F401
            return True
        except Exception:
            return False

    def status(self) -> Tuple[bool, str]:
        if not self.installed():
            return False, "edge-tts kurulu degil: pip install edge-tts (LGPL-3.0, istege bagli)"
        return True, "Edge (cevrimici): " + ", ".join(f"{k}={v}" for k, v in self.voices.items())

    def _rate_str(self) -> str:
        pct = int(round((self.rate - 1.0) * 100))
        return f"{pct:+d}%"

    async def _synth_async(self, text: str, lang: str) -> bytes:
        from edge_tts import Communicate     # (lisans kapisi "edge_tts" + ".communicate" izini arar)
        com = Communicate(text, self.voices.get(lang) or EDGE_VOICES[lang][0], rate=self._rate_str())
        buf = bytearray()
        async for chunk in com.stream():
            if chunk.get("type") == "audio":
                buf += chunk["data"]
        return bytes(buf)

    def synth(self, text: str, lang: str):
        last = None
        for attempt in range(4):
            try:
                data = asyncio.run(self._synth_async(text, lang))
                if data:
                    return decode_to_pcm(data, self.sample_rate)
                last = TTSError("bos ses dondu")
            except Exception as e:                          # noqa: BLE001
                last = e
            import time
            time.sleep(1.5 * (attempt + 1))
        raise TTSError(f"Edge TTS basarisiz: {last}")

    def synth_many(self, items: Sequence[Tuple[str, str]], concurrency: int = 6) -> List[Any]:
        """Bir sayfanin parcalarini eszamanli uret (ag gecikmesini gizler)."""
        async def run_all():
            sem = asyncio.Semaphore(concurrency)

            async def one(text, lang):
                async with sem:
                    last = None
                    for attempt in range(4):
                        try:
                            data = await self._synth_async(text, lang)
                            if data:
                                return data
                        except Exception as e:              # noqa: BLE001
                            last = e
                        await asyncio.sleep(1.5 * (attempt + 1))
                    raise TTSError(f"Edge TTS basarisiz: {last}")
            return await asyncio.gather(*(one(t, l) for t, l in items))
        datas = asyncio.run(run_all())
        return [decode_to_pcm(d, self.sample_rate) for d in datas]


def make_engine(engine: str, voices: Dict[str, str] = None, rate: float = 1.0):
    if engine == "edge":
        return EdgeTTS(voices, rate)
    return PiperTTS(voices, rate)


# ==========================================================================
# Uretim
# ==========================================================================
def _fingerprint(segs: Sequence[Seg], engine) -> str:
    h = hashlib.sha1()
    h.update(json.dumps([s.to_dict() for s in segs], ensure_ascii=False).encode())
    h.update(json.dumps({"e": engine.name, "v": engine.voices, "r": engine.rate,
                         "p": PAUSE_AFTER, "fmt": 2}, sort_keys=True).encode())
    return h.hexdigest()


def page_is_current(book: Book, engine, page: int) -> bool:
    if not book.has_audio(engine.name, page):
        return False
    try:
        meta = json.loads(book.page_timing(engine.name, page).read_text(encoding="utf-8"))
        return meta.get("fingerprint") == _fingerprint(book.script(page), engine)
    except Exception:
        return False


def render_page(book: Book, engine, page: int, force: bool = False,
                cancel: Optional[threading.Event] = None) -> bool:
    """Bir sayfayi uret. Uretildiyse True, zaten guncelse False doner."""
    np = _np()
    segs = book.script(page)
    if not force and page_is_current(book, engine, page):
        return False
    items = [(speakable(s.text), s.lang) for s in segs]
    if isinstance(engine, EdgeTTS):
        pcms = engine.synth_many(items) if items else []
    else:
        pcms = []
        for text, lang in items:
            if cancel is not None and cancel.is_set():
                raise InterruptedError("iptal edildi")
            pcms.append(engine.synth(text, lang))
    sr = int(getattr(engine, "sample_rate", SR))
    parts = [silence(PAGE_LEAD, sr)]
    timings = []
    t = PAGE_LEAD / 1000.0
    prev_lang = None
    for i, (s, pcm) in enumerate(zip(segs, pcms)):
        if prev_lang and prev_lang != s.lang:
            parts.append(silence(LANG_SWITCH_PAD, sr))
            t += LANG_SWITCH_PAD / 1000.0
        pcm = trim_silence(pcm, sr=sr)
        start = t
        parts.append(pcm)
        t += len(pcm) / sr
        timings.append({"i": i, "start": round(start, 3), "end": round(t, 3),
                        "lang": s.lang, "kind": s.kind, "text": s.text})
        pause = PAUSE_AFTER.get(s.kind, 400)
        parts.append(silence(pause, sr))
        t += pause / 1000.0
        prev_lang = s.lang
    pcm = np.concatenate(parts) if parts else silence(500, sr)
    tags = {"title": f"Sayfa {page} - {book.section_of(page)}".strip(" -"),
            "album": book.title, "track": str(page), "artist": f"{engine.name} TTS"}
    encode_mp3(pcm, book.page_audio(engine.name, page), tags=tags, sr=sr)
    book.page_timing(engine.name, page).write_text(json.dumps(
        {"page": page, "engine": engine.name, "voices": engine.voices, "rate": engine.rate,
         "sample_rate": sr, "duration": round(len(pcm) / sr, 3),
         "fingerprint": _fingerprint(segs, engine),
         "segments": timings}, ensure_ascii=False, indent=1), encoding="utf-8")
    return True


# --- paralel uretim (Piper CPU'da calisir; cok cekirdekte sayfalar ayri sureclerde) ---
_W_ENGINE = None


def _worker_init(engine_name: str, voices: Dict[str, str], rate: float, threads: int = 0) -> None:
    global _W_ENGINE
    _W_ENGINE = make_engine(engine_name, voices, rate)
    if isinstance(_W_ENGINE, PiperTTS):
        _W_ENGINE.threads = threads


def _worker_render(book_root: str, page: int, force: bool) -> Tuple[int, bool, str]:
    try:
        return page, render_page(Book(Path(book_root)), _W_ENGINE, page, force=force), ""
    except Exception as e:                                  # noqa: BLE001
        return page, False, f"{type(e).__name__}: {e}"


def default_workers(engine) -> int:
    import os
    if getattr(engine, "name", "") == "edge":
        return 4                                    # 4 sayfa x 6 istek eszamanli
    return max(1, min(8, (os.cpu_count() or 2) // 4))


def render_pages(book: Book, engine, pages: Iterable[int], force: bool = False,
                 on_progress: Callable[[int, int, int, bool], None] = None,
                 cancel: Optional[threading.Event] = None, workers: int = 1) -> Dict[str, Any]:
    """Birden cok sayfayi uret. on_progress(sira, toplam, sayfa, uretildi_mi).

    workers > 1 ise (yalnizca Piper) sayfalar ayri sureclerde paralel uretilir.
    Edge zaten sayfa icinde eszamanli istek gonderir; onda workers yok sayilir.
    """
    pages = list(pages)
    done, skipped, failed = 0, 0, []
    if not force:
        todo = [p for p in pages if not page_is_current(book, engine, p)]
    else:
        todo = pages
    k = 0
    for p in pages:
        if p not in todo:
            k += 1
            skipped += 1
            if on_progress:
                on_progress(k, len(pages), p, False)
    def cancelled() -> bool:
        return cancel is not None and cancel.is_set()

    # Eksik Piper seslerini havuzdan ONCE, ust surecte bir kez indir; aksi halde her
    # isci sureci ayni dosyaya ayni anda indirmeye calisirdi.
    if todo and isinstance(engine, PiperTTS):
        for v in engine.missing_voices():
            if cancelled():
                break
            engine.download_voice(v)

    def consume(fut) -> None:
        nonlocal k, done
        page, made, err = fut.result()
        k += 1
        if err and err != "iptal":
            failed.append((page, err))
        done += made
        if on_progress:
            on_progress(k, len(pages), page, made)

    def drain(ex, futs) -> None:
        """Sonuclari topla; iptal ~0.5 sn icinde fark edilir. Erken cikista (iptal,
        hata, KeyboardInterrupt) kuyruktaki isler iptal edilir: kapatilan uygulama
        arkada gorunmez bir surecte kalan sayfalari uretmeye devam etmez."""
        from concurrent.futures import TimeoutError as FutTimeout, as_completed
        pending = set(futs)
        early = True
        try:
            while pending and not cancelled():
                try:
                    for fut in as_completed(pending, timeout=0.5):
                        pending.discard(fut)
                        consume(fut)
                        if cancelled():
                            break
                except FutTimeout:
                    pass
            early = bool(pending)
        finally:
            ex.shutdown(wait=True, cancel_futures=early)

    if workers > 1 and isinstance(engine, PiperTTS) and len(todo) > 1 and not cancelled():
        import os
        from concurrent.futures import ProcessPoolExecutor
        threads = max(1, (os.cpu_count() or 2) // workers)
        ex = ProcessPoolExecutor(max_workers=workers, initializer=_worker_init,
                                 initargs=(engine.name, engine.voices, engine.rate, threads))
        try:
            futs = [ex.submit(_worker_render, str(book.root), p, True) for p in todo]
        except BaseException:
            ex.shutdown(wait=True, cancel_futures=True)
            raise
        drain(ex, futs)
    elif workers > 1 and isinstance(engine, EdgeTTS) and len(todo) > 1 and not cancelled():
        from concurrent.futures import ThreadPoolExecutor

        def one(p):
            if cancelled():
                return p, False, "iptal"
            try:
                return p, render_page(book, engine, p, force=True), ""
            except Exception as e:                          # noqa: BLE001
                return p, False, f"{type(e).__name__}: {e}"
        ex = ThreadPoolExecutor(max_workers=workers)
        try:
            futs = [ex.submit(one, p) for p in todo]
        except BaseException:
            ex.shutdown(wait=True, cancel_futures=True)
            raise
        drain(ex, futs)
    else:
        for page in todo:
            if cancel is not None and cancel.is_set():
                break
            try:
                made = render_page(book, engine, page, force=True, cancel=cancel)
                done += made
            except InterruptedError:
                break
            except Exception as e:                          # noqa: BLE001
                failed.append((page, f"{type(e).__name__}: {e}"))
                made = False
            k += 1
            if on_progress:
                on_progress(k, len(pages), page, made)
    return {"rendered": done, "skipped": skipped, "failed": sorted(failed),
            "cancelled": bool(cancel is not None and cancel.is_set())}


def page_duration(book: Book, engine_name: str, page: int) -> float:
    try:
        return float(json.loads(book.page_timing(engine_name, page).read_text(encoding="utf-8"))["duration"])
    except Exception:
        return 0.0


def export_sections(book: Book, engine_name: str, out_dir: Optional[Path] = None,
                    sections: Optional[List[Section]] = None,
                    on_progress: Callable[[int, int, str], None] = None) -> Path:
    """Ust seviye bolumleri tek tek MP3'e birlestir (+ M3U8 calma listesi).

    Uretilmemis sayfalar atlanir. Dosya adi: "NN - Baslik.mp3".
    """
    np = _np()
    sr = ENGINE_RATE.get(engine_name, SR)
    out_dir = Path(out_dir or book.export_dir(engine_name))
    out_dir.mkdir(parents=True, exist_ok=True)
    secs = sections or book.top_sections()
    playlist = ["#EXTM3U", f"#PLAYLIST:{book.title}"]
    for k, sec in enumerate(secs, 1):
        parts = []
        for page in sec.pages:
            if book.has_audio(engine_name, page):
                parts.append(decode_to_pcm(book.page_audio(engine_name, page), sr))
        if on_progress:
            on_progress(k, len(secs), sec.title)
        if not parts:
            continue
        title = " ".join(sec.title.split())                 # \r \n \t -> tek bosluk
        safe = re.sub(r'[\x00-\x1f\\/:*?"<>|]+', "-", title).strip()[:80]
        name = f"{k:02d} - {safe}.mp3"
        pcm = np.concatenate(parts)
        encode_mp3(pcm, out_dir / name, tags={"title": title, "album": book.title,
                                               "track": f"{k}/{len(secs)}",
                                               "artist": f"{engine_name} TTS",
                                               "comment": f"Sayfa {sec.first}-{sec.last}"}, sr=sr)
        playlist += [f"#EXTINF:{int(len(pcm) / sr)},{title}", name]
    (out_dir / f"{slugify(book.title)}.m3u8").write_text("\n".join(playlist) + "\n", encoding="utf-8")
    return out_dir


# ==========================================================================
# Whisper ile dogrulama
# ==========================================================================
def verify_page(book: Book, engine_name: str, page: int, whisper_opts=None,
                min_ratio: float = 0.75) -> List[Dict[str, Any]]:
    """Uretilmis sayfanin Rusca parcalarini Whisper ile dinleyip betikle karsilastir.

    Donus: [{i, text, heard, ratio, ok}] - ratio < min_ratio olanlar suphelidir
    (TTS kelimeyi yanlis okumus ya da atlamis olabilir).
    """
    import difflib
    from rca import whisper_engine as W
    np = _np()
    timings = book.timings(engine_name, page)
    if not timings:
        return []
    pcm = decode_to_pcm(book.page_audio(engine_name, page), rate=W.SAMPLE_RATE).astype(np.float32) / 32768.0
    opts = whisper_opts or W.WhisperOptions()
    eng = W.shared_engine()
    out = []
    for seg in timings:
        if seg["lang"] != "ru":
            continue
        a = int(seg["start"] * W.SAMPLE_RATE)
        b = int(seg["end"] * W.SAMPLE_RATE)
        o = W.WhisperOptions.from_dict(dict(opts.to_dict(), language="ru", task="transcribe",
                                            vad_filter=False, word_timestamps=False, batched=False,
                                            condition_on_previous_text=False))
        tr = eng.transcribe(pcm[a:b], o)
        want, got = C.normalize_ru(seg["text"]), C.normalize_ru(tr.text)
        ratio = difflib.SequenceMatcher(a=want, b=got).ratio() if want else 1.0
        out.append({"i": seg["i"], "text": seg["text"], "heard": tr.text.strip(),
                    "ratio": round(ratio, 3), "ok": ratio >= min_ratio})
    return out
