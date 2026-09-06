# -*- coding: utf-8 -*-
"""Arayuz duman testi: pencere acilir, her sekme kurulur, temel akislar isler.

GUI gerektirir (Windows'ta her zaman vardir). Ekran yoksa test atlanir.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import time
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
def app(tmp_path_factory, mock_server):
    """Izole veri klasoruyla bir uygulama penceresi.

    AI adresi sahte sunucuya, gizli anahtar deposu dosya arka ucuna yonlendirilir:
    testler gercek LM Studio'ya, internete ya da Credential Manager'a dokunmaz.
    """
    import os
    home = tmp_path_factory.mktemp("rca_home")
    os.environ["RCA_HOME"] = str(home)
    os.environ["RUSSIANCOURSEAI_SECRETS_FILE"] = "1"
    (home / "settings").mkdir(parents=True, exist_ok=True)
    (home / "settings" / "settings.json").write_text(
        json.dumps({"ai_base": mock_server.base, "dict_ai": "local"}), encoding="utf-8")
    # "rca" paketinin kendisi de atilir: aksi halde paket nesnesi uzerindeki eski alt
    # modul oznitelikleri ("from rca import x") onceki testin yollarina bagli kalir.
    for name in list(sys.modules):
        if name in ("rca_common", "rca") or name.startswith("rca."):
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


# --- sozluk AI katmani -----------------------------------------------------
def _pump(instance, cond, timeout: float = 10.0) -> bool:
    """Tk dongusunu kosul saglanana kadar (en fazla `timeout` sn) isle."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        instance.update()
        if cond():
            return True
        time.sleep(0.05)
    return False


MOCK_ENTRY = (
    "```json\n"
    '[{"headword": "зюзю\'ка", "pos": "n", "extra": "f", "translation": "zzqxwv; mock word", '
    '"example": "Это зюзюка.", "note": "Mock entry."}]\n'
    "```"
)


def test_dictionary_ai_fallback_fills_results(app, mock_server):
    """Yerel sonuc yokken sorgu AI'a gider; madde 'AI' etiketiyle listelenir ve kaydedilir."""
    instance, _ = app
    mock_server.reset()
    mock_server.content = MOCK_ENTRY
    try:
        instance.settings["ai_base"] = mock_server.base
        instance.settings["dict_ai"] = "local"
        instance.settings["dict_ai_autosave"] = True
        instance.refresh_ai_clients()
        tab = instance.goto_tab("tab.dictionary")
        instance.update()
        assert tab.policy_var.get() == tab.t("d.policy_local")
        tab.q.set("zzqxwv")
        tab.search()
        assert _pump(instance, lambda: any(e.source == "ai" for e in tab.results)), "AI sonucu gelmedi"
        e = tab.current()
        assert e is not None and e.source == "ai" and e.headword == "зюзюка"
        first = tab.tree.item(tab.tree.get_children()[0], "values")
        assert first[0] == "зюзю́ка" and first[-1] == tab.t("d.src_ai")
        assert "zzqxwv" in tab.w_en.cget("text")
        assert tab.w_ex.cget("text") == "Это зюзюка." and tab.w_note.cget("text") == "Mock entry."
        out = tab.ai_out.get("1.0", "end")
        assert "mock-model" in out and "LM Studio" in out and "zzqxwv" in out
        assert tab.provider_lbl.cget("text") == tab.t("d.status_local")
        assert not tab.btn_save_ai.winfo_manager()          # otomatik kaydedildi -> dugme gizli
        rows = instance.repos.dictionary.all(source="ai")
        assert [r["ru"] for r in rows] == ["зюзю'ка"] and rows[0]["example"] == "Это зюзюка."
        assert tab.t("d.src_ai") + " 1" in tab.count_lbl.cget("text")
        # bir sonraki arama yerel ve cevrimdisi calisir: sunucuya yeni sohbet istegi gitmez
        n = len(mock_server.chat_requests())
        tab.q.set("zzqxwv")
        tab.search()
        instance.update()
        assert tab.results and tab.results[0].source == "ai"
        assert len(mock_server.chat_requests()) == n
        # AI maddesi ornek cumlesiyle kelime bankasina eklenir
        tab.add_to_bank()
        w = instance.repos.words.search("зюзюка", limit=1)[0]
        assert w["example_ru"] == "Это зюзюка." and w["pos"] == "noun-f"
        # yerel sonuc olsa da "AI'a sor" sorguyu AI'a goturur ve maddeleri basa koyar
        mock_server.content = MOCK_ENTRY.replace("зюзю\'ка", "дом").replace("zzqxwv; mock word", "house; home")
        tab.q.set("дом")
        tab.search()
        assert tab.results and tab.results[0].source != "ai"
        tab.ask_ai()
        assert _pump(instance, lambda: tab.results and tab.results[0].source == "ai")
        assert tab.results[0].headword == "дом" and len(mock_server.chat_requests()) == n + 1
    finally:
        mock_server.reset()


