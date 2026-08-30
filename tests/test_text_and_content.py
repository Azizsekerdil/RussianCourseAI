# -*- coding: utf-8 -*-
"""Rusca metin yardimcilari ve gomulu icerik paketleri testleri."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rca_common as C
from rca import content as K
from rca.i18n import LANGS, LANG_NAMES, S, SYSTEM_PROMPTS, t, ui


# --- metin yardimcilari -------------------------------------------------
def test_strip_stress():
    """Vurgu isareti kaldirilir."""
    assert C.strip_stress("молоко́") == "молоко"
    assert C.strip_stress("дом") == "дом"


def test_normalize_ru_lowercases_and_maps_yo():
    """Normalizasyon kucuk harfe cevirir ve yo -> e yapar."""
    assert C.normalize_ru("Ёлка") == "елка"
    assert C.normalize_ru("  ДОМ  ") == "дом"
    assert C.normalize_ru("Ёлка́") == "елка"


def test_normalize_ru_collapses_punctuation():
    """Noktalama ve fazla bosluk sadelestirilir."""
    assert C.normalize_ru("Как  дела?!") == "как дела"


def test_add_stress_places_mark_after_vowel():
    """Vurgu isareti dogru harften sonra gelir."""
    out = C.add_stress("молоко", 5)
    assert out == "молоко́"
    assert C.add_stress("дом", -1) == "дом"
    assert C.add_stress("дом", 99) == "дом"


def test_syllable_count():
    """Hece sayisi sesli harf sayisidir."""
    assert C.syllables("молоко") == 3
    assert C.syllables("дом") == 1
    assert C.syllables("здравствуйте") == 3


def test_has_cyrillic():
    """Kiril tespiti."""
    assert C.has_cyrillic("дом")
    assert not C.has_cyrillic("ev")
    assert C.has_cyrillic("ev дом")


def test_human_int():
    """Sayi bicimlendirme TR ayiricisiyla."""
    assert C.human_int(1234567) == "1.234.567"
    assert C.human_int(0) == "0"


def test_settings_roundtrip(tmp_path, monkeypatch):
    """Ayarlar yazilip geri okunur; bilinmeyen anahtar yok sayilir."""
    monkeypatch.setenv("RCA_HOME", str(tmp_path))
    monkeypatch.setattr(C, "APP_HOME", tmp_path)
    monkeypatch.setattr(C, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(C, "SETTINGS_DIR", tmp_path / "settings")
    monkeypatch.setattr(C, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(C, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(C, "SETTINGS_PATH", tmp_path / "settings" / "settings.json")

    data = C.load_settings()
    data["daily_goal"] = 42
    data["bilinmeyen"] = "x"
    C.save_settings(data)
    back = C.load_settings()
    assert back["daily_goal"] == 42
    assert "bilinmeyen" not in back
    assert (tmp_path / "settings" / "settings.json").exists()


# --- alfabe / icerik ----------------------------------------------------
def test_alphabet_has_33_letters():
    """Rus alfabesi 33 harftir."""
    assert len(K.ALPHABET) == 33
    letters = [a[0][0] for a in K.ALPHABET]
    assert len(set(letters)) == 33
    assert letters[0] == "А" and letters[-1] == "Я"


def test_cases_are_six():
    """6 hal tanimlidir ve her birinin ornegi vardir."""
    assert len(K.CASES) == 6
    codes = {c["code"] for c in K.CASES}
    assert codes == {"nom", "gen", "dat", "acc", "ins", "pre"}
    for c in K.CASES:
        assert c["ex"][0] and c["ex"][1] and c["use"]


def test_declension_tables_cover_all_cases():
    """Her cekim satiri 6 hali de icerir."""
    codes = [c["code"] for c in K.CASES]
    for table in (K.NOUN_DECLENSION, K.PRONOUN_DECLENSION):
        for name, forms in table.items():
            assert set(forms) == set(codes), name


def test_build_returns_valid_exercises():
    """Uretilen alistirmalarda dogru cevap seceneklerin icindedir."""
    for lab in K.LABS:
        items = K.build(lab, 8)
        assert len(items) == 8
        for it in items:
            assert it["answer"] in it["options"]
            assert it["prompt"] and it["explain"]


def test_build_unknown_lab_returns_empty():
    """Bilinmeyen lab kodu bos liste dondurur, hata firlatmaz."""
    assert K.build("yok", 5) == []


def test_number_agreement_rule_is_applied():
    """1 / 2-4 / 5+ kurali dogru bicimi secer."""
    import random
    items = K.build("numbers", 40, random.Random(3))
    for it in items:
        num = int(it["prompt"].split()[0])
        last, last2 = num % 10, num % 100
        if last == 1 and last2 != 11:
            assert "YALIN" in it["explain"]
        elif last in (2, 3, 4) and last2 not in (12, 13, 14):
            assert "tekil" in it["explain"]
        else:
            assert "cogul" in it["explain"]


def test_parse_sentence_tags_words():
    """Cumle ayristirilir ve her kelime etiketlenir."""
    pairs = K.parse_sentence("Я читаю книгу в доме")
    assert len(pairs) == 5
    assert pairs[0] == ("Я", "pron")
    assert pairs[3] == ("в", "prep")
    assert all(tag in K.POS_LABELS for _w, tag in pairs)


def test_parse_sentence_empty():
    """Bos girdide bos liste."""
    assert K.parse_sentence("") == []
    assert K.parse_sentence(None) == []


def test_rough_ipa_marks_stress():
    """IPA ciktisi vurguyu isaretler ve vurgusuz o'yu indirger."""
    out = K.rough_ipa("молоко", 5)
    assert out.startswith("[") and out.endswith("]")
    assert "ˈ" in out
    assert "o" not in out[:4]


# --- i18n ---------------------------------------------------------------
def test_all_strings_have_all_languages():
    """Her arayuz metni uc dilde de tanimlidir."""
    for key, row in S.items():
        assert set(row) == set(LANGS), key
        assert all(row[l].strip() for l in LANGS), key


def test_translate_falls_back_to_key():
    """Bilinmeyen anahtar oldugu gibi doner."""
    assert t("hicboyle.yok", "tr") == "hicboyle.yok"
    assert t("tab.vocab", "ru") == "Словарь"


def test_visible_text_can_switch_between_all_languages():
    """Anahtarli ve eski sabit metinler iki yonlu cevrilebilir."""
    assert list(LANG_NAMES.values()) == ["Türkçe", "English", "Русский"]
    assert ui("Profil", "en") == "Profile"
    assert ui("Profile", "ru") == "Профиль"
    assert ui("Профиль", "tr") == "Profil"
    assert ui(t("srs.today", "en"), "ru") == "Сегодня"


def test_system_prompts_cover_all_languages():
    """AI sistem yonergesi her arayuz dili icin vardir."""
    assert set(SYSTEM_PROMPTS) == set(LANGS)
    assert all(len(v) > 40 for v in SYSTEM_PROMPTS.values())
