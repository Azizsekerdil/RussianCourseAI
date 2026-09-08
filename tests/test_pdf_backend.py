# -*- coding: utf-8 -*-
"""PDF arka ucu testleri: acma, cizim, kelime kutulari ve isaretli disa aktarma.

Hicbir test aga cikmaz ve ekran gerektirmez; PDF'ler ya gecici klasorde
pypdf ile uretilir ya da deponun kendi belgelerinden okunur.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rca import pdf_backend as B                              # noqa: E402

pypdf = pytest.importorskip("pypdf")
pytest.importorskip("pypdfium2")

#: Depodaki kendi tanitim belgemiz - gercek, cok dilli, gomulu yazi tipli bir PDF.
REPO_PDF = ROOT / "docs" / "presentation" / "Russian-Course-AI-Trilingual.pdf"

PAGE_W, PAGE_H = 400.0, 300.0


@pytest.fixture(scope="module")
def simple_pdf(tmp_path_factory) -> Path:
    """Bilinen olcude, iki sayfali bos bir PDF uret."""
    writer = pypdf.PdfWriter()
    for _ in range(2):
        writer.add_blank_page(width=PAGE_W, height=PAGE_H)
    out = tmp_path_factory.mktemp("pdf") / "bos.pdf"
    with open(out, "wb") as fh:
        writer.write(fh)
    return out


@pytest.fixture(scope="module")
def repo_pdf() -> Path:
    """Metin iceren gercek bir belge."""
    if not REPO_PDF.exists():
        pytest.skip("Tanitim PDF'i bulunamadi")
    return REPO_PDF


# --------------------------------------------------------------------------
# Acma / olcu
# --------------------------------------------------------------------------
def test_backend_is_available() -> None:
    """Kutuphaneler kuruluysa arka uc tam ozellikli bildirilir."""
    assert B.can_view() and B.can_export()
    assert B.available()
    assert B.missing() == []
    assert B.INSTALL_HINT == "pip install pypdfium2 pypdf"


def test_open_reports_page_count_and_size(simple_pdf: Path) -> None:
    """Sayfa sayisi ve sayfa olcusu dogru okunur."""
    doc = B.open_document(str(simple_pdf))
    try:
        assert doc.page_count == 2
        assert len(doc) == 2
        for i in range(2):
            w, h = doc.page_size(i)
            assert w == pytest.approx(PAGE_W, abs=0.51)
            assert h == pytest.approx(PAGE_H, abs=0.51)
    finally:
        doc.close()


def test_open_reports_repo_document(repo_pdf: Path) -> None:
    """Deponun kendi belgesi de dogru acilir."""
    doc = B.open_document(str(repo_pdf))
    try:
        reader = pypdf.PdfReader(str(repo_pdf))
        assert doc.page_count == len(reader.pages)
        w, h = doc.page_size(0)
        box = reader.pages[0].mediabox
        assert w == pytest.approx(float(box.width), abs=1.0)
        assert h == pytest.approx(float(box.height), abs=1.0)
    finally:
        doc.close()


def test_open_missing_file_raises(tmp_path: Path) -> None:
    """Olmayan dosya sessizce yutulmaz, hata yukselir."""
    with pytest.raises(Exception):
        B.open_document(str(tmp_path / "yok.pdf"))


# --------------------------------------------------------------------------
# Cizim
# --------------------------------------------------------------------------
def _ppm_header(data: bytes):
    """P6 PPM basligindaki genislik/yukseklik."""
    m = re.match(rb"P6\s+(\d+)\s+(\d+)\s+(\d+)\s", data)
    assert m, "P6 PPM basligi bekleniyordu"
    return int(m.group(1)), int(m.group(2))


def test_render_scales_with_zoom(repo_pdf: Path) -> None:
    """Iki farkli yakinlastirmada piksel olcusu zoom ile olceklenir."""
    doc = B.open_document(str(repo_pdf))
    try:
        w_pt, h_pt = doc.page_size(0)
        low = doc.render(0, 1.0)
        high = doc.render(0, 2.0)
    finally:
        doc.close()

    assert low.width == pytest.approx(w_pt, abs=1)
    assert low.height == pytest.approx(h_pt, abs=1)
    assert high.width == pytest.approx(low.width * 2, abs=2)
    assert high.height == pytest.approx(low.height * 2, abs=2)

    for page in (low, high):
        assert isinstance(page.data, (bytes, bytearray))
        pw, ph = _ppm_header(bytes(page.data))
        assert (pw, ph) == (page.width, page.height)
        assert len(page.data) >= pw * ph * 3
    assert len(high.data) > len(low.data)


#: Cizim verisinin gercekten tk.PhotoImage'e girdigini AYRI bir surecte dogrular.
#: Ayni surecte Tk penceresi acip kapatmak, sonraki arayuz duman testinin Tk
#: baslatmasini bozabiliyor; bu yuzden kontrol yalitilmis calistirilir.
_PHOTOIMAGE_PROBE = """
import sys, tkinter as tk
sys.path.insert(0, sys.argv[1])
from rca import pdf_backend as B

