# -*- coding: utf-8 -*-
"""Kaynak Merkezi: acik lisansli Rusca ogrenme kaynaklari katalogu ve indirici.

KURAL: Bu katalogda YALNIZCA lisansi acikca dogrulanmis kaynaklar bulunur -
kamu mali (public domain) veya Creative Commons. Lisansi belirsiz hicbir sey
buraya girmez ve program telifli materyal indirmez.

Her kayit indirildiginde yaninda bir `LISANS.txt` yazilir; atif zorunlulugu
olan kaynaklarin atif metni oraya kaydedilir.
"""
from __future__ import annotations

import ssl
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

import rca_common as C

USER_AGENT = f"{C.APP_SLUG}/{C.VERSION} (offline language learning app)"
CHUNK = 128 * 1024

_SSL_CTX = None
_SSL_SOURCE = "varsayilan"


def ssl_context():
    """Dogrulanabilir bir TLS baglami dondur.

    Bazi kurulumlarda Python'un gomulu kok sertifika deposu eskimis olur ve
    gecerli siteler bile 'certificate has expired' hatasi verir. Bu durumda
    once Windows sertifika deposu (truststore), sonra certifi denenir.
    Sertifika DOGRULAMASI HICBIR KOSULDA kapatilmaz.
    """
    global _SSL_CTX, _SSL_SOURCE
    if _SSL_CTX is not None:
        return _SSL_CTX
    try:
        import truststore                     # type: ignore
        _SSL_CTX = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        _SSL_SOURCE = "isletim sistemi deposu"
        return _SSL_CTX
    except Exception:
        pass
    try:
        import certifi                        # type: ignore
        _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
        _SSL_SOURCE = "certifi"
        return _SSL_CTX
    except Exception:
        pass
    _SSL_CTX = ssl.create_default_context()
    _SSL_SOURCE = "varsayilan"
    return _SSL_CTX


def ssl_source() -> str:
    """Hangi sertifika deposunun kullanildigini bildir (ayar ekraninda gosterilir)."""
    ssl_context()
    return _SSL_SOURCE

# --------------------------------------------------------------------------
# Lisans tanimlari
# --------------------------------------------------------------------------
LICENSES: Dict[str, Dict[str, str]] = {
    "PD-USGOV": {
        "short": "Kamu mali (ABD devlet eseri)",
        "url": "https://www.usa.gov/government-works",
        "note": "ABD Disisleri Bakanligi (FSI) tarafindan uretilmistir; ABD "
                "telif yasasina gore kamu malidir. Serbestce kullanilir, "
                "cogaltilir ve dagitilir.",
        "attribution": "",
    },
    "PD-MARK": {
        "short": "Kamu mali (Public Domain Mark 1.0)",
        "url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "note": "Bilinen telif kisitlamasi yoktur.",
        "attribution": "",
    },
    "CC-BY-SA-4.0": {
        "short": "CC BY-SA 4.0",
        "url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "note": "Atif zorunlu; turetilmis eser ayni lisansla paylasilmalidir.",
        "attribution": "",
    },
    "CC-BY-2.0-FR": {
        "short": "CC BY 2.0 FR",
        "url": "https://creativecommons.org/licenses/by/2.0/fr/",
        "note": "Atif zorunlu. Bazi cumleler CC0'dir.",
        "attribution": "",
    },
    "CC-VARIES": {
        "short": "CC (kaynaga gore degisir)",
        "url": "",
        "note": "Sitedeki her materyalin lisansi ayri belirtilmistir; "
                "kullanmadan once ilgili sayfayi okuyun.",
        "attribution": "",
    },
}

KIND_LABELS = {
    "ebook": "E-kitap / PDF",
    "audio": "Ses dersi",
    "data": "Sozluk / veri",
    "link": "Web kaynagi",
    "video": "Video ders",
}


@dataclass
class Resource:
    """Katalogdaki tek bir kaynak."""
    rid: str
    title: str
    kind: str                 # ebook | audio | data | link | video
    provider: str
    license: str              # LICENSES anahtari
    url: str
    note: str = ""
    filename: str = ""
    size_mb: float = 0.0
    level: str = ""
    subdir: str = ""
    attribution: str = ""
    tags: List[str] = field(default_factory=list)

    @property
    def downloadable(self) -> bool:
        """Dosya olarak indirilebilir mi? (link/video kayitlari yalnizca acilir)"""
        return self.kind in ("ebook", "audio", "data") and bool(self.filename)

    def target(self, root: Path) -> Path:
        """Indirilecek tam dosya yolu."""
        return root / (self.subdir or KIND_LABELS.get(self.kind, "Diger")) / self.filename

    def license_info(self) -> Dict[str, str]:
        """Lisans tanimi."""
        return LICENSES.get(self.license, {"short": self.license, "url": "", "note": ""})


