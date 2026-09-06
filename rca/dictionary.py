# -*- coding: utf-8 -*-
"""Uc dilli Rusca <-> Ingilizce / Turkce sozluk.

Dort katman birlesir:
1. Gomulu cekirdek sozluk (`rca/dict_data.py`, ~1000 A1-B1 madde, vurgu isaretli).
2. Kullanicinin ice aktardigi CSV/TSV maddeleri (SQLite `dict_entries` tablosu).
3. Kaynak Merkezi'nden indirilen OpenRussian TSV dosyalari (varsa, on binlerce madde).
4. AI'dan (LM Studio ya da alternatif OpenAI uyumlu uc) alinan yapisal maddeler;
   istenirse `dict_entries` tablosuna "ai" kaynagiyla kaydedilir (`ai_lookup`).

Her madde Ingilizce karsiligi (`translation`) ve istege bagli Turkce karsiligi (`tr`)
tasir. Arama yonu (`DIRECTIONS`): auto | ru2en | en2ru | ru2tr | tr2ru.
- Sabit yonde YALNIZCA kaynak taraf aranir (baslik / Ingilizce / Turkce).
- auto: Kiril yazilirsa baslik (ru2en); Latin yazilirsa Ingilizce ve Turkce taraflari
  puanlanir, en iyi puanli taraf yonu belirler (esitlikte Ingilizce).
Siralama: tam eslesme > kelime basi > kelime icinde > alt dize.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, replace
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
    tr: str = ""           # Turkce karsilik(lar), '; ' ile ayrilmis ("" = henuz yok)

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
    """`headword|pos extra|english[|turkish]` satirini Entry'ye cevir.

    Dorduncu alan istege baglidir: Turkce karsilik(lar), '; ' ile ayrilmis. Yoksa
    (ya da bossa) Entry.tr "" olur; gomulu veri bu alani kademeli olarak kazanir.
    """
    line = (line or "").strip()
    if not line or line.startswith("#"):
        return None
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 3:
        return None
    head, tag, en = parts[0], parts[1], parts[2]
    turkish = parts[3] if len(parts) > 3 else ""
    tokens = tag.split()
    pos = tokens[0] if tokens else ""
    extra = tokens[1] if len(tokens) > 1 else ""
    word, stress = split_stress(head)
    if not word or not en:
        return None
    return Entry(word, stress, pos, extra, en, source, mark_all(head), tr=turkish)


def parse_block(text: str, source: str = SOURCE_BUILTIN) -> List[Entry]:
    out: List[Entry] = []
    for line in text.splitlines():
        e = parse_line(line, source)
        if e:
            out.append(e)
    return out


def _norm(text: str) -> str:
    """Kucuk harf, vurgusuz, ё->е, kirpilmis. Turkce harfler (ç ğ ı ö ş ü) KORUNUR.

    Noktali buyuk İ Python'da 'i' + birlesik nokta (U+0307) olur; once duz 'i'ye
    cevrilir ki "İstanbul" ile "istanbul" ayni anahtari versin.
    """
    text = (text or "").replace("İ", "i").strip().lower().replace("ё", "е")
    return C.strip_stress(text).replace("\u0307", "")   # lower() artigi birlesik nokta


def norm_query(text: str) -> str:
    """Sorgu / baslik karsilastirma anahtari: kucuk harf, vurgusuz, ё->е, kirpilmis."""
    return _norm(text)


_WORD_RE = re.compile(r"[a-zа-яё'\-]+", re.IGNORECASE)
_TURKISH_CHARS = "çğıöşü"


# Turkce sorgu ASCII klavyeyle ya da buyuk harfle yazilabilir: karsilastirma anahtari Turkce
# harfleri ASCII karsiliklarina katlar ("sinav" = "SINAV" = "sınav", "cok" = "çok"). Yalnizca
# Turkce taraf bu anahtari kullanir; gosterilen metin hicbir zaman degismez.
_TR_FOLD = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g", "ç": "c",
                          "Ç": "c", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u", "â": "a", "î": "i", "û": "u"})


def tr_fold(normalised: str) -> str:
    """_norm'dan gecmis metni Turkce karsilastirma anahtarina katla."""
    return (normalised or "").translate(_TR_FOLD)


