# -*- coding: utf-8 -*-
"""Kullanim kilavuzlarini tek uretim hattiyla yenile: .md -> .html -> .pdf.

Depoda dagitilan `docs/KULLANIM_KILAVUZU.pdf` ve `docs/USER_GUIDE.pdf`
dosyalarini uretir. Kaynak her zaman `.md`'dir; ara `.html` yalnizca yazdirma
adimi icindir ve `.gitignore` tarafindan izlenmez.

    python tools/build_manuals.py            # ikisini de yenile
    python tools/build_manuals.py --html     # yalnizca HTML uret (PDF atlanir)
    python tools/build_manuals.py --check    # uretmeden, mevcut PDF'leri denetle

PDF adimi headless Chrome/Edge ile yapilir (`--print-to-pdf`); depodaki
PDF'ler de boyle uretilmistir (`/Producer: Skia/PDF`). Chrome bulunamazsa
betik neyi bulamadigini soyler ve hata koduyla ciker - eski PDF'i sessizce
yerinde birakmaz.

Bu betigin varlik sebebi bir regresyondur: kilavuz metni degistiginde
`.md` ve `.html` yenilenip PDF'ler eski surumde kalmisti, yani kullanicinin
okudugu belge kaldirilmis bir bagimliligi anlatiyordu. `--check` ayni
denetimi `tests/test_pdf_backend.py` icinden de yapilabilir kilar.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

#: (markdown, html, pdf, <html lang>, <title>)
MANUALS = [
    ("KULLANIM_KILAVUZU.md", "KULLANIM_KILAVUZU.html", "KULLANIM_KILAVUZU.pdf",
     "tr", "Russian Course AI \u2014 Kullan\u0131m K\u0131lavuzu"),
    ("USER_GUIDE.md", "USER_GUIDE.html", "USER_GUIDE.pdf",
     "en", "Russian Course AI \u2014 User Guide"),
]

#: Markdown uzantilari: `extra` tablolari, `toc` baslik kimliklerini verir.
EXTENSIONS = ["extra", "toc", "sane_lists"]

#: A4 yazdirma bicimi (docs/*.html basligindaki uslup blogunun kaynagi).
CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", "Calibri", system-ui, sans-serif; font-size: 10.5pt; line-height: 1.55; color: #14171d; margin: 0; }
h1 { font-size: 24pt; margin: 0 0 4pt; color: #3D8DFF; border-bottom: 3px solid #3D8DFF; padding-bottom: 8pt; }
h2 { font-size: 15pt; margin: 22pt 0 6pt; color: #3D8DFF; border-bottom: 1px solid #d7dbe2; padding-bottom: 3pt; page-break-after: avoid; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; color: #1d2430; page-break-after: avoid; }
h4 { font-size: 10.5pt; margin: 10pt 0 3pt; color: #38404f; page-break-after: avoid; }
p, li { orphans: 2; widows: 2; }
ul, ol { padding-left: 20pt; margin: 5pt 0; }
li { margin: 2pt 0; }
code { font-family: "Cascadia Mono", Consolas, monospace; font-size: 9pt; background: #eef1f6; padding: 1pt 3pt; border-radius: 3px; }
pre { background: #f4f6fa; border: 1px solid #dde2ea; border-left: 3px solid #3D8DFF; border-radius: 4px; padding: 8pt 10pt;
      overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.8pt; line-height: 1.4; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9.4pt; page-break-inside: avoid; }
th { background: #3D8DFF; color: #fff; text-align: left; padding: 5pt 7pt; font-weight: 600; }
td { border-bottom: 1px solid #dfe4ec; padding: 5pt 7pt; vertical-align: top; }
tr:nth-child(even) td { background: #f7f9fc; }
blockquote { margin: 8pt 0; padding: 6pt 12pt; background: #f4f6fa; border-left: 3px solid #3D8DFF; color: #38404f; }
a { color: #3D8DFF; text-decoration: none; }
hr { border: none; border-top: 1px solid #dfe4ec; margin: 14pt 0; }
.subtitle { color: #5b6474; font-size: 10pt; margin: 0 0 14pt; }
"""

