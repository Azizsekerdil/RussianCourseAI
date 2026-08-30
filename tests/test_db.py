# -*- coding: utf-8 -*-
"""Veritabani semasi, repositoryler ve seed verisi testleri."""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def repos(tmp_path):
    """Izole bir veritabani ve repository kabi."""
    os.environ["RCA_HOME"] = str(tmp_path)
    for name in list(sys.modules):
        if name == "rca_common" or name.startswith("rca."):
            del sys.modules[name]
    from rca.db import Database, Repos
    db = Database(tmp_path / "test.db")
    yield Repos(db)
    db.close()


def test_seed_loads_words_and_decks(repos):
    """Ilk acilista gomulu deste yuklenir."""
    assert repos.words.count() >= 100
    decks = repos.words.decks()
    assert "A1 Temel" in decks and "Fiiller" in decks


def test_seed_links_aspect_pairs(repos):
    """Gorunus ciftleri karsilikli baglanir."""
    row = repos.db.one("SELECT id, aspect_pair_id FROM words WHERE ru_norm='читать'")
    assert row is not None and row["aspect_pair_id"]
    pair = repos.words.get(int(row["aspect_pair_id"]))
    assert pair["ru"] == "прочитать"
    assert pair["aspect_pair_id"] == row["id"]


def test_search_normalizes_yo_and_stress(repos):
    """Arama yo/e ve vurgu farkini yok sayar."""
    repos.words.add("тёплый", "ilik test", deck="Test")
    assert repos.words.search("теплыи") or repos.words.search("тёплый")
    assert repos.words.search("тепл")


def test_search_matches_turkish_and_english(repos):
    """TR ve EN uzerinden de aranabilir."""
    assert any(w["ru"] == "молоко" for w in repos.words.search("sut"))
    assert any(w["ru"] == "молоко" for w in repos.words.search("milk"))


def test_add_word_is_idempotent_per_deck(repos):
    """Ayni deste icinde ayni kelime iki kez eklenmez."""
    a = repos.words.add("тест", "deneme", deck="Test")
    b = repos.words.add("тест", "deneme", deck="Test")
    assert a == b


def test_profile_lifecycle(repos):
    """Profil olusturma, varsayilan ve silme."""
    pid = repos.profiles.ensure_default()
    other = repos.profiles.create("Ikinci")
    assert other != pid
    assert len(repos.profiles.all()) == 2
    repos.profiles.delete(other)
    assert len(repos.profiles.all()) == 1


def test_progress_save_and_due(repos):
    """Kaydedilen SRS durumu tekrar kuyruguna dogru duser."""
    from rca.srs import SRSState
    pid = repos.profiles.ensure_default()
    word = repos.words.all()[0]
    st = SRSState(due=date.today() - timedelta(days=1), box=2)
    repos.progress.save(pid, int(word["id"]), st, correct_inc=1)
    due = repos.progress.due_words(pid, 10)
    assert any(int(w["id"]) == int(word["id"]) for w in due)
    back = repos.progress.state(pid, int(word["id"]))
    assert back.box == 2


def test_dashboard_counts_are_rule_based(repos):
    """Pano sayilari veriden dogrudan hesaplanir."""
    from rca.srs import SRSState
    pid = repos.profiles.ensure_default()
    d0 = repos.progress.dashboard(pid)
    assert d0["seen"] == 0 and d0["new"] == repos.words.count()
    word = repos.words.all()[0]
    repos.progress.save(pid, int(word["id"]), SRSState(box=4), correct_inc=1)
    d1 = repos.progress.dashboard(pid)
    assert d1["seen"] == 1 and d1["learned"] == 1 and d1["new"] == d0["new"] - 1


def test_wrong_words_listed(repos):
    """Yanlisi dogrusundan fazla olan kelimeler drill listesine girer."""
    from rca.srs import SRSState
    pid = repos.profiles.ensure_default()
    word = repos.words.all()[3]
    repos.progress.save(pid, int(word["id"]), SRSState(), wrong_inc=3)
    assert any(int(w["id"]) == int(word["id"]) for w in repos.progress.wrong_words(pid))


