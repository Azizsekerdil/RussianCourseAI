# -*- coding: utf-8 -*-
"""SM-2 / Leitner aralikli tekrar motoru testleri (arayuzsuz saf mantik)."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rca.srs import (MIN_EASINESS, QUALITY_DONTKNOW, QUALITY_KNOW, QUALITY_UNSURE,
                     SRSState, is_due, leitner_due, mastery, quality_from_button, review)

TODAY = date(2026, 1, 1)


def test_first_correct_gives_one_day():
    """Ilk dogru cevap araligi 1 gun yapar."""
    out = review(SRSState(), QUALITY_KNOW, TODAY)
    assert out.repetition == 1
    assert out.interval == 1
    assert out.due == TODAY + timedelta(days=1)
    assert out.box == 1


def test_second_correct_gives_six_days():
    """Ikinci dogru cevap araligi 6 gune cikarir."""
    s = review(SRSState(), QUALITY_KNOW, TODAY)
    out = review(s, QUALITY_KNOW, TODAY)
    assert out.repetition == 2
    assert out.interval == 6


def test_third_correct_multiplies_by_easiness():
    """Ucuncuden itibaren aralik easiness ile carpilir."""
    s = SRSState()
    for _ in range(2):
        s = review(s, QUALITY_KNOW, TODAY)
    out = review(s, QUALITY_KNOW, TODAY)
    assert out.repetition == 3
    assert out.interval == round(6 * out.easiness)
    assert out.interval > 6


def test_wrong_answer_resets_repetition():
    """Bilmiyorum tekrar sayacini sifirlar ve ayni gune dondurur."""
    s = SRSState()
    for _ in range(3):
        s = review(s, QUALITY_KNOW, TODAY)
    out = review(s, QUALITY_DONTKNOW, TODAY)
    assert out.repetition == 0
    assert out.interval == 0
    assert out.due == TODAY
    assert out.box == s.box - 1


def test_easiness_never_below_floor():
    """Art arda yanlislarda easiness alt sinirin altina inmez."""
    s = SRSState()
    for _ in range(20):
        s = review(s, QUALITY_DONTKNOW, TODAY)
    assert s.easiness == MIN_EASINESS


def test_unsure_shortens_interval():
    """Emin degilim, biliyoruma gore daha kisa aralik verir."""
    base = SRSState()
    for _ in range(2):
        base = review(base, QUALITY_KNOW, TODAY)
    sure = review(base, QUALITY_KNOW, TODAY)
    unsure = review(base, QUALITY_UNSURE, TODAY)
    assert unsure.interval < sure.interval
    assert unsure.interval >= 1


def test_box_caps_at_max():
    """Leitner kutusu ust sinirda kalir."""
    s = SRSState()
    for _ in range(30):
        s = review(s, QUALITY_KNOW, TODAY)
    assert s.box == 6


def test_is_due():
    """Vadesi bugun veya gecmiste olan kelime tekrar edilmelidir."""
    assert is_due(SRSState(due=TODAY), TODAY)
    assert is_due(SRSState(due=TODAY - timedelta(days=3)), TODAY)
    assert not is_due(SRSState(due=TODAY + timedelta(days=1)), TODAY)


def test_leitner_due_uses_box_interval():
    """Saf Leitner: kutu buyudukce bekleme suresi uzar."""
    assert leitner_due(1, TODAY - timedelta(days=1), TODAY)
    assert not leitner_due(3, TODAY - timedelta(days=2), TODAY)
    assert leitner_due(3, TODAY - timedelta(days=4), TODAY)


def test_mastery_is_zero_without_attempts():
    """Deneme yoksa ustalik 0 - tahmin uretilmez."""
    assert mastery(0, 0, 0) == 0.0


def test_mastery_grows_with_accuracy_and_box():
    """Ustalik dogruluk ve kutu ile birlikte artar."""
    low = mastery(3, 3, 1)
    high = mastery(10, 0, 6)
    assert 0 < low < high <= 1.0


def test_mastery_is_cautious_with_few_attempts():
    """Tek denemede tam puan verilmez."""
    assert mastery(1, 0, 0) < mastery(5, 0, 0)


def test_quality_from_button():
    """Buton adlari dogru kalite puanina cevrilir."""
    assert quality_from_button("know") == QUALITY_KNOW
    assert quality_from_button("unsure") == QUALITY_UNSURE
    assert quality_from_button("dontknow") == QUALITY_DONTKNOW
    assert quality_from_button("bilinmeyen") == QUALITY_UNSURE


def test_review_does_not_mutate_input():
    """review() girdiyi degistirmez, yeni durum dondurur."""
    s = SRSState()
    snapshot = (s.easiness, s.interval, s.repetition, s.box, s.due)
    review(s, QUALITY_KNOW, TODAY)
    assert (s.easiness, s.interval, s.repetition, s.box, s.due) == snapshot