#: Kaldirilan AGPL lisansli PDF katmaninin adi. Surum notlarinda "kaldirildi"
#: diye gecmesi normaldir; kurulum ONERISI olarak gecmesi degildir.
OLD_STACK = re.compile(r"pymupdf", re.IGNORECASE)
#: Hicbir kullanici kilavuzunda gecmemesi gereken kaliplar.
FORBIDDEN = (
    re.compile(r"pip install[^\n]*pymupdf", re.IGNORECASE),
    re.compile(r"\bfitz\b", re.IGNORECASE),
)
#: Guncel bir kilavuzda mutlaka gecen izler: yeni katman ve lisans bolumu.
REQUIRED = ("pypdfium2", "pypdf", "MIT")

#: Chrome/Edge'in PATH'te aranacak adlari.
_BROWSER_NAMES = ("chrome", "google-chrome", "google-chrome-stable", "chromium",
                  "chromium-browser", "msedge", "microsoft-edge")
#: PATH'te yoksa bakilacak bilinen kurulum yollari.
_BROWSER_PATHS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
)


def find_browser() -> str:
    """Yazdirma icin kullanilabilecek ilk Chrome/Edge yolunu ver (yoksa "")."""
    for name in _BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    for path in _BROWSER_PATHS:
        if Path(path).exists():
            return path
    return ""


def render_html(md_path: Path, lang: str, title: str) -> str:
    """Markdown'i yazdirmaya hazir tek parca HTML'e cevir."""
    import markdown                            # pip install markdown

    body = markdown.markdown(md_path.read_text(encoding="utf-8"),
                             extensions=EXTENSIONS)
    head = ('<!doctype html><html lang="%s"><head><meta charset="utf-8">'
            "<title>%s</title>\n<style>%s</style></head><body>" % (lang, title, CSS))
    return head + body + "\n</body></html>\n"


def print_pdf(html_path: Path, pdf_path: Path, browser: str) -> None:
    """HTML'i headless Chrome/Edge ile PDF'e yazdir."""
    if pdf_path.exists():
        pdf_path.unlink()                      # eskisi kalmasin: sessiz basari olmaz
    with tempfile.TemporaryDirectory() as profile:
        cmd = [browser, "--headless", "--disable-gpu", "--no-sandbox",
               "--user-data-dir=" + profile, "--no-pdf-header-footer",
               "--run-all-compositor-stages-before-draw",
               "--virtual-time-budget=20000",
               "--print-to-pdf=" + str(pdf_path), html_path.as_uri()]
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        sys.exit("HATA: %s uretilemedi.\n%s" % (pdf_path.name, (done.stderr or "")[-2000:]))


