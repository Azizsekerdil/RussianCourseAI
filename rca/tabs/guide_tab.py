# -*- coding: utf-8 -*-
"""Egitim & Tanitim Modulu: her ekrani neden -> nasil -> fayda biciminde anlatir."""
from __future__ import annotations

import html
import tkinter as tk
import webbrowser
from tkinter import ttk

import rca_common as C
from rca.ui_util import LazyTab, ScrollFrame

# (baslik, neden, nasil, fayda)
SECTIONS = [
    ("Kelime Bankasi & Sozluk",
     "Dil ogrenmenin govdesi kelimedir; dagilmis notlar yerine tek bir aranabilir banka gerekir.",
     "Ustteki kutuya Turkce, Rusca veya Ingilizce yazip Ara'ya basin. Deste ve frekans "
     "filtreleriyle daraltin. Kelimeye cift tiklayarak dinleyin, sagdaki panelden favoriye "
     "ekleyin veya AI'a sorun. CSV ile toplu ice/disa aktarim yapabilirsiniz.",
     "Aradiginiz kelimeyi 2 saniyede bulur, ogrenme dongusunun tum sekmeleri bu bankadan beslenir."),

    ("Sozluk RU-EN",
     "Kelime bankasi yalnizca ogrendiginiz kelimeleri tutar; okurken karsilastiginiz her "
     "kelime icin ayri bir sozluk gerekir.",
     "Kutuya Kiril yazarsaniz Rusca->Ingilizce, Latin yazarsaniz Ingilizce->Rusca arar; "
     "yon otomatik secilir. Gomulu ~1.400 maddelik cekirdek sozluk aninda calisir. Kaynak "
     "Merkezi'nden OpenRussian dosyalarini indirdiyseniz 'OpenRussian'i yukle' ile on binlerce "
     "madde eklenir. Sozlukte olmayan bir kelime otomatik olarak AI'a sorulur (LM Studio ya da "
     "Ayarlar'daki alternatif uc); gelen madde 'AI' etiketiyle listelenir, ornek cumle ve notuyla "
     "gosterilir ve varsayilan olarak yerel sozluge kaydedilir - bir sonraki arama cevrimdisi "
     "calisir. Arac cubugundaki AI secicisiyle otomatik / yerel / alternatif / kapali secin. "
     "Sagdaki panelden dinleyin, kelime bankasina ekleyin, AI'a sorun; kendi CSV/TSV "
     "listelerinizi ice aktarin.",
     "Programdan cikmadan vurgulu, turu ve cinsiyeti belli bir karsilik bulur; bir tikla "
     "tekrar dongusune alirsiniz."),

    ("Aralikli Tekrar",
     "Insan beyni unutur; bir kelimeyi tam unutmadan hemen once tekrar etmek en verimli andir.",
     "'Bugun' panosundaki sayilara bakin, ardindan Tekrar / Yanlis Drill / Yeni Kelime "
     "dugmelerinden birine basin. Kart modunda Space ile cevirin, 1-2-3 ile kendinizi "
     "degerlendirin. Diger modlarda Enter ile kontrol edin.",
     "SM-2 algoritmasi her kelimenin bir sonraki tekrar gununu kendisi hesaplar; "
     "siz sadece dogru/yanlis dersiniz."),

    ("Sinav Motoru",
     "Tanima (tanidim) ile uretme (yazabildim) farkli becerilerdir; sinav ikincisini olcer.",
     "Soru tiplerini isaretleyin, soru sayisini ve kaynagi secip Basla'ya basin. "
     "Ceviri sorularinda program esdeger cevaplari isaretler ama son karari size birakir.",
     "Sinavdaki her yanlis kelime bankasinda otomatik 'yanlis' olur ve tekrar kuyruguna girer."),

    ("Kiril Laboratuvari",
     "Rusca'da ilk duvar alfabedir; ozellikle el yazisi (курсив) basili harflere hic benzemez.",
     "Alfabe sekmesinde 33 harfi inceleyin. Yazim sekmesinde harfi secip 'Yazim sirasini "
     "oynat'a basin, sag tuvale kendiniz yazin ve Karsilastir'a tiklayin.",
     "Sik karistirilan ciftleri (ш/щ, б/в, и/й, ь/ъ) bastan ayirt ederek sonraki tum "
     "okumalarinizi hizlandirirsiniz."),

    ("Telaffuz & Vurgu Studyosu",
     "Rusca'da vurgu yeri anlami degistirir ve vurgusuz 'o' [a] okunur; yazildigi gibi okunmaz.",
     "Kelimeyi yazip Coz'e basin. Vurgulu heceyi acilir listeden degistirebilirsiniz. "
     "Dinle ile seslendirin; Vosk modeli kuruluysa mikrofonla tekrar edip karsilastirin.",
     "Kelimeyi dogru vurguyla ogrenirsiniz - sonradan duzeltmek cok daha zordur."),

    ("Dilbilgisi Laboratuvarlari",
     "Hal, gorunus ve hareket fiilleri Turkce konusan biri icin Rusca'nin en zor uc bolgesidir.",
     "Her lab ayni akista ilerler: kural -> tablo -> canli ornek -> alistirma. Sayfanin "
     "altindaki '10 soruluk tur baslat' ile hemen deneyin.",
     "Kurali okumak degil, uygulayip aninda geri bildirim almak ogretir; sonuclar zayif "
     "konu raporunuza islenir."),

    ("Kurs Kaynaklari & PDF Okuyucu",
     "Ders kitabini ayri bir programda acmak, not almayi ve kelime cikarmayi zorlastirir.",
     "Kaynaklar sekmesinde Resources/ klasorunu gezin, bitirdiginiz dosyalari Space ile "
     "isaretleyin. PDF'i okuyucuda acip Metin sec araciyla bir parcayi secin; sagdaki "
     "panelden AI'a acikla, Sozlukte ara veya Bankaya ekle deyin.",
     "Okuma, not alma ve kelime toplama tek ekranda birlesir; isaretlemeleriniz PDF'e "
     "gomulu olarak disa aktarilabilir."),

    ("AI Ogretmen",
     "Bir cumlenin NEDEN yanlis oldugunu soracak birine ihtiyaciniz var - her saat.",
     "Gorev secin (acikla / cevir / duzelt), metni yazip Ctrl+Enter'a basin. Yazi duzeltici "
     "hatayi isaretler, kuralin adini soyler ve dogrusunu verir.",
     "Model bilgisayarinizda calisir: internet, hesap ve abonelik gerekmez, metinleriniz "
     "makineden cikmaz."),

    ("Konusma Pratigi",
     "Konusmayi ancak konusarak ogrenirsiniz; muhatap bulmak ise en zor kisimdir.",
     "Senaryoyu ve CEFR seviyenizi secip Oturumu baslat deyin. Rusca yazin; model "
     "seviyenize uygun kelimelerle cevap verir. Sonunda 'Bitir ve rapor al'a basin.",
     "Oturum sonunda hata dokumu ve ogrenmeniz gereken 5 kelimeyi alirsiniz."),

    ("El Yazisi Tahtasi",
     "Kiril el yazisi kas hafizasi ister; ekranda okumak yetmez.",
     "Tablet kalemi veya fareyle yazin. Kilavuz harfi secerseniz arkada soluk bir sablon "
     "belirir. 'Ne yazdim?' ile gorsel modele okutabilirsiniz.",
     "Yazdikca harfleri daha hizli taniyip daha hizli okursunuz."),

    ("Ogrenci Takip",
     "Ilerlemeyi gormek motivasyonu tasir; zayif noktayi gormek zaman kazandirir.",
     "Kartlar, 30 gunluk grafik ve zayif konu listesi otomatik hesaplanir. "
     "'Haftalik Ozet' dugmesi tarayicida A4 yazdirilabilir tek sayfa rapor acar.",
     "Nerede zayif oldugunuzu tahmin etmek yerine olcersiniz; veri yoksa program uydurmaz, "
     "'veri yok' der."),

    ("Kaynak Merkezi",
     "Ders materyali aramak, lisansini kontrol etmek ve indirmek ayri ayri is; "
     "hepsi tek listede olmali ve telifli bir sey yanlislikla inmemeli.",
     "Tur filtresinden e-kitap / ses / sozluk / web secin. Sag panelde kaynagin "
     "lisansi ve atif zorunlulugu yazar. Indir'e basin; dosya "
     "Resources/Indirilenler altina, yaninda LISANS.txt ile kaydedilir. "
     "Indirilen bir PDF'i tek tikla PDF Okuyucuda acabilir, indirilen bir "
     "OpenRussian sozlugunu kelime bankasina aktarabilirsiniz.",
     "Katalogda YALNIZCA kamu mali veya Creative Commons kaynaklar bulunur; "
     "lisansi belirsiz hicbir sey listeye girmez. Boylece indirdiginiz her seyi "
     "gonul rahatligiyla kullanip paylasabilirsiniz."),

    ("Paketler",
     "Hazirladiginiz destelerin baska bir makinede veya arkadasinizda da acilmasi gerekir.",
     "Deste secip '.rupack olustur'a basin. Baskasindan gelen paketi 'Paket ac' ile "
     "ice aktarin; eski .json paketleri de acilir.",
     "Icerik tasinabilir olur, ayni desteyi bastan yazmazsiniz."),

    ("Token Defteri",
     "Yerel model bedava calissa da ne kadar islem yaptiginizi bilmek isteyebilirsiniz.",
     "Bugun / 7 gun / 30 gun / tum zamanlar kartlarina bakin; modele, ise veya gune gore "
     "gruplayin, CSV'ye aktarin.",
     "Kullanimi seffaf gorursunuz - ustelik gonderdiginiz metinler kaydedilmez."),

    ("Ayarlar",
     "Herkesin ekrani, kulagi ve tempo tercihi farklidir.",
     "Arayuz dilini (TR/EN/RU), temayi, gunluk hedefi, ses ve AI adresini buradan degistirin. "
     "'Alternatif uc' bolumunde NVIDIA NIM ya da baska bir OpenAI uyumlu adresi, model adini ve "
     "API anahtarini girin, 'Baglantiyi dene' ile sinayin; sozlugun AI kaynagini da burada secin.",
     "Program size uyum saglar; ayarlar %APPDATA%\\RussianCourseAI\\settings altinda saklanir."),
]