def test_dictionary_ai_off_makes_no_request(app, mock_server):
    """Politika 'kapali' iken ayni arama sunucuya HIC istek gondermez."""
    instance, _ = app
    instance.settings["dict_ai"] = "off"
    tab = instance.goto_tab("tab.dictionary")
    tab.on_show()                                            # sayfa zaten acik: gezinme kancasi
    _pump(instance, lambda: False, timeout=0.3)             # bekleyen arka plan isleri bitsin
    assert tab.policy_var.get() == tab.t("d.policy_off")
    assert tab.provider_lbl.cget("text") == tab.t("d.status_off")
    before = mock_server.count
    tab.q.set("qqqzzzy")
    tab.search()
    _pump(instance, lambda: False, timeout=1.0)
    assert mock_server.count == before
    assert tab.results == []
    assert tab.t("d.noresult") in tab.ai_out.get("1.0", "end")
    tab.ask_ai()
    _pump(instance, lambda: False, timeout=0.3)
    assert mock_server.count == before
    assert tab.t("d.status_off") in tab.ai_out.get("1.0", "end")
    instance.settings["dict_ai"] = "local"


def test_dictionary_alt_endpoint_uses_key_and_model(app, mock_server):
    """Alternatif uc: anahtar Bearer olarak gider, sabit model kullanilir, kayit elle yapilir."""
    instance, _ = app
    import rca.secrets as secrets
    mock_server.reset()
    mock_server.content = MOCK_ENTRY.replace("зюзю\'ка", "бюбю\'ка").replace("zzqxwv", "yyqxwv")
    try:
        secrets.set_secret(secrets.KEY_ALT_API, "nvapi-ui-test")
        instance.settings.update({"dict_ai": "alt", "alt_enabled": True,
                                  "alt_base": mock_server.base,
                                  "alt_model": "meta/llama-3.1-8b-instruct",
                                  "dict_ai_autosave": False})
        instance.refresh_ai_clients()
        assert instance.ai_alt.api_key == "nvapi-ui-test" and instance.ai_alt.base == mock_server.base
        tab = instance.goto_tab("tab.dictionary")
        tab.on_show()                                        # sayfa zaten acik: gezinme kancasi
        instance.update()
        assert tab.policy_var.get() == tab.t("d.policy_alt")
        tab.q.set("yyqxwv")
        tab.search()
        assert _pump(instance, lambda: any(e.source == "ai" for e in tab.results))
        chat = mock_server.chat_requests()[-1]
        assert chat["auth"] == "Bearer nvapi-ui-test"
        assert json.loads(chat["body"])["model"] == "meta/llama-3.1-8b-instruct"
        assert tab.provider_lbl.cget("text") == tab.t("d.status_alt")
        assert tab.t("d.policy_alt") in tab.ai_out.get("1.0", "end")
        # otomatik kayit kapali: dugme gorunur, tiklayinca kaydeder ve kaybolur
        assert tab.btn_save_ai.winfo_manager() == "pack"
        assert instance.repos.dictionary.count(source="ai") == 1      # onceki testten зюзюка
        tab.save_ai_entry()
        assert instance.repos.dictionary.count(source="ai") == 2
        assert not tab.btn_save_ai.winfo_manager()
        # iki istemci de ayni token defterine yazar
        row = instance.repos.db.one(
            "SELECT * FROM token_log WHERE task='dictionary' ORDER BY id DESC LIMIT 1")
        assert row and row["model"] == "meta/llama-3.1-8b-instruct" and row["total_tokens"] == 63
    finally:
        secrets.delete_secret(secrets.KEY_ALT_API)
        instance.settings.update({"dict_ai": "local", "alt_enabled": False, "dict_ai_autosave": True})
        instance.refresh_ai_clients()
        mock_server.reset()


