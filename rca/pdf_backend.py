# -*- coding: utf-8 -*-
"""PDF arka ucu: sayfa cizimi, kelime kutulari ve isaretli PDF yazimi.

Goruntuleme ve metin cikarimi icin ``pypdfium2`` (Apache-2.0 VEYA
BSD-3-Clause), isaretli kopyayi yazmak icin ``pypdf`` (BSD-3-Clause)
kullanilir. Ikisi de ISTEGE BAGLIDIR: kurulu degillerse modul sessizce
devre disi kalir, cagiran arayuz cokmez ve kullaniciya kurulum ipucu
gosterir.

KOORDINAT KURALI
----------------
Disariya verilen ve disaridan alinan tum koordinatlar - kelime kutulari,
isaretleme dikdortgenleri, kalem noktalari, not konumlari - sayfanin
GORUNEN halinde, SOL UST kosesi (0, 0) olan nokta (point) uzayindadir.
PDF'in kendi uzayi SOL ALT kokenlidir ve /Rotate donusunu icermez; iki
uzay arasindaki cevrim burada, tek bir yerde yapilir.
"""
from __future__ import annotations

import json
import math
from typing import Iterable, List, Optional, Sequence, Tuple

#: Kutuphaneler eksikse kullaniciya gosterilecek kurulum satiri.
INSTALL_HINT = "pip install pypdfium2 pypdf"
#: Yalnizca goruntuleme/metin icin gereken kurulum satiri.
VIEW_HINT = "pip install pypdfium2"
#: Yalnizca isaretli disa aktarma icin gereken kurulum satiri.
EXPORT_HINT = "pip install pypdf"

#: Isaretleme (highlight) rengi - arayuzdeki "mark" araciyla ayni.
MARK_RGB = (1.0, 0.878, 0.4)
MARK_ALPHA = 0.35
#: Kalem ve metin notu rengi.
INK_RGB = (0.85, 0.2, 0.2)
#: Sayfa notu rengi.
NOTE_RGB = (0.2, 0.4, 0.8)


# --------------------------------------------------------------------------
# Kutuphane erisimi (hepsi istege bagli)
# --------------------------------------------------------------------------
def pdfium():
    """pypdfium2 modulunu dondur (yoksa None)."""
    try:
        import pypdfium2                      # type: ignore
        return pypdfium2
    except Exception:                          # noqa: BLE001
        return None


def pypdf():
    """pypdf modulunu dondur (yoksa None)."""
    try:
        import pypdf                           # type: ignore
        return pypdf
    except Exception:                          # noqa: BLE001
        return None


def can_view() -> bool:
    """PDF goruntuleme/metin cikarimi mumkun mu?"""
    return pdfium() is not None


def can_export() -> bool:
    """Isaretli PDF yazimi mumkun mu?"""
    return pypdf() is not None


def available() -> bool:
    """Sekmenin tam ozellikli calismasi icin gereken her sey var mi?"""
    return can_view() and can_export()


def missing() -> List[str]:
    """Eksik paketlerin adlari."""
    out = []
    if not can_view():
        out.append("pypdfium2")
    if not can_export():
        out.append("pypdf")
    return out