doc = B.open_document(sys.argv[2])
page = doc.render(0, 0.5)
doc.close()
root = tk.Tk()
root.withdraw()
img = tk.PhotoImage(data=page.data)
print(img.width(), img.height(), page.width, page.height)
"""


def test_render_is_photoimage_compatible(repo_pdf: Path, tmp_path: Path) -> None:
    """Cizim verisi dogrudan tk.PhotoImage icine verilebilir."""
    import subprocess

    pytest.importorskip("tkinter")
    probe = tmp_path / "probe.py"
    probe.write_text(_PHOTOIMAGE_PROBE, encoding="utf-8")
    done = subprocess.run([sys.executable, str(probe), str(ROOT), str(repo_pdf)],
                          capture_output=True, text=True, timeout=120)
    if done.returncode != 0:
        if "TclError" in done.stderr or "no display" in done.stderr:
            pytest.skip("Ekran yok")
        pytest.fail(done.stderr[-2000:])
    got_w, got_h, want_w, want_h = done.stdout.split()
    assert (got_w, got_h) == (want_w, want_h)
    assert int(got_w) > 0 and int(got_h) > 0


# --------------------------------------------------------------------------
# Kelime listesi
# --------------------------------------------------------------------------
def test_words_shape_and_coordinates(repo_pdf: Path) -> None:
    """Kelime listesi dolu, sekiz ogeli ve sayfa kutusu icindedir."""
    doc = B.open_document(str(repo_pdf))
    try:
        words = doc.words(0)
        w_pt, h_pt = doc.page_size(0)
    finally:
        doc.close()

    assert words, "ilk sayfada kelime bulunamadi"
    for x0, y0, x1, y1, text, block, line, word_no in words:
        assert isinstance(text, str) and text.strip()
        assert not text[0].isspace() and not text[-1].isspace()
        assert all(isinstance(v, float) for v in (x0, y0, x1, y1))
        assert all(isinstance(v, int) for v in (block, line, word_no))
        assert x0 <= x1 and y0 <= y1
        assert -1.0 <= x0 and x1 <= w_pt + 1.0
        assert -1.0 <= y0 and y1 <= h_pt + 1.0


def test_words_use_top_left_origin(repo_pdf: Path) -> None:
    """Koordinatlar SOL UST kokenlidir: ilk satir sayfanin ust yarisindadir.

    pdfium'un kendi kutulari SOL ALT kokenlidir; bu test cevrimin
    yapildigini dogrular.
    """
    doc = B.open_document(str(repo_pdf))
    try:
        words = doc.words(0)
        _, h_pt = doc.page_size(0)
        text = doc.page_text(0)
    finally:
        doc.close()

    first = words[0]
    assert first[4] and text.startswith(first[4])
    assert first[1] < h_pt * 0.5, "ilk kelime sayfanin ust yarisinda olmali"
    # Metin sirasi asagi dogru ilerler: son kelime ilk kelimeden asagidadir.
    assert words[-1][1] > first[1]


def test_words_of_blank_page_is_empty(simple_pdf: Path) -> None:
    """Bos sayfa bos kelime listesi verir (cokmez)."""
    doc = B.open_document(str(simple_pdf))
    try:
        assert doc.words(0) == []
    finally:
        doc.close()


def test_geometry_round_trip(repo_pdf: Path) -> None:
    """Gorunen <-> PDF nokta cevrimi kendi tersini verir."""
    doc = B.open_document(str(repo_pdf))
    try:
        geom = doc.geometry(0)
    finally:
        doc.close()
    for vx, vy in ((0.0, 0.0), (10.0, 20.0), (geom.width, geom.height)):
        px, py = geom.to_pdf(vx, vy)
        back = geom.to_view(px, py)
        assert back[0] == pytest.approx(vx, abs=1e-6)
        assert back[1] == pytest.approx(vy, abs=1e-6)


# --------------------------------------------------------------------------
# Isaretli disa aktarma
# --------------------------------------------------------------------------
def _notes():
    """Dort turden birer isaretleme (arayuzun kaydettigi bicimde)."""
    return [
        {"page": 0, "kind": "mark",
         "payload": json.dumps({"rect": [40, 50, 200, 80], "color": "#ffe066"})},
        {"page": 0, "kind": "pen",
         "payload": json.dumps({"points": [30, 120, 90, 150, 150, 130],
                                "color": "#d93333"})},
        {"page": 0, "kind": "text",
         "payload": json.dumps({"x": 40, "y": 190, "text": "Not"})},
        {"page": 1, "kind": "note", "payload": "Sayfa notu"},
    ]


def test_export_writes_reopenable_pdf_with_annotations(simple_pdf: Path,
                                                       tmp_path: Path) -> None:
    """Yazilan dosya pypdf ile geri acilir ve beklenen sayida isaret tasir."""
    out = tmp_path / "notlu.pdf"
    written = B.export_annotated(str(simple_pdf), str(out), _notes())
    assert written == 4
    assert out.exists() and out.stat().st_size > 0

    reader = pypdf.PdfReader(str(out))
    assert len(reader.pages) == 2
    first = list(reader.pages[0].get("/Annots", []))
    second = list(reader.pages[1].get("/Annots", []))
    assert len(first) == 3
    assert len(second) == 1
    subtypes = [a.get_object()["/Subtype"] for a in first]
    assert subtypes == ["/Square", "/Line", "/FreeText"]
    assert second[0].get_object()["/Subtype"] == "/FreeText"


def test_export_converts_to_bottom_left_space(simple_pdf: Path,
                                              tmp_path: Path) -> None:
    """Sol-ust koordinatlar PDF'in sol-alt uzayina dogru cevrilir."""
    out = tmp_path / "kutu.pdf"
    notes = [{"page": 0, "kind": "mark",
              "payload": json.dumps({"rect": [40, 50, 200, 80]})}]
    assert B.export_annotated(str(simple_pdf), str(out), notes) == 1

    rect = pypdf.PdfReader(str(out)).pages[0]["/Annots"][0].get_object()["/Rect"]
    x0, y0, x1, y1 = [float(v) for v in rect]
    assert (x0, x1) == pytest.approx((40.0, 200.0), abs=0.51)
    # Ust kenar 50 -> PDF'de PAGE_H - 50, alt kenar 80 -> PAGE_H - 80.
    assert (y0, y1) == pytest.approx((PAGE_H - 80.0, PAGE_H - 50.0), abs=0.51)