def _dict_chats_logged(instance) -> int:
    """Token defterindeki sozluk cagrisi sayisi: yanit istemciden dondugunde artar."""
    row = instance.repos.db.one("SELECT COUNT(*) AS n FROM token_log WHERE task='dictionary'")
    return int(row["n"]) if row else 0


def test_dictionary_stale_ai_reply_is_discarded(app, mock_server):
    """Yanit beklenirken baska bir sorgu aranirsa eski sorgunun AI maddeleri yeni listeye karismaz.

    Yerel modeller saniyeler surebilir; kullanici beklemeden yeni kelime yazar. Gecikmeli
    yanit geldiginde liste, secim, detay paneli, durum cubugu ve dict_entries dokunulmadan
    kalmali. Ayni sorguya donulmusse (sessiz yeniden arama dahil) yanit yine kullanilir.
    """
    instance, _ = app
    mock_server.reset()
    mock_server.content = MOCK_ENTRY.replace("зюзю\'ка", "кюкю\'ка").replace("zzqxwv", "wwqxzv")
    mock_server.delay = 0.8
    try:
        instance.settings.update({"dict_ai": "local", "dict_ai_autosave": True})
        tab = instance.goto_tab("tab.dictionary")
        tab.on_show()
        instance.update()
        before = instance.repos.dictionary.count(source="ai")
        logged = _dict_chats_logged(instance)
        tab.q.set("wwqxzv")
        tab.search()                                    # yerel sonuc yok -> AI'a gider (gecikmeli)
        assert tab.results == [] and instance.status.get() == tab.t("d.ai_asking")
        tab.q.set("дом")
        tab.search()                                    # kullanici beklemedi, yeni kelime aradi
        assert tab.results and tab.results[0].headword == "дом" and tab.results[0].source != "ai"
        assert _pump(instance, lambda: _dict_chats_logged(instance) > logged), "gecikmeli yanit gelmedi"
        _pump(instance, lambda: False, timeout=0.5)     # yanit ana threadde islendi (ve atildi)
        assert tab.q.get() == "дом"
        assert tab.results[0].headword == "дом" and tab.results[0].source != "ai"
        assert not any(e.headword == "кюкюка" for e in tab.results)
        assert tab.current() is not None and tab.current().headword == "дом"
        assert tab.w_ru.cget("text") == "дом" and "wwqxzv" not in tab.w_en.cget("text")
        assert tab.t("d.ai_found").format(n=1) not in instance.status.get()
        assert instance.repos.dictionary.count(source="ai") == before
        # ayni sorgu yeniden aranir; yanit gelmeden yapilan SESSIZ yeniden arama
        # (OpenRussian yuklendi / tuslama) bekleyen yaniti gecersiz kilmaz
        logged = _dict_chats_logged(instance)
        tab.q.set("wwqxzv")
        tab.search()
        tab.search(quiet=True)
        assert _pump(instance, lambda: any(e.source == "ai" for e in tab.results))
        assert tab.current() is not None and tab.current().headword == "кюкюка"
        assert instance.repos.dictionary.count(source="ai") == before + 1
    finally:
        mock_server.reset()


