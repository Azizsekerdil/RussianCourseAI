# -*- coding: utf-8 -*-
"""Sozluk yon secimi + Turkce ucuncu dil.

Kapsam: dorduncu alanli / alansiz satir ayristirma, tr sutunlu CSV gidis-donus (baslikli /
eski duzen), eski dict_entries tablosuna tr sutununun gocu, sabit yonlerde ve otomatik yonde
arama (Turkce sorgu dahil), Turkce harf normalizasyonu, AI ayristirma (translation_en /
translation_tr ve eski "translation"), dict_direction ayari.

Gomulu verinin Turkce KAPSAMI hicbir testte varsayilmaz: Turkce iceren maddeler testte kurulur.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rca_common as C                     # noqa: E402
from rca import dictionary as D            # noqa: E402


def _entry(head: str, pos: str, extra: str, en: str, tr: str = "", source: str = D.SOURCE_USER) -> D.Entry:
    word, stress = D.split_stress(head)
    return D.Entry(word, stress, pos, extra, en, source, D.mark_all(head), tr=tr)


@pytest.fixture()
def tri() -> D.Dictionary:
    """Kucuk uc dilli sozluk: gomulu veriden bagimsiz, Turkce'si olan ve olmayan maddeler."""
    return D.Dictionary([
        _entry("до'м", "n", "m", "house; home", "ev; yuva"),
        _entry("кни'га", "n", "f", "book", "kitap"),
        _entry("ко'шка", "n", "f", "cat", "kedi"),
        _entry("кот", "n", "m", "cat (male)"),                        # Turkce karsiligi yok
        _entry("рука'", "n", "f", "hand; arm", "el; kol"),
        _entry("слон", "n", "m", "elephant", "fil"),
        _entry("го'род", "n", "m", "city; town", "şehir; kent"),
        _entry("тест", "n", "m", "test", "test; sınav"),
        _entry("стол", "n", "m", "table; desk"),                      # Turkce karsiligi yok
        _entry("столо'вая", "n", "f", "canteen; dining room"),        # Turkce karsiligi yok
    ])


# --- ayristirma -----------------------------------------------------------
def test_parse_line_with_and_without_turkish_field():
    e = D.parse_line("до'м|n m|house; home|ev; yuva")
    assert e.translation == "house; home" and e.tr == "ev; yuva"
    assert e.display == "до́м" and e.pos == "n" and e.extra == "m"
    assert D.parse_line("до'м|n m|house; home").tr == ""
    assert D.parse_line("до'м|n m|house; home|").tr == ""
    assert D.parse_line("го'род|n m|city|şehir; kent").tr == "şehir; kent"      # Turkce harfler korunur
    block = D.parse_block("# yorum\nдом|n m|house|ev\nкот|n m|cat\n")
    assert [(x.headword, x.tr) for x in block] == [("дом", "ev"), ("кот", "")]
    assert D.Entry("дом", -1, "n", "m", "house").tr == ""                     # konumsal kurucu geriye uyumlu
    entries = D.builtin_entries()                                              # dorduncu alan olsa da olmasa da yuklenir
    assert entries and all(not C.has_cyrillic(x.tr) for x in entries)


def test_norm_keeps_turkish_letters_and_folds_dotted_i():
    assert D.norm_query("Şehir") == "şehir"
    assert D.norm_query("ÇĞÖŞÜ ığ") == "çğöşü ığ"
    assert D.norm_query("İstanbul") == "istanbul" == D.norm_query("istanbul")
    assert D.looks_turkish("şehir") and D.looks_turkish("kalabalık")
    assert not D.looks_turkish("city") and not D.looks_turkish("дом")