# Katlanarak bulunan eslesme dogrudan eslesmenin altinda kalir: "ask" yazan kullanici Ingilizce
# "to ask" bekler, Turkce "aşk" degil; ama "sinav" gibi karsiligi olmayan sorgu yine bulunur.
FOLD_MAX = 59        # katlanmis puanlar bu tavana oranlanir: tam eslesme 59, onek 35, icerme 5


def _tr_norm(text: str) -> str:
    """Turkce taraf icin karsilastirma anahtari (yalnizca eslestirmede kullanilir)."""
    return tr_fold(_norm(text))


def looks_turkish(text: str) -> bool:
    """Metinde Turkceye ozgu harf var mi? (yalnizca ipucu; sonuc yoksa yon tahmini icin)"""
    return any(ch in _TURKISH_CHARS for ch in _norm(text))


# --------------------------------------------------------------------------
# Arama yonu
# --------------------------------------------------------------------------
TARGET = C.TARGET_LANG                                  # "ru"
DIR_AUTO = "auto"
DIR_TO_EN = f"{TARGET}2en"                               # ru2en: baslik aranir, Ingilizce hedef
DIR_FROM_EN = f"en2{TARGET}"                             # en2ru: Ingilizce aranir
DIR_TO_TR = f"{TARGET}2tr"                               # ru2tr: baslik aranir, Turkce hedef
DIR_FROM_TR = f"tr2{TARGET}"                             # tr2ru: Turkce aranir
DIRECTIONS = (DIR_AUTO, DIR_TO_EN, DIR_FROM_EN, DIR_TO_TR, DIR_FROM_TR)

# yon -> aranan (kaynak) alan: "head" baslik, "en" Ingilizce, "tr" Turkce
_SOURCE_FIELD = {DIR_TO_EN: "head", DIR_TO_TR: "head", DIR_FROM_EN: "en", DIR_FROM_TR: "tr"}
# yon -> hedef sutun: ru2en -> en, en2ru -> ru, ru2tr -> tr, tr2ru -> ru
_TARGET_FIELD = {DIR_TO_EN: "en", DIR_FROM_EN: TARGET, DIR_TO_TR: "tr", DIR_FROM_TR: TARGET}


def valid_direction(code: str) -> str:
    """Bilinmeyen / bos yon kodu -> "auto"."""
    return code if code in DIRECTIONS else DIR_AUTO


def source_field(direction: str) -> str:
    """Sabit yonde aranan alan ("head" | "en" | "tr"); auto icin "" (sorguya gore)."""
    return _SOURCE_FIELD.get(direction, "")


def target_field(direction: str) -> str:
    """Yonun hedef sutunu: ru2en -> "en", en2ru -> "ru", ru2tr -> "tr", tr2ru -> "ru".

    auto icin Ingilizce ("en") varsayilir; sekme sutun sirasini bununla kurar.
    """
    return _TARGET_FIELD.get(direction, "en")


def gloss_field(direction: str) -> str:
    """Yonun Rusca olmayan tarafi: Turkce iceren yonlerde "tr", digerlerinde "en"."""
    return "tr" if direction in (DIR_TO_TR, DIR_FROM_TR) else "en"


def headword_direction(direction: str) -> str:
    """Yonun baslik-tarafli karsiligi (rastgele kelime, secili madde icin): en2ru -> ru2en, tr2ru -> ru2tr."""
    if direction == DIR_FROM_EN:
        return DIR_TO_EN
    if direction == DIR_FROM_TR:
        return DIR_TO_TR
    return direction if direction in DIRECTIONS else DIR_AUTO


def _senses(field: str) -> List[str]:
    return [s.strip() for s in re.split(r"[;,]", field) if s.strip()]