# --------------------------------------------------------------------------
# KATALOG - hepsi lisansi dogrulanmis
# --------------------------------------------------------------------------
_IA = "https://archive.org/download"
_OR = "https://raw.githubusercontent.com/Badestrand/russian-dictionary/master"

CATALOG: List[Resource] = [
    # ---------------- E-kitap / ders kitabi (kamu mali) ----------------
    Resource("fsi-fast-1", "FSI Russian FAST - Ders 1-5 (ogrenci kitabi)", "ebook",
             "US Foreign Service Institute", "PD-USGOV",
             f"{_IA}/Fsi-RussianFastCourse-StudentText/FsiRussianFast-Lessons1-5.pdf",
             "Diyalog, kelime listesi ve alistirmalarla klasik FSI yogun kursu. "
             "Tarama PDF (metin katmanli surumu ayrica var).",
             "FSI_RussianFAST_Ders_1-5.pdf", 2.3, "A1-A2", "E-Kitaplar",
             tags=["kurs", "alistirma", "diyalog"]),
    Resource("fsi-fast-2", "FSI Russian FAST - Ders 6-8 (ogrenci kitabi)", "ebook",
             "US Foreign Service Institute", "PD-USGOV",
             f"{_IA}/Fsi-RussianFastCourse-StudentText/FsiRussianFast-Lessons6-8.pdf",
             "Kursun ikinci bolumu.", "FSI_RussianFAST_Ders_6-8.pdf", 1.5,
             "A2", "E-Kitaplar", tags=["kurs", "alistirma"]),
    Resource("fsi-fast-3", "FSI Russian FAST - Ders 9-11 (ogrenci kitabi)", "ebook",
             "US Foreign Service Institute", "PD-USGOV",
             f"{_IA}/Fsi-RussianFastCourse-StudentText/FsiRussianFast-Lessons9-11.pdf",
             "Kursun ucuncu bolumu.", "FSI_RussianFAST_Ders_9-11.pdf", 2.1,
             "A2-B1", "E-Kitaplar", tags=["kurs", "alistirma"]),
    Resource("fsi-fast-1t", "FSI Russian FAST - Ders 1-5 (aranabilir metin)", "ebook",
             "US Foreign Service Institute", "PD-USGOV",
             f"{_IA}/Fsi-RussianFastCourse-StudentText/FsiRussianFast-Lessons1-5_text.pdf",
             "Ayni kitabin OCR metin katmanli surumu - program icinde metin secip "
             "AI'a sormak icin bunu tercih edin.",
             "FSI_RussianFAST_Ders_1-5_metin.pdf", 5.3, "A1-A2", "E-Kitaplar",
             tags=["kurs", "ocr", "aranabilir"]),
    Resource("fsi-fast-2t", "FSI Russian FAST - Ders 6-8 (aranabilir metin)", "ebook",
             "US Foreign Service Institute", "PD-USGOV",
             f"{_IA}/Fsi-RussianFastCourse-StudentText/FsiRussianFast-Lessons6-8_text.pdf",
             "OCR metin katmanli surum.", "FSI_RussianFAST_Ders_6-8_metin.pdf", 4.0,
             "A2", "E-Kitaplar", tags=["kurs", "ocr"]),
    Resource("fsi-fast-3t", "FSI Russian FAST - Ders 9-11 (aranabilir metin)", "ebook",
             "US Foreign Service Institute", "PD-USGOV",
             f"{_IA}/Fsi-RussianFastCourse-StudentText/FsiRussianFast-Lessons9-11_text.pdf",
             "OCR metin katmanli surum.", "FSI_RussianFAST_Ders_9-11_metin.pdf", 5.2,
             "A2-B1", "E-Kitaplar", tags=["kurs", "ocr"]),

    # ---------------- Ses dersleri (kamu mali) ----------------
    Resource("fsi-audio-s", "FSI Russian FAST - Ek ses (Supplement)", "audio",
             "US Foreign Service Institute", "PD-MARK",
             f"{_IA}/FSIRussianFAST/FSI%20Russian%20FAST%20-%20Supplement.mp3",
             "Kitaba eslik eden ek ses kaydi.", "FSI_FAST_Ek.mp3", 5.8,
             "A1", "Ses", tags=["dinleme"]),
] + [
    Resource(f"fsi-audio-{i}", f"FSI Russian FAST - Kaset {i} (ses)", "audio",
             "US Foreign Service Institute", "PD-MARK",
             f"{_IA}/FSIRussianFAST/FSI%20Russian%20FAST%20-%20Tape%20{i}.mp3",
             "Kitaptaki diyaloglarin ana dili konusan kayitlari.",
             f"FSI_FAST_Kaset_{i}.mp3", size, "A1-B1", "Ses", tags=["dinleme"])
    for i, size in ((1, 16.6), (2, 14.5), (3, 14.5), (4, 16.6),
                    (5, 19.0), (6, 17.7), (7, 18.8), (8, 2.1))
] + [
    # ---------------- Sozluk / veri (CC) ----------------
    Resource("or-nouns", "OpenRussian - isimler (cekim tablolariyla)", "data",
             "OpenRussian.org", "CC-BY-SA-4.0", f"{_OR}/nouns.csv",
             "~30.000 isim: vurgu isaretli bicimler, cinsiyet ve 6 halin tekil/cogul "
             "cekimleri. Sikliga gore siralidir - program bunlari kelime bankasina "
             "aktarabilir.", "openrussian_isimler.tsv", 8.0, "A1-C1", "Sozluk",
             attribution="OpenRussian.org, CC BY-SA 4.0. Ornek cumleler Tatoeba projesinden.",
             tags=["sozluk", "cekim", "iceaktarilabilir"]),
    Resource("or-verbs", "OpenRussian - fiiller (cekim + gorunus cifti)", "data",
             "OpenRussian.org", "CC-BY-SA-4.0", f"{_OR}/verbs.csv",
             "Fiiller: gorunus (вид), gorunus cifti, emir kipi, gecmis ve "
             "simdiki/gelecek cekimleri.", "openrussian_fiiller.tsv", 5.4,
             "A1-C1", "Sozluk",
             attribution="OpenRussian.org, CC BY-SA 4.0.",
             tags=["sozluk", "fiil", "iceaktarilabilir"]),
    Resource("or-adj", "OpenRussian - sifatlar", "data",
             "OpenRussian.org", "CC-BY-SA-4.0", f"{_OR}/adjectives.csv",
             "Sifatlar ve kisa bicimleri, karsilastirma dereceleri.",
             "openrussian_sifatlar.tsv", 8.0, "A1-C1", "Sozluk",
             attribution="OpenRussian.org, CC BY-SA 4.0.",
             tags=["sozluk", "sifat", "iceaktarilabilir"]),
    Resource("or-other", "OpenRussian - diger sozcuk turleri", "data",
             "OpenRussian.org", "CC-BY-SA-4.0", f"{_OR}/others.csv",
             "Zarf, edat, baglac, unlem ve zamirler.",
             "openrussian_digerleri.tsv", 0.3, "A1-C1", "Sozluk",
             attribution="OpenRussian.org, CC BY-SA 4.0.",
             tags=["sozluk", "iceaktarilabilir"]),
    Resource("tatoeba-rus", "Tatoeba - Rusca cumle derlemi", "data",
             "Tatoeba", "CC-BY-2.0-FR",
             "https://downloads.tatoeba.org/exports/per_language/rus/rus_sentences.tsv.bz2",
             "Yuz binlerce ana dili konusan kullanici cumlesi (bz2 sikistirilmis). "
             "Ornek cumle havuzu olarak kullanilir.",
             "tatoeba_rusca_cumleler.tsv.bz2", 14.7, "A1-C1", "Sozluk",
             attribution="Tatoeba.org katkicilar, CC BY 2.0 FR.",
             tags=["cumle", "derlem"]),

    # ---------------- Web kaynaklari (indirilmez, tarayicida acilir) -----
    Resource("mezhdu-nami", "Между нами - acik ders kitabi (web)", "link",
             "Michigan State University", "CC-VARIES",
             "https://openbooks.lib.msu.edu/mezhdunami/",
             "Baslangic seviyesi tam kurs: web kitabi + indirilebilir alistirma ve "
             "odev PDF'leri. Universite tarafindan acik erisimle yayimlanir.",
             level="A1-A2", tags=["kurs", "alistirma"]),
    Resource("llc-commons", "LLC Commons - Rusca acik ders materyalleri", "link",
             "LLC Commons", "CC-VARIES",
             "https://fltmag.com/russian-oers/",
             "Ogretmenlerin serbestce kullanabilecegi CC lisansli ders planlari ve "
             "alistirmalar deposu.", level="A1-C1", tags=["alistirma", "ogretmen"]),
    Resource("sputnik", "Sputnik - giris duzeyi Rusca kursu (web)", "link",
             "sputniktextbook.org", "CC-VARIES", "https://sputniktextbook.org/",
             "Ucretsiz cevrimici giris kursu.", level="A1", tags=["kurs"]),
    Resource("oer-commons", "OER Commons - Rusca acik kaynak aramasi", "link",
             "OER Commons", "CC-VARIES",
             "https://oercommons.org/browse?f.keyword=russian",
             "Binlerce acik egitim kaynagi; her kaydin lisansi listede gorunur.",
             level="A1-C1", tags=["arama", "katalog"]),
    Resource("wikibooks-ru", "Wikibooks - Russian (acik ders kitabi)", "link",
             "Wikibooks", "CC-BY-SA-4.0",
             "https://en.wikibooks.org/wiki/Russian",
             "Toplulukca yazilan, bastan sona ucretsiz Rusca ders kitabi.",
             level="A1-B2", attribution="Wikibooks katkicilari, CC BY-SA.",
             tags=["kurs", "dilbilgisi"]),
    Resource("librivox-ru", "LibriVox - Rusca sesli kitaplar (kamu mali)", "link",
             "LibriVox", "PD-MARK",
             "https://librivox.org/search?primary_key=8&search_category=language"
             "&search_page=1&search_form=get_results",
             "Kamu malindaki Rus edebiyati eserlerinin gonulluler tarafindan "
             "seslendirilmis kayitlari - ileri duzey dinleme icin.",
             level="B1-C1", tags=["dinleme", "edebiyat"]),
    Resource("gutenberg-ru", "Project Gutenberg - Rusca metinler (kamu mali)", "link",
             "Project Gutenberg", "PD-MARK",
             "https://www.gutenberg.org/browse/languages/ru",
             "Telifi dusmus Rus klasikleri; PDF/EPUB/TXT olarak indirilebilir. "
             "PDF Okuyucu sekmesinde acip uzerine not alabilirsiniz.",
             level="B1-C1", tags=["okuma", "edebiyat"]),

    # ---------------- Video ----------------
    Resource("openculture-ru", "Open Culture - ucretsiz Rusca ders videolari", "video",
             "Open Culture", "CC-VARIES",
             "https://www.openculture.com/free_russian_lessons",
             "Ucretsiz video ve ses derslerinin derli toplu listesi (her birinin "
             "lisansi kendi sayfasinda belirtilir).", level="A1-B2",
             tags=["video", "katalog"]),
    Resource("fsi-course-site", "FSI Language Courses - tam Rusca kursu", "video",
             "fsi-language-courses.org", "PD-USGOV",
             "https://www.fsi-language-courses.org/russian/",
             "FSI'nin tum Rusca materyallerinin cevrimici sunumu: metin + ses, "
             "kamu mali.", level="A1-C1", tags=["kurs", "ses"]),
]


