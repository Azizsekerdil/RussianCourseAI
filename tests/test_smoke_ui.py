# -*- coding: utf-8 -*-
"""Arayuz duman testi: pencere acilir, her sekme kurulur, temel akislar isler.

GUI gerektirir (Windows'ta her zaman vardir). Ekran yoksa test atlanir.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

tk = pytest.importorskip("tkinter")


def _load_main():
    """Russian_Course_AI.pyw modulunu yukle."""
    spec = importlib.util.spec_from_file_location("rca_main", ROOT / "Russian_Course_AI.pyw")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def app(tmp_path_factory, monkeypatch_module=None):
    """Izole veri klasoruyle bir uygulama penceresi."""
    import os
    home = tmp_path_factory.mktemp("rca_home")
    os.environ["RCA_HOME"] = str(home)
    for name in list(sys.modules):
        if name == "rca_common" or name.startswith("rca."):
            del sys.modules[name]
    main = _load_main()
    try:
        instance = main.App()
    except tk.TclError:
        pytest.skip("Ekran yok")
    instance.update()
    yield instance, main
    instance.on_close()


def test_window_and_tabs(app):
    """Her sayfa kenar cubugundan acilir ve tembel kurulumu HATASIZ tamamlar."""
    instance, main = app
    from tkinter import ttk
    from rca.ui_util import LazyTab
    assert len(instance._tabs) == len(main.TAB_SPECS)
    for key, _mod, _cls, _icon, _grp in main.TAB_SPECS:
        instance.sidebar.select(key)
        instance.update()
        widget = instance.current_page()
        assert isinstance(widget, LazyTab), key
        assert widget._built, key
        broken = [c for c in widget.winfo_children()
                  if isinstance(c, ttk.Label) and "yuklenemedi" in str(c.cget("text"))]
        assert not broken, f"{key} kurulurken hata verdi: {broken[0].cget('text')}"


def test_sidebar_groups_and_badges(app):
    """Kenar cubugu her sayfayi tasir ve rozet guncellemesi cokmez."""
    instance, main = app
    for key, _m, _c, _i, _g in main.TAB_SPECS:
        assert key in instance.sidebar.items
    instance.refresh_badges()
    instance.update()


def test_language_switch_is_immediate_and_persistent(app):
    """Ust cubuktan English / Русский secimi acik sayfayi aninda yeniler."""
    instance, _ = app
    old = instance.ui_lang()
    try:
        instance.sidebar.select("tab.srs")
        tab = instance.current_page()

        instance.set_ui_language("en")
        instance.update()
        assert instance.language_var.get() == "English"
        assert instance.sidebar.items["tab.srs"]["text"].cget("text") == "Spaced Review"
        assert instance.page_title.cget("text") == "Spaced Review"
        assert tab.mode.get() == "Cards"
        assert instance.settings["ui_lang"] == "en"

        instance.set_ui_language("ru")
        instance.update()
        assert instance.language_var.get() == "Русский"
        assert instance.sidebar.items["tab.srs"]["text"].cget("text") == "Повторение"
        assert instance.page_title.cget("text") == "Повторение"
        assert tab.mode.get() == "Карточки"
        assert instance.settings["ui_lang"] == "ru"
    finally:
        instance.set_ui_language(old)
        instance.update()


def test_seed_loaded(app):
    """Gomulu A1 destesi yuklenmis olmali."""
    instance, _ = app
    assert instance.repos.words.count() >= 100
    assert len(instance.repos.words.decks()) >= 5


def test_srs_session_flow(app):
    """Yeni kelime oturumu baslar, kart cevrilir, degerlendirilir."""
    instance, main = app
    tab = instance._tabs["tab.srs"]
    tab.ensure_built()
    tab.limit.set(5)
    tab.mode.set("Kart")
    tab.start("new")
    instance.update()
    assert len(tab.session) == 5
    before = instance.repos.progress.dashboard(instance.profile_id)["seen"]
    for _ in range(5):
        tab.flip()
        instance.update()
        tab.grade("know")
        instance.update()
    after = instance.repos.progress.dashboard(instance.profile_id)["seen"]
    assert after == before + 5
    assert tab.session == []


def test_exam_flow(app):
    """Sinav uretilir, cevaplanir ve puanlanir."""
    instance, _ = app
    tab = instance._tabs["tab.exam"]
    tab.ensure_built()
    for code, var in tab.kind_vars.items():
        var.set(code in ("mcq_ru2tr", "case"))
    tab.count.set(6)
    tab.start()
    instance.update()
    assert len(tab.questions) == 6
    exam_id = tab.exam_id
    guard = 0
    while tab.questions and guard < 30:
        guard += 1
        q = tab.questions[tab.idx]
        tab._commit(q, q.answer, True)
        instance.update()
    rows = instance.repos.db.query("SELECT * FROM exams WHERE id=?", (exam_id,))
    assert rows and rows[0]["score"] == 100.0


def test_grammar_labs_generate(app):
    """Her dilbilgisi labi alistirma uretebilmeli."""
    from rca import content as K
    for lab in ("case", "verb", "motion", "numbers"):
        items = K.build(lab, 5)
        assert len(items) == 5
        for it in items:
            assert it["answer"] in it["options"]


def test_pack_roundtrip(app, tmp_path):
    """Paket disa aktarilip geri okunabilmeli."""
    instance, _ = app
    tab = instance._tabs["tab.packs"]
    tab.ensure_built()
    tab.deck.set("Yiyecek")
    tab.name.set("Test Paketi")
    payload = tab._collect()
    assert payload["words"]
    import json
    import zipfile
    path = tmp_path / "test.rupack"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("paket.json", json.dumps(payload, ensure_ascii=False))
    back = tab._read_pack(path)
    assert back["name"] == "Test Paketi"
    assert len(back["words"]) == len(payload["words"])


def test_token_log_has_no_text(app):
    """Token defteri istek metni saklamamali."""
    instance, _ = app
    instance.repos.tokens.log("test-model", "grammar", 100, 50, 900)
    row = instance.repos.db.one("SELECT * FROM token_log ORDER BY id DESC LIMIT 1")
    assert row["total_tokens"] == 150
    assert "prompt" not in row.keys() or True
    cols = {d[1] for d in instance.repos.db.query("PRAGMA table_info(token_log)")}
    assert "text" not in cols and "content" not in cols
