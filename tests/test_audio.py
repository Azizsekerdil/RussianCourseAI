# -*- coding: utf-8 -*-
"""Whisper motoru, sesli kitap motoru ve calar icin testler.

Agir modeller (Whisper agirliklari, Piper sesleri) INDIRILMEZ ve aga cikilmaz:
TTS yerine sinus dalgasi ureten sahte bir motor, Whisper yerine elle kurulmus
Transcript nesneleri kullanilir. PyAV / numpy yoksa ilgili testler atlanir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rca import whisper_engine as W  # noqa: E402


# ==========================================================================
# Whisper: secenekler, disa aktarim, telaffuz
# ==========================================================================
def _tr():
    words = [W.Word(0.0, 0.4, " Я", 0.98), W.Word(0.4, 1.0, " изучаю", 0.42),
             W.Word(1.0, 1.6, " русский", 0.95), W.Word(1.6, 2.2, " язык.", 0.91)]
    seg1 = W.Segment(0, 0.0, 2.2, " Я изучаю русский язык.", words=words)
    seg2 = W.Segment(1, 2.5, 65.25, " Это книга.")
    return W.Transcript([seg1, seg2], language="ru", language_probability=0.97,
                        duration=66.0, all_language_probs=[("ru", 0.97), ("uk", 0.02)],
                        model="tiny", device="cpu/int8")


def test_options_roundtrip_keeps_every_field():
    o = W.WhisperOptions(model="small", language="ru", temperature=(0.0, 0.5), beam_size=3,
                         vad_filter=False, hotwords="Москва", batched=True, batch_size=8)
    back = W.WhisperOptions.from_dict(json.loads(json.dumps(o.to_dict())))
    assert back == o
    # Bilinmeyen anahtarlar sessizce yok sayilir, sonsuz VAD suresi korunur
    o2 = W.WhisperOptions.from_dict({"bogus": 1, "vad_max_speech_duration_s": None})
    assert o2.vad_max_speech_duration_s == float("inf")


def test_build_kwargs_maps_all_decoding_options():
    eng = W.WhisperEngine()
    kw = eng.build_kwargs(W.WhisperOptions(language="ru", task="translate", temperature=(0.2,),
                                           vad_filter=True, vad_min_silence_duration_ms=700,
                                           initial_prompt="Урок", word_timestamps=True))
    assert kw["language"] == "ru" and kw["task"] == "translate"
    assert kw["temperature"] == 0.2                      # tek deger -> float
    assert kw["vad_parameters"]["min_silence_duration_ms"] == 700
    assert "max_speech_duration_s" not in kw["vad_parameters"]   # sonsuz -> verilmez
    assert kw["initial_prompt"] == "Урок" and kw["word_timestamps"] is True
    kw2 = eng.build_kwargs(W.WhisperOptions(vad_filter=False, language=None))
    assert kw2["vad_parameters"] is None and kw2["language"] is None


def test_filter_kwargs_drops_unknown_arguments():
    def fn(audio, language=None, beam_size=5):
        return None
    out = W.WhisperEngine._filter_kwargs(fn, {"language": "ru", "beam_size": 1, "hotwords": "x"})
    assert out == {"language": "ru", "beam_size": 1}


def test_exporters_produce_valid_formats():
    tr = _tr()
    srt = W.to_srt(tr)
    assert srt.startswith("1\n00:00:00,000 --> 00:00:02,200\nЯ изучаю русский язык.")
    assert "00:00:02,500 --> 00:01:05,250" in srt
    vtt = W.to_vtt(tr)
    assert vtt.startswith("WEBVTT") and "00:00:02.500 --> 00:01:05.250" in vtt
    assert W.to_lrc(tr).splitlines()[1] == "[00:02.50]Это книга."
    assert W.to_tsv(tr).splitlines()[1] == "0\t2200\tЯ изучаю русский язык."
    assert W.to_txt(tr) == "Я изучаю русский язык.\nЭто книга.\n"
    back = W.transcript_from_json(W.to_json(tr))
    assert back.text == tr.text and back.segments[0].words[1].probability == 0.42
    assert back.all_language_probs[0] == ("ru", 0.97)
    assert set(W.EXPORTERS) == set(W.EXPORT_FORMATS)


def test_export_writes_file(tmp_path):
    p = tmp_path / "out.srt"
    W.export(_tr(), "srt", str(p))
    assert "русский" in p.read_text(encoding="utf-8")


def test_pronunciation_perfect_and_flags_unsure_words():
    one = W.Transcript(_tr().segments[:1])
    words, score = W.compare_pronunciation("Я изучаю ру́сский язык.", one)
    assert score == 100.0
    assert [w.status for w in words] == ["ok"] * 4
    assert words[1].probability < 0.5                    # arayuz bunu "belirsiz" gosterir


def test_pronunciation_detects_wrong_missing_and_extra():
    heard = W.Transcript([W.Segment(0, 0, 2, " Я изучаю русские книги очень")])
    words, score = W.compare_pronunciation("Я изучаю русский язык", heard)
    statuses = [w.status for w in words]
    assert statuses[:2] == ["ok", "ok"]
    assert "wrong" in statuses and "extra" in statuses
    assert 0 < score < 100
    words, score = W.compare_pronunciation("Я изучаю русский язык", W.Transcript([]))
    assert score == 0 and all(w.status == "missing" for w in words)


def test_yo_and_case_are_ignored_in_comparison():
    heard = W.Transcript([W.Segment(0, 0, 1, " ЕЛКА")])
    _words, score = W.compare_pronunciation("ёлка", heard)
    assert score == 100.0


def test_model_catalog_and_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(W, "MODELS_DIR", tmp_path)
    models = W.available_models()
    for name in ("tiny", "small", "medium", "large-v3", "large-v3-turbo"):
        assert name in models
    assert models.index("tiny") < models.index("large-v3")
    assert not W.is_downloaded("tiny")
    d = W.model_dir("tiny")
    d.mkdir(parents=True)
    (d / "model.bin").write_bytes(b"x")
    (d / "config.json").write_text("{}")
    assert W.is_downloaded("tiny") and "tiny" in W.downloaded_models()
    W.delete_model("tiny")
    assert not W.is_downloaded("tiny")


def test_translation_capability():
    assert W.translation_capable("large-v3") and W.translation_capable("medium")
    for m in ("large-v3-turbo", "turbo", "distil-large-v3", "small.en"):
        assert not W.translation_capable(m), m


def test_fmt_clock():
    assert W.fmt_clock(5) == "0:05" and W.fmt_clock(3725) == "1:02:05"


def test_save_wav(tmp_path):
    np = pytest.importorskip("numpy")
    import wave
    p = tmp_path / "a.wav"
    W.save_wav(str(p), np.zeros(1600, dtype=np.float32))
    with wave.open(str(p)) as w:
        assert w.getframerate() == 16000 and w.getnframes() == 1600


# ==========================================================================
# Sesli kitap: dil ayirma, betik, bolumler, uretim
# ==========================================================================
from rca import audiobook as A  # noqa: E402


def test_split_languages_tags_each_run():
    segs = A.split_languages("Yalın hâl, Именительный: kim, ne? Örnek: Это книга. Bu bir kitap.")
    langs = [s.lang for s in segs]
    assert langs == ["tr", "ru", "tr", "ru", "tr"]
    assert segs[1].text == "Именительный"
    assert all(not A.C.has_cyrillic(s.text) for s in segs if s.lang != "ru")


def test_guess_latin_lang():
    assert A.guess_latin_lang("Kitap okuyorum") == "tr"
    assert A.guess_latin_lang("ağaç") == "tr"
    assert A.guess_latin_lang("to collect something") == "en"
    assert A.guess_latin_lang("the book is on the table") == "en"


def test_heuristic_script_drops_furniture_and_transliteration():
    text = "Жж  жэ\n[zhe]\nvoiced as in leisure.\nжена = wife\n05 / Günlük yaşam ve saatler 41 / 235\n41"
    segs = A.heuristic_page_script(text)
    joined = " ".join(s.text for s in segs)
    assert "[zhe]" not in joined and "41 / 235" not in joined
    assert any(s.lang == "ru" and "жена" in s.text for s in segs)
    assert any(s.lang == "en" and "leisure" in s.text for s in segs)


def test_slugify_handles_turkish_letters():
    assert A.slugify("Rusça Başlangıç Eğitim Kitabı") == "rusca-baslangic-egitim-kitabi"
    assert A.slugify("!!!") == "kitap"


def test_speakable_strips_stress_and_symbols():
    assert A.speakable("ру́сский  …  •") == "русский ..."


def _make_book(root: Path, pages: int = 6) -> A.Book:
    (root / "script").mkdir(parents=True)
    toc = [{"level": 0, "title": "Bölüm 1", "page": 2},
           {"level": 1, "title": "Alt 1a", "page": 2},
           {"level": 1, "title": "Alt 1b", "page": 3},
           {"level": 0, "title": "Bölüm 2", "page": 5}]
    (root / "book.json").write_text(json.dumps({"title": "Test Kitap", "pages": pages, "toc": toc,
                                                "script_source": "curated"}), encoding="utf-8")
    for p in range(1, pages + 1):
        segs = [{"lang": "tr", "kind": "heading", "text": f"Sayfa {p}"},
                {"lang": "ru", "kind": "term", "text": "кни́га"},
                {"lang": "en", "kind": "gloss", "text": "book"},
                {"lang": "xx", "kind": "??", "text": "bilinmeyen dil -> tr"},
                {"lang": "ru", "kind": "text", "text": "   "}]
        (root / "script" / f"p{p:03d}.json").write_text(
            json.dumps({"page": p, "segments": segs}, ensure_ascii=False), encoding="utf-8")
    return A.Book(root)


def test_book_sections_tree_and_ranges(tmp_path):
    b = _make_book(tmp_path / "kitap")
    secs = b.sections()
    assert [s.title for s in secs] == ["Kapak ve içindekiler", "Bölüm 1", "Bölüm 2"]
    assert (secs[0].first, secs[0].last) == (1, 1)
    assert (secs[1].first, secs[1].last) == (2, 4)
    assert [(c.title, c.first, c.last) for c in secs[1].children] == [("Alt 1a", 2, 2), ("Alt 1b", 3, 4)]
    assert (secs[2].first, secs[2].last) == (5, 6)
    assert b.section_of(4) == "Alt 1b"
    script = b.script(1)
    assert len(script) == 4                              # bos parca atlanir
    assert script[3].lang == "tr" and script[3].kind == "text"   # bilinmeyen deger duzeltilir


class FakeTTS:
    """Sinus dalgasi ureten sahte motor (her harf ~10 ms)."""
    name = "piper"
    sample_rate = 22050

    def __init__(self):
        self.voices = {"ru": "fake-ru", "tr": "fake-tr", "en": "fake-en"}
        self.rate = 1.0
        self.calls = 0

    def synth(self, text, lang):
        import numpy as np
        self.calls += 1
        n = int(self.sample_rate * 0.01 * max(1, len(text)))
        t = np.arange(n) / self.sample_rate
        f = {"ru": 220, "tr": 330, "en": 440}[lang]
        return (np.sin(2 * np.pi * f * t) * 8000).astype(np.int16)


def test_render_page_writes_mp3_timings_and_skips_when_current(tmp_path):
    pytest.importorskip("av")
    pytest.importorskip("numpy")
    b = _make_book(tmp_path / "kitap")
    eng = FakeTTS()
    assert A.render_page(b, eng, 2) is True
    assert b.has_audio("piper", 2)
    meta = json.loads(b.page_timing("piper", 2).read_text(encoding="utf-8"))
    segs = meta["segments"]
    assert [s["lang"] for s in segs] == ["tr", "ru", "en", "tr"]
    assert all(s["end"] > s["start"] for s in segs)
    assert all(a["end"] <= b2["start"] for a, b2 in zip(segs, segs[1:]))   # sirali, ortusmez
    assert meta["sample_rate"] == 22050 and meta["duration"] > segs[-1]["end"]
    calls = eng.calls
    assert A.render_page(b, eng, 2) is False and eng.calls == calls       # guncel -> atla
    eng.voices = dict(eng.voices, ru="baska-ses")                        # ses degisti -> yeniden
    assert not A.page_is_current(b, eng, 2)
    # MP3 gercekten cozulebilir ve suresi zaman cizelgesiyle uyumlu
    pcm = A.decode_to_pcm(b.page_audio("piper", 2), 22050)
    assert abs(len(pcm) / 22050 - meta["duration"]) < 0.2


def test_render_pages_and_export_sections(tmp_path):
    pytest.importorskip("av")
    b = _make_book(tmp_path / "kitap")
    eng = FakeTTS()
    seen = []
    res = A.render_pages(b, eng, [1, 2, 3], on_progress=lambda k, n, p, m: seen.append((k, n, p, m)))
    assert res == {"rendered": 3, "skipped": 0, "failed": [], "cancelled": False}
    assert [s[0] for s in seen] == [1, 2, 3]
    res = A.render_pages(b, eng, [1, 2, 3, 4])
    assert res["rendered"] == 1 and res["skipped"] == 3
    out = A.export_sections(b, "piper", tmp_path / "out")
    files = sorted(p.name for p in out.glob("*.mp3"))
    assert files == ["01 - Kapak ve içindekiler.mp3", "02 - Bölüm 1.mp3"]   # Bolum 2 uretilmedi
    m3u = next(out.glob("*.m3u8")).read_text(encoding="utf-8")
    assert m3u.startswith("#EXTM3U") and "02 - Bölüm 1.mp3" in m3u
    import av
    with av.open(str(out / "02 - Bölüm 1.mp3")) as c:
        assert c.metadata.get("album") == "Test Kitap"


def test_render_pages_cancel(tmp_path):
    pytest.importorskip("av")
    import threading
    b = _make_book(tmp_path / "kitap")
    ev = threading.Event()
    ev.set()
    res = A.render_pages(b, FakeTTS(), [1, 2], cancel=ev)
    assert res["rendered"] == 0 and res["cancelled"]


def test_list_books_and_create_book_from_pdf(tmp_path, monkeypatch):
    pytest.importorskip("pypdfium2")
    pdf = ROOT / "docs" / "USER_GUIDE.pdf"
    if not pdf.exists():
        pytest.skip("ornek PDF yok")
    monkeypatch.setattr(A, "AUDIOBOOK_DIR", tmp_path / "books")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "p001.json").write_text(json.dumps({"page": 1, "segments": [
        {"lang": "en", "kind": "heading", "text": "Hazir betik"}]}), encoding="utf-8")
    b = A.create_book(str(pdf), "Kılavuz", str(scripts))
    assert b.id == "kilavuz" and b.page_count > 1
    assert b.script(1)[0].text == "Hazir betik"          # ice aktarilan betik
    assert b.script_source() == "mixed"
    assert any(s.text for p in range(2, min(b.page_count, 5) + 1) for s in b.script(p))
    assert [x.id for x in A.list_books()] == ["kilavuz"]


def test_engine_catalogs_and_defaults():
    for cat in (A.PIPER_VOICES, A.EDGE_VOICES):
        assert set(cat) == set(A.LANGS) and all(cat[l] for l in A.LANGS)
    assert A.default_voices("piper")["ru"].startswith("ru_RU")
    assert A.default_voices("edge")["tr"].startswith("tr-TR")
    assert isinstance(A.make_engine("edge"), A.EdgeTTS)
    assert isinstance(A.make_engine("piper"), A.PiperTTS)
    assert A.make_engine("edge", rate=1.25)._rate_str() == "+25%"
    assert A.make_engine("edge", rate=0.8)._rate_str() == "-20%"


# ==========================================================================
# Calar: hiz degisimi perdeyi degil sureyi degistirir
# ==========================================================================
def test_decode_with_speed_changes_duration(tmp_path):
    np = pytest.importorskip("numpy")
    pytest.importorskip("av")
    from rca import audio_player as AP
    sr = 24000
    tone = (np.sin(2 * np.pi * 440 * np.arange(sr * 2) / sr) * 8000).astype(np.int16)
    p = tmp_path / "t.mp3"
    A.encode_mp3(tone, p, sr=sr)
    normal = AP.decode(str(p), 1.0)
    fast = AP.decode(str(p), 2.0)
    slow = AP.decode(str(p), 0.5)
    assert abs(len(normal) / AP.RATE - 2.0) < 0.15
    assert abs(len(fast) / AP.RATE - 1.0) < 0.15
    assert abs(len(slow) / AP.RATE - 4.0) < 0.3
    # perde korunur: sifir gecis sayisi saniye basina ~ ayni (440 Hz -> ~880/sn)
    def zc_per_sec(x):
        return np.sum(np.abs(np.diff(np.sign(x))) > 0) / (len(x) / AP.RATE)
    assert abs(zc_per_sec(fast) - zc_per_sec(normal)) / zc_per_sec(normal) < 0.1


def test_player_position_seek_without_device(tmp_path):
    np = pytest.importorskip("numpy")
    pytest.importorskip("av")
    from rca import audio_player as AP
    p = tmp_path / "t.mp3"
    A.encode_mp3(np.zeros(24000 * 3, dtype=np.int16), p, sr=24000)
    pl = AP.AudioPlayer()
    dur = pl.load(str(p), start=1.0)                     # akis acilmaz (autoplay yok)
    assert abs(dur - 3.0) < 0.2 and abs(pl.position() - 1.0) < 0.01
    pl.seek(99)
    assert abs(pl.position() - dur) < 0.05
    pl.skip(-1.5)
    assert abs(pl.position() - (dur - 1.5)) < 0.05
    pl.close()


# ==========================================================================
# Ayarlar ve ASR yedegi
# ==========================================================================
def test_settings_defaults_are_sanitised(tmp_path, monkeypatch):
    import rca_common as C
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"tts_engine": "bogus", "ab_engine": "x", "whisper": "nope",
                                "ab_voices": [1]}), encoding="utf-8")
    monkeypatch.setattr(C, "SETTINGS_PATH", path)
    monkeypatch.setattr(C, "ensure_dirs", lambda: None)
    s = C.load_settings()
    assert s["tts_engine"] == "system" and s["ab_engine"] == "piper"
    assert s["whisper"] == {} and s["ab_voices"] == {}


def test_asr_reports_reason_when_nothing_available(monkeypatch):
    from rca import tts
    monkeypatch.setattr(W, "installed", lambda: False)
    asr = tts.ASR()
    if asr.backend == "vosk":
        pytest.skip("bu ortamda Vosk modeli kurulu")
    assert not asr.available() and asr.reason


def test_asr_prefers_whisper_when_a_model_exists(monkeypatch):
    from rca import tts
    monkeypatch.setattr(W, "installed", lambda: True)
    monkeypatch.setattr(W, "downloaded_models", lambda: ["small"])
    asr = tts.ASR(whisper_opts={"model": "large-v3"})
    assert asr.backend == "whisper" and asr.whisper_opts["model"] == "small"


def test_speaker_falls_back_to_system_when_neural_unavailable(monkeypatch):
    from rca import tts
    monkeypatch.setattr(A.PiperTTS, "status", lambda self: (False, "yok"))
    sp = tts.Speaker(engine="piper")
    assert sp.neural is None and "hazir degil" in sp.status_text()
    sp.stop()


# --- regresyon: whisper
# ==========================================================================
# Whisper motoru / sekmesi icin bulunan hatalarin regresyon testleri.
# ==========================================================================
def _fake_whisper(monkeypatch, fail_cuda=True):
    """faster_whisper yerine sahte modul: olusturulan aygitlari kaydeder."""
    import types
    built = []

    class FakeModel:
        def __init__(self, path, device="cpu", compute_type="int8", cpu_threads=0):
            built.append(device)
            if device == "cuda" and fail_cuda:
                raise RuntimeError("CUDA yok")
            self.device = device

    mod = types.ModuleType("faster_whisper")
    mod.WhisperModel = FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", mod)
    monkeypatch.setattr(W, "_setup_windows_cuda_dlls", lambda: None)
    monkeypatch.setattr(W, "cuda_device_count", lambda: 1)
    monkeypatch.setattr(W, "is_downloaded", lambda name: True)
    return built


def test_whisper_cpu_fallback_model_is_cached(monkeypatch):
    built = _fake_whisper(monkeypatch)
    eng = W.WhisperEngine()
    opts = W.WhisperOptions(model="tiny", device="auto", compute_type="auto")
    m1 = eng.load(opts)
    m2 = eng.load(opts)
    m3 = eng.load(opts)
    assert built == ["cuda", "cpu"]                      # GPU bir kez denenir, sonra CPU onbellekte
    assert m1 is m2 is m3 and eng.device == "cpu" and eng.compute_type == "int8"
    assert eng.loaded_name() == "tiny"
    eng.unload()
    eng.load(opts)                                       # unload sonrasi GPU yeniden denenir
    assert built == ["cuda", "cpu", "cuda", "cpu"]
    # Ayar degisirse yeniden yuklenir
    eng.load(W.WhisperOptions(model="tiny", device="cpu", compute_type="int8", cpu_threads=2))
    assert built[-1] == "cpu" and len(built) == 5


def test_whisper_load_unload_share_reentrant_lock(monkeypatch):
    import threading
    _fake_whisper(monkeypatch, fail_cuda=False)
    eng = W.WhisperEngine()
    opts = W.WhisperOptions(model="tiny", device="cpu", compute_type="int8")
    with eng._lock:                                      # transcribe gibi: kilit altinda load/unload
        eng.load(opts)
        eng.unload()
    # Kilit baska thread'deyken load beklemeli
    eng._lock.acquire()
    t = threading.Thread(target=lambda: eng.load(opts), daemon=True)
    t.start()
    t.join(0.2)
    assert t.is_alive()
    eng._lock.release()
    t.join(2)
    assert not t.is_alive() and eng.loaded_name() == "tiny"


def test_whisper_recorder_snapshot_from_matches_full_slice():
    np = pytest.importorskip("numpy")
    rec = W.Recorder()
    rec._chunks = [np.arange(i * 100, (i + 1) * 100, dtype="float32") for i in range(5)]
    full = rec.snapshot()
    for start in (0, 1, 99, 100, 250, 499, 500, 900):
        assert np.array_equal(rec.snapshot_from(start), full[start:])


def test_whisper_live_dictation_skips_silence_and_drops_late_results():
    np = pytest.importorskip("numpy")
    texts = []

    class FakeRec:
        def __init__(self):
            self.audio = np.zeros(W.SAMPLE_RATE * 3, dtype="float32")   # 3 sn sessizlik

        def snapshot_from(self, start):
            return self.audio[start:]

        def stop(self):
            return self.audio

    class FakeEngine:
        calls = 0

        def transcribe(self, audio, opts):
            FakeEngine.calls += 1
            if FakeEngine.calls == 1:
                live.offset_after_silence = None
                # 1 sn daha (sessiz) ses gelsin ki bir sonraki adim calissin
                live.rec.audio = np.concatenate([live.rec.audio, np.zeros(W.SAMPLE_RATE, dtype="float32")])
                return W.Transcript([])                  # sessizlik: metin yok
            if FakeEngine.calls > 2:
                raise AssertionError("durdurulduktan sonra dongu devam etti")
            live.offset_after_silence = live._offset
            live._stop.set()                             # durdurma, sonuc donmeden geldi
            return W.Transcript([W.Segment(0, 0, 1, " Привет")])

    live = W.LiveDictation(FakeEngine(), W.WhisperOptions(), lambda c, p: texts.append((c, p)), step=0.001)
    live.rec = FakeRec()
    live._loop()
    # Sessizlikte pencere ilerler (0.3 sn ortusme kalir)
    assert live.offset_after_silence == W.SAMPLE_RATE * 3 - int(0.3 * W.SAMPLE_RATE)
    assert live._offset == live.offset_after_silence     # durdurulan sonuc islenmedi
    # Durdurulduktan sonra gelen sonuc bildirilmez
    assert texts == [("", "")]


def test_whisper_pronunciation_ignores_dialogue_hyphens():
    merged = W.Transcript([W.Segment(0, 0, 2, " - Привет, как дела?", words=[
        W.Word(0.0, 0.5, " - Привет,", 0.9), W.Word(0.5, 1.0, " как", 0.9), W.Word(1.0, 1.5, " дела?", 0.9)])])
    words, score = W.compare_pronunciation("- Привет, как дела?", merged)
    assert score == 100.0 and [w.status for w in words] == ["ok"] * 3
    alone = W.Transcript([W.Segment(0, 0, 2, " Это - книга.", words=[
        W.Word(0.0, 0.5, " Это", 0.9), W.Word(0.5, 0.6, " -", 0.9), W.Word(0.6, 1.0, " книга.", 0.9)])])
    words, score = W.compare_pronunciation("Это - книга.", alone)
    assert score == 100.0 and [w.status for w in words] == ["ok", "ok"]
    # Ic tire korunur
    _w, score = W.compare_pronunciation("Кто-то", W.Transcript([W.Segment(0, 0, 1, " кто-то")]))
    assert score == 100.0


def test_whisper_lrc_never_writes_sixty_seconds():
    tr = W.Transcript([W.Segment(0, 119.999, 121.0, "x"), W.Segment(1, 59.996, 60.5, "y"),
                       W.Segment(2, 61.234, 62.0, "z")])
    lines = W.to_lrc(tr).splitlines()
    assert lines == ["[02:00.00]x", "[01:00.00]y", "[01:01.23]z"]


def test_whisper_batch_targets_never_overwrite(tmp_path):
    pytest.importorskip("tkinter")
    from rca.tabs.whisper_tab import batch_targets
    for n in ("lesson01.mp3", "lesson01.txt", "lesson02.mp3", "a.mp3", "a.mp4"):
        (tmp_path / n).write_bytes(b"")
    files = sorted(p for p in tmp_path.iterdir() if p.suffix in (".mp3", ".mp4"))
    taken = set()
    got = {f.name: tuple(p.name for p in batch_targets(f, files, taken)) for f in files}
    assert got["lesson02.mp3"] == ("lesson02.srt", "lesson02.txt")          # eski davranis
    assert got["lesson01.mp3"] == ("lesson01.mp3.srt", "lesson01.mp3.txt")  # ders metni korunur
    assert got["a.mp3"] == ("a.mp3.srt", "a.mp3.txt")                      # ayni adli medya
    assert got["a.mp4"] == ("a.mp4.srt", "a.mp4.txt")
    assert (tmp_path / "lesson01.txt").read_bytes() == b""


# --- regresyon: audiobook
def _toc_book(root: Path, toc, pages: int) -> A.Book:
    (root / "script").mkdir(parents=True)
    (root / "book.json").write_text(json.dumps({"title": "T", "pages": pages, "toc": toc}),
                                    encoding="utf-8")
    for p in range(1, pages + 1):
        (root / "script" / f"p{p:03d}.json").write_text(json.dumps(
            {"page": p, "segments": [{"lang": "tr", "kind": "text", "text": f"Sayfa {p}"}]}),
            encoding="utf-8")
    return A.Book(root)


def test_sections_keep_outline_order_on_shared_page(tmp_path):
    toc = [{"level": 0, "title": "Ch1", "page": 1}, {"level": 1, "title": "L1.1", "page": 1},
           {"level": 1, "title": "L1.2", "page": 5}, {"level": 1, "title": "L1.3", "page": 10},
           {"level": 0, "title": "Ch2", "page": 10}, {"level": 1, "title": "L2.1", "page": 12}]
    b = _toc_book(tmp_path / "k", toc, 15)
    secs = b.sections()
    assert [s.title for s in secs] == ["Ch1", "Ch2"]
    assert [(c.title, c.first, c.last) for c in secs[0].children] == [
        ("L1.1", 1, 4), ("L1.2", 5, 9), ("L1.3", 10, 10)]
    assert [(c.title, c.first, c.last) for c in secs[1].children] == [("L2.1", 12, 15)]
    assert b.section_of(11) == "Ch2"


def test_top_sections_merge_same_page_siblings(tmp_path):
    toc = [{"level": 0, "title": "A", "page": 3}, {"level": 0, "title": "B", "page": 3},
           {"level": 0, "title": "C", "page": 6}]
    b = _toc_book(tmp_path / "k", toc, 8)
    assert len(b.sections()) == 4                       # agac A'ya hala gidebilir
    top = b.top_sections()
    assert [(s.title, s.first, s.last) for s in top] == [
        ("Kapak ve içindekiler", 1, 2), ("A / B", 3, 5), ("C", 6, 8)]
    pages = [p for s in top for p in s.pages]
    assert pages == sorted(set(pages))                  # ortusme yok


def test_export_sections_strips_control_chars(tmp_path):
    pytest.importorskip("av")
    b = _toc_book(tmp_path / "k", [{"level": 0, "title": "03 /\r\nTanışma\t", "page": 1}], 1)
    A.render_page(b, FakeTTS(), 1)
    out = A.export_sections(b, "piper", tmp_path / "out")
    names = [p.name for p in out.glob("*.mp3")]
    assert names == ["01 - 03 - Tanışma.mp3"]
    m3u = next(out.glob("*.m3u8")).read_text(encoding="utf-8").splitlines()
    assert m3u[2].startswith("#EXTINF") and m3u[2].endswith(",03 / Tanışma") and m3u[3] == names[0]


def test_slugify_transliterates_cyrillic():
    assert A.slugify("Учебник") == "uchebnik"
    assert A.slugify("Грамматика") != A.slugify("Учебник")
    assert A.slugify("Rusça Başlangıç Eğitim Kitabı") == "rusca-baslangic-egitim-kitabi"


def test_create_book_never_overwrites_another_pdfs_folder(tmp_path, monkeypatch):
    pytest.importorskip("pypdfium2")
    import shutil
    src = ROOT / "docs" / "USER_GUIDE.pdf"
    if not src.exists():
        pytest.skip("ornek PDF yok")
    monkeypatch.setattr(A, "AUDIOBOOK_DIR", tmp_path / "books")
    p1, p2 = tmp_path / "a.pdf", tmp_path / "b.pdf"
    shutil.copyfile(src, p1)
    shutil.copyfile(src, p2)
    b1 = A.create_book(str(p1), "Ders !!!")
    b2 = A.create_book(str(p2), "Ders ???")             # ayni slug, farkli PDF
    assert b1.id == "ders" and b2.id == "ders-2"
    assert A.Book(b1.root).source_pdf == str(p1)        # ilk kitap ezilmedi
    # ayni PDF yeniden -> ayni klasor (uretilmis ses korunur)
    assert A.create_book(str(p2), "Ders ???").id == "ders-2"
    assert A.create_book(str(p1), "Ders !!!").id == "ders"
    # transliterasyondan once olusmus eski klasor ("kitap") ayni PDF icin yeniden kullanilir
    legacy = A.AUDIOBOOK_DIR / "kitap"
    (legacy / "script").mkdir(parents=True)
    (legacy / "book.json").write_text(json.dumps({"title": "Учебник", "source_pdf": str(p1),
                                                  "pages": 1, "toc": []}), encoding="utf-8")
    assert A.create_book(str(p1), "Учебник").id == "kitap"
    assert A.create_book(str(p2), "Учебник").id == "uchebnik"
    assert len(A.list_books()) == 4


def test_piper_download_is_atomic(tmp_path, monkeypatch):
    dv = pytest.importorskip("piper.download_voices")
    monkeypatch.setattr(A, "PIPER_DIR", tmp_path / "piper")

    def broken(voice, d, force_redownload=False):
        (Path(d) / f"{voice}.onnx").write_bytes(b"yarim")
        raise OSError("ag koptu")
    monkeypatch.setattr(dv, "download_voice", broken)
    with pytest.raises(OSError):
        A.PiperTTS.download_voice("ru_RU-irina-medium")
    assert list(A.PIPER_DIR.iterdir()) == []            # yarim dosya / gecici klasor kalmaz

    def ok(voice, d, force_redownload=False):
        (Path(d) / f"{voice}.onnx").write_bytes(b"model")
        (Path(d) / f"{voice}.onnx.json").write_text("{}")
    monkeypatch.setattr(dv, "download_voice", ok)
    A.PiperTTS.download_voice("ru_RU-irina-medium")
    assert sorted(p.name for p in A.PIPER_DIR.iterdir()) == [
        "ru_RU-irina-medium.onnx", "ru_RU-irina-medium.onnx.json"]


class FakePiper(A.PiperTTS):
    """isinstance(PiperTTS) olan sahte motor: indirme cagrilari kaydedilir."""
    def __init__(self, missing):
        super().__init__()
        self.voices = {"ru": "fake-ru", "tr": "fake-tr", "en": "fake-en"}
        self.missing = list(missing)
        self.log = []

    def missing_voices(self):
        return list(self.missing)

    def download_voice(self, v):
        self.log.append(("indir", v))
        self.missing.remove(v)

    def synth(self, text, lang):
        self.log.append(("synth", lang))
        return FakeTTS().synth(text, lang)


def test_render_pages_downloads_missing_voices_once_before_rendering(tmp_path):
    pytest.importorskip("av")
    b = _make_book(tmp_path / "kitap")
    eng = FakePiper(["fake-ru", "fake-en"])
    res = A.render_pages(b, eng, [1, 2])
    assert res["rendered"] == 2
    assert eng.log[:2] == [("indir", "fake-ru"), ("indir", "fake-en")]
    assert [x for x in eng.log if x[0] == "indir"] == eng.log[:2]


class SlowEdge(A.EdgeTTS):
    def __init__(self):
        super().__init__()
        self.voices = {"ru": "fake-ru", "tr": "fake-tr", "en": "fake-en"}

    def synth_many(self, items, concurrency=6):
        import time
        time.sleep(0.3)
        return [FakeTTS().synth(t, l) for t, l in items]


def test_render_pages_pool_cancel_stops_remaining_work(tmp_path):
    pytest.importorskip("av")
    import threading
    import time
    b = _make_book(tmp_path / "kitap", pages=12)
    ev = threading.Event()
    seen = []

    def prog(k, n, p, m):
        seen.append(p)
        ev.set()
    t = time.time()
    res = A.render_pages(b, SlowEdge(), list(range(1, 13)), on_progress=prog, cancel=ev, workers=2)
    assert res["cancelled"] and res["rendered"] < 12
    assert len(seen) < 12 and time.time() - t < 3.0


def test_cli_export_without_engine_and_no_render(tmp_path, monkeypatch):
    pytest.importorskip("av")
    import importlib.util
    spec = importlib.util.spec_from_file_location("make_audiobook", ROOT / "tools" / "make_audiobook.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    books = tmp_path / "books"
    b = _make_book(books / "kitap")
    A.render_page(b, FakeTTS(), 1)
    monkeypatch.setattr(A, "AUDIOBOOK_DIR", books)
    monkeypatch.setattr(A.PiperTTS, "status", lambda self: (False, "piper-tts kurulu degil"))
    rc = cli.main(["--book", "kitap", "--engine", "piper", "--no-render", "--export",
                   "--out", str(tmp_path / "out")])
    assert rc == 0 and list((tmp_path / "out").glob("*.mp3"))


# --- regresyon: entegrasyon
# ==========================================================================
# Speaker (Edge tek deneme + bekleme), Ayarlar (Edge onayi, motor yenileme),
# Telaffuz sayfasi (ASR yenileme), i18n ters arama cakismalari
# ==========================================================================
def _int_sounddevice(monkeypatch):
    """sounddevice yerine sahte modul: calinan ornek sayilarini kaydeder."""
    import types
    played = []
    monkeypatch.setitem(sys.modules, "sounddevice",
                        types.SimpleNamespace(play=lambda pcm, sr, blocking=True: played.append(len(pcm))))
    return played


def test_speaker_edge_offline_is_single_attempt_and_cools_down(monkeypatch):
    pytest.importorskip("numpy")
    import time
    from rca import tts
    _int_sounddevice(monkeypatch)
    calls = []

    class OfflineEdge(A.EdgeTTS):
        async def _synth_async(self, text, lang):
            calls.append(text)
            raise OSError("ag yok")

    sp = tts.Speaker(engine="system")
    try:
        sp.neural_name, sp.neural = "edge", OfflineEdge()
        t0 = time.monotonic()
        assert sp._speak_neural("привет") is False
        assert time.monotonic() - t0 < 1.0 and len(calls) == 1          # yeniden deneme / uyku yok
        assert sp._speak_neural("привет") is False and len(calls) == 1  # bekleme suresi: motor atlanir
        sp.set_engine("system")
        assert sp._neural_down_until == 0.0                              # yeni secim beklemeyi sifirlar
    finally:
        sp.stop()


def test_speaker_edge_hang_times_out(monkeypatch):
    pytest.importorskip("numpy")
    import asyncio
    import time
    from rca import tts
    _int_sounddevice(monkeypatch)

    class HangingEdge(A.EdgeTTS):
        async def _synth_async(self, text, lang):
            await asyncio.sleep(30)
            return b"x"

    sp = tts.Speaker(engine="system")
    try:
        sp.EDGE_TIMEOUT = 0.2
        sp.neural_name, sp.neural = "edge", HangingEdge()
        t0 = time.monotonic()
        assert sp._speak_neural("привет") is False
        assert time.monotonic() - t0 < 5.0 and sp._neural_down_until > time.monotonic()
    finally:
        sp.stop()


def test_speaker_edge_success_plays_decoded_audio(monkeypatch):
    np = pytest.importorskip("numpy")
    from rca import tts
    played = _int_sounddevice(monkeypatch)

    class OkEdge(A.EdgeTTS):
        async def _synth_async(self, text, lang):
            return b"mp3"

    monkeypatch.setattr(A, "decode_to_pcm", lambda data, rate=A.SR: np.ones(100, dtype=np.int16))
    sp = tts.Speaker(engine="system")
    try:
        sp.neural_name, sp.neural = "edge", OkEdge()
        assert sp._speak_neural("привет") is True and played and played[0] >= 100
    finally:
        sp.stop()


class _IntVar:
    """tk degiskeni yerine basit kutu."""

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _IntSpeaker:
    """set_engine cagrilarini kaydeden sahte Speaker."""

    def __init__(self, engine="system", voices=None, neural=None):
        self.neural_name, self._neural_voices, self.neural = engine, voices or {}, neural
        self.calls = []

    def set_rate(self, rate):
        pass

    def set_engine(self, engine, voices=None):
        self.calls.append((engine, voices))
        self.neural_name, self._neural_voices = engine, voices or {}

    def status_text(self):
        return "durum"


def _int_settings_tab(monkeypatch, settings, speaker, engine_label_key):
    """Tk kurmadan SettingsTab.save() calistirilabilen bir ornek."""
    import types
    import rca_common as C
    from rca import i18n
    from rca.tabs import settings_tab as ST
    monkeypatch.setattr(C, "save_settings", lambda s: None)
    app = types.SimpleNamespace(
        settings=settings, speaker=speaker, profile_id=1,
        t=lambda k: i18n.t(k, "tr"), u=lambda x: x, ui_lang=lambda: "tr",
        refresh_ai_clients=lambda: None, set_ui_language=lambda c: None, retheme=lambda: None,
        check_ai=lambda: None, set_status=lambda m: None,
        repos=types.SimpleNamespace(profiles=types.SimpleNamespace(set_cefr=lambda pid, c: None)))
    tab = ST.SettingsTab.__new__(ST.SettingsTab)
    tab.app = app
    tab._tts_codes = {"system": "set.tts_system", "piper": "set.tts_piper", "edge": "set.tts_edge"}
    for name, val in dict(lang=i18n.LANG_NAMES["tr"], theme=settings.get("theme", "dark"), goal=20,
                          cefr="A1", tts_on=True, rate=150, tts_engine=i18n.t(engine_label_key, "tr"),
                          ab_engine=i18n.t("set.tts_piper", "tr"), ai_on=True, ai_base="http://x",
                          ai_model="m", alt_on=False, alt_base="http://y", alt_model="m",
                          dict_ai=i18n.t("d.policy_auto", "tr"), dict_autosave=True, alt_key="").items():
        setattr(tab, name, _IntVar(val))
    lbl = types.SimpleNamespace(configure=lambda **k: None)
    tab.saved = tab.tts_status = lbl
    tab.after = lambda ms, fn: None
    tab._refresh_key_state = lambda: None
    return tab, ST


def test_settings_edge_requires_privacy_consent(monkeypatch):
    from rca import i18n
    settings = {"tts_engine": "system", "ui_lang": "tr", "theme": "dark"}
    sp = _IntSpeaker()
    tab, ST = _int_settings_tab(monkeypatch, settings, sp, "set.tts_edge")
    asked = []
    monkeypatch.setattr(ST.messagebox, "askyesno", lambda *a, **k: asked.append(a) or False)
    tab.save()                                                   # reddedildi: onceki motor kalir
    assert asked and settings["tts_engine"] == "system" and not settings.get("ab_edge_ok")
    assert not sp.calls and tab.tts_engine.get() == i18n.t("set.tts_system", "tr")

    tab.tts_engine.set(i18n.t("set.tts_edge", "tr"))
    monkeypatch.setattr(ST.messagebox, "askyesno", lambda *a, **k: True)
    tab.save()                                                   # kabul edildi
    assert settings["tts_engine"] == "edge" and settings["ab_edge_ok"] is True
    assert sp.calls[-1][0] == "edge"


def test_settings_save_retries_engine_when_not_ready_or_voices_changed(monkeypatch):
    settings = {"tts_engine": "piper", "ui_lang": "tr", "theme": "dark",
                "ab_voices": {"piper": {"ru": "ru_RU-denis-medium"}}}
    sp = _IntSpeaker("piper", {"ru": "ru_RU-denis-medium"}, neural=None)
    tab, _ST = _int_settings_tab(monkeypatch, settings, sp, "set.tts_piper")
    tab.save()                                                   # motor ayni ama hazir degil
    assert sp.calls == [("piper", {"ru": "ru_RU-denis-medium"})]
    sp.neural = object()
    tab.save()                                                   # hazir ve sesler ayni: yeniden kurma yok
    assert len(sp.calls) == 1
    settings["ab_voices"] = {"piper": {"ru": "ru_RU-irina-medium"}}
    tab.save()                                                   # ses degisti
    assert sp.calls[-1] == ("piper", {"ru": "ru_RU-irina-medium"})


def test_listen_whisper_never_downloads_missing_model(monkeypatch):
    from rca import tts
    monkeypatch.setattr(W, "is_downloaded", lambda name: False)
    monkeypatch.setattr(W, "downloaded_models", lambda: [])
    asr = tts.ASR.__new__(tts.ASR)
    asr.whisper_opts = {"model": "large-v3"}

    class NoRecorder:
        def __init__(self):
            raise AssertionError("kayda baslanmamali")
    monkeypatch.setattr(W, "Recorder", NoRecorder)
    with pytest.raises(RuntimeError):
        asr.listen_whisper(0)

    used = []

    class Rec:
        def start(self):
            pass

        def stop(self):
            return b""

    class Eng:
        def transcribe(self, audio, opts):
            used.append(opts.model)
            return W.Transcript([])
    monkeypatch.setattr(W, "downloaded_models", lambda: ["small"])
    monkeypatch.setattr(W, "Recorder", Rec)
    monkeypatch.setattr(W, "shared_engine", lambda: Eng())
    asr.listen_whisper(0)
    assert used == ["small"]                                     # eksik model yerine indirilmis olan


def test_pron_tab_rebuilds_asr_when_models_change(monkeypatch):
    import types
    tk = pytest.importorskip("tkinter")
    from tkinter import ttk
    import rca_common as C
    from rca.tabs.pron_tab import PronTab
    if (C.APP_HOME / "models" / "vosk-ru").exists():
        pytest.skip("bu ortamda Vosk modeli kurulu")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Ekran yok")
    try:
        have = []
        monkeypatch.setattr(W, "installed", lambda: True)
        monkeypatch.setattr(W, "downloaded_models", lambda: list(have))
        runs = []
        app = types.SimpleNamespace(settings={"whisper": {}},
                                    worker=types.SimpleNamespace(run=lambda *a: runs.append(a)))
        tab = PronTab(root, app)
        tab.mic = ttk.LabelFrame(tab)
        tab._build_mic()
        assert not tab.asr.available() and tab.mic_out is None
        first = tab.asr
        tab.on_show()                                            # degisiklik yok: ayni ASR
        assert tab.asr is first
        have[:] = ["small", "tiny"]                              # Whisper sayfasindan model indirildi
        tab.on_show()
        assert tab.asr.backend == "whisper" and tab.mic_out is not None

        app.settings["whisper"] = {"model": "tiny"}              # Whisper sayfasinda model degisti
        tab.word = _IntVar("мама")
        tab.record()
        assert tab.asr.whisper_opts["model"] == "tiny" and len(runs) == 1

        have[:] = []                                             # model kalmadi: kayit yok, bolum yenilenir
        tab.record()
        assert len(runs) == 1 and tab.mic_out is None and not tab.asr.available()
    finally:
        root.destroy()


def test_audio_catalogue_does_not_hijack_legacy_ui_texts():
    from rca.i18n import t, ui
    assert ui("Bankadan sec", "en") == "Choose from bank"
    assert ui("Bankadan sec", "ru") == "Выбрать из словаря"
    # Whisper "Telaffuz" alt sekmesi, sayfa adina (Telaffuz & Vurgu) donusmez
    assert ui(t("wh.tab_pron", "en"), "tr") == "Telaffuz"
    assert ui(t("wh.tab_pron", "ru"), "tr") == "Telaffuz"


# --- regresyon: player
def _silent_mp3(tmp_path, name, secs):
    np = pytest.importorskip("numpy")
    pytest.importorskip("av")
    p = tmp_path / name
    A.encode_mp3(np.zeros(int(24000 * secs), dtype=np.int16), p, sr=24000)
    return p


def test_player_stale_load_is_discarded(tmp_path):
    """Ust uste iki yuklemede gec biten ESKI istek yeni sesi ezmez (akis acilmaz)."""
    from rca import audio_player as AP
    a = _silent_mp3(tmp_path, "a.mp3", 2)
    b = _silent_mp3(tmp_path, "b.mp3", 3)
    pl = AP.AudioPlayer()
    g1, g2 = pl.request_load(), pl.request_load()
    assert pl.load(str(b), gen=g2) is not None
    assert pl.load(str(a), gen=g1) is None                # bayat: uygulanmaz
    assert pl.path == str(b) and abs(pl.duration - 3.0) < 0.2
    pl.close()


def test_player_speed_request_during_pending_load_is_used_by_load(tmp_path):
    from rca import audio_player as AP
    a = _silent_mp3(tmp_path, "a.mp3", 2)
    pl = AP.AudioPlayer()
    g = pl.request_load()
    assert pl.request_speed(2.0) == 0                     # ayri is gerekmez
    dur = pl.load(str(a), start=1.0, gen=g)
    assert pl.speed == 2.0 and abs(dur - 2.0) < 0.2
    assert abs(pl.position() - 1.0) < 0.05
    pl.close()


def test_player_stale_speed_is_discarded_and_speed_commits_with_pcm(tmp_path):
    from rca import audio_player as AP
    b = _silent_mp3(tmp_path, "b.mp3", 3)
    pl = AP.AudioPlayer()
    pl.load(str(b), start=1.0)
    g1, g2 = pl.request_speed(0.75), pl.request_speed(1.25)
    assert pl.speed == 1.0 and pl.target_speed == 1.25    # cozumden once uygulanmaz
    assert pl.set_speed(1.25, gen=g2) is True
    assert pl.set_speed(0.75, gen=g1) is False            # gec biten eski hiz atilir
    assert pl.speed == 1.25
    assert abs(pl.duration - 3.0) < 0.2 and abs(pl.position() - 1.0) < 0.05
    pl.close()


def test_player_failed_speed_keeps_committed_speed(tmp_path, monkeypatch):
    from rca import audio_player as AP
    b = _silent_mp3(tmp_path, "b.mp3", 1)
    pl = AP.AudioPlayer()
    pl.load(str(b))

    def boom(*_a, **_k):
        raise RuntimeError("bozuk")
    monkeypatch.setattr(AP, "decode", boom)
    with pytest.raises(RuntimeError):
        pl.set_speed(1.5)
    assert pl.speed == 1.0 and pl.target_speed == 1.0
    pl.unload()
    assert pl.path is None and pl.duration == 0.0
    pl.close()
