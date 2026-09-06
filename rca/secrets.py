# -*- coding: utf-8 -*-
"""Gizli anahtar deposu (API anahtarlari).

- Windows'ta Credential Manager kullanilir (advapi32 CredWriteW / CredReadW /
  CredDeleteW, ctypes ile; harici paket yok). Hedef adi "<APP_SLUG>/<ad>",
  blob UTF-16-LE olarak saklanir.
- API yoksa ya da hata verirse <SETTINGS_DIR>/secrets.json dosyasina duser
  (mumkun olan yerde 0o600).
- Testler gercek Credential Manager'a ASLA dokunmaz: FORCE_FILE_BACKEND ya da
  <APP_SLUG_UPPER>_SECRETS_FILE=1 ortam degiskeni dosya arka ucunu zorlar.
- <APP_SLUG_UPPER>_API_KEY ortam degiskeni tanimliysa "alt_api_key" icin o kazanir.
- Anahtar hicbir kosulda settings.json'a yazilmaz.
"""
from __future__ import annotations

import ctypes
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import rca_common as C

KEY_ALT_API = "alt_api_key"                                    # alternatif ucun anahtari
ENV_FILE_BACKEND = f"{C.APP_SLUG.upper()}_SECRETS_FILE"        # RUSSIANCOURSEAI_SECRETS_FILE=1
ENV_API_KEY = f"{C.APP_SLUG.upper()}_API_KEY"                  # RUSSIANCOURSEAI_API_KEY
FORCE_FILE_BACKEND = False                                     # testler icin anahtar
SECRETS_FILENAME = "secrets.json"

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168

_advapi = None
_CREDENTIALW = None
try:                                                           # Windows disinda da import edilebilsin
    from ctypes import wintypes as _wt
except Exception:                                              # noqa: BLE001
    _wt = None


# --------------------------------------------------------------------------
# Arka uc secimi
# --------------------------------------------------------------------------
def file_backend_forced() -> bool:
    """Dosya arka ucu zorlanmis mi (test / ortam degiskeni)?"""
    if FORCE_FILE_BACKEND:
        return True
    return os.environ.get(ENV_FILE_BACKEND, "").strip().lower() in ("1", "true", "yes", "on")


def backend_name() -> str:
    """Aktif arka ucun adi: 'credman' ya da 'file'."""
    return "credman" if _credman() is not None else "file"