# --------------------------------------------------------------------------
# Koordinat cevrimi
# --------------------------------------------------------------------------
class PageGeometry:
    """Bir sayfanin donus/kirpma bilgisi ve iki uzay arasindaki cevrim.

    ``uw`` / ``uh`` dondurulmemis kirpma kutusunun olculeri, ``ox`` / ``oy``
    o kutunun PDF uzayindaki sol alt kosesi, ``rot`` ise /Rotate degeridir.
    ``width`` / ``height`` ise sayfanin GORUNEN (dondurulmus) olcusudur.
    """

    __slots__ = ("rot", "uw", "uh", "ox", "oy", "width", "height")

    def __init__(self, rot: int, uw: float, uh: float,
                 ox: float = 0.0, oy: float = 0.0) -> None:
        self.rot = int(rot) % 360
        if self.rot not in (0, 90, 180, 270):
            self.rot = 0
        self.uw = float(uw)
        self.uh = float(uh)
        self.ox = float(ox)
        self.oy = float(oy)
        if self.rot in (90, 270):
            self.width, self.height = self.uh, self.uw
        else:
            self.width, self.height = self.uw, self.uh

    # -- PDF (sol alt) -> gorunen (sol ust) -------------------------------
    def to_view(self, x: float, y: float) -> Tuple[float, float]:
        """PDF uzayindaki bir noktayi gorunen sol-ust uzaya cevir."""
        px, py = x - self.ox, y - self.oy
        if self.rot == 90:
            return py, px
        if self.rot == 180:
            return self.uw - px, py
        if self.rot == 270:
            return self.uh - py, self.uw - px
        return px, self.uh - py

    # -- gorunen (sol ust) -> PDF (sol alt) -------------------------------
    def to_pdf(self, vx: float, vy: float) -> Tuple[float, float]:
        """Gorunen sol-ust uzaydaki bir noktayi PDF uzayina cevir."""
        if self.rot == 90:
            px, py = vy, vx
        elif self.rot == 180:
            px, py = self.uw - vx, vy
        elif self.rot == 270:
            px, py = self.uw - vy, self.uh - vx
        else:
            px, py = vx, self.uh - vy
        return px + self.ox, py + self.oy

    def view_rect(self, box: Sequence[float]) -> Tuple[float, float, float, float]:
        """PDF kutusunu (sol, alt, sag, ust) gorunen (x0, y0, x1, y1)'e cevir."""
        ax, ay = self.to_view(box[0], box[1])
        bx, by = self.to_view(box[2], box[3])
        return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)

    def pdf_rect(self, x0: float, y0: float, x1: float,
                 y1: float) -> Tuple[float, float, float, float]:
        """Gorunen dikdortgeni PDF (sol, alt, sag, ust) kutusuna cevir."""
        ax, ay = self.to_pdf(x0, y0)
        bx, by = self.to_pdf(x1, y1)
        return min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)


# --------------------------------------------------------------------------
# Cizilmis sayfa
# --------------------------------------------------------------------------
class RenderedPage:
    """Tuvale konulmaya hazir sayfa goruntusu.

    ``data`` ikili P6 PPM verisidir; dogrudan ``tk.PhotoImage(data=...)``
    icine verilebilir. ``width`` / ``height`` piksel olcusudur.
    """

    __slots__ = ("data", "width", "height")

    def __init__(self, data: bytes, width: int, height: int) -> None:
        self.data = data
        self.width = int(width)
        self.height = int(height)


def _bitmap_to_ppm(bitmap) -> Tuple[bytes, int, int]:
    """pdfium bit eslemesini P6 PPM baytlarina cevir.

    Once Pillow denenir (zaten bir bagimliliktir); yoksa ham arabellek
    elle PPM'e paketlenir - boylece Pillow olmadan da cizim surer.
    """
    w, h = int(bitmap.width), int(bitmap.height)
    try:
        import io
        img = bitmap.to_pil().convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PPM")
        return buf.getvalue(), w, h
    except Exception:                          # noqa: BLE001
        pass
    raw = bytes(bitmap.buffer)
    stride = int(bitmap.stride)
    mode = str(getattr(bitmap, "mode", "BGR"))
    step = int(getattr(bitmap, "n_channels", 3)) or 3
    reverse = mode.startswith("BGR")            # BGR{,A,x} -> RGB
    gray = mode == "L"
    rows = []
    for y in range(h):
        line = raw[y * stride:y * stride + w * step]
        out = bytearray(w * 3)
        for x in range(w):
            base = x * step
            if gray:
                v = line[base]
                out[x * 3:x * 3 + 3] = bytes((v, v, v))
            elif reverse:
                out[x * 3:x * 3 + 3] = bytes((line[base + 2], line[base + 1], line[base]))
            else:
                out[x * 3:x * 3 + 3] = line[base:base + 3]
        rows.append(bytes(out))
    body = b"".join(rows)
    return b"P6\n%d %d\n255\n" % (w, h) + body, w, h