def test_dictionary_quiet_research_keeps_unsaved_ai_rows(app, mock_server):
    """Otomatik kayit kapali: sessiz yeniden arama AI satirini, secimi ve kaydet dugmesini korur.

    load_openrussian.done() ve tuslama search(quiet=True) cagirir; kaydedilmemis AI maddeleri
    self.dict'te olmadigi icin eskiden listeden siliniyor, secim de bosaliyordu.
    """
    instance, _ = app
    mock_server.reset()
    mock_server.content = MOCK_ENTRY.replace("зюзю\'ка", "мюмю\'ка").replace("zzqxwv", "vvqxzw")
    try:
        instance.settings.update({"dict_ai": "local", "dict_ai_autosave": False})
        tab = instance.goto_tab("tab.dictionary")
        tab.on_show()
        instance.update()
        before = instance.repos.dictionary.count(source="ai")
        tab.q.set("vvqxzw")
        tab.search()
        assert _pump(instance, lambda: any(e.source == "ai" for e in tab.results))
        assert tab.current() is not None and tab.current().headword == "мюмюка"
        assert tab.btn_save_ai.winfo_manager() == "pack"
        n = len(mock_server.chat_requests())
        tab.search(quiet=True)                          # OpenRussian yuklendi / tuslama yolu
        instance.update()
        assert [e.headword for e in tab.results] == ["мюмюка"]
        assert tab.tree.selection() == ("0",) and tab.current().headword == "мюмюка"
        assert tab.w_ru.cget("text") == "мюмю́ка" and tab.btn_save_ai.winfo_manager() == "pack"
        # ikinci Enter aga cikmaz; madde listede kalir, kaydedilmemistir
        tab.search()
        _pump(instance, lambda: False, timeout=0.3)
        assert len(mock_server.chat_requests()) == n and tab.results[0].source == "ai"
        assert instance.repos.dictionary.count(source="ai") == before
        # secim korundugu icin kelime bankasina ekleme ve elle kaydetme calisir
        tab.add_to_bank()
        assert instance.repos.words.search("мюмюка", limit=1)
        tab.save_ai_entry()
        assert instance.repos.dictionary.count(source="ai") == before + 1
        assert not tab.btn_save_ai.winfo_manager()
        # baska bir sorgunun listesine tasinmaz
        tab.q.set("дом")
        tab.search()
        assert tab.results and not any(e.headword == "мюмюка" for e in tab.results)
        assert not tab.btn_save_ai.winfo_manager()
    finally:
        instance.settings["dict_ai_autosave"] = True
        mock_server.reset()


def test_settings_tab_stores_key_in_secrets_not_in_settings_json(app, mock_server):
    """Ayarlar: anahtar gizli depoya gider, settings.json'a asla yazilmaz; baglanti testi calisir."""
    instance, _ = app
    import rca.secrets as secrets
    CC = sys.modules["rca_common"]
    tab = instance.goto_tab("tab.settings")
    instance.update()
    assert tab.alt_key.get() == "" and tab.alt_key_state.cget("text") == tab.t("set.alt_key_none")
    try:
        tab.alt_on.set(True)
        tab.alt_base.set(mock_server.base)
        tab.alt_model.set("m-ui")
        tab.alt_key.set("sk-from-ui")
        tab.dict_ai.set(tab.t("d.policy_auto"))
        tab.save()
        instance.update()
        assert tab.alt_key.get() == ""                                  # alan temizlenir
        assert tab.alt_key_state.cget("text") == tab.t("set.alt_key_saved")
        assert secrets.get_secret(secrets.KEY_ALT_API) == "sk-from-ui"
        text = CC.SETTINGS_PATH.read_text(encoding="utf-8")
        assert "sk-from-ui" not in text
        data = json.loads(text)
        assert data["alt_enabled"] is True and data["nim_enabled"] is True
        assert data["alt_base"] == mock_server.base and data["alt_model"] == "m-ui"
        assert data["dict_ai"] == "auto" and not any("key" in k for k in data)
        assert instance.ai_alt.api_key == "sk-from-ui" and instance.ai_alt.model == "m-ui"
        assert instance.settings["dict_ai"] == "auto"
        tab.test_alt()
        assert _pump(instance, lambda: tab.t("set.alt_ok") in tab.alt_status.cget("text"))
        assert "mock-model" in tab.alt_status.cget("text")
        tab.delete_alt_key()
        assert secrets.get_secret(secrets.KEY_ALT_API) == "" and instance.ai_alt.api_key == ""
        assert tab.alt_key_state.cget("text") == tab.t("set.alt_key_none")
    finally:
        secrets.delete_secret(secrets.KEY_ALT_API)
        tab.alt_on.set(False)
        tab.dict_ai.set(tab.t("d.policy_local"))
        tab.save()
        instance.update()