def _credman():
    """advapi32 tanitici (yalnizca Windows + zorlanmamis dosya modu)."""
    global _advapi, _CREDENTIALW
    if file_backend_forced() or not sys.platform.startswith("win") or _wt is None:
        return None
    if _advapi is not None:
        return _advapi
    try:
        class CREDENTIALW(ctypes.Structure):
            _fields_ = [
                ("Flags", _wt.DWORD),
                ("Type", _wt.DWORD),
                ("TargetName", _wt.LPWSTR),
                ("Comment", _wt.LPWSTR),
                ("LastWritten", _wt.FILETIME),
                ("CredentialBlobSize", _wt.DWORD),
                ("CredentialBlob", _wt.LPBYTE),
                ("Persist", _wt.DWORD),
                ("AttributeCount", _wt.DWORD),
                ("Attributes", ctypes.c_void_p),
                ("TargetAlias", _wt.LPWSTR),
                ("UserName", _wt.LPWSTR),
            ]

        adv = ctypes.WinDLL("advapi32", use_last_error=True)
        adv.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), _wt.DWORD]
        adv.CredWriteW.restype = _wt.BOOL
        adv.CredReadW.argtypes = [_wt.LPCWSTR, _wt.DWORD, _wt.DWORD,
                                  ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
        adv.CredReadW.restype = _wt.BOOL
        adv.CredDeleteW.argtypes = [_wt.LPCWSTR, _wt.DWORD, _wt.DWORD]
        adv.CredDeleteW.restype = _wt.BOOL
        adv.CredFree.argtypes = [ctypes.c_void_p]
        adv.CredFree.restype = None
        _CREDENTIALW = CREDENTIALW
        _advapi = adv
    except Exception:                                          # noqa: BLE001
        _advapi = None
    return _advapi


def _target(name: str) -> str:
    return f"{C.APP_SLUG}/{name}"


# --------------------------------------------------------------------------
# Credential Manager
# --------------------------------------------------------------------------
def _cred_read(name: str) -> Optional[str]:
    """Kayit yoksa None; API hatasinda istisna (cagiran dosyaya duser)."""
    adv = _credman()
    pcred = ctypes.POINTER(_CREDENTIALW)()
    if not adv.CredReadW(_target(name), CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
        err = ctypes.get_last_error()
        if err == ERROR_NOT_FOUND:
            return None
        raise ctypes.WinError(err)
    try:
        cred = pcred.contents
        size = int(cred.CredentialBlobSize)
        data = ctypes.string_at(cred.CredentialBlob, size) if size else b""
        return data.decode("utf-16-le", errors="replace")
    finally:
        adv.CredFree(pcred)


def _cred_write(name: str, value: str) -> None:
    adv = _credman()
    blob = value.encode("utf-16-le")
    buf = ctypes.create_string_buffer(blob, len(blob))
    cred = _CREDENTIALW()
    cred.Flags = 0
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = _target(name)
    cred.Comment = f"{C.APP_NAME} API anahtari"
    cred.CredentialBlobSize = len(blob)
    cred.CredentialBlob = ctypes.cast(buf, _wt.LPBYTE)
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.AttributeCount = 0
    cred.Attributes = None
    cred.TargetAlias = None
    cred.UserName = C.APP_SLUG
    if not adv.CredWriteW(ctypes.byref(cred), 0):
        raise ctypes.WinError(ctypes.get_last_error())


def _cred_delete(name: str) -> None:
    adv = _credman()
    if not adv.CredDeleteW(_target(name), CRED_TYPE_GENERIC, 0):
        err = ctypes.get_last_error()
        if err != ERROR_NOT_FOUND:
            raise ctypes.WinError(err)


# --------------------------------------------------------------------------
# Dosya yedegi
# --------------------------------------------------------------------------
def secrets_path() -> Path:
    """Dosya arka ucunun yolu (ayar klasoru altinda)."""
    return Path(C.SETTINGS_DIR) / SECRETS_FILENAME


def _file_load() -> Dict[str, str]:
    try:
        path = secrets_path()
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {str(k): str(v) for k, v in raw.items() if isinstance(v, str)}
    except Exception:                                          # noqa: BLE001
        pass
    return {}


def _file_save(data: Dict[str, str]) -> None:
    path = secrets_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(payload)
    try:
        os.chmod(str(path), 0o600)
    except Exception:                                          # noqa: BLE001
        pass


def _file_get(name: str) -> str:
    return _file_load().get(name, "")


def _file_set(name: str, value: str) -> None:
    data = _file_load()
    data[name] = value
    _file_save(data)


def _file_delete(name: str) -> None:
    data = _file_load()
    if name in data:
        del data[name]
        try:
            _file_save(data)
        except Exception:                                      # noqa: BLE001
            pass


# --------------------------------------------------------------------------
# Genel API
# --------------------------------------------------------------------------
def get_secret(name: str) -> str:
    """Anahtari dondur; yoksa bos dize. Hicbir zaman istisna firlatmaz."""
    if name == KEY_ALT_API:
        env = os.environ.get(ENV_API_KEY, "").strip()
        if env:
            return env
    if _credman() is not None:
        try:
            val = _cred_read(name)
            if val:
                return val
        except Exception:                                      # noqa: BLE001
            pass
    return _file_get(name)


def set_secret(name: str, value: str) -> str:
    """Anahtari sakla; kullanilan arka ucun adini dondur ('credman' | 'file' | 'none')."""
    value = (value or "").strip()
    if not value:
        delete_secret(name)
        return "none"
    if _credman() is not None:
        try:
            _cred_write(name, value)
            _file_delete(name)                                 # tek kaynak kalsin
            return "credman"
        except Exception:                                      # noqa: BLE001
            pass
    try:
        _file_set(name, value)
        return "file"
    except Exception:                                          # noqa: BLE001
        return "none"


def delete_secret(name: str) -> None:
    """Anahtari her iki arka uctan da sil (yoksa sessizce gec)."""
    if _credman() is not None:
        try:
            _cred_delete(name)
        except Exception:                                      # noqa: BLE001
            pass
    _file_delete(name)


def has_secret(name: str) -> bool:
    return bool(get_secret(name))