class LookupResult(list):
    """lookup() sonucu: Entry listesi + cozumlenen yon (`direction`).

    Duz liste gibi davranir (eski cagiranlar / testler degismez); sekme etkin yonu okur.
    """

    def __init__(self, entries: Iterable[Entry] = (), direction: str = DIR_AUTO) -> None:
        super().__init__(entries)
        self.direction = direction


# --------------------------------------------------------------------------
# Sozluk
# --------------------------------------------------------------------------
class Dictionary:
    """Bellek ici indeksli, uc dilli sozluk."""

    def __init__(self, entries: Iterable[Entry] = ()) -> None:
        self._entries: List[Entry] = []
        self._seen: Dict[tuple, int] = {}          # tekillik anahtari -> _entries indeksi
        self.extend(entries)

    # -- yukleme -----------------------------------------------------------
    def extend(self, entries: Iterable[Entry]) -> int:
        """Yeni maddeleri ekle; eklenen sayiyi dondur.

        Ayni madde (baslik, tur, Ingilizce) zaten varsa eklenmez; ama yeni gelen Turkce
        karsilik tasiyor ve eldeki tasimiyorsa eldeki madde ZENGINLESTIRILIR (tr dolar).
        Boylece AI'in / kullanicinin sakladigi Turkce gloss gomulu maddeye islenir.
        """
        added = 0
        for e in entries:
            key = self.key(e)
            idx = self._seen.get(key)
            if idx is not None:
                if e.tr and not self._entries[idx].tr:
                    self._entries[idx] = replace(self._entries[idx], tr=e.tr)
                continue
            self._seen[key] = len(self._entries)
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

    def find(self, e: Entry) -> Optional[Entry]:
        """Ayni anahtarli SAKLI madde (zenginlestirilmis guncel nesne) ya da None."""
        idx = self._seen.get(self.key(e))
        return self._entries[idx] if idx is not None else None

    def fill_tr(self, e: Entry, tr: str) -> Optional[Entry]:
        """Sakli maddenin bos Turkce alanini doldur; guncel sakli maddeyi dondur (yoksa None)."""
        idx = self._seen.get(self.key(e))
        if idx is None:
            return None
        cur = self._entries[idx]
        if tr and not cur.tr:
            cur = replace(cur, tr=tr)
            self._entries[idx] = cur
        return cur

    def remove_source(self, source: str) -> None:
        keep = [e for e in self._entries if e.source != source]
        self._entries = []
        self._seen = {}
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
        """Yazi tipine gore kaba tahmin: Kiril -> ru2en, aksi halde en2ru.

        Turkce/Ingilizce ayrimi yazidan yapilamaz; kesin yon `lookup(..., "auto")`
        sonucunun `.direction` alanindadir (en iyi puanli taraf).
        """
        return DIR_TO_EN if C.has_cyrillic(query or "") else DIR_FROM_EN

    def _score_side(self, q: str, side: str) -> List[Tuple[int, int, int, Entry]]:
        """Tek bir tarafi (head / en / tr) puanla: (puan, tr-eksik, uzunluk, madde) listesi."""
        scored = []
        for e in self._entries:
            if side == "head":
                field = _norm(e.headword)
                score = _score(q, field, [field])
            elif side == "tr":
                score = 0
                if e.tr:
                    plain = _norm(e.tr)                                     # once dogrudan eslesme
                    score = _score(q, plain, _senses(plain))
                    if not score:                                           # sonra ASCII/buyuk harf katlamasi
                        folded = _tr_norm(e.tr)
                        score = _score(_tr_norm(q), folded, _senses(folded)) * FOLD_MAX // 100
            else:
                field = _norm(e.translation)
                score = _score(q, field, _senses(field))
            if score:
                scored.append((score, 0 if e.tr else 1, len(e.headword), e))
        return scored

    def lookup(self, query: str, direction: str = DIR_AUTO, limit: int = 200) -> LookupResult:
        """Sorguyu verilen yonde ara; sonuc listesi `.direction` ile etkin yonu tasir.

        Sabit yon: yalnizca kaynak taraf aranir. auto: Kiril => ru2en; Latin => Ingilizce
        ve Turkce taraflari puanlanir, en iyi puan hangi taraftaysa o yon secilir
        (esitlikte Ingilizce; hic sonuc yoksa Turkce harf iceren sorgu tr2ru sayilir).
        Esit puanda Turkce karsiligi olan madde one gelir (ru2tr icin anlamli).
        """
        if isinstance(direction, int):                         # eski cagri: lookup(q, limit)
            direction, limit = DIR_AUTO, direction
        direction = valid_direction(direction)
        q = _norm(query)
        if not q:
            return LookupResult([], self._resolve_empty(query, direction))
        if direction != DIR_AUTO:
            scored = self._score_side(q, source_field(direction))
        elif C.has_cyrillic(query):
            direction, scored = DIR_TO_EN, self._score_side(q, "head")
        else:
            en_side = self._score_side(q, "en")
            tr_side = self._score_side(q, "tr")
            best_en = max((s[0] for s in en_side), default=0)
            best_tr = max((s[0] for s in tr_side), default=0)
            if best_tr > best_en:
                direction, scored = DIR_FROM_TR, tr_side
            elif best_en or not looks_turkish(query):
                direction, scored = DIR_FROM_EN, en_side
            else:
                direction, scored = DIR_FROM_TR, tr_side
        prefer_tr = gloss_field(direction) == "tr"              # Turkce yonlerde gloss'u olan one
        scored.sort(key=lambda t: (-t[0], t[1] if prefer_tr else 0, t[2], t[3].headword))
        return LookupResult((e for _s, _t, _l, e in scored[:limit]), direction)

    @staticmethod
    def _resolve_empty(query: str, direction: str) -> str:
        if direction != DIR_AUTO:
            return direction
        if C.has_cyrillic(query or ""):
            return DIR_TO_EN
        return DIR_FROM_TR if looks_turkish(query or "") else DIR_FROM_EN

    def random_entry(self, rng=None) -> Optional[Entry]:
        import random
        pool = [e for e in self._entries if e.source == SOURCE_BUILTIN] or self._entries
        if not pool:
            return None
        return (rng or random).choice(pool)