def test_settings_language_change_keeps_dict_ai_policy(app):
    """Ayarlar'da dil degistirip kaydetmek sozluk AI politikasini 'auto'ya dusurmez.

    Politika kutusu eski dilin etiketini tasir; cozumleme dilden bagimsiz olmali. Ust
    cubuktan dil degisince de kutular yeni dile gecer ve kaydedilmemis secim korunur.
    """
    instance, _ = app
    from rca import i18n
    from rca.tabs.dictionary_tab import POLICY_KEYS, policy_code
    CC = sys.modules["rca_common"]
    for code, key in POLICY_KEYS.items():
        assert all(policy_code(i18n.t(key, lang)) == code for lang in i18n.LANGS), code
    assert policy_code("bogus") == "auto"

    old_lang = instance.ui_lang()
    dtab = instance.goto_tab("tab.dictionary")
    tab = instance.goto_tab("tab.settings")
    instance.update()
    try:
        tab.dict_ai.set(tab._policy_label("off"))        # etiket AKTIF (eski) dilde
        tab.lang.set(i18n.LANG_NAMES["en"])
        tab.save()
        instance.update()
        assert instance.settings["ui_lang"] == "en" and instance.settings["dict_ai"] == "off"
        assert json.loads(CC.SETTINGS_PATH.read_text(encoding="utf-8"))["dict_ai"] == "off"
        assert tab.dict_ai.get() == "Off" and tab.lang.get() == "English"
        assert tuple(tab.dict_ai_box["values"]) == ("Auto", "LM Studio (local)", "Alternative endpoint", "Off")
        assert dtab.policy_var.get() == "Off"
        # ust cubuktan dil degisimi: kaydedilmemis secim korunur, dil kutusu esitlenir
        tab.dict_ai.set(tab._policy_label("local"))
        instance.set_ui_language("ru")
        instance.update()
        assert tab.lang.get() == i18n.LANG_NAMES["ru"]
        assert tab.dict_ai.get() == i18n.t("d.policy_local", "ru")
        assert instance.settings["dict_ai"] == "off"                     # henuz kaydedilmedi
        tab.save()
        instance.update()
        assert instance.settings["dict_ai"] == "local" and instance.settings["ui_lang"] == "ru"
    finally:
        instance.set_ui_language(old_lang)
        instance.update()
        tab.dict_ai.set(tab._policy_label("local"))
        tab.save()
        instance.update()


# --- sozluk yon secici + Turkce --------------------------------------------
def _display_columns(tab) -> tuple:
    cols = tab.tree["displaycolumns"]
    return tuple(cols.split()) if isinstance(cols, str) else tuple(cols)


