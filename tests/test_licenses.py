# -*- coding: utf-8 -*-
"""THIRD_PARTY_NOTICES.md dogrulanabilir mi?

Bildirim dosyasi her bilesenin lisansini "yayimci meta verisinden dogrulandi"
diye sunar. Bu test o iddiayi tekrar edilebilir kilar: kurulu olan her dagitim
icin `importlib.metadata`'nin bildirdigi lisansi bildirim dosyasindaki iddiayla
karsilastirir, kurulu olmayanlari ATLAR (agdan hicbir sey indirilmez).

Surum numaralari BILEREK karsilastirilmaz: gelistirme ortaminda pytest,
PyInstaller ya da Pillow'un daha yeni bir surumu kurulu olabilir. Onemli olan
lisansin degismemis olmasidir - Pillow'un HPND -> MIT-CMU ad degisikligi gibi
ayni metnin iki adi da kabul edilir ve bu bildirim dosyasinda aciklanmistir.
"""
from __future__ import annotations

import importlib.metadata as md
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"

#: dagitim adi -> (bildirim dosyasindaki iddiayi karsilayan lisans kaliplari)
#: Kalip, meta verideki `License-Expression` / `License` alanina ya da
#: `License ::` siniflandiricilarina uymalidir.
CLAIMS = {
    "pypdfium2": r"BSD-3-Clause|Apache-2\.0",
    "pypdf": r"BSD-3-Clause",
    # Pillow 10.x meta verisi "HPND" der, 12.x ayni metni "MIT-CMU" olarak adlandirir.
    "pillow": r"HPND|MIT-CMU",
    "pymorphy3": r"\bMIT\b",
    "DAWG-Python": r"\bMIT\b",
    "pymorphy3-dicts-ru": r"\bMIT\b",
    "vosk": r"Apache",
    "sounddevice": r"\bMIT\b",
    "cffi": r"\bMIT\b",
    "truststore": r"\bMIT\b",
    "certifi": r"MPL-2\.0|Mozilla Public License",
    "pytest": r"\bMIT\b",
    "pyinstaller": r"GPL",
    # Bilerek kurulmaz ve ikili pakete alinmaz; kurulu ise lisansi yine GPL olmali.
    "pyttsx3": r"GPL",
}


def _declared_license(dist: "md.Distribution") -> str:
    """Dagitimin meta verisinde bildirdigi lisansi tek bir metin olarak ver."""
    meta = dist.metadata
    parts = [meta.get("License-Expression") or "", meta.get("License") or ""]
    parts += [c for c in (meta.get_all("Classifier") or [])
              if c.startswith("License")]
    return " | ".join(p for p in parts if p)


@pytest.mark.parametrize("name,pattern", sorted(CLAIMS.items()))
def test_installed_metadata_matches_the_notices_claim(name: str, pattern: str) -> None:
    """Kurulu her dagitimin lisansi bildirim dosyasindaki iddiayla ortusur."""
    try:
        dist = md.distribution(name)
    except md.PackageNotFoundError:
        pytest.skip(f"{name} bu ortamda kurulu degil - iddia PyPI meta verisinden gelir")
    declared = _declared_license(dist)
    assert declared, f"{name} lisansini meta verisinde hic bildirmiyor"
    assert re.search(pattern, declared, re.IGNORECASE), (
        f"{name} {dist.version} lisansi degismis:\n"
        f"  meta veri : {declared}\n"
        f"  beklenen  : /{pattern}/\n"
        f"THIRD_PARTY_NOTICES.md guncellenmeli.")


def test_notices_file_names_every_claimed_component() -> None:
    """Tabloda karsiligi olmayan bir bilesen kalmasin."""
    text = NOTICES.read_text(encoding="utf-8")
    missing = [n for n in CLAIMS if n.lower() not in text.lower()]
    assert not missing, f"THIRD_PARTY_NOTICES.md'de gecmiyor: {missing}"


def test_every_pinned_requirement_is_documented() -> None:
    """requirements.txt'e eklenen her paket bildirim dosyasinda anlatilir."""
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pinned = re.findall(r"^([A-Za-z0-9_.\-]+)\s*==", text, re.MULTILINE)
    assert pinned, "requirements.txt'te sabitlenmis paket bulunamadi"
    notices = NOTICES.read_text(encoding="utf-8").lower()
    undocumented = [p for p in pinned if p.lower() not in notices]
    assert not undocumented, (
        "requirements.txt'te sabitlenen ama THIRD_PARTY_NOTICES.md'de anlatilmayan "
        f"paketler: {undocumented}")