# --------------------------------------------------------------------------
# Belge
# --------------------------------------------------------------------------
class PdfDoc:
    """Acilmis bir PDF: sayfa sayisi, olcu, cizim ve kelime kutulari."""

    def __init__(self, path: str) -> None:
        lib = pdfium()
        if lib is None:
            raise RuntimeError(
                f"PDF goruntulemek icin pypdfium2 gerekli:\n\n{INSTALL_HINT}")
        self.path = str(path)
        self._lib = lib
        self._doc = lib.PdfDocument(self.path)
        self._count = len(self._doc)

    # -- temel bilgi -------------------------------------------------------
    def __len__(self) -> int:
        return self._count

    @property
    def page_count(self) -> int:
        """Sayfa sayisi."""
        return self._count

    def _page(self, index: int):
        """Sinirlar icine kirpilmis sayfa nesnesi."""
        i = max(0, min(self._count - 1, int(index)))
        return self._doc[i]

    def geometry(self, index: int) -> PageGeometry:
        """Sayfanin donus/kirpma bilgisi."""
        page = self._page(index)
        try:
            rot = int(page.get_rotation() or 0)
        except Exception:                      # noqa: BLE001
            rot = 0
        dw, dh = page.get_size()
        uw, uh = (dh, dw) if rot % 360 in (90, 270) else (dw, dh)
        ox = oy = 0.0
        for getter in ("get_cropbox", "get_mediabox"):
            try:
                box = getattr(page, getter)()
            except Exception:                  # noqa: BLE001
                box = None
            if box:
                ox, oy = float(box[0]), float(box[1])
                break
        return PageGeometry(rot, uw, uh, ox, oy)

    def page_size(self, index: int) -> Tuple[float, float]:
        """Sayfanin GORUNEN genislik/yuksekligi (nokta)."""
        w, h = self._page(index).get_size()
        return float(w), float(h)

    # -- cizim -------------------------------------------------------------
    def render(self, index: int, zoom: float = 1.0) -> RenderedPage:
        """Sayfayi verilen yakinlastirmayla ciz."""
        page = self._page(index)
        bitmap = page.render(scale=float(zoom))
        data, w, h = _bitmap_to_ppm(bitmap)
        try:
            bitmap.close()
        except Exception:                      # noqa: BLE001
            pass
        return RenderedPage(data, w, h)

    # -- metin -------------------------------------------------------------
    def words(self, index: int) -> List[tuple]:
        """Sayfadaki kelimeleri sekiz ogeli demetler halinde ver.

        Her oge ``(x0, y0, x1, y1, kelime, blok_no, satir_no, kelime_no)``
        biciminde bir demettir; koordinatlar sayfanin gorunen halinde ve
        SOL UST kokenlidir. Bu, metin secimi ve sozluk aramasinin bekledigi
        sekildir. Kutular satir yuksekligindedir (yazi tipinin ust/alt
        sinirlari), harfin murekkebini siki siki saran kutu degil; boylece
        satir aralarina degen bir fare surtmesi de kelimeyi yakalar. pdfium karakter karakter calisir, bu yuzden karakterler
        bosluklarda kelimelere, satir sonlarinda satirlara bolunur; blok
        numarasi ise satirlar arasindaki dikey bosluktan cikarilir (pdfium'da
        blok kavrami yoktur).
        """
        page = self._page(index)
        geom = self.geometry(index)
        try:
            textpage = page.get_textpage()
        except Exception:                      # noqa: BLE001
            return []
        try:
            return _collect_words(textpage, geom)
        finally:
            try:
                textpage.close()
            except Exception:                  # noqa: BLE001
                pass

    def page_text(self, index: int) -> str:
        """Sayfanin duz metni."""
        page = self._page(index)
        try:
            textpage = page.get_textpage()
        except Exception:                      # noqa: BLE001
            return ""
        try:
            return textpage.get_text_range() or ""
        except Exception:                      # noqa: BLE001
            return ""
        finally:
            try:
                textpage.close()
            except Exception:                  # noqa: BLE001
                pass

    def close(self) -> None:
        """Belgeyi kapat (dosya kilidini birak)."""
        try:
            self._doc.close()
        except Exception:                      # noqa: BLE001
            pass


