# -*- coding: utf-8 -*-
"""Sozluk motoru: gomulu veri butunlugu, iki yonlu arama, ice/disa aktarim, DB katmani."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rca_common as C                     # noqa: E402
from rca import dictionary as D            # noqa: E402


@pytest.fixture(scope="module")
def dic():
    return D.Dictionary(D.builtin_entries())


def test_builtin_data_is_large_and_well_formed(dic):
    entries = D.builtin_entries()
    assert len(entries) >= 1200
    assert len(dic) == len(entries), "gomulu veride tekrar eden madde var"
    for e in entries:
        assert e.headword and e.translation and e.pos, e
        assert C.has_cyrillic(e.headword), e
        assert not C.has_cyrillic(e.translation), e
        assert e.pos in D.POS_LABELS, e
        if e.extra:
            assert e.extra in D.EXTRA_LABELS, e
        if e.stress >= 0:
            assert e.headword[e.stress].lower() in C.VOWELS, e
        if e.pos == "n":
            assert e.extra in ("m", "f", "n", "pl"), e
        if e.pos == "v":
            assert e.extra in ("ipf", "pf"), e


def test_multisyllable_words_carry_stress(dic):
    missing = [e.headword for e in dic.entries
               if e.pos != "phr" and e.stress < 0
               and sum(1 for c in e.headword if c in C.VOWELS) > 1]
    assert not missing, missing


def test_direction_detection():
    assert D.Dictionary.direction("привет") == "ru2en"
    assert D.Dictionary.direction("hello") == "en2ru"
    assert D.Dictionary.direction("") == "en2ru"


def test_lookup_both_directions(dic):
    ru = dic.lookup("привет")
    assert ru and ru[0].translation.startswith("hi")
    en = dic.lookup("house")
    assert en and en[0].headword == "дом"
    assert dic.lookup("to go")[0].headword in ("пойти", "идти", "поехать")
    assert dic.lookup("ПРИВЕТ")[0].headword == "привет"
    assert dic.lookup("приве́т")[0].headword == "привет"      # vurgulu giris
    assert dic.lookup("ещё")[0].headword == "ещё" and dic.lookup("еще")[0].headword == "ещё"
    assert dic.lookup("") == [] and dic.lookup("zzzzqqq") == []


def test_ranking_prefers_exact_then_prefix(dic):
    rows = dic.lookup("дом")
    assert rows[0].headword == "дом"
    assert all(r.headword.startswith("дом") for r in rows[:3])
    rows = dic.lookup("book")
    assert rows[0].headword == "книга"


def test_stress_display_and_phrases():
    assert D.split_stress("приве'т") == ("привет", 4)
    assert D.mark_all("приве'т") == "приве́т"
    assert D.mark_all("до'брое у'тро").count(C.STRESS_MARK) == 2
    assert D.split_stress("ёлка") == ("ёлка", 0)
    assert D.mark_all("ёлка") == "ёлка"
    e = D.parse_line("дом|n m|house")
    assert e.display == "дом" and e.stress == -1


def test_parse_line_rejects_garbage():
    assert D.parse_line("") is None
    assert D.parse_line("# yorum") is None
    assert D.parse_line("tek|alan") is None


def test_table_roundtrip(tmp_path):
    src = tmp_path / "in.csv"
    src.write_text("ru,en,pos\nсло'во,word,n\nplain,ignored\nhello,приве'т\n", encoding="utf-8")
    rows = D.read_table(src)
    assert [(r.headword, r.translation) for r in rows] == [("слово", "word"), ("привет", "hello")]
    assert rows[0].source == D.SOURCE_USER and rows[0].stress == 2
    out = tmp_path / "out.csv"
    assert D.write_table(out, rows) == 2
    assert "сло'во" in out.read_text(encoding="utf-8")
    tsv = tmp_path / "in.tsv"
    tsv.write_text("ru\ten\nкни'га\tbook\n", encoding="utf-8")
    assert D.read_table(tsv)[0].headword == "книга"


def test_openrussian_loader(tmp_path):
    folder = tmp_path / "Sozluk"
    folder.mkdir()
    (folder / "openrussian_isimler.tsv").write_text(
        "bare\taccented\ttranslations_en\tgender\n"
        "стол\tстол\ttable; desk\tm\n"
        "книга\tкни'га\tbook\tf\n"
        "boş\t\t\t\n", encoding="utf-8")
    (folder / "openrussian_fiiller.tsv").write_text(
        "bare\taccented\ttranslations_en\taspect\n"
        "читать\tчита'ть\tto read\timperfective\n", encoding="utf-8")
    rows = D.load_openrussian(folder)
    assert len(rows) == 3
    by = {r.headword: r for r in rows}
    assert by["стол"].extra == "m" and by["книга"].stress == 2
    assert by["читать"].pos == "v" and by["читать"].extra == "ipf"
    assert all(r.source == D.SOURCE_OPENRUSSIAN for r in rows)
    assert D.load_openrussian(tmp_path / "yok") == []


def test_dictionary_merges_sources_and_counts(dic):
    d = D.Dictionary(dic.entries)
    n = len(d)
    added = d.extend([D.Entry("тест", 0, "n", "m", "test", D.SOURCE_USER),
                      D.Entry("тест", 0, "n", "m", "test", D.SOURCE_USER)])
    assert added == 1 and len(d) == n + 1
    assert d.count_by_source()[D.SOURCE_USER] == 1
    d.remove_source(D.SOURCE_USER)
    assert len(d) == n


def test_dict_repo_persists_user_entries(tmp_path, monkeypatch):
    monkeypatch.setenv("RCA_HOME", str(tmp_path))
    for name in list(sys.modules):
        if name == "rca_common" or name.startswith("rca."):
            del sys.modules[name]
    import rca_common as CC                # noqa: F811
    from rca.db import Database, Repos
    db = Database(tmp_path / "t.db")
    repos = Repos(db)
    assert repos.dictionary.count() == 0
    assert repos.dictionary.add_many([("сло'во", "word", "n", "n"), ("сло'во", "word"), ("", "x")]) == 1
    assert repos.dictionary.add("самова'р", "samovar", "n", "m") == 1
    rows = repos.dictionary.all()
    assert {r["ru"] for r in rows} == {"сло'во", "самова'р"}
    d = D.build_dictionary([(r["ru"], r["en"], r["pos"], r["extra"]) for r in rows])
    hit = d.lookup("самовар")
    assert hit and hit[0].source == D.SOURCE_USER and hit[0].display == "самова́р"
    assert d.lookup("слово")[0].source == D.SOURCE_BUILTIN      # gomulu ile ayni madde tekrar eklenmez
    repos.dictionary.clear()
    assert repos.dictionary.count() == 0
    db.close()