def test_star_toggle(repos):
    """Favori isareti acilip kapanir."""
    pid = repos.profiles.ensure_default()
    wid = int(repos.words.all()[1]["id"])
    assert repos.progress.toggle_star(pid, wid) is True
    assert [int(w["id"]) for w in repos.progress.starred(pid)] == [wid]
    assert repos.progress.toggle_star(pid, wid) is False
    assert repos.progress.starred(pid) == []


def test_streak_counts_consecutive_days(repos):
    """Seri, kesintisiz gunleri sayar."""
    pid = repos.profiles.ensure_default()
    assert repos.study.streak(pid) == 0
    for back in (0, 1, 2, 5):
        day = (date.today() - timedelta(days=back)).isoformat()
        repos.db.execute(
            "INSERT INTO study_log(profile_id,day,activity,correct,wrong,seconds) "
            "VALUES(?,?,'srs',1,0,10)", (pid, day))
    assert repos.study.streak(pid) == 3


def test_daily_fills_missing_days_with_zero(repos):
    """Bos gunler icin 0 dondurulur, satir atlanmaz."""
    pid = repos.profiles.ensure_default()
    rows = repos.study.daily(pid, 7)
    assert len(rows) == 7
    assert all(r["correct"] == 0 for r in rows)


def test_exam_scoring(repos):
    """Sinav puani dogru/toplam oranidir."""
    pid = repos.profiles.ensure_default()
    eid = repos.exams.start(pid, "mcq")
    repos.exams.answer(eid, None, "mcq", "s1", "a", "a", True)
    repos.exams.answer(eid, None, "mcq", "s2", "b", "c", False)
    summary = repos.exams.finish(eid)
    assert summary == {"total": 2, "correct": 1, "score": 50.0}
    assert len(repos.exams.wrong_answers(eid)) == 1


def test_token_log_summary_and_grouping(repos):
    """Token defteri toplar ve gruplar."""
    repos.tokens.log("m1", "grammar", 100, 50, 800)
    repos.tokens.log("m1", "translate", 40, 10, 300)
    repos.tokens.log("m2", "grammar", 10, 5, 100)
    s = repos.tokens.summary()
    assert s["today"]["calls"] == 3 and s["today"]["tokens"] == 215
    by_model = {r["k"]: r["tokens"] for r in repos.tokens.grouped("model")}
    assert by_model["m1"] == 200 and by_model["m2"] == 15


def test_topic_weak_needs_minimum_attempts(repos):
    """3 denemeden az konu zayif listesine girmez - uydurma yapilmaz."""
    pid = repos.profiles.ensure_default()
    repos.topics.ensure("case.gen", "Родительный", "case")
    repos.topics.record(pid, "case.gen", 0, 2)
    assert repos.topics.weak(pid) == []
    repos.topics.record(pid, "case.gen", 0, 1)
    weak = repos.topics.weak(pid)
    assert weak and weak[0]["code"] == "case.gen" and weak[0]["pct"] == 0.0


def test_notes_roundtrip(repos):
    """PDF notu yazilir, okunur, silinir."""
    pid = repos.profiles.ensure_default()
    repos.notes.add(pid, "C:/x.pdf", 2, "note", "deneme")
    assert len(repos.notes.for_page("C:/x.pdf", 2)) == 1
    repos.notes.clear_page("C:/x.pdf", 2)
    assert repos.notes.for_page("C:/x.pdf", 2) == []


def test_resource_toggle(repos):
    """Bitirdim isareti kalicidir."""
    pid = repos.profiles.ensure_default()
    assert repos.resources.toggle(pid, "a.pdf") is True
    assert "a.pdf" in repos.resources.done_set(pid)
    assert repos.resources.toggle(pid, "a.pdf") is False
    assert repos.resources.done_set(pid) == set()