def test_export_annotations_have_appearance_streams(simple_pdf: Path,
                                                    tmp_path: Path) -> None:
    """Her isaretin kendi gorunum akisi vardir - her goruntuleyicide gorunur."""
    out = tmp_path / "gorunum.pdf"
    B.export_annotated(str(simple_pdf), str(out), _notes())
    reader = pypdf.PdfReader(str(out))
    for page in reader.pages:
        for ref in page.get("/Annots", []):
            obj = ref.get_object()
            appearance = obj.get("/AP")
            assert appearance is not None, obj["/Subtype"]
            normal = appearance["/N"].get_object()
            assert normal["/Subtype"] == "/Form"
            assert normal.get_data()


def test_exported_marks_are_actually_drawn(simple_pdf: Path, tmp_path: Path) -> None:
    """Isaretler cizildikleri yerde gercekten piksele donusur."""
    pdfium = pytest.importorskip("pypdfium2")
    out = tmp_path / "cizili.pdf"
    notes = [{"page": 0, "kind": "mark",
              "payload": json.dumps({"rect": [40, 50, 200, 80],
                                     "color": "#ffe066"})}]
    B.export_annotated(str(simple_pdf), str(out), notes)

    doc = pdfium.PdfDocument(str(out))
    try:
        image = doc[0].render(scale=1.0, draw_annots=True).to_pil().convert("RGB")
        inside = image.getpixel((120, 65))
        outside = image.getpixel((320, 250))
    finally:
        doc.close()
    assert outside == (255, 255, 255), "isaretin disi bos sayfa olmali"
    assert inside != (255, 255, 255), "isaretin ici boyanmis olmali"
    assert inside[0] > inside[2], "isaret sari tonunda olmali"


