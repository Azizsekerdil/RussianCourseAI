# -*- coding: utf-8 -*-
"""Uretilen ikili paket gercekten MIT kosullariyla dagitilabilir mi?

Depo MIT lisanslidir ve indirme sayfasi da oyle der. Bunu ikili paket icin
bozabilecek iki sey vardir:

* AGPL lisansli **PyMuPDF / MuPDF** - kaldirildi, geri gelmemeli;
* GPL-3.0 lisansli **pyttsx3** - `requirements.txt`'te yoktur ve iki derleme
  betigi de `--exclude-module pyttsx3` verir, ama derleme makinesinde kurulu
  olabilecegi icin sonuc ayrica denetlenir.

Betik `dist/` altindaki dosyalarin BAYTLARINI tarar; hicbir sey ithal etmez,
calistirmaz ve aga cikmaz.

    python tools/check_build_licence.py                 # dist/ altini tara
    python tools/check_build_licence.py dist/App.exe    # tek dosya / klasor

Cikis kodu 0 temiz, 1 sorunlu, 2 taranacak dosya yok. Derleme betikleri bunu
paketi yayimlamadan once cagirir; eski bir `dist/` agacinin yanlislikla
yuklenmesi de boylece yakalanir.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Pakette bulunmasi lisans acisindan SORUN olan izler.
#:
#: Izler PAKETIN ADI degil, paketin KENDI dosyalarinin izidir. Fark onemli:
#: `rca/tts.py` kaynak kodunda "pyttsx3" adi gecer (istege bagli ithal ve
#: durum metni), bu yuzden dogru derlenmis bir pakette de o dizge bulunur.
#: Bundan `pyttsx3.drivers` gibi yalnizca paket gercekten gomuluyse ortaya
#: cikan alt modul adlari kullanilir. PyMuPDF ise depoda hicbir yerde
#: gecmez (tests/test_pdf_backend.py bunu zorlar), o yuzden duz ad yeter.
FORBIDDEN = {
    b"pymupdf": "PyMuPDF (AGPL-3.0) - PDF katmani pypdfium2 + pypdf olmali",
    b"mupdf": "MuPDF (AGPL-3.0) - PyMuPDF'in yerel kutuphanesi",
    b"pyttsx3.drivers": "pyttsx3 (GPL-3.0) - --exclude-module pyttsx3 verilmemis",
    b"pyttsx3/drivers": "pyttsx3 (GPL-3.0) - --exclude-module pyttsx3 verilmemis",
    b"pyttsx3\\drivers": "pyttsx3 (GPL-3.0) - --exclude-module pyttsx3 verilmemis",
    b"pyttsx3.engine": "pyttsx3 (GPL-3.0) - --exclude-module pyttsx3 verilmemis",
}
#: Yeni PDF katmaninin pakette bulunmasi beklenen izi.
EXPECTED = b"pypdfium"

#: Yalnizca kod/ikili tasiyan dosyalar taranir; ders materyali degil.
SUFFIXES = {".exe", ".dll", ".pyd", ".so", ".dylib", ".zip", ".toc", ".pkg", ""}


def _scan_bytes(blob: bytes) -> tuple:
    """Ham baytlarda izleri ara."""
    low = blob.lower()
    return {marker for marker in FORBIDDEN if marker in low}, EXPECTED in low


def scan(path: Path) -> tuple:
    """Bir dosyayi tara: (bulunan yasak izler, beklenen iz var mi).

    Zip arsivleri ACILARAK taranir: sikistirilmis bir dagitim zip'inde
    izler ham baytlarda gorunmez, oysa yayimlanan sey tam da o zip'tir.
    """
    if path.suffix.lower() == ".zip" and zipfile.is_zipfile(path):
        found, expected = _scan_bytes(path.read_bytes())
        try:
            with zipfile.ZipFile(path) as archive:
                names = "\n".join(archive.namelist()).encode("utf-8", "replace")
                hit, saw = _scan_bytes(names)
                found |= hit
                expected = expected or saw
                for info in archive.infolist():
                    if info.is_dir() or info.file_size > 400 * 1024 * 1024:
                        continue
                    if Path(info.filename).suffix.lower() not in SUFFIXES:
                        continue
                    hit, saw = _scan_bytes(archive.read(info))
                    found |= hit
                    expected = expected or saw
        except (OSError, zipfile.BadZipFile):
            pass
        return found, expected
    try:
        return _scan_bytes(path.read_bytes())
    except OSError:
        return set(), False


def targets(root: Path) -> list:
    """Taranacak dosyalari topla."""
    if root.is_file():
        return [root]
    return [p for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix.lower() in SUFFIXES]


def main(argv: list) -> int:
    """Verilen yolu (varsayilan `dist/`) tara ve sonucu yazdir."""
    root = Path(argv[1]) if len(argv) > 1 else ROOT / "dist"
    if not root.exists():
        print("Taranacak bir sey yok: %s" % root)
        return 2
    files = targets(root)
    if not files:
        print("Taranacak dosya bulunamadi: %s" % root)
        return 2

    problems = []
    saw_expected = False
    for path in files:
        found, expected = scan(path)
        saw_expected = saw_expected or expected
        for marker in sorted(found):
            problems.append("%s: %s" % (path, FORBIDDEN[marker]))

    for line in problems:
        print("LISANS HATASI:", line)
    if not saw_expected:
        print("LISANS UYARISI: %s altinda pypdfium izi yok - paket eski bir "
              "derlemeden kalmis olabilir." % root)
    if problems:
        print("\n%d dosya tarandi. Paketi YAYIMLAMAYIN: MIT olarak duyurulan "
              "ikili, copyleft bir bilesen tasiyor. dist/ ve build/ klasorlerini "
              "silip yeniden derleyin." % len(files))
        return 1
    print("%d dosya tarandi, lisans acisindan temiz%s."
          % (len(files), "" if saw_expected else " (pypdfium izi goremedim)"))
    return 0 if saw_expected else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