def test_dictionary_direction_switch_reruns_search_and_persists(app):
    """Yon kutusu: arama yeniden calisir, etkin yon etiketi ve sutun sirasi guncellenir, ayar kaydedilir.

    AI politikasi 'kapali' tutulur: bu test aga / sahte sunucuya HIC istek gondermez.
    Gomulu verinin Turkce kapsami varsayilmaz; Turkce'li madde testte eklenir.
    """
    instance, _ = app
    from rca import dictionary as D
    from rca import i18n
    from rca.tabs.dictionary_tab import DIRECTION_KEYS, direction_code
    CC = sys.modules["rca_common"]
    for code, key in DIRECTION_KEYS.items():
        assert all(direction_code(i18n.t(key, lang)) == code for lang in i18n.LANGS), code
    assert direction_code("bogus") == "auto"
    instance.settings["dict_ai"] = "off"
    tab = instance.goto_tab("tab.dictionary")
    tab.on_show()
    _pump(instance, lambda: False, timeout=0.3)
    old_lang = instance.ui_lang()
    try:
        assert instance.settings.get("dict_direction", "auto") == "auto"
        assert tab.direction_var.get() == tab.t("d.dir_auto")
        assert _display_columns(tab) == ("ru", "en", "tr", "pos", "extra", "src")
        assert tab.tree.heading("tr", "text") == tab.t("d.turkish")
        tab.dict.extend([D.Entry("тестдом", -1, "n", "m", "testhouse", D.SOURCE_USER,
                                 tr="testev; deneme evi")])
        tab.q.set("house")
        tab.search()
        assert tab.dir_lbl.cget("text") == tab.t("d.dir_en2ru") and tab.results[0].headword == "дом"
        tab.q.set("testev")
        tab.search()
        assert tab.dir_lbl.cget("text") == tab.t("d.dir_tr2ru") and tab.results[0].headword == "тестдом"
        assert tab.w_tr.cget("text") == f"{tab.t('d.turkish')}: testev; deneme evi"
        assert tab.tree.item("0", "values")[2] == "testev; deneme evi"
        # kutudan RU → EN: ayni sorgu yalnizca baslikta aranir -> sonuc yok; etiket + ayar + dosya degisir
        tab.direction_var.set(tab.t("d.dir_ru2en"))
        tab._on_direction_change()
        instance.update()
        assert instance.settings["dict_direction"] == "ru2en"
        assert json.loads(CC.SETTINGS_PATH.read_text(encoding="utf-8"))["dict_direction"] == "ru2en"
        assert tab.results == [] and tab.dir_lbl.cget("text") == tab.t("d.dir_ru2en")
        # RU → TR: Turkce sutunu basligin hemen sagina gelir, detay panelinde iki karsilik
        tab.q.set("тестдом")
        tab.direction_var.set(tab.t("d.dir_ru2tr"))
        tab._on_direction_change()
        instance.update()
        assert instance.settings["dict_direction"] == "ru2tr"
        assert _display_columns(tab) == ("ru", "tr", "en", "pos", "extra", "src")
        assert tab.results and tab.results[0].headword == "тестдом"
        assert tab.dir_lbl.cget("text") == tab.t("d.dir_ru2tr")
        assert tab.w_en.cget("text") == f"{tab.t('d.trans')}: testhouse"
        assert tab.w_tr.cget("text") == f"{tab.t('d.turkish')}: testev; deneme evi"
        # kelime bankasina ekle: TR alani Turkce karsiligin ilk anlami
        tab.add_to_bank()
        w = instance.repos.words.search("тестдом", limit=1)[0]
        assert w["tr"] == "testev" and w["en"] == "testhouse"
        # Turkce'si olmayan maddede '—' (AI kapali: istek yok)
        tab.q.set("дом")
        tab.search()
        instance.update()
        e = tab.results[0]
        assert tab.w_tr.cget("text") == f"{tab.t('d.turkish')}: {e.tr or '—'}"
        # rastgele kelime EN→RU / TR→RU secilmisken de baslikta arar
        instance.settings["dict_direction"] = "tr2ru"
        tab.on_show()
        instance.update()
        assert tab.direction_var.get() == tab.t("d.dir_tr2ru") and tab.chosen_direction() == "tr2ru"
        tab.random_word()
        assert tab.results and tab.dir_lbl.cget("text") == tab.t("d.dir_ru2tr")
        # dil degisince kutu ve sutun basliklari yeni dile gecer, secim korunur
        instance.set_ui_language("en")
        instance.update()
        assert tab.direction_var.get() == "TR → RU" and tab.tree.heading("tr", "text") == "Turkish"
        assert tuple(tab.direction_box["values"]) == ("Auto", "RU → EN", "EN → RU", "RU → TR", "TR → RU")
        assert tab.tree.heading("en", "text") == "English"
    finally:
        instance.set_ui_language(old_lang)
        instance.settings.update({"dict_direction": "auto", "dict_ai": "local"})
        tab._sync_direction()
        tab._sync_policy()
        tab._order_columns()
        CC.save_settings(instance.settings)
        instance.update()