def by_kind(kind: str = "") -> List[Resource]:
    """Turune gore kaynaklari sirala (bos = hepsi)."""
    if not kind:
        return list(CATALOG)
    return [r for r in CATALOG if r.kind == kind]


def get(rid: str) -> Optional[Resource]:
    """Kimlikle kaynak bul."""
    return next((r for r in CATALOG if r.rid == rid), None)


def download_root() -> Path:
    """Indirilenlerin kok klasoru."""
    return C.RESOURCES_DIR / "Indirilenler"


def total_size(resources: List[Resource]) -> float:
    """Secili kaynaklarin toplam boyutu (MB)."""
    return round(sum(r.size_mb for r in resources), 1)


# --------------------------------------------------------------------------
# Indirici
# --------------------------------------------------------------------------
class Downloader:
    """Tek dosyayi parca parca indirir; iptal edilebilir, ilerleme bildirir."""

    def __init__(self) -> None:
        self.cancelled = threading.Event()

    def cancel(self) -> None:
        """Suren indirmeyi durdur."""
        self.cancelled.set()

    def fetch(self, res: Resource, root: Path,
              on_progress: Callable[[int, int], None] = None) -> Path:
        """Kaynagi indir ve kaydedilen yolu dondur.

        Dosya zaten varsa ve boyutu makulse yeniden indirilmez.
        Yaninda LISANS.txt yazilir.
        """
        target = res.target(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size > 1024:
            write_license_file(res, target.parent)
            return target

        tmp = target.with_suffix(target.suffix + ".part")
        req = urllib.request.Request(res.url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60, context=ssl_context()) as resp:
                total = int(resp.headers.get("Content-Length") or 0)
                done = 0
                with open(tmp, "wb") as f:
                    while True:
                        if self.cancelled.is_set():
                            raise InterruptedError("kullanici durdurdu")
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if on_progress:
                            on_progress(done, total)
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            raise
        tmp.replace(target)
        write_license_file(res, target.parent)
        return target


def write_license_file(res: Resource, folder: Path) -> None:
    """Indirilen dosyanin yanina lisans ve atif bilgisini yaz/guncelle."""
    info = res.license_info()
    line = (f"[{res.filename or res.title}]\n"
            f"  Baslik  : {res.title}\n"
            f"  Kaynak  : {res.provider}\n"
            f"  Adres   : {res.url}\n"
            f"  Lisans  : {info['short']}  {info.get('url', '')}\n"
            f"  Not     : {info.get('note', '')}\n")
    if res.attribution:
        line += f"  Atif    : {res.attribution}\n"
    line += "\n"
    path = folder / "LISANS.txt"
    try:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if f"[{res.filename or res.title}]" in existing:
            return
        header = ("" if existing else
                  "Bu klasordeki dosyalar acik lisansli kaynaklardan indirilmistir.\n"
                  "Her dosyanin lisansi ve atif bilgisi asagida listelenmistir.\n"
                  "Telifli materyal indirilmez.\n\n" + "=" * 70 + "\n\n")
        path.write_text(existing + header + line, encoding="utf-8")
    except Exception:
        pass


# --------------------------------------------------------------------------
# OpenRussian TSV -> kelime bankasi
# --------------------------------------------------------------------------
def _stress_from_accented(accented: str) -> tuple:
    """OpenRussian'in `бу'дьте` bicimini (temiz_kelime, vurgu_indeksi) yap.

    Kaynakta vurgu, vurgulu sesli harften SONRA gelen tek tirnakla gosterilir.
    """
    clean, pos = [], -1
    for ch in accented or "":
        if ch in ("'", "́"):
            pos = len(clean) - 1
        else:
            clean.append(ch)
    return "".join(clean), pos


def import_openrussian(path: Path, repos, limit: int = 2000,
                       deck: str = "OpenRussian",
                       fill_tr_with_en: bool = True,
                       on_progress: Callable[[int, int], None] = None) -> Dict[str, int]:
    """Indirilen OpenRussian TSV dosyasini kelime bankasina aktar.

    Dosya siklik sirasindadir; `limit` en sik N kelimeyi alir.
    Ceviriler Ingilizcedir - Turkce alani istege bagli olarak Ingilizce ile
    doldurulur, sonradan duzenlenebilir.
    """
    import csv

    kind = "noun"
    name = path.name.lower()
    if "fiil" in name or "verb" in name:
        kind = "verb"
    elif "sifat" in name or "adject" in name:
        kind = "adj"
    elif "diger" in name or "other" in name:
        kind = "other"

    pos_map = {"noun": "noun", "verb": "verb", "adj": "adj", "other": ""}
    added = skipped = 0
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for i, row in enumerate(reader):
            if added >= limit:
                break
            bare = (row.get("bare") or "").strip()
            en = (row.get("translations_en") or "").strip()
            if not bare or not en:
                skipped += 1
                continue
            clean, stress = _stress_from_accented(row.get("accented") or bare)
            pos = pos_map.get(kind, "")
            if kind == "noun" and row.get("gender"):
                pos = f"noun-{row['gender'].strip()[:1]}"
            example = ""
            if kind == "verb" and row.get("presfut_sg1"):
                example = (f"я {row.get('presfut_sg1', '')} · "
                           f"ты {row.get('presfut_sg2', '')} · "
                           f"они {row.get('presfut_pl3', '')}")
            elif kind == "noun" and row.get("sg_gen"):
                example = (f"им. {row.get('sg_nom', '')} · род. {row.get('sg_gen', '')} · "
                           f"вин. {row.get('sg_acc', '')} · пред. {row.get('sg_prep', '')}")
            short_en = en.split(";")[0].strip()[:120]
            repos.words.add(clean or bare, short_en if fill_tr_with_en else "",
                            en[:200], stress_pos=stress, pos=pos, deck=deck,
                            example_ru=example, example_tr="",
                            freq_rank=min(9998, i + 1))
            added += 1
            if on_progress and added % 100 == 0:
                on_progress(added, limit)
    return {"added": added, "skipped": skipped}