# --- CSV ------------------------------------------------------------------
def test_csv_roundtrip_with_turkish_and_legacy_layout(tmp_path):
    rows = [_entry("до'м", "n", "m", "house; home", "ev; yuva"), _entry("стол", "n", "m", "table")]
    out = tmp_path / "out.csv"
    assert D.write_table(out, rows) == 2
    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "ru,en,tr,pos,extra,source" and "ev; yuva" in text
    back = D.read_table(out)
    assert [(x.headword, x.translation, x.tr, x.pos, x.extra) for x in back] == [
        ("дом", "house; home", "ev; yuva", "n", "m"), ("стол", "table", "", "n", "m")]
    assert back[0].stress == 1 and back[0].source == D.SOURCE_USER
    # baslikli dosyada sutunlar adiyla eslenir (sira serbest, esanlamli adlar kabul)
    hdr = tmp_path / "hdr.csv"
    hdr.write_text("Türkçe,English,Tur,Rusca\nkitap,book,n,кни'га\n", encoding="utf-8")
    x = D.read_table(hdr)[0]
    assert (x.headword, x.translation, x.tr, x.pos) == ("книга", "book", "kitap", "n")
    # eski konumsal duzen: basliksiz `ru, en, pos, extra` (ters sirali satir da duzeltilir)
    old = tmp_path / "old.csv"
    old.write_text("сло'во,word,n,n\nhello,приве'т\nplain,ignored\n", encoding="utf-8")
    got = D.read_table(old)
    assert [(r.headword, r.translation, r.pos, r.extra, r.tr) for r in got] == [
        ("слово", "word", "n", "n", ""), ("привет", "hello", "", "", "")]
    # eski baslikli duzen (tr sutunu yok)
    old2 = tmp_path / "old2.tsv"
    old2.write_text("ru\ten\tpos\textra\nкни'га\tbook\tn\tf\n", encoding="utf-8")
    r = D.read_table(old2)[0]
    assert (r.headword, r.pos, r.extra, r.tr) == ("книга", "n", "f", "")


def test_openrussian_layer_has_empty_turkish(tmp_path):
    folder = tmp_path / "Sozluk"
    folder.mkdir()
    (folder / "openrussian_isimler.tsv").write_text(
        "bare\taccented\ttranslations_en\tgender\nстол\tстол\ttable; desk\tm\n", encoding="utf-8")
    rows = D.load_openrussian(folder)
    assert rows and rows[0].tr == "" and rows[0].source == D.SOURCE_OPENRUSSIAN