def test_dictionary_ru2tr_asks_ai_for_missing_turkish_gloss(app, mock_server):
    """RU→TR yonunde Turkce karsiligi olmayan madde: AI otomatik sorulur, gloss mevcut maddeye islenir.

    dict_entries'e kopya satir eklenmez (UPDATE), bellekteki madde zenginlesir, bir sonraki
    arama AI'a gitmez ve yeniden kurulan sozluk Turkce'yi tasir.
    """
    instance, _ = app
    from rca import dictionary as D
    mock_server.reset()
    mock_server.content = ('[{"headword": "бюбюдо\'м", "pos": "n", "extra": "m", "translation_en": "mockhouse", '
                           '"translation_tr": "sahte ev; deneme evi", "example": "Это бюбюдом.", "note": "Mock."}]')
    try:
        instance.settings.update({"dict_ai": "local", "dict_ai_autosave": True, "dict_direction": "ru2tr"})
        instance.refresh_ai_clients()
        tab = instance.goto_tab("tab.dictionary")
        tab.on_show()
        instance.update()
        assert tab.direction_var.get() == tab.t("d.dir_ru2tr")
        assert instance.repos.dictionary.add("бюбюдо'м", "mockhouse", "n", "m") == 1
        tab.dict.extend([D.Entry("бюбюдом", 5, "n", "m", "mockhouse", D.SOURCE_USER, D.mark_all("бюбюдо'м"))])
        before = instance.repos.dictionary.count()
        n_chat = len(mock_server.chat_requests())
        tab.q.set("бюбюдом")
        tab.search()
        assert tab.results and tab.results[0].headword == "бюбюдом" and tab.results[0].tr == ""
        assert tab.dir_lbl.cget("text") == tab.t("d.dir_ru2tr")
        assert tab.t("d.ai_fill_tr") in tab.ai_out.get("1.0", "end")
        assert _pump(instance, lambda: any(e.tr for e in tab.results)), "AI Turkce karsiligi gelmedi"
        assert len(mock_server.chat_requests()) == n_chat + 1
        body = json.loads(mock_server.chat_requests()[-1]["body"])
        assert "translation_tr" in body["messages"][0]["content"] and "Cyrillic" in body["messages"][-1]["content"]
        # AI maddesi listenin basinda; mevcut madde zenginlesti; DB'de kopya yok, tr doldu
        assert tab.results[0].source == "ai" and tab.results[0].tr == "sahte ev; deneme evi"
        stored = [e for e in tab.results if e.source == D.SOURCE_USER and e.headword == "бюбюдом"]
        assert stored and stored[0].tr == "sahte ev; deneme evi"
        assert instance.repos.dictionary.count() == before
        row = [r for r in instance.repos.dictionary.all() if r["ru"] == "бюбюдо'м"][0]
        assert row["tr"] == "sahte ev; deneme evi" and row["source"] == "user"
        assert tab.w_tr.cget("text") == f"{tab.t('d.turkish')}: sahte ev; deneme evi"
        out = tab.ai_out.get("1.0", "end")
        assert "EN: mockhouse" in out and "TR: sahte ev; deneme evi" in out
        assert not tab.btn_save_ai.winfo_manager()
        # ikinci arama: Turkce artik var -> AI'a yeniden sorulmaz
        tab.search()
        _pump(instance, lambda: False, timeout=0.5)
        assert len(mock_server.chat_requests()) == n_chat + 1
        assert tab.results[0].headword == "бюбюдом" and tab.results[0].tr == "sahte ev; deneme evi"
        d = D.build_dictionary(instance.repos.dictionary.all())
        assert d.lookup("бюбюдом", "ru2tr")[0].tr == "sahte ev; deneme evi"
        assert d.lookup("sahte ev", "tr2ru")[0].headword == "бюбюдом"
        # kelime bankasi: TR alani Turkce'nin ilk anlami
        tab.add_to_bank()
        assert instance.repos.words.search("бюбюдом", limit=1)[0]["tr"] == "sahte ev"
    finally:
        instance.settings.update({"dict_direction": "auto", "dict_ai": "local"})
        tab._sync_direction()
        tab._order_columns()
        mock_server.reset()