_ARTICLE_RE = re.compile(r"^(to|the|a|an) ")


def _score(q: str, field: str, senses: List[str]) -> int:
    """Tam eslesme 100, kelime basi 60, kelime icinde 30, alt dize 10.

    Ingilizce anlamlarin basindaki "to / the / a / an" hem tam eslesmede (95) hem de
    kelime basi eslesmesinde (60) yok sayilir: "ask" sorgusu "to ask (a question)" icin
    60 alir. Aksi halde otomatik yonde Turkce on ek eslesmesi (asker -> 60) Ingilizce
    fiili (30) yenip listeyi TR→RU'ya cevirirdi.
    """
    if not field:
        return 0
    if q == field or q in senses:
        return 100
    bare = [_ARTICLE_RE.sub("", s) for s in senses]
    if q in bare:
        return 95
    if any(s.startswith(q) for s in senses) or any(b.startswith(q) for b in bare) or field.startswith(q):
        return 60
    if re.search(r"(^|[\s\-(])" + re.escape(q), field):
        return 30
    if len(q) >= 3 and q in field:
        return 10
    return 0


# --------------------------------------------------------------------------
# Dosya ice/disa aktarim
# --------------------------------------------------------------------------
CSV_COLUMNS = ("ru", "en", "tr", "pos", "extra", "source")
# baslik satirindaki ad -> sutun (kucuk harf, Turkce/Ingilizce/Rusca esanlamlilar)
_CSV_ALIASES = {
    "ru": "ru", "rus": "ru", "russian": "ru", "rusca": "ru", "rusça": "ru", "headword": "ru",
    "en": "en", "eng": "en", "english": "en", "ingilizce": "en", "translation": "en",
    "tr": "tr", "turkish": "tr", "turkce": "tr", "türkçe": "tr",
    "pos": "pos", "tur": "pos", "tür": "pos", "type": "pos", "part of speech": "pos",
    "extra": "extra", "ek": "extra", "gender": "extra", "aspect": "extra",
    "source": "source", "kaynak": "source",
}