PRIVACY = [
    "Hicbir veri makineden cikmaz; bulut, hesap veya internet gerekmez.",
    "AI yerelde LM Studio ile calisir; modele yalnizca sectiginiz metin gonderilir.",
    "Token defteri sadece sayaclari tutar, istek metinlerini saklamaz.",
    "Alternatif AI ucunun API anahtari Windows Credential Manager'da tutulur (diger sistemlerde "
    "ayar klasorundeki yerel dosyada); settings.json'a asla yazilmaz.",
    "Ag cagrisi yalnizca alternatif AI ucunu (NVIDIA NIM ya da baska bir OpenAI uyumlu adres) "
    "Ayarlar'dan acikca acarsaniz veya Kaynak Merkezinden bir dosya indirdiginizde yapilir - "
    "ikisi de sizin baslattiginiz islemlerdir.",
    "Kaynak Merkezi yalnizca acik lisansli kaynak indirir; TLS sertifika "
    "dogrulamasi hicbir kosulda kapatilmaz.",
]

SHORTCUTS = [
    ("Space", "Kelime kartini cevir"),
    ("1 / 2 / 3", "Bilmiyorum / Emin degilim / Biliyorum"),
    ("Enter", "Alistirmada cevabi kontrol et"),
    ("Ctrl+Enter", "AI Ogretmen'de soruyu gonder"),
    ("Ctrl+1 .. 9", "Ilk dokuz sayfaya dogrudan gec"),
    ("Ctrl+PgUp / PgDn", "Onceki / sonraki sayfa"),
    ("F5", "Gorunen sayfayi tazele"),
    ("Ctrl+Q", "Programi kapat"),
    ("Space (Kaynaklar)", "Bitirdim isaretini degistir"),
]