def open_document(path: str) -> PdfDoc:
    """PDF'i ac."""
    return PdfDoc(path)


# --------------------------------------------------------------------------
# Karakterlerden kelime toplama
# --------------------------------------------------------------------------
#: pdfium'un "burada karakter yok" anlaminda dondurdugu isaretciler.
_SEPARATORS = {"\x00", "\ufffe", "\ufeff", "\uffff"}


def _charbox(textpage, index: int):
    """Karakterin GENIS (loose) kutusunu ver.

    pdfium'un varsayilan kutusu yalnizca harfin murekkebini sarar; bu da
    kelime kutularini satir yuksekliginden ~8 nokta kisa yapar ve fareyle
    dikdortgen secimini gereksiz yere hassas hale getirir. ``loose=True``
    ise yazi tipinin tam ust/alt sinirlarini kullanir; boylece kutular
    satir yuksekligiyle ortusur. Cok eski bir pypdfium2 bu secenegi
    tanimazsa dar kutuya duseriz.
    """
    try:
        return textpage.get_charbox(index, loose=True)
    except TypeError:                          # pypdfium2 < 4.x: loose yok
        return textpage.get_charbox(index)


def _char_stream(textpage, count: int):
    """(karakter, kutu) ciftlerini uret.

    Sayfa metninin uzunlugu karakter sayisiyla ortusuyorsa tek seferde
    alinan metin kullanilir (hizli yol); ortusmuyorsa karakterler tek tek
    okunur.
    """
    text = ""
    try:
        text = textpage.get_text_range() or ""
    except Exception:                          # noqa: BLE001
        text = ""
    aligned = len(text) == count
    for i in range(count):
        if aligned:
            ch = text[i]
        else:
            try:
                ch = (textpage.get_text_range(i, 1) or "")[:1]
            except Exception:                  # noqa: BLE001
                ch = ""
        try:
            box = _charbox(textpage, i)
        except Exception:                      # noqa: BLE001
            box = None
        yield ch, box


def _collect_words(textpage, geom: PageGeometry) -> List[tuple]:
    """Karakter akisini kelime demetlerine cevir.

    Kelimeler bosluklarda, satirlar ``\\r`` / ``\\n`` karakterlerinde biter.
    pdfium'da blok kavrami olmadigindan blok numarasi, iki satir arasindaki
    dikey bosluk onceki satirin yuksekligini asinca artirilir - yani gorsel
    paragraf araliklari blok siniri sayilir.
    """
    try:
        count = int(textpage.count_chars())
    except Exception:                          # noqa: BLE001
        return []
    out: List[tuple] = []
    block_no = line_no = word_no = 0
    prev_line_bottom: Optional[float] = None
    prev_line_height = 0.0
    line_top: Optional[float] = None
    line_bottom = 0.0
    buf: List[str] = []
    bx0 = by0 = bx1 = by1 = 0.0

    def flush() -> None:
        """Biriken karakterleri bir kelime olarak listeye ekle."""
        nonlocal buf, word_no
        if not buf:
            return
        word = "".join(buf)
        buf = []
        if not word.strip():
            return
        out.append((bx0, by0, bx1, by1, word, block_no, line_no, word_no))
        word_no += 1

    def newline() -> None:
        """Satiri kapat; bir sonraki karakter yeni satirin ilki olur."""
        nonlocal line_no, word_no, line_top, line_bottom
        nonlocal prev_line_bottom, prev_line_height
        flush()
        if line_top is None:                   # bos satir - sayilmaz
            return
        prev_line_bottom = line_bottom
        prev_line_height = max(0.0, line_bottom - line_top)
        line_top = None
        line_no += 1
        word_no = 0

    for ch, box in _char_stream(textpage, count):
        if ch in ("\r", "\n"):
            newline()
            continue
        if not ch or ch in _SEPARATORS or ch.isspace():
            flush()
            continue
        if box is None:
            flush()
            continue
        x0, y0, x1, y1 = geom.view_rect(box)
        if not all(math.isfinite(v) for v in (x0, y0, x1, y1)):
            flush()
            continue
        if line_top is None:
            # Satirin ilk karakteri: onceki satirla arasindaki bosluk
            # yeterince buyukse yeni bir blok baslar.
            if (prev_line_bottom is not None
                    and y0 - prev_line_bottom > max(prev_line_height, 2.0)):
                block_no += 1
                line_no = 0
                word_no = 0
            line_top, line_bottom = y0, y1
        else:
            line_top, line_bottom = min(line_top, y0), max(line_bottom, y1)
        if not buf:
            bx0, by0, bx1, by1 = x0, y0, x1, y1
        else:
            bx0, by0 = min(bx0, x0), min(by0, y0)
            bx1, by1 = max(bx1, x1), max(by1, y1)
        buf.append(ch)
    flush()
    return out


