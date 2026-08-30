# -*- coding: utf-8 -*-
"""Aralikli tekrar motoru: SM-2 + Leitner kutulari.

Saf fonksiyonlar - arayuzden ve veritabanindan tamamen bagimsizdir, bu yuzden
dogrudan pytest ile test edilebilir.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

QUALITY_DONTKNOW = 0    # "Bilmiyorum"
QUALITY_UNSURE = 3      # "Emin degilim"
QUALITY_KNOW = 5        # "Biliyorum"

MIN_EASINESS = 1.3
MAX_INTERVAL = 3650      # 10 yil - date tasmasini onler
MAX_BOX = 6
LEITNER_DAYS = {0: 0, 1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 32}


@dataclass
class SRSState:
    """Bir kelimenin tekrar durumu."""
    easiness: float = 2.5
    interval: int = 0
    repetition: int = 0
    box: int = 0
    due: date = None

    def __post_init__(self) -> None:
        if self.due is None:
            self.due = date.today()


def review(state: SRSState, quality: int, today: date = None) -> SRSState:
    """SM-2 adimini uygula ve YENI durumu dondur (girdiyi degistirmez).

    quality 0..5 arasidir; 3'un altindaki cevaplar tekrar sayacini sifirlar.
    """
    today = today or date.today()
    q = max(0, min(5, int(quality)))

    ef = state.easiness + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    ef = max(MIN_EASINESS, round(ef, 4))

    if q < 3:
        rep = 0
        interval = 0
        box = max(0, state.box - 1)
    else:
        rep = state.repetition + 1
        if rep == 1:
            interval = 1
        elif rep == 2:
            interval = 6
        else:
            interval = max(1, int(round(state.interval * ef)))
        box = min(MAX_BOX, state.box + 1)
        if q == 3:
            interval = max(1, int(round(interval * 0.6)))
        interval = min(MAX_INTERVAL, interval)

    return SRSState(easiness=ef, interval=interval, repetition=rep, box=box,
                    due=today + timedelta(days=interval))


def is_due(state: SRSState, today: date = None) -> bool:
    """Kelime bugun (veya daha once) tekrar edilmeli mi?"""
    today = today or date.today()
    return state.due <= today


def mastery(correct: int, wrong: int, box: int) -> float:
    """0..1 arasi ustalik skoru; deneme sayisi az ise temkinli davranir."""
    total = correct + wrong
    if total == 0:
        return 0.0
    acc = correct / total
    confidence = min(1.0, total / 5.0)
    box_bonus = min(1.0, box / MAX_BOX)
    return round(min(1.0, (acc * confidence * 0.7) + (box_bonus * 0.3)), 4)


def leitner_due(box: int, last_seen: date, today: date = None) -> bool:
    """Saf Leitner kontrolu - SM-2 verisi yoksa yedek yol."""
    today = today or date.today()
    days = LEITNER_DAYS.get(max(0, min(MAX_BOX, box)), 32)
    return (today - last_seen).days >= days


def quality_from_button(name: str) -> int:
    """Buton adini SM-2 kalite puanina cevir."""
    table = {"know": QUALITY_KNOW, "unsure": QUALITY_UNSURE, "dontknow": QUALITY_DONTKNOW}
    return table.get(name, QUALITY_UNSURE)