def pdf_text(pdf_path: Path) -> str:
    """PDF'in duz metni (pypdf ile), NFKC ile normallestirilmis.

    Normallestirme sart: Chrome basliklari dizerken tipografik bag kullanir,
    "Telaffuz" PDF'e tek kod noktasi olan "Telaﬀuz" (U+FB00), "Artificial" ise
    "Artiﬁcial" (U+FB01) olarak girer. Sayfada dogru gorunur ama cikarilan
    metin kaynaktaki iki harfle duz karsilastirmada eslesmez ve check_pdf
    guncel bir PDF'i "eski" diye isaretler. NFKC baglari bilesenlerine geri
    acar, boylece denetim dizgiyi degil metni olcer.
    """
    import pypdf

    reader = pypdf.PdfReader(str(pdf_path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return unicodedata.normalize("NFKC", text)


def check_pdf(pdf_path: Path, md_path: Path = None) -> list:
    """Dagitilan PDF gercekten `.md`'nin bugunku halinden mi uretilmis?

    Uc soru sorulur ve bulunan sorunlar liste olarak dondurulur:

    1. `.md` icindeki her baslik PDF'te var mi? (Eksik baslik = eski PDF.
       Bu denetim, "12. Lisans" bolumu eklendigi halde PDF'lerin
       yenilenmedigi gercek regresyonu yakalar.)
    2. Guncel PDF katmaninin adlari ve lisans ibaresi geciyor mu?
    3. Kaldirilan katmani KURULUM olarak oneren bir satir kalmis mi? Surum
       notlarindaki "PyMuPDF kaldirildi" cumlesi mesru oldugu icin sayi
       kaynak `.md` ile karsilastirilir: PDF kaynaktan fazla soz ediyorsa
       eski metinden kalmistir.
    """
    if not pdf_path.exists():
        return ["%s: dosya yok" % pdf_path.name]
    try:
        text = pdf_text(pdf_path)
    except ImportError:
        return ["%s: pypdf kurulu degil, denetlenemedi" % pdf_path.name]

    problems = []
    # Baslik denetimi bosluklardan tumuyle bagimsiz yapilir. Neden: baslik
    # `#### Speaking (`Konusma Pratigi`)` gibi bir kod parcasi tasidiginda PDF
    # icinde yazi tipi Segoe UI'dan Consolas'a gecer ve metin cikarici bu
    # sinira kendiliginden bosluk koyar ("Speaking ( Konusma Pratigi )").
    # Sayfada gorunen baslik degismez; ama bosluga duyarli karsilastirma
    # yeni uretilmis bir PDF'i "eski" diye isaretlerdi. Bosluklari tumden
    # atmak, bir basligin GERCEKTEN eksik oldugu durumu yakalamayi surdurur.
    squeezed = re.sub(r"\s+", "", text)
    lower = text.lower()

    if md_path is not None and md_path.exists():
        source = unicodedata.normalize("NFKC", md_path.read_text(encoding="utf-8"))
        for head in re.findall(r"^##+ (.+)$", source, re.MULTILINE):
            shown = re.sub(r"\s+", " ", head.replace("`", "")).strip()
            if re.sub(r"\s+", "", shown) not in squeezed:
                problems.append("%s: %r basligi PDF'te yok - PDF %s'den eski"
                                % (pdf_path.name, shown, md_path.name))
        md_hits = len(OLD_STACK.findall(source))
        pdf_hits = len(OLD_STACK.findall(text))
        if pdf_hits > md_hits:
            problems.append("%s: kaldirilan PDF katmanindan kaynaktan cok soz "
                            "ediyor (%d > %d) - eski metinden kalmis"
                            % (pdf_path.name, pdf_hits, md_hits))

    for pattern in FORBIDDEN:
        hit = pattern.search(text)
        if hit:
            problems.append("%s: kaldirilan PDF katmanini oneriyor (%r)"
                            % (pdf_path.name, hit.group(0)))
    for needle in REQUIRED:
        if needle.lower() not in lower:
            problems.append("%s: %r gecmiyor - kilavuz eski surumden kalmis olabilir"
                            % (pdf_path.name, needle))
    return problems


def main() -> int:
    """Kilavuzlari uret (ya da yalnizca denetle)."""
    ap = argparse.ArgumentParser(description="docs/*.md -> docs/*.html -> docs/*.pdf")
    ap.add_argument("--html", action="store_true", help="yalnizca HTML uret")
    ap.add_argument("--check", action="store_true",
                    help="uretme, mevcut PDF'leri denetle")
    args = ap.parse_args()

    # Windows konsolu cp1252 ile acilir ve Turkce uyari metinleri ('g', 'i',
    # 'c' ...) yazilirken UnicodeEncodeError ile cokerdi: PDF'ler uretilmis
    # olmasina ragmen betik hata koduyla biterdi. Cikti akislari UTF-8'e
    # alinir; desteklenmiyorsa eski davranis korunur.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    problems = []
    if args.check:
        for md, _html, pdf, _lang, _title in MANUALS:
            problems += check_pdf(DOCS / pdf, DOCS / md)
    else:
        browser = "" if args.html else find_browser()
        if not args.html and not browser:
            print("HATA: PDF yazdirmak icin Chrome/Edge bulunamadi.\n"
                  "      --html ile yalnizca ara HTML uretebilirsiniz.", file=sys.stderr)
            return 2
        for md, html, pdf, lang, title in MANUALS:
            html_path, pdf_path = DOCS / html, DOCS / pdf
            html_path.write_text(render_html(DOCS / md, lang, title), encoding="utf-8")
            print("HTML  %s" % html_path.relative_to(ROOT))
            if args.html:
                continue
            print_pdf(html_path, pdf_path, browser)
            print("PDF   %s  (%s bayt)"
                  % (pdf_path.relative_to(ROOT), format(pdf_path.stat().st_size, ",")))
            problems += check_pdf(pdf_path, DOCS / md)

    for line in problems:
        print("UYARI:", line)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