# --------------------------------------------------------------------------
# Isaretli PDF yazimi
# --------------------------------------------------------------------------
def _hex(rgb: Sequence[float]) -> str:
    """(r, g, b) oranlarini pypdf'in bekledigi altili onaltilik dizgeye cevir."""
    return "".join("%02x" % max(0, min(255, int(round(c * 255)))) for c in rgb)


def _ops_color(rgb: Sequence[float], stroke: bool = False) -> str:
    """PDF icerik akisi icin renk operatoru."""
    return "%.3f %.3f %.3f %s" % (rgb[0], rgb[1], rgb[2], "RG" if stroke else "rg")


def drawn_text_is_complete(text: str) -> bool:
    """Metin, sayfaya CIZILEN kopyada eksiksiz gorunur mu?

    Gorunum akisi Base-14 Helvetica + WinAnsiEncoding kullanir; bu kume
    Kiril harflerini ve Turkce ``i-noktasiz / s-cedilli / g-yumusak``
    harflerini icermez, onlar sayfada '?' olur. Metnin tam Unicode hali
    her zaman annotation'in ``/Contents`` alanindadir (okuyucunun yorum
    panelinde eksiksiz gorunur), yani veri kaybolmaz - yalnizca sayfa
    uzerindeki kopya eksiktir. Arayuz bunu kullaniciya soyleyebilsin diye
    bu yardimci disariya aciktir.
    """
    try:
        text.encode("cp1252")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _pdf_string(text: str) -> str:
    """Metni PDF ``( )`` dizgesine kacisla.

    Gomulu Helvetica yalnizca WinAnsi kapsar; Kiril gibi disarida kalan
    harfler '?' olur (bkz. :func:`drawn_text_is_complete`). Notun tam
    Unicode hali her zaman annotation'in ``/Contents`` alaninda saklanir,
    yani veri kaybolmaz.
    """
    raw = text.encode("cp1252", "replace").decode("cp1252")
    out = []
    for ch in raw:
        if ch in "()\\":
            out.append("\\" + ch)
        elif ch == "\n":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def _attach_appearance(writer, annotation, rect: Sequence[float], ops: str,
                       alpha: Optional[float] = None, font: bool = False) -> bool:
    """Annotation'a bir ``/AP /N`` gorunum akisi bagla.

    Bircok goruntuleyici (Chrome/Edge gibi pdfium tabanlilar) yalnizca bazi
    annotation turleri icin gorunum uretir; kendi gorunumumuzu yazinca
    isaretler HER goruntuleyicide dogru yerde gorunur.
    """
    mod = pypdf()
    if mod is None:
        return False
    try:
        from pypdf.generic import (ArrayObject, DecodedStreamObject, DictionaryObject,
                                   FloatObject, NameObject, NumberObject)
    except Exception:                          # noqa: BLE001
        return False
    try:
        stream = DecodedStreamObject()
        stream.set_data(ops.encode("latin-1", "replace"))
        stream[NameObject("/Type")] = NameObject("/XObject")
        stream[NameObject("/Subtype")] = NameObject("/Form")
        stream[NameObject("/FormType")] = NumberObject(1)
        stream[NameObject("/BBox")] = ArrayObject([FloatObject(v) for v in rect])

        resources = DictionaryObject()
        resources[NameObject("/ProcSet")] = ArrayObject(
            [NameObject("/PDF"), NameObject("/Text")])
        if alpha is not None:
            gstate = DictionaryObject()
            gstate[NameObject("/Type")] = NameObject("/ExtGState")
            gstate[NameObject("/ca")] = FloatObject(alpha)
            gstate[NameObject("/CA")] = FloatObject(alpha)
            holder = DictionaryObject()
            holder[NameObject("/GS")] = gstate
            resources[NameObject("/ExtGState")] = holder
        if font:
            helv = DictionaryObject()
            helv[NameObject("/Type")] = NameObject("/Font")
            helv[NameObject("/Subtype")] = NameObject("/Type1")
            helv[NameObject("/BaseFont")] = NameObject("/Helvetica")
            helv[NameObject("/Encoding")] = NameObject("/WinAnsiEncoding")
            holder = DictionaryObject()
            holder[NameObject("/Helv")] = helv
            resources[NameObject("/Font")] = holder
        stream[NameObject("/Resources")] = resources

        ref = writer._add_object(stream)       # noqa: SLF001 - pypdf'te acik es yok
        appearance = DictionaryObject()
        appearance[NameObject("/N")] = ref
        annotation[NameObject("/AP")] = appearance
        return True
    except Exception:                          # noqa: BLE001
        return False


