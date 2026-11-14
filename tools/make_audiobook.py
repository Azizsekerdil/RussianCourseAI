# -*- coding: utf-8 -*-
"""Komut satirindan sesli kitap uretimi (uygulamadaki "Sesli Kitap" sayfasiyla ayni motor).

Ornekler:
    # PDF + hazir seslendirme betiginden kitap olustur, Piper ile tum sayfalari uret
    python tools/make_audiobook.py --pdf Kitap.pdf --script Sesli_Kitap/script --engine piper

    # Var olan kitabin 4-9. sayfalarini Edge sesleriyle uret ve bolum MP3'lerini disa aktar
    python tools/make_audiobook.py --book rusca-baslangic-egitim-kitabi --engine edge --pages 4-9 --export

    # Bolum MP3'lerini istenen klasore kopyala
    python tools/make_audiobook.py --book rusca-baslangic-egitim-kitabi --engine piper --export --out D:/Sesli
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rca import audiobook as A  # noqa: E402


def parse_pages(spec: str, n: int):
    if not spec or spec == "all":
        return list(range(1, n + 1))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += range(int(a), int(b) + 1)
        else:
            out.append(int(part))
    return [p for p in out if 1 <= p <= n]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", help="kaynak PDF (yeni kitap olusturmak icin)")
    ap.add_argument("--script", help="hazir seslendirme betigi klasoru (pNNN.json)")
    ap.add_argument("--title", default="", help="kitap basligi")
    ap.add_argument("--book", help="var olan kitabin kimligi (klasor adi)")
    ap.add_argument("--engine", choices=A.ENGINES, default="piper")
    ap.add_argument("--rate", type=float, default=1.0, help="konusma hizi (1.0 = normal)")
    ap.add_argument("--pages", default="all", help="or. 4-9,15,20-22 (varsayilan: hepsi)")
    ap.add_argument("--force", action="store_true", help="guncel sayfalari da yeniden uret")
    ap.add_argument("--export", action="store_true", help="bolum MP3'leri + M3U8 uret")
    ap.add_argument("--out", help="bolum MP3'lerinin yazilacagi klasor")
    ap.add_argument("--no-render", action="store_true", help="yalnizca disa aktar")
    ap.add_argument("--workers", type=int, default=0, help="paralel surec (Piper; 0 = otomatik)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    if a.pdf:
        book = A.create_book(a.pdf, a.title, a.script)
        print(f"Kitap: {book.title} ({book.id}) · {book.page_count} sayfa · betik: {book.script_source()}")
    elif a.book:
        book = A.Book(A.AUDIOBOOK_DIR / a.book)
    else:
        books = A.list_books()
        if not books:
            ap.error("--pdf ya da --book gerekli")
        book = books[0]

    engine = A.make_engine(a.engine, rate=a.rate)
    # Motor durumu yalnizca uretim icin gerekir; disa aktarma sadece PyAV kullanir.
    if not a.no_render:
        ok, why = engine.status()
        if not ok and isinstance(engine, A.PiperTTS) and A.PiperTTS.installed():
            # Tek sorun eksik ses modeliyse indir (havuz baslamadan, tek surecte)
            for v in engine.missing_voices():
                print(f"Ses indiriliyor: {v}")
                try:
                    A.PiperTTS.download_voice(v)
                except Exception as e:                      # noqa: BLE001
                    print(f"  indirilemedi: {type(e).__name__}: {e}")
                    break
            ok, why = engine.status()
        print(f"Motor: {why}")
        if not ok:
            return 2

    if not a.no_render:
        pages = parse_pages(a.pages, book.page_count)
        # Guncel sayfalar render_pages tarafindan once ve aninda bildirilir; tahmin
        # yalnizca gercekten uretilen sayfalardan ve uretimin basladigi andan hesaplanir.
        k0 = 0 if a.force else sum(A.page_is_current(book, engine, p) for p in pages)
        t1 = [time.time()]

        def prog(k, total, page, made):
            now = time.time()
            if k <= k0:
                t1[0] = now
                eta_txt = "?"
            else:
                el = now - t1[0]
                eta_txt = f"{el / (k - k0) * (total - k) / 60:.1f}"
            print(f"\r[{k}/{total}] sayfa {page} {'uretildi' if made else 'guncel'} · "
                  f"{(now - t0) / 60:.1f} dk · kalan ~{eta_txt} dk   ", end="", flush=True)
        t0 = time.time()
        res = A.render_pages(book, engine, pages, force=a.force, on_progress=prog,
                             workers=a.workers or A.default_workers(engine))
        print(f"\nUretilen: {res['rendered']} · atlanan: {res['skipped']} · hata: {len(res['failed'])}")
        for page, err in res["failed"]:
            print(f"  sayfa {page}: {err}")

    if a.export:
        out = A.export_sections(book, engine.name, Path(a.out) if a.out else None,
                                on_progress=lambda k, n, t: print(f"  [{k}/{n}] {t}"))
        print(f"Bolumler: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