class GuideTab(LazyTab):
    """Cevrimdisi tek sayfa kullanim kilavuzu."""

    def build(self) -> None:
        p = self.palette()
        head = ttk.Frame(self, padding=(12, 12, 12, 0))
        head.pack(fill="x")
        ttk.Label(head, text=f"{C.APP_NAME} · Kullanim Kilavuzu",
                  style="Title.TLabel").pack(side="left")
        ttk.Button(head, text="🖨 Yazdirilabilir surum", style="Accent.TButton",
                   command=self.print_version).pack(side="right")

        sf = ScrollFrame(self)
        sf.paint(p)
        sf.pack(fill="both", expand=True, padx=4, pady=8)
        b = sf.body

        ttk.Label(b, style="Dim.TLabel", wraplength=980, justify="left", padding=(10, 6),
                  text="Bu kilavuz tamamen cevrimdisidir. Her bolum ayni sirayi izler: "
                       "NEDEN var · NASIL kullanilir · NE kazandirir.").pack(anchor="w")

        for title, why, how, gain in SECTIONS:
            box = ttk.Frame(b, style="Card.TFrame", padding=14)
            box.pack(fill="x", padx=10, pady=5)
            ttk.Label(box, text=title, style="Card.TLabel",
                      font=("Segoe UI", 13, "bold")).pack(anchor="w")
            for label, text, color in (("NEDEN", why, p["warn"]),
                                       ("NASIL", how, p["fg"]),
                                       ("FAYDA", gain, p["ok"])):
                row = ttk.Frame(box, style="Card.TFrame")
                row.pack(fill="x", pady=(6, 0))
                ttk.Label(row, text=label, style="Card.TLabel", foreground=color,
                          width=8, font=C.FONT_UI_BOLD).pack(side="left", anchor="n")
                ttk.Label(row, text=text, style="Card.TLabel", wraplength=880,
                          justify="left").pack(side="left", anchor="w")

        ttk.Label(b, text="Gizlilik", style="Title.TLabel",
                  padding=(10, 18, 0, 4)).pack(anchor="w")
        for line in PRIVACY:
            ttk.Label(b, text="· " + line, style="Dim.TLabel", wraplength=960,
                      justify="left", padding=(16, 1)).pack(anchor="w")

        ttk.Label(b, text="Kisayollar", style="Title.TLabel",
                  padding=(10, 18, 0, 4)).pack(anchor="w")
        grid = ttk.Frame(b, padding=(16, 0, 0, 20))
        grid.pack(anchor="w")
        for i, (key, desc) in enumerate(SHORTCUTS):
            ttk.Label(grid, text=key, style="TLabel", font=C.FONT_MONO,
                      width=18).grid(row=i, column=0, sticky="w", pady=1)
            ttk.Label(grid, text=desc, style="Dim.TLabel").grid(row=i, column=1, sticky="w")

    # ------------------------------------------------------------------
    def print_version(self) -> None:
        """Renkli/gri yazdirilabilir HTML kilavuz uret ve tarayicida ac."""
        parts = []
        for title, why, how, gain in SECTIONS:
            parts.append(
                f"<section><h2>{html.escape(title)}</h2>"
                f"<p><b class='why'>NEDEN</b> {html.escape(why)}</p>"
                f"<p><b class='how'>NASIL</b> {html.escape(how)}</p>"
                f"<p><b class='gain'>FAYDA</b> {html.escape(gain)}</p></section>")
        privacy = "".join(f"<li>{html.escape(x)}</li>" for x in PRIVACY)
        keys = "".join(f"<tr><td><code>{html.escape(k)}</code></td>"
                       f"<td>{html.escape(d)}</td></tr>" for k, d in SHORTCUTS)

        doc = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>{html.escape(C.APP_NAME)} - Kilavuz</title>
