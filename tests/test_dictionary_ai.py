# -*- coding: utf-8 -*-
"""Sozluk AI katmani: yapisal ai_lookup, saglam ayristirma, saglayici secimi, ayar gocu.

Hicbir test gercek aga cikmaz: sahte OpenAI uyumlu sunucu (conftest.mock_server)
ve kapali bir yerel port kullanilir.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rca_common as C                                                      # noqa: E402
from rca import dictionary as D                                             # noqa: E402
from rca.ai_client import (AIClient, AIError, alt_usable, needs_key,        # noqa: E402
                           resolve_dict_provider)
from conftest import free_port                                              # noqa: E402


# --- ai_lookup ------------------------------------------------------------
def test_ai_lookup_parses_fenced_json_and_sends_bearer_key(mock_server):
    mock_server.reset()
    client = AIClient(mock_server.base, api_key="sk-test-123")
    entries = D.ai_lookup(client, "hello", "en")
    assert len(entries) >= 1
    e = entries[0]
    assert e.source == D.SOURCE_AI
    assert e.headword == "привет" and e.stress == 4 and e.display == "приве́т"
    assert e.pos == "int" and e.extra == ""
    assert e.translation == "hi; hello"
    assert e.example.startswith("Привет") and "greeting" in e.note
    assert entries[1].headword == "здравствуйте"
    chats = mock_server.chat_requests()
    assert chats and chats[-1]["auth"] == "Bearer sk-test-123"
    body = json.loads(chats[-1]["body"])
    assert body["model"] == "mock-model" and body["stream"] is False
    assert body["messages"][0]["role"] == "system" and "JSON" in body["messages"][0]["content"]
    assert "hello" in body["messages"][-1]["content"]
    # model listesi de ayni anahtarla istenmis olmali
    assert all(r["auth"] == "Bearer sk-test-123" for r in mock_server.model_requests())
    assert client.last_model == "mock-model"


def test_ai_lookup_without_key_sends_no_authorization(mock_server):
    mock_server.reset()
    client = AIClient(mock_server.base, api_key="")
    assert D.ai_lookup(client, "hello", "tr")
    assert all(r["auth"] == "" for r in mock_server.requests)


def test_ai_lookup_uses_fixed_model_without_listing(mock_server):
    mock_server.reset()
    client = AIClient(mock_server.base, api_key="k", model="meta/llama-3.1-8b-instruct")
    assert D.ai_lookup(client, "дом", "ru")
    assert json.loads(mock_server.chat_requests()[-1]["body"])["model"] == "meta/llama-3.1-8b-instruct"
    assert mock_server.model_requests() == []


def test_ai_lookup_prompt_explains_convention_and_direction():
    system, user = D.ai_prompt("привет", "tr")
    assert "apostrophe" in system and "приве'т" in system
    assert "n v adj adv pron prep conj num part int phr" in system
    assert "ipf / pf" in system and "Turkish" in system
    assert "Cyrillic" in user
    assert "Latin" in D.ai_prompt("hello", "en")[1]
    assert "Russian" in D.ai_prompt("hello", "ru")[0]


def test_ai_lookup_garbage_returns_empty_without_raising(mock_server):
    mock_server.reset()
    client = AIClient(mock_server.base)
    try:
        mock_server.content = "Sorry, I cannot help with that."
        assert D.ai_lookup(client, "hello") == []
        mock_server.content = "[{\"headword\": 5}, \"x\", null]"
        assert D.ai_lookup(client, "hello") == []
        mock_server.content = "[{\"headword\": \"дом\", \"translation\": \"house\""   # kesik JSON
        assert D.ai_lookup(client, "hello") == []
        mock_server.content = ""
        assert D.ai_lookup(client, "hello") == []
    finally:
        mock_server.reset()
    assert D.ai_lookup(client, "") == []
    assert D.ai_lookup(None, "hello") == []


def test_ai_lookup_closed_port_raises_quickly():
    port = free_port()
    client = AIClient(f"http://127.0.0.1:{port}")
    t0 = time.time()
    with pytest.raises(AIError):                       # model listesi alinamaz -> model-yok
        D.ai_lookup(client, "hello")
    with pytest.raises(AIError):                       # dogrudan sohbet: baglanti hatasi
        D.ai_lookup(client, "hello", model="anything")
    assert time.time() - t0 < 5.0
    assert client.models() == [] and not client.is_online()


# --- ayristirma -----------------------------------------------------------
def test_parse_ai_entries_normalises_and_truncates():
    text = json.dumps([
        {"headword": "кни'га", "pos": "Noun", "extra": "feminine", "translation": ["book", "volume"],
         "example": "Э'то моя' кни'га.", "note": "x" * 900},
        {"headword": "table", "translation": "стол", "pos": "weird-tag", "extra": "masc"},
        {"headword": "чита'ть", "pos": "verb", "extra": "imperfective", "translation": "to read"},
        {"headword": "чита'ть", "pos": "v", "extra": "ipf", "translation": "to read"},   # tekrar
        {"headword": "hello", "translation": "hi"},                                     # Kiril yok
        {"headword": "быстро", "pos": "adv", "extra": "m", "translation": "fast; " + "q" * 500},
        7, None, "str",
    ], ensure_ascii=False)
    out = D.parse_ai_entries(text)
    assert [e.headword for e in out] == ["книга", "стол", "читать", "быстро"]
    book = out[0]
    assert book.pos == "n" and book.extra == "f" and book.translation == "book; volume"
    assert book.stress == 2 and book.example == "Э́то моя́ кни́га." and len(book.note) == 400
    assert out[1].pos == "phr" and out[1].extra == "" and out[1].translation == "table"
    assert out[2].pos == "v" and out[2].extra == "ipf"
    assert out[3].extra == "" and len(out[3].translation) == 240
    assert all(e.source == D.SOURCE_AI for e in out)
    # tek nesne ve sarmalanmis liste de kabul edilir, en fazla 5 madde
    assert D.parse_ai_entries('{"headword": "дом", "translation": "house", "pos": "n", "extra": "m"}')[0].extra == "m"
    many = json.dumps({"entries": [{"headword": f"сло'во{i}", "translation": f"w{i}"} for i in range(8)]})
    assert len(D.parse_ai_entries(many)) == 5
    assert D.normalize_pos("adjective") == "adj" and D.normalize_pos("") == "phr"
    assert D.normalize_extra("perf", "v") == "pf" and D.normalize_extra("pf", "n") == ""


def test_parse_ai_entries_keeps_final_syllable_stress():
    """Son hecesi vurgulu basliklarda (хорошо', вода') sondaki kesme VURGU isaretidir, tirnak degil.

    Yonerge modele tam bu bicimi ogretir; kesme kirpilirsa madde vurgusuz (stress=-1)
    kaydedilir ve hata dict_entries / kelime bankasinda kalici olur.
    """
    text = json.dumps([
        {"headword": "хорошо'", "pos": "adv", "translation": "well (mock)"},
        {"headword": "вода'", "pos": "n", "extra": "f", "translation": "water (mock)"},
        {"headword": "'она'", "pos": "pron", "translation": "she"},              # tek tirnakla sarili
        {"headword": "'хорошо''", "pos": "adv", "translation": "good"},           # sarili + vurgulu
        {"headword": "«окно'»", "pos": "n", "extra": "n", "translation": "window"},
        {"headword": "\"дом'\"", "pos": "n", "extra": "m", "translation": "house"},  # sesliden sonra degil: tirnak
    ], ensure_ascii=False)
    out = D.parse_ai_entries(text, limit=10)                     # varsayilan sinir 5 madde
    assert [(e.headword, e.stress, e.display) for e in out] == [
        ("хорошо", 5, "хорошо́"), ("вода", 3, "вода́"), ("она", 2, "она́"),
        ("хорошо", 5, "хорошо́"), ("окно", 3, "окно́"), ("дом", -1, "дом")]
    assert out[0].marked == "хорошо́" and all(e.source == D.SOURCE_AI for e in out)
    # sekmenin kaydettigi bicim (display -> ') geri okununca vurgu korunur
    rows = [(e.display.replace(C.STRESS_MARK, "'"), e.translation, e.pos, e.extra, "ai") for e in out[:2]]
    assert rows[0][0] == "хорошо'" and rows[1][0] == "вода'"
    d = D.build_dictionary(rows)
    saved = [e for e in d.lookup("вода") if e.source == D.SOURCE_AI]
    assert saved and saved[0].stress == 3 and saved[0].display == "вода́"
    assert [e for e in d.lookup("well (mock)") if e.source == D.SOURCE_AI][0].display == "хорошо́"


def test_entry_keeps_positional_constructor_and_example_default():
    e = D.Entry("дом", -1, "n", "m", "house", D.SOURCE_USER, "дом")
    assert e.example == "" and e.note == ""
    d = D.Dictionary([e])
    assert d.contains(D.Entry("ДОМ", -1, "n", "m", "House", D.SOURCE_AI, "дом", "Это дом.", "n"))
    assert not d.contains(D.Entry("дом", -1, "n", "m", "building", D.SOURCE_AI))


def test_build_dictionary_maps_stored_source():
    d = D.build_dictionary([
        ("самова'р", "samovar", "n", "m"),
        {"ru": "зюзю'ка", "en": "zzqxwv; mock word", "pos": "n", "extra": "f", "source": "ai",
         "example": "Это зюзюка.", "note": "Mock entry."},
        ("тестосло'во", "testword", "n", "n", "ai", "Пример.", ""),
        ("бозуксло'во", "brokenword", "", "", "weird"),
    ])
    assert d.lookup("самовар")[0].source == D.SOURCE_USER
    hit = d.lookup("zzqxwv")[0]
    assert hit.source == D.SOURCE_AI and hit.example == "Это зюзюка." and hit.note == "Mock entry."
    assert d.lookup("testword")[0].source == D.SOURCE_AI
    assert d.lookup("brokenword")[0].source == D.SOURCE_USER
    assert d.count_by_source()[D.SOURCE_AI] == 2


# --- saglayici secimi -----------------------------------------------------
def test_needs_key_for_local_and_private_hosts():
    assert not needs_key("http://127.0.0.1:1234")
    assert not needs_key("http://localhost:11434/v1")
    assert not needs_key("http://192.168.1.20:8080")
    assert not needs_key("http://10.0.0.5")
    assert needs_key(C.NIM_BASE)
    assert needs_key("https://openrouter.ai/api/v1")
    assert needs_key("")


def test_resolve_dict_provider_policies(mock_server):
    mock_server.reset()
    local = AIClient(mock_server.base)
    dead = AIClient(f"http://127.0.0.1:{free_port()}")
    alt = AIClient(mock_server.base, api_key="k", model="m")
    alt_nokey = AIClient(C.NIM_BASE, api_key="")
    alt_local_nokey = AIClient("http://localhost:11434", api_key="")

    def S(policy, alt_enabled=True, ai_enabled=True):
        return {"dict_ai": policy, "alt_enabled": alt_enabled, "ai_enabled": ai_enabled}

    assert resolve_dict_provider(S("off"), local, alt) is None
    assert resolve_dict_provider(S("local"), local, alt) is local
    assert resolve_dict_provider(S("local"), dead, alt) is None
    assert resolve_dict_provider(S("alt"), local, alt) is alt
    assert resolve_dict_provider(S("alt", alt_enabled=False), local, alt) is None
    assert resolve_dict_provider(S("alt"), local, alt_nokey) is None
    assert resolve_dict_provider(S("alt"), local, alt_local_nokey) is alt_local_nokey
    assert resolve_dict_provider(S("auto"), local, alt) is local
    assert resolve_dict_provider(S("auto"), dead, alt) is alt
    assert resolve_dict_provider(S("auto", alt_enabled=False), dead, alt) is None
    assert resolve_dict_provider(S("auto"), dead, alt_nokey) is None
    assert resolve_dict_provider(S("auto", ai_enabled=False), local, alt) is None
    assert resolve_dict_provider(S("auto"), None, None) is None
    assert alt_usable(S("auto"), alt) and not alt_usable(S("auto"), None)
    # alternatif uc icin erisilebilirlik denenmez (ag yok); yerel icin GET /v1/models atilir
    assert any(r["path"].endswith("/v1/models") for r in mock_server.requests)


def test_reachability_is_cached_and_reset_on_reconfigure(mock_server):
    dead = AIClient(f"http://127.0.0.1:{free_port()}")
    assert dead.reachable() is False
    calls = []
    original = dead.models
    dead.models = lambda force=False: (calls.append(force), original(force=force))[1]
    assert dead.reachable() is False and calls == []                  # onbellekten
    dead.base = mock_server.base                                       # adres degisti -> sifirla
    assert dead.reachable() is True and calls == [True]
    dead.configure(api_key="other")
    assert dead._checked_at == 0.0
    client = AIClient(mock_server.base, api_key="a")
    client.configure(base=mock_server.base + "/", api_key="a", model="m2")
    assert client.base == mock_server.base and client.model == "m2" and client.resolve("chat") == "m2"


# --- ayar gocu ------------------------------------------------------------
def test_settings_defaults_and_nim_migration(tmp_path, monkeypatch):
    for k, v in (("alt_enabled", False), ("alt_base", C.NIM_BASE),
                 ("alt_model", "meta/llama-3.1-8b-instruct"), ("dict_ai", "auto"),
                 ("dict_ai_autosave", True), ("nim_enabled", False)):
        assert C.DEFAULT_SETTINGS[k] == v, k
    assert not any("key" in k.lower() for k in C.DEFAULT_SETTINGS)
    sdir = tmp_path / "settings"
    monkeypatch.setattr(C, "APP_HOME", tmp_path)
    monkeypatch.setattr(C, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(C, "SETTINGS_DIR", sdir)
    monkeypatch.setattr(C, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(C, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(C, "SETTINGS_PATH", sdir / "settings.json")
    sdir.mkdir(parents=True)
    (sdir / "settings.json").write_text(json.dumps({"nim_enabled": True}), encoding="utf-8")
    data = C.load_settings()
    assert data["alt_enabled"] is True and data["nim_enabled"] is True and data["dict_ai"] == "auto"
    (sdir / "settings.json").write_text(json.dumps({"nim_enabled": True, "alt_enabled": False,
                                                    "dict_ai": "bogus"}), encoding="utf-8")
    data = C.load_settings()
    assert data["alt_enabled"] is False and data["dict_ai"] == "auto"


def test_rank_models_skips_specialist_models_and_prefers_fitting_general_models():
    from rca import ai_client as A
    installed = ["qwen/qwen3.6-35b-a3b", "google/gemma-4-12b-qat", "qwen/qwen3-vl-8b", "biomistral-7b",
                 "qwen2.5-math-7b-instruct", "moondream-2b-2025-04-14", "text-embedding-nomic-embed-text-v1.5"]
    ranked = A.rank_models(installed, "dictionary")
    assert ranked[0] == "google/gemma-4-12b-qat"                 # genel, 4-16B, sigar
    assert "qwen2.5-math-7b-instruct" not in ranked              # matematik modeli sozluk icin secilmez
    assert "text-embedding-nomic-embed-text-v1.5" not in ranked
    assert A.rank_models(["text-embedding-x"], "chat") == ["text-embedding-x"]   # baska secenek yoksa yine de dondur
    assert A.rank_models(["qwen2.5-7b-instruct", "gemma-4-12b-qat"], "chat")[0] == "qwen2.5-7b-instruct"  # tam tercih once
    assert A.model_size_b("qwen/qwen3.6-35b-a3b") == 35.0 and A.model_size_b("gemma-4-12b-qat") == 12.0
    assert A.is_specialist("qwen/qwen3-vl-8b") and not A.is_specialist("google/gemma-4-12b-qat")


# --------------------------------------------------------------------------
# Dusunen modeller (gemma-4 / qwen3): reasoning_effort alani, kesik yanit yinelemesi, vurgu onarimi
# --------------------------------------------------------------------------
def _client_for(mock_server, **kw):
    from rca import ai_client as A
    return A.AIClient(mock_server.base, **kw)


def test_local_client_sends_reasoning_off_and_records_finish_reason(mock_server):
    import json
    from rca import dictionary as D
    mock_server.reset(); mock_server.reasoning_tokens = 3
    client = _client_for(mock_server)
    assert client.is_local
    entries = D.ai_lookup(client, "думскроллинг", "tr")
    assert entries and entries[0].source == D.SOURCE_AI
    body = json.loads(mock_server.chat_requests()[-1]["body"])
    assert body.get("reasoning_effort") == "none" and body["max_tokens"] == D.AI_MAX_TOKENS
    assert client.last_finish_reason == "stop" and client.last_reasoning_tokens == 3


def test_remote_client_does_not_send_reasoning_field(mock_server):
    import json
    from rca import ai_client as A
    from rca import dictionary as D
    mock_server.reset()

    class RemoteClient(A.AIClient):              # uzak uc taklidi (anahtarli, yerel degil)
        is_local = property(lambda self: False)

    client = RemoteClient(mock_server.base, api_key="k")
    assert D.ai_lookup(client, "кошка", "tr")
    body = json.loads(mock_server.chat_requests()[-1]["body"])
    assert "reasoning_effort" not in body
    assert A.AIClient(mock_server.base).is_local        # sinif ozelligi bozulmadi


def test_server_rejecting_extra_fields_gets_a_retry_without_them(mock_server):
    import json
    from rca import dictionary as D
    mock_server.reset(); mock_server.reject_fields = {"reasoning_effort"}
    client = _client_for(mock_server)
    entries = D.ai_lookup(client, "думскроллинг", "tr")
    assert entries, "400 sonrasi ek alansiz yineleme basarili olmali"
    reqs = mock_server.chat_requests()
    assert len(reqs) == 2
    assert "reasoning_effort" in json.loads(reqs[0]["body"]) and "reasoning_effort" not in json.loads(reqs[1]["body"])


def test_truncated_empty_answer_is_retried_with_a_bigger_budget(mock_server):
    import json
    from rca import dictionary as D
    mock_server.reset()
    mock_server.queue = [("", "length"), (mock_server.content, "stop")]
    client = _client_for(mock_server)
    entries = D.ai_lookup(client, "прокрастинировать", "tr")
    assert entries
    reqs = mock_server.chat_requests()
    assert len(reqs) == 2
    assert json.loads(reqs[1]["body"])["max_tokens"] == D.AI_MAX_TOKENS * 3
    # kesik olmayan bos yanit yinelenmez
    mock_server.reset(); mock_server.queue = [("Sorry, I cannot help.", "stop")]
    assert D.ai_lookup(client, "прокрастинировать", "tr") == [] and len(mock_server.chat_requests()) == 1


def test_repair_stress_moves_marks_off_consonants():
    from rca import dictionary as D
    assert D.repair_stress("думскрол'линг") == "думскро'ллинг"
    assert D.mark_all(D.repair_stress("думскрол'линг")) == "думскро́ллинг"
    assert D.repair_stress("приве'т") == "приве'т" and D.repair_stress("хорошо'") == "хорошо'"
    assert D.repair_stress("дом'") == "до'м" and D.repair_stress("'она") == "она"
    assert D.repair_stress("откладыва'ть на пото'м") == "откладыва'ть на пото'м"
    entries = D.parse_ai_entries('[{"headword": "думскрол\'линг", "pos": "n", "extra": "m", '
                                 '"translation": "doomscrolling", "example": "Он часами занимается думскроллингом."}]')
    assert entries and entries[0].display == "думскро́ллинг" and entries[0].headword == "думскроллинг"