def _page_geometry_from_pypdf(page) -> PageGeometry:
    """pypdf sayfasindan donus/kirpma bilgisi cikar."""
    try:
        box = page.cropbox
    except Exception:                          # noqa: BLE001
        box = None
    if box is None:
        box = page.mediabox
    ox, oy = float(box.left), float(box.bottom)
    uw, uh = float(box.width), float(box.height)
    try:
        rot = int(page.get("/Rotate", 0) or 0)
    except Exception:                          # noqa: BLE001
        rot = 0
    return PageGeometry(rot, uw, uh, ox, oy)


def _mark_annotation(writer, index: int, geom: PageGeometry, data: dict) -> bool:
    """Sari isaretleme dikdortgeni."""
    from pypdf.annotations import Rectangle
    rect = data.get("rect") or []
    if len(rect) != 4:
        return False
    x0, y0, x1, y1 = geom.pdf_rect(*[float(v) for v in rect])
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return False
    color = data.get("color") or ""
    rgb = _rgb_from_hex(color, MARK_RGB)
    try:
        ann = Rectangle(rect=(x0, y0, x1, y1), interior_color=_hex(rgb))
    except TypeError:                          # pypdf < 5.1: eski yazim
        ann = Rectangle(rect=(x0, y0, x1, y1), interiour_color=_hex(rgb))
    obj = writer.add_annotation(page_number=index, annotation=ann)
    ops = ("/GS gs %s %.2f %.2f %.2f %.2f re f"
           % (_ops_color(rgb), x0, y0, x1 - x0, y1 - y0))
    _attach_appearance(writer, obj, (x0, y0, x1, y1), ops, alpha=MARK_ALPHA)
    return True


def _pen_annotation(writer, index: int, geom: PageGeometry, data: dict) -> bool:
    """Serbest el cizimi - tek bir cok parcali cizgi olarak yazilir."""
    from pypdf.annotations import Line
    pts = [float(v) for v in (data.get("points") or [])]
    if len(pts) < 4:
        return False
    view = [(pts[i], pts[i + 1]) for i in range(0, len(pts) - 1, 2)]
    pdf_pts = [geom.to_pdf(vx, vy) for vx, vy in view]
    xs = [p[0] for p in pdf_pts]
    ys = [p[1] for p in pdf_pts]
    pad = 2.0
    rect = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    ann = Line(p1=pdf_pts[0], p2=pdf_pts[-1], rect=rect)
    obj = writer.add_annotation(page_number=index, annotation=ann)
    segs = ["%s 1.5 w 1 J 1 j" % _ops_color(INK_RGB, stroke=True),
            "%.2f %.2f m" % pdf_pts[0]]
    segs += ["%.2f %.2f l" % p for p in pdf_pts[1:]]
    segs.append("S")
    _attach_appearance(writer, obj, rect, " ".join(segs))
    return True