<style>
 @page {{ size:A4; margin:16mm; }}
 body {{ font-family:"Segoe UI",Arial,sans-serif; color:#1c1e24; line-height:1.45; }}
 h1 {{ font-size:20pt; margin-bottom:2px; }}
 .sub {{ color:#5d6470; margin-bottom:16px; }}
 section {{ break-inside:avoid; border-left:3px solid #dfe2e8; padding-left:12px;
            margin-bottom:14px; }}
 h2 {{ font-size:12.5pt; margin:0 0 6px; }}
 p {{ margin:3px 0; font-size:10pt; }}
 b.why {{ color:#a8701c; }} b.how {{ color:#2f6fe0; }} b.gain {{ color:#2f8f52; }}
 b {{ display:inline-block; width:58px; font-size:8.5pt; letter-spacing:.5px; }}
 ul {{ font-size:10pt; }} table {{ border-collapse:collapse; font-size:10pt; }}
 td {{ border-bottom:1px solid #e6e8ee; padding:4px 12px 4px 0; }}
 code {{ background:#f0f2f6; padding:1px 5px; border-radius:3px; }}
 @media print {{ body {{ color:#000; }} b.why,b.how,b.gain {{ color:#000; }} }}
</style></head><body>
<h1>{html.escape(C.APP_NAME)} · Kullanim Kilavuzu</h1>
<div class="sub">Surum {C.VERSION} · tamamen cevrimdisi · Ctrl+P ile yazdirin</div>
{''.join(parts)}
<h2>Gizlilik</h2><ul>{privacy}</ul>
<h2>Kisayollar</h2><table>{keys}</table>
</body></html>"""
        out = C.EXPORT_DIR / "kilavuz.html"
        try:
            C.ensure_dirs()
            out.write_text(doc, encoding="utf-8")
            webbrowser.open(out.as_uri())
            self.app.set_status(f"Kilavuz: {out}")
        except Exception as e:                          # noqa: BLE001
            self.app.set_status(f"Kilavuz yazilamadi: {e}")