def test_export_skips_broken_and_out_of_range_notes(simple_pdf: Path,
                                                    tmp_path: Path) -> None:
    """Bozuk JSON ve var olmayan sayfa sessizce atlanir."""
    out = tmp_path / "bozuk.pdf"
    notes = [
        {"page": 0, "kind": "mark", "payload": "{bozuk"},
        {"page": 99, "kind": "note", "payload": "olmayan sayfa"},
        {"page": 0, "kind": "bilinmeyen", "payload": "{}"},
        {"page": 0, "kind": "note", "payload": "   "},
        {"page": 0, "kind": "note", "payload": "gecerli"},
    ]
    assert B.export_annotated(str(simple_pdf), str(out), notes) == 1
    reader = pypdf.PdfReader(str(out))
    assert len(list(reader.pages[0].get("/Annots", []))) == 1


def test_export_keeps_unicode_note_text(simple_pdf: Path, tmp_path: Path) -> None:
    """Kiril / Turkce not metni annotation icinde kaybolmaz."""
    out = tmp_path / "unicode.pdf"
    text = "Привет — Rusça açıklama"
    notes = [{"page": 0, "kind": "text",
              "payload": json.dumps({"x": 20, "y": 40, "text": text})}]
    assert B.export_annotated(str(simple_pdf), str(out), notes) == 1
    obj = pypdf.PdfReader(str(out)).pages[0]["/Annots"][0].get_object()
    assert text in str(obj["/Contents"])


# --------------------------------------------------------------------------
# Regresyon: AGPL bagimliligi geri gelmesin
# --------------------------------------------------------------------------
_FORBIDDEN = re.compile(r"pymupdf|\bfitz\b", re.IGNORECASE)


def test_package_never_mentions_pymupdf() -> None:
    """`rca` paketi ve giris dosyasi PyMuPDF/fitz'e hicbir sekilde deginmez."""
    sources = list((ROOT / "rca").rglob("*.py"))
    sources += [ROOT / "rca_common.py", ROOT / "Russian_Course_AI.pyw"]
    hits = []
    for path in sources:
        if "__pycache__" in path.parts or not path.exists():
            continue
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _FORBIDDEN.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{no}: {line.strip()}")
    assert not hits, "AGPL lisansli PyMuPDF geri gelmis:\n" + "\n".join(hits)


def test_requirements_pin_the_permissive_pdf_stack() -> None:
    """requirements.txt PyMuPDF yerine pypdfium2 + pypdf sabitler."""
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert not _FORBIDDEN.search(text), "requirements.txt hala PyMuPDF istiyor"
    assert re.search(r"^pypdfium2==\d", text, re.MULTILINE)
    assert re.search(r"^pypdf==\d", text, re.MULTILINE)


def test_repository_has_mit_license_and_notices() -> None:
    """MIT lisans dosyasi ve ucuncu taraf bildirimleri yerinde."""
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.splitlines()[0].strip() == "MIT License"
    assert "Copyright (c) 2026 Azizsekerdil" in license_text
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for name in ("pypdfium2", "pypdf", "Pillow", "PyInstaller"):
        assert name in notices, name