def test_gpl_speech_dependency_is_not_pinned() -> None:
    """pyttsx3 (GPL-3.0) MIT ikili pakete girmesin diye kurulum listesinde olmaz."""
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pinned = re.findall(r"^([A-Za-z0-9_.\-]+)\s*==", text, re.MULTILINE)
    assert "pyttsx3" not in [p.lower() for p in pinned], (
        "pyttsx3 GPL-3.0'dir; requirements.txt ile kurulursa dagitilan paket "
        "MIT kalamaz (bkz. THIRD_PARTY_NOTICES.md).")


def test_build_scripts_exclude_the_gpl_speech_module() -> None:
    """Iki derleme betigi de PyInstaller'a pyttsx3'u disarida birak der."""
    for script in ("build.bat", "build_macos.sh"):
        text = (ROOT / script).read_text(encoding="utf-8")
        assert "--exclude-module pyttsx3" in text, (
            f"{script} pyttsx3'u haric tutmuyor: uretilen ikili paket GPL-3.0 olur, "
            "oysa indirme sayfasi MIT diyor.")


def test_build_scripts_run_the_licence_gate() -> None:
    """Derleme betikleri ve macOS is akisi paketi yayimdan once denetler."""
    for path in ("build.bat", "build_macos.sh",
                 ".github/workflows/build-macos.yml"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "check_build_licence.py" in text, (
            f"{path} lisans denetimini calistirmiyor: eski bir dist/ agaci "
            "fark edilmeden yayimlanabilir.")


# --------------------------------------------------------------------------
# Yayim kapisi: uretilen paketin kendisi
# --------------------------------------------------------------------------
def _gate():
    """tools/check_build_licence.py modulunu yukle."""
    sys.path.insert(0, str(ROOT / "tools"))
    try:
        import check_build_licence
        return check_build_licence
    finally:
        sys.path.pop(0)


def test_licence_gate_flags_a_copyleft_bundle(tmp_path) -> None:
    """Pakette PyMuPDF / MuPDF / pyttsx3 izi varsa kapi kirmizi yanar."""
    gate = _gate()
    for marker in (b"pymupdf", b"libmupdf.dylib",
                   b"pyttsx3.drivers", b"pyttsx3/drivers", b"pyttsx3.engine"):
        blob = tmp_path / "RussianCourseAI.exe"
        blob.write_bytes(b"\x00" * 32 + marker + b"\x00pypdfium2\x00")
        found, expected = gate.scan(blob)
        assert found, marker
        assert expected                        # yeni katman da orada - yine de hata
        assert gate.main(["x", str(blob)]) == 1


def test_licence_gate_ignores_the_optional_import_in_our_own_source(tmp_path) -> None:
    """`rca/tts.py` pyttsx3 adini anar; bu, paketin gomuldugu anlamina GELMEZ.

    Yanlis pozitif olsaydi kapi her dogru derlemede kirmizi yanar ve
    kimse ona bakmazdi - bu yuzden iz olarak yalnizca paket gercekten
    gomuluyse ortaya cikan alt modul adlari kullanilir.
    """
    gate = _gate()
    source = (ROOT / "rca" / "tts.py").read_bytes()
    assert b"pyttsx3" in source.lower(), "kaynak zaten adi aniyor olmali"
    blob = tmp_path / "RussianCourseAI.exe"
    blob.write_bytes(source + b"\x00pypdfium2_raw\x00")
    assert gate.scan(blob) == (set(), True)
    assert gate.main(["x", str(blob)]) == 0


def test_licence_gate_passes_a_clean_bundle(tmp_path) -> None:
    """Yalnizca izin verici katmani tasiyan paket temiz sayilir."""
    gate = _gate()
    blob = tmp_path / "RussianCourseAI.exe"
    blob.write_bytes(b"\x00pypdfium2_raw\x00pdfium.dll\x00pypdf\x00")
    assert gate.scan(blob) == (set(), True)
    assert gate.main(["x", str(blob)]) == 0


def test_licence_gate_looks_inside_the_published_zip(tmp_path) -> None:
    """Sikistirilmis dagitim zip'i ACILARAK taranir - ham baytlar yetmez."""
    import zipfile

    gate = _gate()
    archive = tmp_path / "RussianCourseAI-Windows.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        # Dosya ADI ele vermiyor; iz yalnizca SIKISTIRILMIS icerikte.
        zf.writestr("App/_internal/render.dll", b"MuPDF renderer " * 4000)
        zf.writestr("App/_internal/pypdfium2_raw/pdfium.dll", b"pypdfium2 " * 100)
    assert b"mupdf" not in archive.read_bytes().lower(), "sikistirma bekleniyordu"
    found, expected = gate.scan(archive)
    assert found and expected
    assert gate.main(["x", str(archive)]) == 1
