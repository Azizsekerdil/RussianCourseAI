# -*- coding: utf-8 -*-
"""Soru uretimi ve cevap dogrulama - arayuzden bagimsiz saf mantik."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple

from rca_common import normalize_ru, strip_stress

MCQ = "mcq"                 # coktan secmeli
TYPE_IN = "type"            # yazarak cevaplama
LISTEN = "listen"           # dinle-yaz
MATCH = "match"             # eslestirme
CASE_PICK = "case"          # dogru hali sec
CONJUGATE = "conj"          # fiili cek

KIND_LABELS = {
    MCQ: "Coktan secmeli",
    TYPE_IN: "Yazarak",
    LISTEN: "Dinleme",
    MATCH: "Eslestirme",
    CASE_PICK: "Dogru hali sec",
    CONJUGATE: "Fiili cek",
}


@dataclass
class Question:
    """Tek bir sinav/alistirma sorusu."""
    kind: str
    prompt: str
    answer: str
    options: List[str] = field(default_factory=list)
    word_id: Any = None
    hint: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


def _distractors(correct: str, pool: Sequence[str], n: int, rng: random.Random) -> List[str]:
    """Havuzdan n adet yanlis secenek uret; dogru cevabi ve tekrarlari eler."""
    seen = {normalize_ru(correct)}
    out: List[str] = []
    candidates = [c for c in pool if normalize_ru(c) not in seen]
    rng.shuffle(candidates)
    for c in candidates:
        key = normalize_ru(c)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= n:
            break
    return out


def make_mcq(prompt: str, correct: str, pool: Sequence[str], n_options: int = 4,
             rng: random.Random = None, **kw) -> Question:
    """Coktan secmeli soru uret. Havuz yetersizse secenek sayisi kendiliginden azalir."""
    rng = rng or random.Random()
    opts = _distractors(correct, pool, max(0, n_options - 1), rng)
    opts.append(correct)
    rng.shuffle(opts)
    return Question(kind=MCQ, prompt=prompt, answer=correct, options=opts, **kw)


def make_type_in(prompt: str, correct: str, **kw) -> Question:
    """Yazarak cevaplanan soru uret."""
    return Question(kind=TYPE_IN, prompt=prompt, answer=correct, **kw)


def check_answer(question: Question, given: str) -> bool:
    """Cevabi normalize ederek karsilastir: buyuk/kucuk harf, yo/e ve vurgu farki yok sayilir."""
    return normalize_ru(given) == normalize_ru(question.answer)


def equivalent(a: str, b: str) -> bool:
    """Iki cevap esdeger mi? Ceviri sorularinda tolerans icin kullanilir."""
    na, nb = normalize_ru(a), normalize_ru(b)
    if na == nb:
        return True
    sa, sb = set(na.split()), set(nb.split())
    return bool(sa) and sa == sb


def diff_chars(given: str, correct: str) -> List[Tuple[str, bool]]:
    """Harf harf karsilastirma.

    Her karakter icin (karakter, dogru_mu) cifti dondurur. Kullanici eksik
    yazdiysa kalan dogru harfler de yanlis olarak eklenir.
    """
    g = strip_stress(given or "")
    c = strip_stress(correct or "")
    out: List[Tuple[str, bool]] = []
    for i, ch in enumerate(g):
        ok = i < len(c) and ch.lower() == c[i].lower()
        out.append((ch, ok))
    for ch in c[len(g):]:
        out.append((ch, False))
    return out


def accuracy(results: Sequence[bool]) -> float:
    """Dogru oranini yuzde olarak dondur; sonuc yoksa 0.0."""
    if not results:
        return 0.0
    return round(100.0 * sum(1 for r in results if r) / len(results), 1)


def build_session(words: Sequence[Dict[str, Any]], kinds: Sequence[str],
                  limit: int = 20, rng: random.Random = None,
                  direction: str = "ru2tr") -> List[Question]:
    """Kelime kayitlarindan karisik bir soru oturumu kur.

    words: en az id / ru / tr anahtarlarini iceren sozluk listesi.
    """
    rng = rng or random.Random()
    if not words or not kinds:
        return []
    pool_tr = [w.get("tr", "") for w in words if w.get("tr")]
    pool_ru = [w.get("ru", "") for w in words if w.get("ru")]
    qs: List[Question] = []
    chosen = list(words)
    rng.shuffle(chosen)
    for w in chosen[:limit]:
        kind = kinds[len(qs) % len(kinds)]
        ru, tr, wid = w.get("ru", ""), w.get("tr", ""), w.get("id")
        if not ru or not tr:
            continue
        if kind == MCQ:
            if direction == "ru2tr":
                qs.append(make_mcq(ru, tr, pool_tr, rng=rng, word_id=wid))
            else:
                qs.append(make_mcq(tr, ru, pool_ru, rng=rng, word_id=wid))
        elif kind == LISTEN:
            qs.append(Question(kind=LISTEN, prompt=ru, answer=ru, word_id=wid,
                               hint=tr, meta={"speak": ru}))
        elif kind == MATCH:
            qs.append(Question(kind=MATCH, prompt=ru, answer=tr, word_id=wid))
        else:
            qs.append(make_type_in(tr, ru, word_id=wid, hint=str(w.get("en") or "")))
    return qs
