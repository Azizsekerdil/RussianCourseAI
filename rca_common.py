# -*- coding: utf-8 -*-
"""Russian Course AI - ortak sabitler, yollar, tema ve metin yardimcilari.

Bu modul uygulamanin TEK kaynagidir: baslik, surum, dizinler, tema renkleri ve
model varsayilanlari yalnizca burada tanimlanir. Baska hicbir modul bu
degerleri yeniden yazmaz.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict

# --------------------------------------------------------------------------
# Kimlik
# --------------------------------------------------------------------------
APP_NAME = "Russian Course AI"
APP_SLUG = "RussianCourseAI"
VERSION = "1.1.0"
TARGET_LANG = "ru"          # hedef dil kodu (baska dile uyarlamak icin tek nokta)
TARGET_LANG_NAME = "Rusca"

# --------------------------------------------------------------------------
# Yollar  -  kullanici verisi %APPDATA%\RussianCourseAI altinda
# --------------------------------------------------------------------------
def _appdata_root() -> Path:
    base = os.environ.get("RCA_HOME")
    if base:
        return Path(base)
    if sys.platform.startswith("win"):
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / APP_SLUG
    return Path.home() / f".{APP_SLUG.lower()}"


APP_HOME = _appdata_root()
DATA_DIR = APP_HOME / "data"
SETTINGS_DIR = APP_HOME / "settings"
EXPORT_DIR = APP_HOME / "exports"
LOG_DIR = APP_HOME / "logs"
DB_PATH = DATA_DIR / "rca.db"
SETTINGS_PATH = SETTINGS_DIR / "settings.json"

# program dizini (salt okunur icerik: Resources/, grammar/)
PROGRAM_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = PROGRAM_DIR / "Resources"
GRAMMAR_DIR = PROGRAM_DIR / "grammar"


def ensure_dirs() -> None:
    """Kullanici veri dizinlerini olustur (idempotent)."""
    for d in (APP_HOME, DATA_DIR, SETTINGS_DIR, EXPORT_DIR, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# Tema  -  tek sozluk, iki palet
# --------------------------------------------------------------------------
THEME: Dict[str, Dict[str, str]] = {
    "dark": {
        # yuzeyler: deep (kenar cubugu) < bg (icerik) < bg_alt (kart) < panel (kart ustu)
        "deep": "#0f1116",
        "bg": "#14161d",
        "bg_alt": "#1c1f28",
        "panel": "#232733",
        "hover": "#2a2f3d",
        # metin
        "fg": "#e8eaf0",
        "fg_dim": "#8b93a5",
        "fg_mute": "#5f6675",
        # vurgu
        "accent": "#5b8def",
        "accent_soft": "#1e2a45",
        "accent_fg": "#ffffff",
        # durum
        "ok": "#3fbf7f",
        "ok_soft": "#16301f",
        "warn": "#e2a54c",
        "warn_soft": "#332715",
        "err": "#f0625d",
        "err_soft": "#3a1a1b",
        # cizgi / secim
        "border": "#272b36",
        "border_hi": "#39404f",
        "sel": "#2c3a58",
        "shadow": "#0b0d11",
    },
    "light": {
        "deep": "#eceff4",
        "bg": "#f6f7fa",
        "bg_alt": "#ffffff",
        "panel": "#f0f2f6",
        "hover": "#e6eaf1",
        "fg": "#171a21",
        "fg_dim": "#5c6474",
        "fg_mute": "#8d94a3",
        "accent": "#2f6fe0",
        "accent_soft": "#e4ecfd",
        "accent_fg": "#ffffff",
        "ok": "#1f8a4c",
        "ok_soft": "#e2f5ea",
        "warn": "#9c6b16",
        "warn_soft": "#fbf0dc",
        "err": "#c8322d",
        "err_soft": "#fdeae9",
        "border": "#dfe3ea",
        "border_hi": "#c3cad6",
        "sel": "#d7e3fa",
        "shadow": "#c8ccd4",
    },
}

# Yazi olcegi - tek yerden
FONT_FAMILY = "Segoe UI"
FONT_UI = (FONT_FAMILY, 10)
FONT_UI_SM = (FONT_FAMILY, 9)
FONT_UI_BOLD = (FONT_FAMILY, 10, "bold")
FONT_TITLE = (FONT_FAMILY, 15, "bold")
FONT_PAGE = (FONT_FAMILY, 19, "bold")
FONT_NUM = (FONT_FAMILY, 22, "bold")
FONT_RU = (FONT_FAMILY, 14)          # Kiril icin genis kapsamli
FONT_RU_BIG = (FONT_FAMILY, 30, "bold")
FONT_MONO = ("Consolas", 10)

RADIUS = 10                          # kart kose yaricapi (Canvas cizimlerinde)

# --------------------------------------------------------------------------
# Yapay zeka  -  LM Studio (OpenAI uyumlu) + istege bagli alternatif uc
# --------------------------------------------------------------------------
LMSTUDIO_BASE = "http://127.0.0.1:1234"
NIM_BASE = "https://integrate.api.nvidia.com/v1"
ALT_DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"

# Sozluk sekmesinin AI politikasi:
#   auto  -> LM Studio ulasilabiliyorsa yerel, degilse (acik ise) alternatif uc
#   local -> yalnizca LM Studio
#   alt   -> yalnizca alternatif uc
#   off   -> sozlukte AI kullanilmaz
DICT_AI_POLICIES = ("auto", "local", "alt", "off")

# gorev -> tercih edilen model listesi (ilk kurulu olan secilir)
MODEL_PROFILES: Dict[str, list] = {
    "chat":      ["qwen2.5-7b-instruct", "qwen2.5-14b-instruct", "llama-3.1-8b-instruct"],
    "dictionary": ["qwen2.5-7b-instruct", "qwen2.5-14b-instruct", "llama-3.1-8b-instruct"],
    "grammar":   ["qwen2.5-7b-instruct", "qwen2.5-14b-instruct"],
    "translate": ["qwen2.5-7b-instruct", "gemma-2-9b-it"],
    "correct":   ["qwen2.5-7b-instruct", "qwen2.5-14b-instruct"],
    "dialogue":  ["qwen2.5-7b-instruct", "llama-3.1-8b-instruct"],
    "vision":    ["qwen2-vl-7b-instruct", "llava-v1.6-mistral-7b"],
}
DEFAULT_MODEL = MODEL_PROFILES["chat"][0]

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1"]

# --------------------------------------------------------------------------
# Ayarlar
# --------------------------------------------------------------------------
DEFAULT_SETTINGS: Dict[str, Any] = {
    "ui_lang": "tr",              # tr | en | ru
    "theme": "dark",
    "profile_id": None,
    "daily_goal": 20,
    "tts_enabled": True,
    "tts_rate": 150,
    "ai_base": LMSTUDIO_BASE,
    "ai_model": DEFAULT_MODEL,
    "ai_enabled": True,
    "nim_enabled": False,         # eski surumlerle uyumluluk icin korunur (bkz. alt_enabled)
    "alt_enabled": False,         # alternatif OpenAI uyumlu uc (NIM / OpenRouter / Groq / Ollama...)
    "alt_base": NIM_BASE,
    "alt_model": ALT_DEFAULT_MODEL,
    "dict_ai": "auto",            # sozluk AI politikasi: auto | local | alt | off
    "dict_ai_autosave": True,     # AI'dan gelen sozluk maddeleri yerel sozluge kaydedilsin mi
    "cefr": "A1",
    "last_pdf": "",
}
# API anahtari ASLA settings.json'a yazilmaz; rca/secrets.py uzerinden saklanir.


def load_settings() -> Dict[str, Any]:
    """Ayarlari diskten oku; eksik anahtarlari varsayilanla tamamla."""
    ensure_dirs()
    data = dict(DEFAULT_SETTINGS)
    try:
        if SETTINGS_PATH.exists():
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if k in DEFAULT_SETTINGS})
                # eski "nim_enabled" isaretini yeni alternatif uc ayarina tasi
                if raw.get("nim_enabled") and "alt_enabled" not in raw:
                    data["alt_enabled"] = True
    except Exception:
        pass  # bozuk ayar dosyasi programi durdurmaz
    if data.get("dict_ai") not in DICT_AI_POLICIES:
        data["dict_ai"] = "auto"
    return data


def save_settings(data: Dict[str, Any]) -> None:
    """Ayarlari diske yaz; hata olursa sessizce gec (program calismaya devam eder)."""
    ensure_dirs()
    try:
        SETTINGS_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


# --------------------------------------------------------------------------
# Rusca metin yardimcilari
# --------------------------------------------------------------------------
STRESS_MARK = "\u0301"          # birlesik akut vurgu isareti
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
VOWELS = "аеёиоуыэюя"
CONSONANTS = "бвгджзйклмнпрстфхцчшщ"


def strip_stress(text: str) -> str:
    """Vurgu isaretlerini (U+0301) kaldir."""
    return unicodedata.normalize("NFC", text).replace(STRESS_MARK, "")


def normalize_ru(text: str) -> str:
    """Karsilastirma icin normalize et: kucuk harf, yo->e, vurgusuz, sadelestirilmis bosluk."""
    t = strip_stress(text or "").strip().lower()
    t = t.replace("\u0451", "\u0435")           # ё -> е
    t = re.sub(r"[\u0300-\u036f]", "", t)
    t = re.sub(r"[^\w\s\-']", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def has_cyrillic(text: str) -> bool:
    """Metinde Kiril harfi var mi?"""
    return bool(CYRILLIC_RE.search(text or ""))


def add_stress(word: str, pos: int) -> str:
    """`pos` indeksindeki sesli harfe vurgu isareti ekle (-1 => degisiklik yok)."""
    w = strip_stress(word)
    if pos is None or pos < 0 or pos >= len(w):
        return w
    return w[: pos + 1] + STRESS_MARK + w[pos + 1:]


def syllables(word: str) -> int:
    """Hece sayisi = sesli harf sayisi."""
    return sum(1 for ch in strip_stress(word).lower() if ch in VOWELS)


def human_int(n: int) -> str:
    """1234567 -> '1.234.567' (TR bicimi)."""
    return f"{int(n):,}".replace(",", ".")
