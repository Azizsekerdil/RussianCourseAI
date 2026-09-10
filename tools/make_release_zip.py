# -*- coding: utf-8 -*-
"""Windows dagitim arsivini uretir: dist/RussianCourseAI-Windows.zip.

Arsivin kokunde uc dosya bulunur - RussianCourseAI.exe, LICENSE ve
THIRD_PARTY_NOTICES.md - boylece MIT metni ve ucuncu taraf bildirimleri
indirilen paketle birlikte gelir. macOS tarafinda ayni ikisi
RussianCourseAI.app/Contents/Resources altina kopyalanir (bkz. build_macos.sh).

Arsiv zipfile ile yazilir; sonuc hangi kabuk ya da PowerShell surumunun
calistigina bagli degildir.

    python tools/make_release_zip.py

Cikis kodu 0 basarili, 1 eksik dosya. build.bat derlemeden sonra cagirir;
Windows is akisi de ayni betigi kullanir, boylece elde ve CI'da uretilen
paketin icerigi birebir aynidir.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "dist" / "RussianCourseAI-Windows.zip"
MEMBERS = [
    ROOT / "dist" / "RussianCourseAI.exe",
    ROOT / "LICENSE",
    ROOT / "THIRD_PARTY_NOTICES.md",
]


def main() -> int:
    missing = [p for p in MEMBERS if not p.is_file()]
    if missing:
        for path in missing:
            print(f"HATA: {path} bulunamadi.", file=sys.stderr)
        print("Lisanssiz ya da eksik paket uretilmez.", file=sys.stderr)
        return 1

    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    ZIP_PATH.unlink(missing_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in MEMBERS:
            archive.write(path, path.name)

    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = archive.namelist()
    expected = [p.name for p in MEMBERS]
    if names != expected:
        print(f"HATA: ZIP icerigi beklenenden farkli: {names}", file=sys.stderr)
        return 1

    print(f"Packaged: {ZIP_PATH} ({ZIP_PATH.stat().st_size} bayt)")
    print("  " + ", ".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
