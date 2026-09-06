# -*- coding: utf-8 -*-
"""Cift yonlu Rusca <-> Ingilizce sozluk.

Uc katman birlesir:
1. Gomulu cekirdek sozluk (`rca/dict_data.py`, ~1000 A1-B1 madde, vurgu isaretli).
2. Kullanicinin ice aktardigi CSV/TSV maddeleri (SQLite `dict_entries` tablosu).
3. Kaynak Merkezi'nden indirilen OpenRussian TSV dosyalari (varsa, on binlerce madde).

Arama iki yonde calisir: Kiril yazilirsa RU->EN, Latin yazilirsa EN->RU.
Siralama: tam eslesme > kelime basi > icerme.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

import rca_common as C

POS_LABELS: Dict[str, Dict[str, str]] = {
    "n":    {"tr": "isim", "en": "noun", "ru": "сущ."},
    "v":    {"tr": "fiil", "en": "verb", "ru": "глаг."},
    "adj":  {"tr": "sifat", "en": "adjective", "ru": "прил."},
    "adv":  {"tr": "zarf", "en": "adverb", "ru": "нареч."},
    "pron": {"tr": "zamir", "en": "pronoun", "ru": "мест."},
    "prep": {"tr": "edat", "en": "preposition", "ru": "предл."},
    "conj": {"tr": "baglac", "en": "conjunction", "ru": "союз"},
    "num":  {"tr": "sayi", "en": "numeral", "ru": "числ."},
    "part": {"tr": "edat/parcacik", "en": "particle", "ru": "част."},
    "int":  {"tr": "unlem", "en": "interjection", "ru": "межд."},
    "phr":  {"tr": "deyim", "en": "phrase", "ru": "фраза"},
}

EXTRA_LABELS: Dict[str, Dict[str, str]] = {
    "m":   {"tr": "eril", "en": "masculine", "ru": "м.р."},
    "f":   {"tr": "disil", "en": "feminine", "ru": "ж.р."},
    "n":   {"tr": "notr", "en": "neuter", "ru": "с.р."},
    "pl":  {"tr": "cogul", "en": "plural only", "ru": "мн.ч."},
    "ipf": {"tr": "bitmemis gorunus", "en": "imperfective", "ru": "несов."},
    "pf":  {"tr": "bitmis gorunus", "en": "perfective", "ru": "сов."},
}

SOURCE_BUILTIN = "builtin"
SOURCE_USER = "user"
SOURCE_OPENRUSSIAN = "openrussian"


@dataclass(frozen=True)
class Entry:
    """Tek bir sozluk maddesi."""
    headword: str          # vurgusuz temiz Rusca
    stress: int            # vurgulu sesli harfin indeksi (-1 bilinmiyor / tek hece)
    pos: str               # n / v / adj / ...
    extra: str             # m / f / n / pl / ipf / pf / ""
    translation: str       # Ingilizce karsilik(lar), ';' ile ayrilmis
    source: str = SOURCE_BUILTIN
    marked: str = ""       # tum kelimeleri vurgu isaretli baslik (deyimler icin)

    @property
    def display(self) -> str:
        """Vurgu isaretli baslik (tek heceli ve ё'lu kelimeler isaretsiz)."""
        return self.marked or C.add_stress(self.headword, self.stress)

    def pos_label(self, lang: str) -> str:
        return POS_LABELS.get(self.pos, {}).get(lang, self.pos)

    def extra_label(self, lang: str) -> str:
        return EXTRA_LABELS.get(self.extra, {}).get(lang, self.extra)


# --------------------------------------------------------------------------
# Ayristirma
# --------------------------------------------------------------------------
_STRESS_MARKS = ("'", "́", "´")


def split_stress(marked: str) -> tuple:
    """`приве'т` -> ("привет", 4). Isaret vurgulu sesliden hemen SONRA gelir.

    Birden fazla isaret varsa (deyim) ilk isaret dondurulur; `mark_all` tum
    kelimeleri isaretli gosterim metnini uretir.
    """
    clean: List[str] = []
    pos = -1
    for ch in marked or "":
        if ch in _STRESS_MARKS:
            if pos < 0:
                pos = len(clean) - 1
        else:
            clean.append(ch)
    word = "".join(clean).strip()
    if pos < 0 and "ё" in word.lower():
        pos = word.lower().index("ё")
    return word, pos


def mark_all(marked: str) -> str:
    """Tum tirnak isaretlerini birlesik akut vurguya cevir (ё isaretlenmez)."""
    out: List[str] = []
    for ch in marked or "":
        if ch in _STRESS_MARKS:
            if out and out[-1].lower() != "ё":
                out.append(C.STRESS_MARK)
        else:
            out.append(ch)
    return "".join(out).strip()


def parse_line(line: str, source: str = SOURCE_BUILTIN) -> Optional[Entry]:
    """`headword|pos extra|translation` satirini Entry'ye cevir."""
    line = (line or "").strip()
    if not line or line.startswith("#"):
        return None
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 3:
        return None
    head, tag, tr = parts[0], parts[1], parts[2]
    tokens = tag.split()
    pos = tokens[0] if tokens else ""
    extra = tokens[1] if len(tokens) > 1 else ""
    word, stress = split_stress(head)
    if not word or not tr:
        return None
    return Entry(word, stress, pos, extra, tr, source, mark_all(head))


def parse_block(text: str, source: str = SOURCE_BUILTIN) -> List[Entry]:
    out: List[Entry] = []
    for line in text.splitlines():
        e = parse_line(line, source)
        if e:
            out.append(e)
    return out


def _norm(text: str) -> str:
    return C.strip_stress((text or "").strip().lower().replace("ё", "е"))


_WORD_RE = re.compile(r"[a-zа-яё'\-]+", re.IGNORECASE)


# --------------------------------------------------------------------------
# Sozluk
# --------------------------------------------------------------------------
class Dictionary:
    """Bellek ici indeksli, iki yonlu sozluk."""

    def __init__(self, entries: Iterable[Entry] = ()) -> None:
        self._entries: List[Entry] = []
        self._seen = set()
        self.extend(entries)

    # -- yukleme -----------------------------------------------------------
    def extend(self, entries: Iterable[Entry]) -> int:
        added = 0
        for e in entries:
            key = (_norm(e.headword), e.pos, _norm(e.translation))
            if key in self._seen:
                continue
            self._seen.add(key)
            self._entries.append(e)
            added += 1
        return added

    def remove_source(self, source: str) -> None:
        keep = [e for e in self._entries if e.source != source]
        self._entries = []
        self._seen = set()
        self.extend(keep)

    def __len__(self) -> int:
        return len(self._entries)

    def count_by_source(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self._entries:
            out[e.source] = out.get(e.source, 0) + 1
        return out

    @property
    def entries(self) -> Sequence[Entry]:
        return self._entries

    # -- arama -------------------------------------------------------------
    @staticmethod
    def direction(query: str) -> str:
        """'ru2en' Kiril icin, aksi halde 'en2ru'."""
        return "ru2en" if C.has_cyrillic(query or "") else "en2ru"

    def lookup(self, query: str, limit: int = 200) -> List[Entry]:
        q = _norm(query)
        if not q:
            return []
        ru_side = self.direction(query) == "ru2en"
        scored = []
        for e in self._entries:
            if ru_side:
                field = _norm(e.headword)
                score = _score(q, field, [field])
            else:
                field = _norm(e.translation)
                senses = [s.strip() for s in re.split(r"[;,]", field) if s.strip()]
                score = _score(q, field, senses)
            if score:
                scored.append((score, len(e.headword), e))
        scored.sort(key=lambda t: (-t[0], t[1], t[2].headword))
        return [e for _s, _l, e in scored[:limit]]

    def random_entry(self, rng=None) -> Optional[Entry]:
        import random
        pool = [e for e in self._entries if e.source == SOURCE_BUILTIN] or self._entries
        if not pool:
            return None
        return (rng or random).choice(pool)


def _score(q: str, field: str, senses: List[str]) -> int:
    """Tam eslesme 100, kelime basi 60, kelime icinde 30, alt dize 10."""
    if not field:
        return 0
    if q == field or q in senses:
        return 100
    for s in senses:
        stripped = re.sub(r"^(to|the|a|an) ", "", s)
        if stripped == q:
            return 95
    if any(s.startswith(q) for s in senses) or field.startswith(q):
        return 60
    if re.search(r"(^|[\s\-(])" + re.escape(q), field):
        return 30
    if len(q) >= 3 and q in field:
        return 10
    return 0


# --------------------------------------------------------------------------
# Dosya ice/disa aktarim
# --------------------------------------------------------------------------
def read_table(path: Path) -> List[Entry]:
    """CSV/TSV oku: sutunlar `ru, en[, pos[, extra]]` (baslik satiri istege bagli)."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    delim = "\t" if path.suffix.lower() in (".tsv", ".txt") or raw.count("\t") > raw.count(",") else ","
    out: List[Entry] = []
    for row in csv.reader(raw.splitlines(), delimiter=delim):
        if len(row) < 2:
            continue
        ru, en = row[0].strip(), row[1].strip()
        if not ru or not en:
            continue
        if not C.has_cyrillic(ru):
            if C.has_cyrillic(en):
                ru, en = en, ru
            else:
                continue
        pos = row[2].strip() if len(row) > 2 else ""
        extra = row[3].strip() if len(row) > 3 else ""
        word, stress = split_stress(ru)
        out.append(Entry(word, stress, pos, extra, en, SOURCE_USER, mark_all(ru)))
    return out


def write_table(path: Path, entries: Iterable[Entry]) -> int:
    n = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ru", "en", "pos", "extra", "source"])
        for e in entries:
            w.writerow([e.display.replace(C.STRESS_MARK, "'"), e.translation, e.pos, e.extra, e.source])
            n += 1
    return n


def load_openrussian(folder: Path, limit_per_file: int = 60000,
                     on_progress: Callable[[str, int], None] = None) -> List[Entry]:
    """Kaynak Merkezi'nin indirdigi OpenRussian TSV'lerini sozluk maddesine cevir."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    kinds = {"isimler": "n", "nouns": "n", "fiiller": "v", "verbs": "v",
             "sifatlar": "adj", "adjectives": "adj", "digerleri": "", "others": ""}
    out: List[Entry] = []
    for path in sorted(folder.glob("openrussian_*.tsv")):
        name = path.stem.lower()
        pos = next((v for k, v in kinds.items() if k in name), "")
        try:
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter="\t")
                n = 0
                for row in reader:
                    if n >= limit_per_file:
                        break
                    bare = (row.get("bare") or "").strip()
                    en = (row.get("translations_en") or "").strip()
                    if not bare or not en:
                        continue
                    accented = row.get("accented") or bare
                    word, stress = split_stress(accented)
                    extra = ""
                    if pos == "n":
                        extra = (row.get("gender") or "").strip()[:1]
                        if extra not in ("m", "f", "n"):
                            extra = "pl" if extra == "p" else ""
                    elif pos == "v":
                        asp = (row.get("aspect") or "").strip().lower()
                        extra = "pf" if asp.startswith("perf") else ("ipf" if asp else "")
                    elif not pos:
                        pos = (row.get("type") or "").strip()[:4] or "phr"
                    out.append(Entry(word or bare, stress, pos, extra,
                                     en.replace("; ", ";").replace(";", "; ")[:240],
                                     SOURCE_OPENRUSSIAN, mark_all(accented)))
                    n += 1
            if on_progress:
                on_progress(path.name, len(out))
        except OSError:
            continue
    return out


def openrussian_dir() -> Path:
    return C.RESOURCES_DIR / "Indirilenler" / "Sozluk"


# --------------------------------------------------------------------------
# Fabrika
# --------------------------------------------------------------------------
def builtin_entries() -> List[Entry]:
    from rca.dict_data import DATA
    return parse_block(DATA, SOURCE_BUILTIN)


def build_dictionary(user_rows: Iterable[Sequence] = ()) -> Dictionary:
    """Gomulu + kullanici maddelerinden sozluk kur (OpenRussian ayrica yuklenir)."""
    d = Dictionary(builtin_entries())
    users = []
    for r in user_rows:
        ru, en = r[0], r[1]
        pos = r[2] if len(r) > 2 else ""
        extra = r[3] if len(r) > 3 else ""
        word, stress = split_stress(ru)
        users.append(Entry(word, stress, pos or "", extra or "", en, SOURCE_USER, mark_all(ru)))
    d.extend(users)
    return d