def _header_map(row: List[str]) -> Optional[Dict[str, int]]:
    """Ilk satir baslik satiriysa {sutun: indeks}; degilse None (ru ve en zorunlu)."""
    cols: Dict[str, int] = {}
    for i, cell in enumerate(row):
        name = _CSV_ALIASES.get((cell or "").strip().lower().replace("İ", "i"))
        if name and name not in cols:
            cols[name] = i
    if "ru" in cols and "en" in cols and not any(C.has_cyrillic(c) for c in row):
        return cols
    return None


def read_table(path: Path) -> List[Entry]:
    """CSV/TSV oku.

    Baslik satiri varsa sutunlar ADIYLA eslenir (`ru, en, tr, pos, extra, source` ya da
    esanlamlilari, herhangi bir sirada). Baslik yoksa eski konumsal duzen gecerlidir:
    `ru, en[, pos[, extra]]`. Turkce sutunu her iki durumda da istege baglidir.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    delim = "\t" if path.suffix.lower() in (".tsv", ".txt") or raw.count("\t") > raw.count(",") else ","
    out: List[Entry] = []
    rows = list(csv.reader(raw.splitlines(), delimiter=delim))
    cols = {"ru": 0, "en": 1, "pos": 2, "extra": 3}                # eski konumsal duzen
    if rows and _header_map(rows[0]):
        cols = _header_map(rows[0])
        rows = rows[1:]

    def cell(row, name):
        i = cols.get(name)
        return row[i].strip() if i is not None and len(row) > i else ""

    for row in rows:
        if len(row) < 2:
            continue
        ru, en = cell(row, "ru"), cell(row, "en")
        if not ru or not en:
            continue
        if not C.has_cyrillic(ru):
            if C.has_cyrillic(en):
                ru, en = en, ru
            else:
                continue
        word, stress = split_stress(ru)
        out.append(Entry(word, stress, cell(row, "pos"), cell(row, "extra"), en, SOURCE_USER,
                         mark_all(ru), tr=cell(row, "tr")))
    return out


def write_table(path: Path, entries: Iterable[Entry]) -> int:
    """CSV yaz: `ru, en, tr, pos, extra, source` (baslikli; read_table ayni dosyayi geri okur)."""
    n = 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(CSV_COLUMNS))
        for e in entries:
            w.writerow([e.display.replace(C.STRESS_MARK, "'"), e.translation, e.tr,
                        e.pos, e.extra, e.source])
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
_AI_LIMITS = {"headword": 80, "translation": 240, "translation_en": 240, "translation_tr": 240,
              "tr": 240, "turkish": 240, "example": 300, "note": 400}
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


def query_language(query: str, direction: str = DIR_AUTO) -> str:
    """Sorgunun dili (AI yonergesi icin): Kiril her zaman Rusca; Latin'de sabit yon belirler."""
    if C.has_cyrillic(query or ""):
        return "Cyrillic (Russian)"
    if direction == DIR_FROM_TR:
        return "Latin (Turkish)"
    if direction == DIR_FROM_EN:
        return "Latin (English)"
    return "Latin (probably English or Turkish)"


