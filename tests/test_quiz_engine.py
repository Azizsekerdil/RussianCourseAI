# -*- coding: utf-8 -*-
"""Soru uretimi ve cevap dogrulama testleri."""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rca.quiz_engine import (LISTEN, MCQ, TYPE_IN, Question, accuracy, build_session,
                             check_answer, diff_chars, equivalent, make_mcq, make_type_in)

WORDS = [
    {"id": 1, "ru": "молоко", "tr": "sut", "en": "milk"},
    {"id": 2, "ru": "хлеб", "tr": "ekmek", "en": "bread"},
    {"id": 3, "ru": "вода", "tr": "su", "en": "water"},
    {"id": 4, "ru": "дом", "tr": "ev", "en": "house"},
    {"id": 5, "ru": "книга", "tr": "kitap", "en": "book"},
]


def test_mcq_contains_correct_answer():
    """Uretilen secenekler dogru cevabi icermeli."""
    q = make_mcq("молоко", "sut", [w["tr"] for w in WORDS], rng=random.Random(1))
    assert q.kind == MCQ
    assert q.answer in q.options
    assert len(q.options) == 4


def test_mcq_options_are_unique():
    """Secenekler tekrarsiz olmali."""
    q = make_mcq("дом", "ev", ["ev", "ev", "su", "kitap", "ekmek"], rng=random.Random(2))
    assert len(q.options) == len(set(q.options))


def test_mcq_shrinks_when_pool_is_small():
    """Havuz yetersizse secenek sayisi kucultulur, hata verilmez."""
    q = make_mcq("дом", "ev", ["su"], rng=random.Random(3))
    assert q.options == ["ev", "su"] or q.options == ["su", "ev"]


def test_check_answer_ignores_case_and_yo():
    """Buyuk/kucuk harf ve yo/e farki yok sayilir."""
    q = make_type_in("elma", "Ёлка")
    assert check_answer(q, "елка")
    assert check_answer(q, "ЁЛКА")


def test_check_answer_ignores_stress_mark():
    """Vurgu isareti karsilastirmayi bozmaz."""
    q = make_type_in("sut", "молоко")
    assert check_answer(q, "молоко́")


def test_check_answer_rejects_wrong():
    """Farkli kelime yanlis sayilir."""
    q = make_type_in("sut", "молоко")
    assert not check_answer(q, "молодой")


def test_equivalent_matches_word_order():
    """Kelime sirasi farkli ayni kume esdeger sayilir."""
    assert equivalent("kitap okuyorum", "okuyorum kitap")
    assert not equivalent("kitap okuyorum", "kitap yaziyorum")


def test_diff_chars_marks_wrong_letters():
    """Yanlis harfler False isaretlenir."""
    out = diff_chars("малако", "молоко")
    flags = [ok for _c, ok in out]
    assert flags == [True, False, True, False, True, True]


def test_diff_chars_reports_missing_tail():
    """Eksik yazilan harfler de yanlis olarak eklenir."""
    out = diff_chars("моло", "молоко")
    assert len(out) == 6
    assert out[4][1] is False and out[5][1] is False


def test_diff_chars_handles_empty_input():
    """Bos cevap tum harfleri yanlis isaretler."""
    out = diff_chars("", "дом")
    assert len(out) == 3
    assert all(not ok for _c, ok in out)


def test_accuracy():
    """Dogruluk yuzdesi ve bos durum."""
    assert accuracy([]) == 0.0
    assert accuracy([True, True, False, True]) == 75.0
    assert accuracy([False, False]) == 0.0


def test_build_session_respects_limit_and_kinds():
    """Oturum, verilen sinir ve soru tipleriyle kurulur."""
    qs = build_session(WORDS, [MCQ, TYPE_IN], limit=4, rng=random.Random(7))
    assert len(qs) == 4
    assert {q.kind for q in qs} == {MCQ, TYPE_IN}
    assert all(q.word_id for q in qs)


def test_build_session_listen_carries_audio_text():
    """Dinleme sorusu seslendirilecek metni tasir."""
    qs = build_session(WORDS, [LISTEN], limit=2, rng=random.Random(11))
    assert all(q.meta.get("speak") == q.answer for q in qs)


def test_build_session_empty_inputs():
    """Bos girdide bos liste doner, hata olmaz."""
    assert build_session([], [MCQ]) == []
    assert build_session(WORDS, []) == []


def test_build_session_direction_tr2ru():
    """tr2ru yonunde soru Turkce, cevap Rusca olur."""
    qs = build_session(WORDS, [MCQ], limit=3, rng=random.Random(5), direction="tr2ru")
    trs = {w["tr"] for w in WORDS}
    rus = {w["ru"] for w in WORDS}
    assert all(q.prompt in trs and q.answer in rus for q in qs)
