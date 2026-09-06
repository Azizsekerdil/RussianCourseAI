# -*- coding: utf-8 -*-
"""Cift yonlu Rusca <-> Ingilizce sozluk.

Dort katman birlesir:
1. Gomulu cekirdek sozluk (`rca/dict_data.py`, ~1000 A1-B1 madde, vurgu isaretli).
2. Kullanicinin ice aktardigi CSV/TSV maddeleri (SQLite `dict_entries` tablosu).
3. Kaynak Merkezi'nden indirilen OpenRussian TSV dosyalari (varsa, on binlerce madde).
4. AI'dan (LM Studio ya da alternatif OpenAI uyumlu uc) alinan yapisal maddeler;
   istenirse `dict_entries` tablosuna "ai" kaynagiyla kaydedilir (`ai_lookup`).

Arama iki yonde calisir: Kiril yazilirsa RU->EN, Latin yazilirsa EN->RU.
Siralama: tam eslesme > kelime basi > icerme.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

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
SOURCE_AI = "ai"


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
    example: str = ""      # kisa Rusca ornek cumle (AI maddeleri)
    note: str = ""         # kisa kullanim notu / tanim (AI maddeleri, arayuz dilinde)

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


def repair_stress(marked: str) -> str:
    """Sessiz harften sonraya konmus vurgu isaretini ayni kelimedeki en yakin onceki sesliye tasi.

    Modeller bazen dumskrol'ling gibi yazar; dogru bicim dumskro'lling'dir. Onunde sesli
    bulunmayan isaret atilir. Sesliden sonraki isaretler oldugu gibi kalir.
    """
    out: List[str] = []
    for ch in marked or "":
        if ch in _STRESS_MARKS:
            i = len(out) - 1
            while i >= 0 and out[i] not in _STRESS_MARKS and out[i] != " " and out[i].lower() not in C.VOWELS:
                i -= 1
            if i >= 0 and out[i].lower() in C.VOWELS:
                out.insert(i + 1, "'")
            continue
        out.append(ch)
    return "".join(out)


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


def norm_query(text: str) -> str:
    """Sorgu / baslik karsilastirma anahtari: kucuk harf, vurgusuz, ё->е, kirpilmis."""
    return _norm(text)


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
            key = self.key(e)
            if key in self._seen:
                continue
            self._seen.add(key)
            self._entries.append(e)
            added += 1
        return added

    @staticmethod
    def key(e: Entry) -> tuple:
        """Tekillik anahtari: (baslik, tur, ceviri) - vurgu ve buyuk/kucuk harf farksiz."""
        return (_norm(e.headword), e.pos, _norm(e.translation))

    def contains(self, e: Entry) -> bool:
        """Ayni madde (kaynagindan bagimsiz) sozlukte zaten var mi?"""
        return self.key(e) in self._seen

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
# AI sozluk sorgusu (yapisal JSON)
# --------------------------------------------------------------------------
AI_TIMEOUT = 90.0
AI_MAX_ENTRIES = 5
AI_MAX_TOKENS = 1200
_AI_LIMITS = {"headword": 80, "translation": 240, "example": 300, "note": 400}
_AI_NOTE_LANG = {"tr": "Turkish", "en": "English", "ru": "Russian"}
_POS_ALIASES = {
    "noun": "n", "verb": "v", "adjective": "adj", "adverb": "adv", "pronoun": "pron",
    "preposition": "prep", "conjunction": "conj", "numeral": "num", "number": "num",
    "particle": "part", "interjection": "int", "interj": "int", "phrase": "phr",
    "expression": "phr", "idiom": "phr", "article": "phr",
    "сущ": "n", "существительное": "n", "глаг": "v", "глагол": "v", "прил": "adj",
    "прилагательное": "adj", "нареч": "adv", "наречие": "adv", "мест": "pron",
    "местоимение": "pron", "предл": "prep", "предлог": "prep", "союз": "conj",
    "числ": "num", "числительное": "num", "част": "part", "частица": "part",
    "межд": "int", "междометие": "int", "фраза": "phr",
    "isim": "n", "fiil": "v", "sifat": "adj", "zarf": "adv", "zamir": "pron",
    "edat": "prep", "baglac": "conj", "sayi": "num", "unlem": "int", "deyim": "phr",
}
_EXTRA_ALIASES = {
    "masc": "m", "masculine": "m", "м": "m", "м.р": "m", "мужской": "m", "eril": "m",
    "fem": "f", "feminine": "f", "ж": "f", "ж.р": "f", "женский": "f", "disil": "f",
    "neut": "n", "neuter": "n", "с": "n", "с.р": "n", "средний": "n", "notr": "n",
    "plural": "pl", "pl.": "pl", "мн": "pl", "мн.ч": "pl", "cogul": "pl",
    "impf": "ipf", "imperf": "ipf", "imperfective": "ipf", "несов": "ipf", "нсв": "ipf",
    "perf": "pf", "perfective": "pf", "сов": "pf", "св": "pf",
}
_STRESSED_APOSTROPHE_RE = re.compile(r"[аеёиоуыэюя]'", re.IGNORECASE)
_QUOTE_CHARS = " \"`«»"


def _clean_headword(head: str) -> str:
    """Modelin basliga sardigi tirnak / bosluklari at; VURGU isaretini koru.

    Kesme isareti bu sozlugun vurgu isaretidir ve son hecesi vurgulu kelimelerde
    (хорошо', вода', она') basligin SON karakteridir - sagdan korunmesi gerekir.
    Sesliden sonra gelmeyen bir son kesme (дом') ya da basta olan kesme ('она')
    vurgu olamaz; onlar tirnak sayilip atilir.
    """
    head = head.strip(_QUOTE_CHARS).lstrip("'")
    while head.endswith("''"):                                  # 'хорошо'' -> хорошо'
        head = head[:-1]
    if head.endswith("'") and not _STRESSED_APOSTROPHE_RE.search(head[-2:]):
        head = head[:-1].rstrip(_QUOTE_CHARS)
    return head


def ai_prompt(query: str, ui_lang: str = "tr") -> Tuple[str, str]:
    """AI icin (sistem yonergesi, kullanici mesaji) cifti. Yanit yalnizca JSON dizisi olmali."""
    direction = Dictionary.direction(query)
    note_lang = _AI_NOTE_LANG.get(ui_lang, "Turkish")
    system = (
        "You are a precise Russian-English dictionary engine. You answer ONLY with a JSON array - "
        "no prose, no markdown, no code fences, nothing before or after the array.\n"
        "Each element is an object with exactly these keys:\n"
        '  "headword": the Russian dictionary form (nominative singular for nouns, infinitive for '
        "verbs) in Cyrillic, with an apostrophe placed immediately AFTER the stressed vowel, e.g. "
        "приве'т, кни'га, говори'ть, хорошо'. One-syllable words and words containing ё take no "
        "apostrophe. In multi-word phrases mark the stress of every word.\n"
        '  "pos": one of n v adj adv pron prep conj num part int phr\n'
        '  "extra": for nouns the gender m / f / n (pl for plural-only nouns); for verbs the aspect '
        'ipf / pf; for everything else "".\n'
        '  "translation": the English meanings, senses separated by "; " (for example "house; home").\n'
        '  "example": one short natural Russian sentence in Cyrillic that uses the word (no stress marks).\n'
        f'  "note": a short usage note or definition written in {note_lang} (at most 25 words).\n'
        "Return between 1 and 5 objects, the most common sense or word first.\n"
        "The query may be Russian or English (or occasionally another language written in Latin "
        "letters). If the query is Russian, describe that word in its dictionary form. If it is not "
        "Russian, return the Russian words that translate it. Never invent words; when unsure return "
        "fewer entries. If the query is not a real word or phrase, return []."
    )
    user = (f"Query: {query.strip()}\n"
            f"Query script: {'Cyrillic (Russian)' if direction == 'ru2en' else 'Latin (probably English)'}\n"
            "JSON array:")
    return system, user


def _ai_str(obj: Dict[str, Any], key: str) -> str:
    val = obj.get(key, "")
    if val is None:
        return ""
    if isinstance(val, (list, tuple)):
        val = "; ".join(str(v) for v in val if v is not None)
    if not isinstance(val, str):
        val = str(val)
    val = re.sub(r"\s+", " ", val).strip()
    limit = _AI_LIMITS.get(key)
    return val[:limit] if limit else val


def normalize_pos(pos: str) -> str:
    """Model ciktisindaki tur etiketini sozlugun kodlarina indirge (bilinmeyen -> phr)."""
    p = (pos or "").strip().lower().rstrip(".")
    if p in POS_LABELS:
        return p
    p2 = _POS_ALIASES.get(p) or _POS_ALIASES.get(p.split()[0] if p else "")
    if p2:
        return p2
    for key, code in _POS_ALIASES.items():
        if p.startswith(key):
            return code
    return "phr"


def normalize_extra(extra: str, pos: str) -> str:
    """Cins / gorunus etiketini m f n pl ipf pf kumesine indirge (uyumsuz -> bos)."""
    x = (extra or "").strip().lower().rstrip(".")
    x = x.replace("ё", "е")
    if x not in EXTRA_LABELS:
        x = _EXTRA_ALIASES.get(x, _EXTRA_ALIASES.get(x.split()[0] if x else "", ""))
    if pos == "n":
        return x if x in ("m", "f", "n", "pl") else ""
    if pos == "v":
        return x if x in ("ipf", "pf") else ""
    return ""                                   # gomulu veri kurali: cins/gorunus yalnizca isim ve fiilde


def _extract_json_array(text: str) -> Optional[Any]:
    """Kod citlerini at, ilk '[' ile son ']' arasini JSON olarak coz; olmazsa None."""
    raw = (text or "").strip()
    if not raw:
        return None
    raw = re.sub(r"^\s*```[a-zA-Z]*\s*", "", raw)
    raw = re.sub(r"\s*```\s*$", "", raw)
    start, end = raw.find("["), raw.rfind("]")
    candidates = []
    if start >= 0 and end > start:
        candidates.append(raw[start:end + 1])
    s2, e2 = raw.find("{"), raw.rfind("}")
    if s2 >= 0 and e2 > s2:
        candidates.append(raw[s2:e2 + 1])
    for cand in candidates:
        for attempt in (cand, re.sub(r",\s*([\]}])", r"\1", cand)):
            try:
                return json.loads(attempt)
            except ValueError:
                continue
    return None


def parse_ai_entries(text: str, limit: int = AI_MAX_ENTRIES) -> List[Entry]:
    """Model ciktisini Entry listesine cevir. Cop ciktida istisna YOK: bos liste."""
    try:
        data = _extract_json_array(text)
    except Exception:                                           # noqa: BLE001
        return []
    if isinstance(data, dict):
        inner = data.get("entries") or data.get("results") or data.get("items")
        data = inner if isinstance(inner, list) else [data]
    if not isinstance(data, list):
        return []
    out: List[Entry] = []
    seen = set()
    for obj in data:
        if not isinstance(obj, dict):
            continue
        try:
            head = _ai_str(obj, "headword") or _ai_str(obj, "word") or _ai_str(obj, "ru")
            trans = _ai_str(obj, "translation") or _ai_str(obj, "en") or _ai_str(obj, "meaning")
            if head and trans and not C.has_cyrillic(head) and C.has_cyrillic(trans):
                head, trans = trans, head                       # yon karistiysa duzelt
            head = repair_stress(_clean_headword(head))
            trans = "; ".join(dict.fromkeys(t.strip() for t in trans.split(";") if t.strip()))   # tekrar eden anlamlari at
            if not head or not trans or not C.has_cyrillic(head):
                continue
            head = head[:_AI_LIMITS["headword"]]
            pos = normalize_pos(_ai_str(obj, "pos"))
            extra = normalize_extra(_ai_str(obj, "extra") or _ai_str(obj, "gender")
                                    or _ai_str(obj, "aspect"), pos)
            example = _ai_str(obj, "example")
            if example and _STRESSED_APOSTROPHE_RE.search(example):
                example = mark_all(repair_stress(example))
            note = _ai_str(obj, "note") or _ai_str(obj, "definition")
            word, stress = split_stress(head)
            if not word:
                continue
            key = (_norm(word), pos, _norm(trans))
            if key in seen:
                continue
            seen.add(key)
            out.append(Entry(word, stress, pos, extra, trans, SOURCE_AI, mark_all(head),
                             example, note))
        except Exception:                                       # noqa: BLE001
            continue
        if len(out) >= limit:
            break
    return out


def ai_lookup(client, query: str, ui_lang: str = "tr", model: str = "") -> List[Entry]:
    """Sorguyu AI'a sor ve yapisal maddeleri dondur.

    Baglanti / model hatasi (AIError) cagirana yayilir ki sekme cevrimdisi
    mesajini gosterebilsin; anlamsiz cikti ise sessizce bos liste olur.
    """
    query = (query or "").strip()
    if not query or client is None:
        return []
    system, user = ai_prompt(query, ui_lang)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    # Dusunen modellerde (gemma-4, qwen3...) akil yurutme metni butceyi yiyip icerigi bos
    # birakabilir; yerel sunucuya "dusunme" isteyen alan gonderilir (tanimayan sunucu 400
    # verirse istemci alani atip yineler). Yine de bos + kesik yanit gelirse butce uc kat
    # artirilarak bir kez daha denenir.
    extra = {"reasoning_effort": "none"} if getattr(client, "is_local", False) else None
    text = client.chat(messages, task="dictionary", temperature=0.1, max_tokens=AI_MAX_TOKENS,
                       model=model or None, timeout=AI_TIMEOUT, extra=extra)
    entries = parse_ai_entries(text)
    if not entries and getattr(client, "last_finish_reason", "") == "length":
        text = client.chat(messages, task="dictionary", temperature=0.1, max_tokens=AI_MAX_TOKENS * 3,
                           model=model or None, timeout=AI_TIMEOUT * 2, extra=extra)
        entries = parse_ai_entries(text)
    return entries


# --------------------------------------------------------------------------
# Fabrika
# --------------------------------------------------------------------------
def builtin_entries() -> List[Entry]:
    from rca.dict_data import DATA
    return parse_block(DATA, SOURCE_BUILTIN)


def _row_field(row, index: int, key: str, default: str = "") -> str:
    """Satir demet ya da sozluk olabilir (DictRepo.all() sozluk dondurur)."""
    if isinstance(row, dict):
        val = row.get(key, default)
    else:
        val = row[index] if len(row) > index else default
    return val if val is not None else default


def build_dictionary(user_rows: Iterable[Sequence] = ()) -> Dictionary:
    """Gomulu + kullanici/AI maddelerinden sozluk kur (OpenRussian ayrica yuklenir).

    Satirlar `(ru, en[, pos[, extra[, source[, example[, note]]]]])` demetleri ya da
    `dict_entries` sozlukleri olabilir; saklanan "source" degeri Entry.source'a
    ("user" / "ai") aktarilir ki sekme maddeleri etiketleyebilsin.
    """
    d = Dictionary(builtin_entries())
    users = []
    for r in user_rows:
        ru, en = _row_field(r, 0, "ru"), _row_field(r, 1, "en")
        if not ru or not en:
            continue
        pos = _row_field(r, 2, "pos")
        extra = _row_field(r, 3, "extra")
        source = _row_field(r, 4, "source", SOURCE_USER) or SOURCE_USER
        if source not in (SOURCE_USER, SOURCE_AI):
            source = SOURCE_USER
        example = _row_field(r, 5, "example")
        note = _row_field(r, 6, "note")
        word, stress = split_stress(ru)
        users.append(Entry(word, stress, pos or "", extra or "", en, source, mark_all(ru),
                           example or "", note or ""))
    d.extend(users)
    return d