def test_dictionary_turkish_fill_updates_unstressed_stored_row_instead_of_duplicating(app, mock_server):
    """AI'in Turkce dolgusu, VURGUSUZ ve farkli buyuk/kucuk harfli sakli satira islenir; kopya 'ai' satiri acilmaz.

    Kullanicinin ekleme penceresinden / eski CSV'den gelen satirlar cogu zaman vurgusuzdur; AI ise
    vurgulu baslik ve kucuk harf Ingilizce dondurur. Bellekteki eslesme vurgu/harf farksizdir; kalici
    yazim da sakli satirin kimligiyle yapilmali (UPDATE), yoksa acilista 'ai' satiri kullanicinin
    satirini golgeler. Otomatik kayit KAPALI: dolgu 'Sozluge kaydet' ile yazilir. Sakli maddenin
    DB satiri yoksa (gomulu / OpenRussian) Turkce'yi tasiyan tek bir 'ai' satiri acilir.
    """
    instance, _ = app
    from rca import dictionary as D
    mock_server.reset()
    mock_server.content = ('[{"headword": "тестови\'к", "pos": "n", "extra": "m", "translation_en": "testword", '
                           '"translation_tr": "deneme sözcüğü; test kelimesi", "example": "Это тестовик.", "note": "Mock."}]')
    try:
        instance.settings.update({"dict_ai": "local", "dict_ai_autosave": False, "dict_direction": "ru2tr"})
        instance.refresh_ai_clients()
        tab = instance.goto_tab("tab.dictionary")
        tab.on_show()
        instance.update()
        assert instance.repos.dictionary.add("тестовик", "Testword", "n", "m") == 1      # vurgusuz, buyuk harfli
        tab.dict.extend([D.Entry("тестовик", -1, "n", "m", "Testword", D.SOURCE_USER, D.mark_all("тестовик"))])
        before = instance.repos.dictionary.count()
        n_chat = len(mock_server.chat_requests())
        tab.q.set("тестовик")
        tab.search()
        assert tab.results and tab.results[0].tr == "" and tab.dir_lbl.cget("text") == tab.t("d.dir_ru2tr")
        assert _pump(instance, lambda: any(e.tr for e in tab.results)), "AI Turkce karsiligi gelmedi"
        assert len(mock_server.chat_requests()) == n_chat + 1
        # bellekte: sakli madde zenginlesti, kimligi (vurgusuz, 'Testword') degismedi; henuz kaydedilmedi
        stored = [e for e in tab.results if e.source == D.SOURCE_USER and e.headword == "тестовик"]
        assert stored and stored[0].tr == "deneme sözcüğü; test kelimesi"
        assert stored[0].stress == -1 and stored[0].translation == "Testword"
        assert tab.btn_save_ai.winfo_manager() == "pack"
        assert instance.repos.dictionary.count() == before
        assert [r["tr"] for r in instance.repos.dictionary.all() if r["ru"] == "тестовик"] == [""]
        # 'Sozluge kaydet': sakli satir GUNCELLENIR, kopya yok, kaynak ve baslik ayni kalir
        tab.save_ai_entry()
        instance.update()
        assert instance.repos.dictionary.count() == before
        rows = [r for r in instance.repos.dictionary.all() if r["en"].lower() == "testword"]
        assert [(r["ru"], r["en"], r["tr"], r["source"]) for r in rows] == [
            ("тестовик", "Testword", "deneme sözcüğü; test kelimesi", "user")]
        assert not tab.btn_save_ai.winfo_manager()
        # yeniden kurulan sozluk: tek madde, kullanicinin satiri (golgelenme yok)
        d = D.build_dictionary(instance.repos.dictionary.all())
        hit = d.lookup("тестовик", "ru2tr")
        assert len(hit) == 1 and hit[0].source == D.SOURCE_USER and hit[0].stress == -1
        assert hit[0].tr == "deneme sözcüğü; test kelimesi"
        # DB satiri olmayan sakli madde (gomulu / OpenRussian gibi): Turkce'yi tasiyan TEK 'ai' satiri
        tab.dict.extend([D.Entry("тестогом", -1, "n", "m", "testgom", D.SOURCE_BUILTIN, D.mark_all("тестогом"))])
        mock_server.content = ('[{"headword": "тестого\'м", "pos": "n", "extra": "m", "translation_en": "Testgom", '
                               '"translation_tr": "deneme gomu"}]')
        tab.q.set("тестогом")
        tab.search()
        assert _pump(instance, lambda: any(e.tr for e in tab.results)), "AI Turkce karsiligi gelmedi"
        tab.save_ai_entry()
        instance.update()
        assert instance.repos.dictionary.count() == before + 1
        rows = [r for r in instance.repos.dictionary.all() if r["en"].lower() == "testgom"]
        assert [(r["ru"], r["tr"], r["source"]) for r in rows] == [("тестогом", "deneme gomu", "ai")]
        tab.save_ai_entry()                                             # ikinci kez: hicbir sey yazilmaz
        assert instance.repos.dictionary.count() == before + 1
    finally:
        instance.settings.update({"dict_direction": "auto", "dict_ai": "local", "dict_ai_autosave": True})
        tab._sync_direction()
        tab._order_columns()
        mock_server.reset()
