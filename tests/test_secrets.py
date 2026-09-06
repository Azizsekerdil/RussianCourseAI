# -*- coding: utf-8 -*-
"""Gizli anahtar deposu: dosya arka ucu zorlanir, gercek Credential Manager'a dokunulmaz."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Izole ayar klasoru + dosya arka ucu; modulleri temiz yukle."""
    monkeypatch.setenv("RCA_HOME", str(tmp_path))
    monkeypatch.setenv("RUSSIANCOURSEAI_SECRETS_FILE", "1")
    monkeypatch.delenv("RUSSIANCOURSEAI_API_KEY", raising=False)
    # "rca" paketi de atilir; boylece her test kendi RCA_HOME yoluna bagli taze modul alir
    for name in list(sys.modules):
        if name in ("rca_common", "rca") or name.startswith("rca."):
            del sys.modules[name]
    import rca_common as CC
    import rca.secrets as S
    assert S.C is CC and CC.APP_HOME == tmp_path
    return CC, S


def test_file_backend_is_forced_in_tests(env):
    CC, S = env
    assert S.file_backend_forced() and S.backend_name() == "file"
    assert S._credman() is None
    assert S.secrets_path() == CC.SETTINGS_DIR / "secrets.json"
    assert S.ENV_FILE_BACKEND == "RUSSIANCOURSEAI_SECRETS_FILE"
    assert S.ENV_API_KEY == "RUSSIANCOURSEAI_API_KEY"


def test_force_flag_also_selects_file_backend(env, monkeypatch):
    CC, S = env
    monkeypatch.delenv("RUSSIANCOURSEAI_SECRETS_FILE")
    monkeypatch.setattr(S, "FORCE_FILE_BACKEND", True)
    assert S.backend_name() == "file"


def test_set_get_delete_roundtrip(env):
    CC, S = env
    assert S.get_secret("alt_api_key") == ""
    assert S.set_secret("alt_api_key", "nvapi-ABC-123") == "file"
    assert S.get_secret("alt_api_key") == "nvapi-ABC-123"
    assert S.has_secret("alt_api_key")
    path = S.secrets_path()
    assert path.exists() and json.loads(path.read_text(encoding="utf-8")) == {"alt_api_key": "nvapi-ABC-123"}
    S.set_secret("other", "  x-y-z  ")
    assert S.get_secret("other") == "x-y-z"
    S.delete_secret("alt_api_key")
    assert S.get_secret("alt_api_key") == "" and not S.has_secret("alt_api_key")
    assert "nvapi" not in path.read_text(encoding="utf-8")
    S.delete_secret("hic-yok")                                   # sessiz
    assert S.set_secret("other", "") == "none" and S.get_secret("other") == ""


def test_env_override_wins_for_alt_api_key(env, monkeypatch):
    CC, S = env
    S.set_secret("alt_api_key", "file-key")
    monkeypatch.setenv("RUSSIANCOURSEAI_API_KEY", "env-key")
    assert S.get_secret("alt_api_key") == "env-key"
    assert S.get_secret("other") == ""                          # yalnizca alt_api_key icin
    monkeypatch.delenv("RUSSIANCOURSEAI_API_KEY")
    assert S.get_secret("alt_api_key") == "file-key"


def test_settings_json_never_contains_the_key(env):
    CC, S = env
    data = CC.load_settings()
    data["alt_enabled"] = True
    CC.save_settings(data)
    S.set_secret("alt_api_key", "sk-super-secret-value")
    text = CC.SETTINGS_PATH.read_text(encoding="utf-8")
    assert "sk-super-secret-value" not in text
    assert "api_key" not in json.loads(text)
    assert CC.SETTINGS_PATH != S.secrets_path()
    assert S.get_secret("alt_api_key") == "sk-super-secret-value"