# --- veritabani gocu ------------------------------------------------------
def test_dict_entries_tr_column_is_added_to_old_databases(tmp_path):
    """Onceki surumun (tr sutunsuz) dict_entries tablosu acilista eklemeli gocle guncellenir; satirlar korunur."""
    os.environ["RCA_HOME"] = str(tmp_path)
    for name in list(sys.modules):
        if name == "rca_common" or name.startswith("rca."):
            del sys.modules[name]
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
        INSERT INTO meta VALUES('schema_version', '1');
        CREATE TABLE dict_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ru TEXT NOT NULL,
            en TEXT NOT NULL,
            pos TEXT DEFAULT '',
            extra TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'user',
            example TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            UNIQUE(ru, en)
        );
        INSERT INTO dict_entries(ru, en, pos, extra, created_at, source, example, note)
            VALUES('самова''р', 'samovar', 'n', 'n', '2025-01-01T00:00:00', 'user', '', '');
    """)
    con.commit()
    con.close()

    from rca.db import Database, Repos
    db = Database(path)
    assert "tr" in db.columns("dict_entries")
    repos = Repos(db)
    rows = repos.dictionary.all()
    assert len(rows) == 1 and rows[0]["ru"] == "самова'р" and rows[0]["tr"] == "" and rows[0]["source"] == "user"
    # yeni satir Turkce'siyle eklenir
    assert repos.dictionary.add("кни'га", "book", "n", "f", tr="kitap") == 1
    assert [r["tr"] for r in repos.dictionary.all() if r["ru"] == "кни'га"] == ["kitap"]
    # ayni (ru, en) satiri kopyalanmaz; bos tr alani DOLDURULUR, kaynak degismez
    assert repos.dictionary.add_many([("самова'р", "samovar", "n", "n", "", "", "semaver; çay kazanı")], source="ai") == 0
    row = [r for r in repos.dictionary.all() if r["ru"] == "самова'р"][0]
    assert row["tr"] == "semaver; çay kazanı" and row["source"] == "user"
    assert repos.dictionary.count() == 2
    # dolu alan varsayilan olarak ezilmez
    assert repos.dictionary.set_tr("самова'р", "samovar", "baska") == 0
    assert repos.dictionary.set_tr("самова'р", "samovar", "baska", overwrite=True) == 1
    assert repos.dictionary.set_tr("самова'р", "samovar", "") == 0
    # build_dictionary tr'yi Entry.tr'ye tasir
    d = D.build_dictionary(repos.dictionary.all())
    hit = d.lookup("kitap", "tr2ru")
    assert hit and hit[0].headword == "книга" and hit[0].tr == "kitap" and hit.direction == "tr2ru"
    assert d.lookup("baska", "tr2ru")[0].headword == "самовар"
    db.close()

    db2 = Database(path)                       # goc yeniden calisir, sutun ikinci kez eklenmez
    assert db2.columns("dict_entries").count("tr") == 1
    db2.close()


def test_dict_repo_matches_rows_stress_and_case_insensitively(tmp_path):
    """AI'in sonradan buldugu Turkce gloss, vurgusuz ya da farkli buyuk/kucuk harfli sakli
    satira islenir (UPDATE); ikinci bir 'ai' satiri ACILMAZ, kullanicinin satiri golgelenmez."""
    os.environ["RCA_HOME"] = str(tmp_path)
    for name in list(sys.modules):
        if name == "rca_common" or name.startswith("rca."):
            del sys.modules[name]
    from rca.db import Database, Repos
    db = Database(tmp_path / "t.db")
    repos = Repos(db)
    key = repos.dictionary.entry_key
    assert key("самова'р", "Samovar") == key("САМОВАР", "samovar") == key("самова́р", " samovar ")
    assert key("дом", "house") != key("дома", "house") != key("дом", "home")
    assert repos.dictionary.add("самовар", "samovar", "n", "m") == 1            # vurgusuz (ekleme / eski CSV)
    assert repos.dictionary.add("кни'га", "Book", "n", "f") == 1                 # buyuk harfli Ingilizce
    before = repos.dictionary.count()
    # AI satiri vurgulu baslik / kucuk harf Ingilizce tasir -> kopya degil, tr dolar, satir kimligi ayni kalir
    assert repos.dictionary.add_many([("самова'р", "samovar", "n", "m", "Это самовар.", "Mock.", "semaver"),
                                      ("кни'га", "book", "n", "f", "", "", "kitap")], source="ai") == 0
    assert repos.dictionary.count() == before
    rows = {r["ru"]: r for r in repos.dictionary.all()}
    assert set(rows) == {"самовар", "кни'га"}
    assert rows["самовар"]["tr"] == "semaver" and rows["самовар"]["source"] == "user"
    assert rows["кни'га"]["tr"] == "kitap" and rows["кни'га"]["en"] == "Book" and rows["кни'га"]["source"] == "user"
    # set_tr ayni anahtarla bulur; dolu alan varsayilan olarak ezilmez, satir yoksa 0
    assert repos.dictionary.set_tr("САМОВА'Р", "SAMOVAR", "baska") == 0
    assert repos.dictionary.set_tr("самова'р", "Samovar", "baska", overwrite=True) == 1
    assert repos.dictionary.set_tr("нет", "none", "x") == 0
    # ayni toplu istekteki tekrarlar: tek satir (ilk bicim), tr ilk dolu degerden
    assert repos.dictionary.add_many([("до'м", "house", "n", "m"), ("дом", "House", "n", "m", "", "", "ev"),
                                      ("ДОМ", "house", "n", "m", "", "", "yuva")]) == 1
    home = [r for r in repos.dictionary.all() if r["en"].lower() == "house"]
    assert len(home) == 1 and home[0]["ru"] == "до'м" and home[0]["tr"] == "ev"
    # yeniden kurulan sozluk: tek madde, kullanici kaynakli ve Turkce'li (golgelenen satir yok)
    d = D.build_dictionary(repos.dictionary.all())
    hit = d.lookup("самовар", "ru2tr")
    assert len(hit) == 1 and hit[0].source == D.SOURCE_USER and hit[0].tr == "baska" and hit[0].stress == -1
    assert d.lookup("kitap", "tr2ru")[0].headword == "книга"
    db.close()


# --- arama yonleri --------------------------------------------------------
def test_direction_helpers():
    assert D.DIRECTIONS == ("auto", "ru2en", "en2ru", "ru2tr", "tr2ru") == C.DICT_DIRECTIONS
    assert D.target_field("ru2tr") == "tr" and D.target_field("ru2en") == "en"
    assert D.target_field("en2ru") == "ru" and D.target_field("tr2ru") == "ru" and D.target_field("auto") == "en"
    assert D.gloss_field("ru2tr") == D.gloss_field("tr2ru") == "tr"
    assert D.gloss_field("en2ru") == D.gloss_field("ru2en") == D.gloss_field("auto") == "en"
    assert D.source_field("ru2tr") == D.source_field("ru2en") == "head"
    assert D.source_field("tr2ru") == "tr" and D.source_field("en2ru") == "en" and D.source_field("auto") == ""
    assert D.headword_direction("en2ru") == "ru2en" and D.headword_direction("tr2ru") == "ru2tr"
    assert D.headword_direction("ru2tr") == "ru2tr" and D.headword_direction("auto") == "auto"
    assert D.valid_direction("bogus") == "auto" and D.valid_direction("") == "auto"


def test_lookup_fixed_directions_search_only_the_source_side(tri):
    r = tri.lookup("дом", "ru2en")
    assert r.direction == "ru2en" and r[0].headword == "дом"
    r = tri.lookup("дом", "ru2tr")
    assert r.direction == "ru2tr" and r[0].headword == "дом" and r[0].tr == "ev; yuva"
    r = tri.lookup("house", "en2ru")
    assert r.direction == "en2ru" and r[0].headword == "дом"
    r = tri.lookup("kitap", "tr2ru")
    assert r.direction == "tr2ru" and [e.headword for e in r] == ["книга"]
    assert tri.lookup("kitap", "en2ru") == []                           # yalnizca Ingilizce taraf
    assert tri.lookup("book", "tr2ru") == []                            # yalnizca Turkce taraf
    assert tri.lookup("дом", "en2ru") == [] and tri.lookup("house", "ru2en") == []
    assert tri.lookup("ev", "tr2ru")[0].headword == "дом"               # tam anlam eslesmesi
    assert tri.lookup("kol", "tr2ru")[0].headword == "рука"
    assert tri.lookup("şehir", "tr2ru")[0].headword == "город"          # Turkce harf
    assert tri.lookup("Kent", "tr2ru")[0].headword == "город"
    assert tri.lookup("ki", "tr2ru")[0].headword == "книга"             # on ek
    assert tri.lookup("sınav", "tr2ru")[0].headword == "тест"
    # ru2tr: Turkce karsiligi olmayan madde de bulunur (AI sonradan doldurur); esit puanda gloss'u olan onde
    r = tri.lookup("стол", "ru2tr")
    assert r[0].headword == "стол" and r[0].tr == ""
    assert [e.headword for e in tri.lookup("ко", "ru2tr")][:2] == ["кошка", "кот"]
    assert [e.headword for e in tri.lookup("ко", "ru2en")][:2] == ["кот", "кошка"]   # Ingilizce yonde eski siralama
    assert tri.lookup("bogus", "weird").direction == "en2ru"           # bilinmeyen yon -> auto
    assert tri.lookup("дом", 1) == tri.lookup("дом")[:1]                # eski cagri bicimi: lookup(q, limit)
    assert isinstance(tri.lookup("дом"), list)


def test_lookup_auto_direction_with_turkish_query(tri):
    r = tri.lookup("kitap")
    assert r.direction == "tr2ru" and r[0].headword == "книга"
    r = tri.lookup("book")
    assert r.direction == "en2ru" and r[0].headword == "книга"
    assert tri.lookup("дом").direction == "ru2en"
    r = tri.lookup("el")                                                # Turkce tam anlam > Ingilizce 'elephant' on eki
    assert r.direction == "tr2ru" and r[0].headword == "рука"
    r = tri.lookup("test")                                              # iki tarafta da tam eslesme: Ingilizce
    assert r.direction == "en2ru" and r[0].headword == "тест"
    r = tri.lookup("şehir")
    assert r.direction == "tr2ru" and r[0].headword == "город"
    assert tri.lookup("kedi").direction == "tr2ru" and tri.lookup("KEDİ")[0].headword == "кошка"
    assert tri.lookup("qqqzz").direction == "en2ru"                     # sonuc yok: Latin -> Ingilizce
    assert tri.lookup("qqqzzş").direction == "tr2ru"                    # sonuc yok ama Turkce harf -> Turkce
    assert tri.lookup("") == [] and tri.lookup("").direction == "en2ru"
    assert tri.lookup("", "ru2tr").direction == "ru2tr"
    assert D.Dictionary.direction("kitap") == "en2ru"                   # yazi tipine gore kaba tahmin degismedi


def test_score_ignores_leading_article_for_prefix_matches():
    """'to / the / a / an' hem tam (95) hem kelime basi (60) eslesmesinde yok sayilir."""
    field = "to ask (a question)"
    senses = D._senses(field)
    assert D._score("ask", field, senses) == 60
    assert D._score("to ask", field, senses) == 60
    assert D._score("ask (a question)", field, senses) == 95
    assert D._score(field, field, senses) == 100
    assert D._score("question", field, senses) == 30
    assert D._score("ask", "asker", ["asker"]) == 60                    # Turkce on ek ayni sinifta
    two = "to go; to set off"
    assert D._score("go", two, D._senses(two)) == 95 and D._score("set", two, D._senses(two)) == 60
    assert D._score("house", "the house", ["the house"]) == 95
    assert D._score("hou", "the house", ["the house"]) == 60


def test_lookup_auto_keeps_english_for_verb_senses_and_their_prefixes(tri):
    """Ingilizce fiil anlami ('to ask') ile Turkce on ek ('asker') esit puanlanir -> esitlikte Ingilizce."""
    tri.extend([_entry("спроси'ть", "v", "pf", "to ask (a question)", "sormak"),
                _entry("солда'т", "n", "m", "soldier", "asker"),
                _entry("сохрани'ть", "v", "pf", "to save; to keep", "kaydetmek; saklamak"),
                _entry("война'", "n", "f", "war", "savaş")])
    r = tri.lookup("ask")
    assert r.direction == "en2ru" and r[0].headword == "спросить"
    r = tri.lookup("sav")
    assert r.direction == "en2ru" and r[0].headword == "сохранить"
    r = tri.lookup("asker")                                             # Turkce tam eslesme yine Turkce
    assert r.direction == "tr2ru" and r[0].headword == "солдат"
    assert tri.lookup("savaş").direction == "tr2ru" and tri.lookup("kitap").direction == "tr2ru"
    assert tri.lookup("ask", "tr2ru")[0].headword == "солдат"           # sabit yon etkilenmez
    # gomulu sozluk: yaygin Ingilizce fiiller ve yazarken gecilen on ekleri otomatik yonde Ingilizce kalir
    d = D.build_dictionary()
    for q in ("ask", "to ask", "sav", "dev", "mak", "ren", "org", "organiz", "book"):
        assert d.lookup(q).direction == "en2ru", q
    assert d.lookup("ask")[0].headword in ("спросить", "просить")


def test_dictionary_enriches_existing_entry_with_turkish(tri):
    n = len(tri)
    stol = _entry("стол", "n", "m", "table; desk", "masa", source=D.SOURCE_AI)
    assert tri.extend([stol]) == 0 and len(tri) == n                   # kopya eklenmez
    stored = tri.find(stol)
    assert stored.tr == "masa" and stored.source == D.SOURCE_USER       # eldeki madde zenginlesti, kaynagi degismedi
    assert tri.lookup("masa", "tr2ru")[0].headword == "стол"
    assert tri.extend([_entry("стол", "n", "m", "table; desk", "sofra")]) == 0
    assert tri.find(stol).tr == "masa"                                  # dolu alan ezilmez
    assert tri.fill_tr(_entry("нет", "n", "m", "none"), "x") is None
    got = tri.fill_tr(_entry("столо'вая", "n", "f", "canteen; dining room"), "yemekhane")
    assert got.tr == "yemekhane" and tri.lookup("столовая", "ru2tr")[0].tr == "yemekhane"
    tri.remove_source(D.SOURCE_USER)
    assert len(tri) == 0 and tri.find(stol) is None
    # build_dictionary: gomulu maddeyle ayni satir eklenmez, Turkce'si gomulu maddeye islenir
    d = D.build_dictionary([
        {"ru": "дом", "en": "house; home", "pos": "n", "extra": "m", "source": "ai", "tr": "ev (test)"},
        ("зюзю'ка", "zzqxwv; mock word", "n", "f", "ai", "Это зюзюка.", "Mock.", "sahte kelime; deneme"),
    ])
    hit = d.lookup("дом", "ru2tr")[0]
    assert hit.source == D.SOURCE_BUILTIN and hit.tr                   # gomulu maddenin kendi ya da islenen Turkce'si
    assert d.count_by_source()[D.SOURCE_AI] == 1                        # yalnizca gercekten yeni madde eklendi
    z = d.lookup("sahte kelime", "tr2ru")
    assert z.direction == "tr2ru" and z[0].headword == "зюзюка" and z[0].example == "Это зюзюка."


# --- AI ayristirma --------------------------------------------------------
def test_parse_ai_entries_reads_english_and_turkish_glosses():
    text = json.dumps([
        {"headword": "до'м", "pos": "n", "extra": "m", "translation_en": "house; home",
         "translation_tr": "ev; yuva; ev", "example": "Это дом.", "note": "n"},
        {"headword": "кни'га", "pos": "n", "extra": "f", "translation": "book"},                  # eski anahtar
        {"headword": "ко'шка", "pos": "n", "extra": "f", "translation_en": "cat", "translation_tr": "кошка"},
        {"headword": "стол", "pos": "n", "extra": "m", "translation_tr": "masa"},                 # Ingilizce yok
    ], ensure_ascii=False)
    out = D.parse_ai_entries(text)
    assert [(e.headword, e.translation, e.tr) for e in out] == [
        ("дом", "house; home", "ev; yuva"), ("книга", "book", ""), ("кошка", "cat", "")]
    assert all(e.source == D.SOURCE_AI for e in out) and out[0].example == "Это дом."
    # tekillik anahtari Turkce'yi icermez: (baslik, tur, Ingilizce)
    assert D.Dictionary.key(out[0]) == ("дом", "n", "house; home")
    d = D.Dictionary([out[0]])
    assert d.contains(D.Entry("дом", -1, "n", "m", "House; Home", D.SOURCE_USER, tr="baska"))
    assert D.parse_ai_entries('[{"headword": "стол", "translation": "table", "tr": "masa; masa"}]')[0].tr == "masa"


def test_ai_prompt_asks_for_both_glosses_and_names_the_query_language():
    system, user = D.ai_prompt("kitap", "tr", "tr2ru")
    assert '"translation_en"' in system and '"translation_tr"' in system and "Turkish" in system
    assert "Turkish" in user and "Latin" in user
    assert "English" in D.ai_prompt("book", "en", "en2ru")[1]
    assert "Cyrillic" in D.ai_prompt("дом", "en", "tr2ru")[1]           # Kiril her zaman Rusca
    assert "English or Turkish" in D.ai_prompt("word", "en")[1]          # auto: belirsiz Latin
    assert D.query_language("дом") == "Cyrillic (Russian)"
    assert D.query_language("ev", "tr2ru") == "Latin (Turkish)"


def test_ai_lookup_passes_direction_and_fills_turkish(mock_server):
    from rca.ai_client import AIClient
    mock_server.reset()
    mock_server.content = ('[{"headword": "кни\'га", "pos": "n", "extra": "f", '
                           '"translation_en": "book", "translation_tr": "kitap"}]')
    client = AIClient(mock_server.base)
    try:
        entries = D.ai_lookup(client, "kitap", "tr", direction="tr2ru")
        assert entries and entries[0].headword == "книга"
        assert entries[0].translation == "book" and entries[0].tr == "kitap"
        body = json.loads(mock_server.chat_requests()[-1]["body"])
        assert "Turkish" in body["messages"][-1]["content"]
        assert "translation_tr" in body["messages"][0]["content"]
    finally:
        mock_server.reset()


# --- ayar -------------------------------------------------------------------
def test_settings_dict_direction_default_and_validation(tmp_path, monkeypatch):
    assert C.DEFAULT_SETTINGS["dict_direction"] == "auto"
    assert C.DICT_DIRECTIONS == ("auto", "ru2en", "en2ru", "ru2tr", "tr2ru")
    sdir = tmp_path / "settings"
    monkeypatch.setattr(C, "APP_HOME", tmp_path)
    monkeypatch.setattr(C, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(C, "SETTINGS_DIR", sdir)
    monkeypatch.setattr(C, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(C, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(C, "SETTINGS_PATH", sdir / "settings.json")
    sdir.mkdir(parents=True)
    (sdir / "settings.json").write_text(json.dumps({"dict_direction": "ru2tr"}), encoding="utf-8")
    assert C.load_settings()["dict_direction"] == "ru2tr"
    (sdir / "settings.json").write_text(json.dumps({"dict_direction": "bogus"}), encoding="utf-8")
    assert C.load_settings()["dict_direction"] == "auto"
    (sdir / "settings.json").write_text(json.dumps({"ui_lang": "en"}), encoding="utf-8")
    assert C.load_settings()["dict_direction"] == "auto"
    data = C.load_settings()
    data["dict_direction"] = "tr2ru"
    C.save_settings(data)
    assert C.load_settings()["dict_direction"] == "tr2ru"