def _text_annotation(writer, index: int, geom: PageGeometry, text: str,
                     vx: float, vy: float, size: float,
                     rgb: Sequence[float]) -> bool:
    """Sayfaya yazilmis serbest metin notu."""
    from pypdf.annotations import FreeText
    text = (text or "").strip()
    if not text:
        return False
    width = max(40.0, min(geom.width - vx - 4.0, len(text) * size * 0.55 + 8.0))
    x0, y0, x1, y1 = geom.pdf_rect(vx, vy, vx + width, vy + size * 1.6)
    ann = FreeText(text=text, rect=(x0, y0, x1, y1),
                   font="Helvetica", font_size="%dpt" % int(round(size)),
                   font_color=_hex(rgb), border_color=None, background_color=None)
    obj = writer.add_annotation(page_number=index, annotation=ann)
    ops = ("BT /Helv %.1f Tf %s %.2f %.2f Td (%s) Tj ET"
           % (size, _ops_color(rgb), x0 + 1.0, y0 + size * 0.35,
              _pdf_string(text)))
    _attach_appearance(writer, obj, (x0, y0, x1, y1), ops, font=True)
    return True


def _rgb_from_hex(value: str, default: Sequence[float]) -> Tuple[float, float, float]:
    """'#rrggbb' dizgesini 0-1 araligina cevir (bozuksa varsayilan)."""
    text = (value or "").strip().lstrip("#")
    if len(text) != 6:
        return tuple(default)                  # type: ignore[return-value]
    try:
        return (int(text[0:2], 16) / 255.0, int(text[2:4], 16) / 255.0,
                int(text[4:6], 16) / 255.0)
    except ValueError:
        return tuple(default)                  # type: ignore[return-value]


def export_annotated(src_path: str, out_path: str,
                     notes: Iterable[dict]) -> int:
    """Isaretlemeleri gomulu yeni bir PDF yaz ve yazilan annotation sayisini dondur.

    ``notes`` ogeleri veritabanindaki satirlarla ayni sekildedir:
    ``page`` (0 tabanli), ``kind`` (``mark`` | ``pen`` | ``text`` | ``note``)
    ve ``payload`` (``note`` icin duz metin, digerleri icin JSON).
    """
    mod = pypdf()
    if mod is None:
        raise RuntimeError(
            f"Isaretli PDF yazmak icin pypdf gerekli:\n\n{INSTALL_HINT}")
    writer = mod.PdfWriter(clone_from=str(src_path))
    pages = len(writer.pages)
    geoms = {}
    written = 0
    for row in notes:
        try:
            index = int(row["page"])
            kind = str(row["kind"])
            payload = row["payload"]
        except Exception:                      # noqa: BLE001
            continue
        if index < 0 or index >= pages:
            continue
        if index not in geoms:
            geoms[index] = _page_geometry_from_pypdf(writer.pages[index])
        geom = geoms[index]
        data = None
        if kind == "note":
            if not str(payload).strip():       # bos not - yazacak bir sey yok
                continue
        else:
            try:
                data = json.loads(payload)
            except Exception:                  # noqa: BLE001
                continue
            if not isinstance(data, dict):
                continue
        try:
            if kind == "mark":
                ok = _mark_annotation(writer, index, geom, data)
            elif kind == "pen":
                ok = _pen_annotation(writer, index, geom, data)
            elif kind == "text":
                ok = _text_annotation(writer, index, geom,
                                      str(data.get("text", "")),
                                      float(data.get("x", 0.0)),
                                      float(data.get("y", 0.0)),
                                      10.0, INK_RGB)
            elif kind == "note":
                ok = _text_annotation(writer, index, geom,
                                      "[not] " + str(payload)[:120],
                                      30.0, 30.0, 8.0, NOTE_RGB)
            else:
                ok = False
        except Exception:                      # noqa: BLE001
            ok = False
        if ok:
            written += 1
    with open(str(out_path), "wb") as fh:
        writer.write(fh)
    try:
        writer.close()
    except Exception:                          # noqa: BLE001
        pass
    return written