def ai_prompt(query: str, ui_lang: str = "tr", direction: str = DIR_AUTO) -> Tuple[str, str]:
    """AI icin (sistem yonergesi, kullanici mesaji) cifti. Yanit yalnizca JSON dizisi olmali.

    Modelden HEM Ingilizce (`translation_en`) HEM Turkce (`translation_tr`) karsilik istenir;
    `direction` sorgunun dilini (Ingilizce / Turkce) kesinlestirir, Kiril her zaman Rusca'dir.
    """
    note_lang = _AI_NOTE_LANG.get(ui_lang, "Turkish")
    system = (
        "You are a precise Russian-English-Turkish dictionary engine. You answer ONLY with a JSON "
        "array - no prose, no markdown, no code fences, nothing before or after the array.\n"
        "Each element is an object with exactly these keys:\n"
        '  "headword": the Russian dictionary form (nominative singular for nouns, infinitive for '
        "verbs) in Cyrillic, with an apostrophe placed immediately AFTER the stressed vowel, e.g. "
        "приве'т, кни'га, говори'ть, хорошо'. One-syllable words and words containing ё take no "
        "apostrophe. In multi-word phrases mark the stress of every word.\n"
        '  "pos": one of n v adj adv pron prep conj num part int phr\n'
        '  "extra": for nouns the gender m / f / n (pl for plural-only nouns); for verbs the aspect '
        'ipf / pf; for everything else "".\n'
        '  "translation_en": the English meanings, senses separated by "; " (for example "house; home").\n'
        '  "translation_tr": the Turkish meanings, senses separated by "; " (for example "ev; yuva"), '
        "written with proper Turkish letters (ç ğ ı ö ş ü).\n"
        '  "example": one short natural Russian sentence in Cyrillic that uses the word (no stress marks).\n'
        f'  "note": a short usage note or definition written in {note_lang} (at most 25 words).\n'
        "Return between 1 and 5 objects, the most common sense or word first. Always fill BOTH "
        "translation_en and translation_tr.\n"
        "The query may be Russian, English or Turkish (or occasionally another language written in "
        "Latin letters). If the query is Russian, describe that word in its dictionary form. If it is "
        "English or Turkish, return the Russian words that translate it. Never invent words; when "
        "unsure return fewer entries. If the query is not a real word or phrase, return []."
    )
    user = (f"Query: {query.strip()}\n"
            f"Query script: {query_language(query, direction)}\n"
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
            trans = (_ai_str(obj, "translation_en") or _ai_str(obj, "translation")
                     or _ai_str(obj, "en") or _ai_str(obj, "meaning"))
            turkish = _ai_str(obj, "translation_tr") or _ai_str(obj, "tr") or _ai_str(obj, "turkish")
            if head and trans and not C.has_cyrillic(head) and C.has_cyrillic(trans):
                head, trans = trans, head                       # yon karistiysa duzelt
            head = repair_stress(_clean_headword(head))
            trans = _dedupe_senses(trans)                       # tekrar eden anlamlari at
            turkish = "" if C.has_cyrillic(turkish) else _dedupe_senses(turkish)
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
                             example, note, turkish))
        except Exception:                                       # noqa: BLE001
            continue
        if len(out) >= limit:
            break
    return out


def _dedupe_senses(text: str) -> str:
    """'; ' ile ayrilmis anlam listesinde tekrarlari (sira korunarak) at."""
    return "; ".join(dict.fromkeys(t.strip() for t in (text or "").split(";") if t.strip()))


def ai_lookup(client, query: str, ui_lang: str = "tr", model: str = "",
              direction: str = DIR_AUTO) -> List[Entry]:
    """Sorguyu AI'a sor ve yapisal maddeleri dondur.

    Baglanti / model hatasi (AIError) cagirana yayilir ki sekme cevrimdisi
    mesajini gosterebilsin; anlamsiz cikti ise sessizce bos liste olur.
    `direction` yalnizca yonergedeki sorgu dilini kesinlestirir (tr2ru -> Turkce).
    """
    query = (query or "").strip()
    if not query or client is None:
        return []
    system, user = ai_prompt(query, ui_lang, direction)
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

    Satirlar `(ru, en[, pos[, extra[, source[, example[, note[, tr]]]]]])` demetleri ya da
    `dict_entries` sozlukleri olabilir; saklanan "source" degeri Entry.source'a
    ("user" / "ai") aktarilir ki sekme maddeleri etiketleyebilsin. Gomulu bir maddeyle
    ayni olan satir eklenmez ama Turkce karsiligi varsa gomulu maddeye islenir.
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
        turkish = _row_field(r, 7, "tr")
        word, stress = split_stress(ru)
        users.append(Entry(word, stress, pos or "", extra or "", en, source, mark_all(ru),
                           example or "", note or "", turkish or ""))
    d.extend(users)
    return d
