# -*- coding: utf-8 -*-
"""Gercek modelle uctan uca deneme (ISTEGE BAGLI).

Varsayilan test kosusunda ATLANIR; modelleri indirmez, aga cikmaz. Calistirmak icin
Whisper modeli ve Piper Rusca sesi onceden indirilmis olmali:

    set RCA_REAL_WHISPER=1 && python -m pytest tests/test_whisper_real.py -q
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytestmark = pytest.mark.skipif(os.environ.get("RCA_REAL_WHISPER") != "1",
                                reason="RCA_REAL_WHISPER=1 verilmedi")


def test_piper_speech_is_recognised_by_whisper(tmp_path):
    from rca import audiobook as A
    from rca import whisper_engine as W
    have = W.downloaded_models()
    if not have:
        pytest.skip("indirilmis Whisper modeli yok")
    eng = A.PiperTTS()
    ok, why = eng.status()
    if not ok:
        pytest.skip(why)
    text = "Меня зовут Анна. Я изучаю русский язык."
    pcm = eng.synth(text, "ru")
    path = tmp_path / "s.mp3"
    A.encode_mp3(pcm, path, sr=eng.sample_rate)
    model = W.DEFAULT_MODEL if W.DEFAULT_MODEL in have else have[0]
    e = W.WhisperEngine()
    tr = e.transcribe(str(path), W.WhisperOptions(model=model, language="ru"))
    words, score = W.compare_pronunciation(text, tr)
    assert score >= 80, (tr.text, score)
    langs = e.detect_language(str(path), W.WhisperOptions(model=model))
    assert langs[0][0] == "ru"
    batched = e.transcribe(str(path), W.WhisperOptions(model=model, language="ru", batched=True))
    assert W.compare_pronunciation(text, batched)[1] >= 80
    e.unload()
