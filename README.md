# Russian Course AI

**Türkçe** | [English](README.en.md)

[Üç dilli tanıtım PDF'i](output/pdf/Russian-Course-AI-Trilingual.pdf) ·
[Düzenlenebilir PowerPoint](docs/presentation/Russian-Course-AI-Trilingual.pptx)

Windows uzerinde **%100 cevrimdisi** calisan, Rusca'yi A1'den C1'e (ТРКИ-3) goturmek
icin tasarlanmis masaustu dil ogrenme istasyonu.

Tek pencerede: PDF ders kitabi okuyucu + not alma, yerel yapay zeka ogretmen,
Kiril yazi laboratuvari, dilbilgisi laboratuvarlari (hal / gorunus / hareket fiilleri),
telaffuz & vurgu studyosu, kelime bankasi + aralikli tekrar, sinav motoru,
el yazisi cizim tahtasi, cift yonlu TR<->RU kelime bankasi ve **Rusca<->Ingilizce sozluk**
(1.360 gomulu madde + OpenRussian ile 45.000+ madde).

**Hicbir veri makineden cikmaz.** Yapay zeka yerelde LM Studio ile calisir; program
dosyalari kendisi okur ve modele yalnizca sectiginiz metni gonderir.
Bulut yok, hesap yok, internet gerekmez. Istege bagli olarak sozluk, LM Studio
kapaliyken NVIDIA NIM ya da baska bir OpenAI uyumlu uca (API anahtariyla) sorabilir;
bu yalnizca Ayarlar'dan acikca acilirsa olur.

---

## Hizli baslangic

Kaynaktan calistirmak icin:

```bash
python Russian_Course_AI.pyw
```

Baska hicbir sey gerekmez. Program ilk acilista:
- `%APPDATA%\RussianCourseAI` altinda veri klasorlerini olusturur,
- SQLite semasini kurar,
- **125 kelimelik hazir A1 destesini** (9 deste) yukler,
- bir "Ogrenci" profili acar.

Istege bagli ozellikler icin:

```bash
pip install -r requirements.txt
```

---

## .exe uretimi ve masaustu kisayolu

```bash
build.bat
```

Bu komut sirasiyla: PyInstaller'i kontrol eder (yoksa kurar), `assets/app.ico`
simgesini uretir, tek dosyalik `dist\RussianCourseAI.exe` derler ve
**masaustune "Russian Course AI" kisayolu koyar**.

| Secenek | Etki |
|---|---|
| `build.bat` | exe + masaustu kisayolu |
| `build.bat /noshortcut` | yalnizca exe |
| `build.bat /onedir` | tek dosya yerine klasor (belirgin sekilde daha hizli acilir) |

Yalnizca kisayol isterseniz (exe olmadan, kaynaktan calisan):

```bash
powershell -ExecutionPolicy Bypass -File tools\make_shortcut.ps1
```

Betik once `dist\` altinda exe arar; bulamazsa `pythonw.exe` + `.pyw` ile
calisan bir kisayol olusturur, boylece derlemeden de kullanabilirsiniz.

---

## Arayuz

Sol tarafta gruplu bir **kenar cubugu** vardir: Ogren · Laboratuvar · Oku ·
Pratik · Sistem. Bekleyen tekrar sayisi "Aralikli Tekrar" ogesinin yaninda
rozet olarak gorunur. Ust barda profil secici ve LM Studio durum isareti,
altta durum cubugu bulunur.

Ust cubuktaki dil seciciden **Türkçe, English veya Русский** secilebilir.
Secim aninda uygulanir ve bir sonraki acilis icin kaydedilir.

| Kisayol | Islev |
|---|---|
| `Ctrl+1..9` | Ilk dokuz sayfaya dogrudan gec |
| `Ctrl+PgUp` / `Ctrl+PgDn` | Onceki / sonraki sayfa |
| `F5` | Gorunen sayfayi tazele |

Koyu ve acik tema tek bir `THEME` sozlugunden gelir; kartlar, grafikler ve
kenar cubugu harici bir arayuz kutuphanesi olmadan tkinter Canvas ile cizilir.

---

## Bagimliliklar

Cekirdek calisma icin **hicbir harici paket gerekmez** - Python 3.11 standart
kutuphanesi (tkinter, sqlite3, urllib) yeterlidir. Asagidakiler eksikse ilgili
dugmeler gri kalir, program acilmaya ve diger ozellikler calismaya devam eder:

| Paket | Kapatilan ozellik |
|---|---|
| `pymupdf` | PDF goruntuleme, isaretleme, metin secimi |
| `pyttsx3` | Cevrimdisi seslendirme (yedek: Windows System.Speech) |
| `pillow` | El yazisi PNG kaydi, "ne yazdim?" gorsel sorusu |
| `pymorphy3` | Kesin morfoloji etiketleri (yedek: sonek tabanli yaklasik etiketleme) |
| `vosk` + `sounddevice` | Mikrofonla telaffuz karsilastirmasi |
| `truststore` veya `certifi` | Kaynak Merkezi indirmeleri (bkz. asagidaki not) |

Vosk icin ayrica bir Rusca model indirip su klasore acmalisiniz:
`%APPDATA%\RussianCourseAI\models\vosk-ru`

---

## Yapay zeka kurulumu (istege bagli)

1. [LM Studio](https://lmstudio.ai) kurun.
2. Bir model indirin - onerilen: `qwen2.5-7b-instruct`.
   Gorsel/OCR icin ayrica `qwen2-vl-7b-instruct` gibi bir vision modeli.
3. LM Studio icinde **Local Server**'i baslatin (varsayilan `http://127.0.0.1:1234`).
4. Programdaki **AI durumu** dugmesi yesile donunce hazirdir.

Model bulunamazsa ozellik **cokmez**: profiller kurulu modellere karsi cozumlenir,
hicbiri yoksa arayuz sakin bir uyari gosterir ve program calismaya devam eder.

### Sozluk icin alternatif uc (istege bagli, internet)

Sozluk RU-EN sekmesi, yerel sozlukte bulunmayan bir kelimeyi bir yapay zeka
modeline sorar ve yapisal madde (baslik + vurgu, tur, cins/gorunus, ceviri, ornek
cumle, not) olarak alir. Iki saglayici vardir:

| Saglayici | Adres | Anahtar |
|---|---|---|
| **LM Studio** (yerel) | `http://127.0.0.1:1234` | gerekmez |
| **Alternatif uc** | varsayilan NVIDIA NIM `https://integrate.api.nvidia.com/v1`; OpenRouter, Groq, Ollama gibi herhangi bir OpenAI uyumlu adres girilebilir | Ayarlar'da girilir |

- Alternatif uc **varsayilan olarak kapalidir**; yalnizca Ayarlar'dan acikca
  acarsaniz ag cagrisi yapilir.
- API anahtari **Windows Credential Manager**'da saklanir (Windows disinda ayar
  klasorundeki yerel bir dosyada); `settings.json`'a asla yazilmaz. Anahtar
  `RUSSIANCOURSEAI_API_KEY` ortam degiskeniyle de verilebilir.
- **Politika** (`dict_ai` ayari, sozluk arac cubugundan da secilir):
  `auto` = LM Studio ulasilabiliyorsa yerel, degilse alternatif uc;
  `local` = yalnizca LM Studio; `alt` = yalnizca alternatif uc; `off` = sozlukte AI yok.
- AI'dan gelen maddeler varsayilan olarak yerel sozluge (`dict_entries`, kaynak
  `ai`) kaydedilir; bir sonraki arama aninda ve cevrimdisi calisir. Otomatik
  kayit kapaliysa secili madde "Sozluge kaydet" ile tek tek kaydedilir.

---

## Sekmeler

| Sekme | Ne yapar |
|---|---|
| **Kelime Bankasi** | TR<->RU<->EN sozluk, frekans listeleri, gorunus ciftleri, CSV ice/disa aktarim |
| **Sozluk RU-EN** | Cift yonlu Rusca<->Ingilizce sozluk: Kiril yazinca RU->EN, Latin yazinca EN->RU; 1.360 gomulu vurgulu madde, indirilen OpenRussian verisiyle 45.000+ madde; bulunamayan kelime LM Studio'ya ya da alternatif uca sorulur ve yerel sozluge kaydedilir; dinle, kelime bankasina ekle, CSV/TSV ice/disa aktar |
| **Aralikli Tekrar** | "Bugun" panosu + SM-2/Leitner kart oturumu, 5 calisma modu |
| **Sinav** | 9 soru tipi, otomatik puanlama, esdeger cevap toleransi |
| **Kiril Lab** | 33 harf, basili/el yazisi formlari, yazim animasyonu, karisan ciftler |
| **Telaffuz & Vurgu** | Vurgu yeri, редукция kurallari, IPA, TTS, mikrofonla karsilastirma |
| **Dilbilgisi Lab** | Hal / Fiil / Hareket / Sayi / Soz Dizimi + `grammar/*.md` notlari |
| **Kurs Kaynaklari** | `Resources/` agaci, "bitirdim" tiki, arama, yazdirma |
| **PDF Okuyucu** | Zoom, kalem/isaretleme/metin/silgi, Kiril metin secimi, isaretli PDF cikti |
| **Kaynak Merkezi** | Acik lisansli e-kitap / ses / sozluk indirme, lisans gosterimi, sozluk ice aktarma |
| **AI Ogretmen** | Acikla / cevir / duzelt / gorsel-OCR, gorev bazli model yonlendirme |
| **Konusma Pratigi** | CEFR seviyeli rol-yapma senaryolari + oturum sonu hata dokumu |
| **El Yazisi** | Kiril el yazisi tahtasi, PNG kaydi, "ne yazdim?" |
| **Ogrenci Takip** | Ustalik tablosu, zayif konular, sinav trendi, haftalik A4 rapor |
| **Paketler** | `.rupack` (ZIP) disa/ice aktarim, `.json` geriye donuk uyumlu |
| **Token Defteri** | Bugun/7/30/tum zamanlar sayaclari, CSV cikti - **istek metinleri saklanmaz** |
| **Kilavuz** | Her ekrani neden -> nasil -> fayda biciminde anlatan cevrimdisi rehber |
| **Ayarlar** | Dil (TR/EN/RU), tema, hedef, ses, AI adresi, alternatif uc (adres / model / API anahtari / baglanti testi), sozluk AI politikasi, profiller, veri yonetimi |

---

## Kisayollar

| Tus | Islev |
|---|---|
| `Space` | Kelime kartini cevir |
| `1` / `2` / `3` | Bilmiyorum / Emin degilim / Biliyorum |
| `Enter` | Alistirmada cevabi kontrol et |
| `Ctrl+Enter` | AI Ogretmen'de soruyu gonder |
| `Ctrl+1/2/3` | Ilk uc sekmeye gec |
| `F5` | Gorunen sekmeyi tazele |
| `Ctrl+Q` | Programi kapat |
| `Space` (Kaynaklar) | "Bitirdim" isaretini degistir |

---

## CSV bicimi

Kelime Bankasi -> **CSV Ice Aktar** su bicimi okur (noktali virgul veya virgul):

```
kelime;anlam;ornek cumle;deste
молоко;sut;Молоко в холодильнике.;Yiyecek
хлеб;ekmek;Я купил хлеб.;Yiyecek
```

Baslik satiri isteğe baglidir - ilk sutunda Kiril harf yoksa atlanir.
Disa aktarim ayrica `ingilizce` ve `ornek_tr` sutunlarini da yazar.

## Paket bicimi (.rupack)

`.rupack` bir ZIP dosyasidir:

```
paket.json     # {format, version, name, author, words[], questions[]}
audio/         # istege bagli ses dosyalari
images/        # istege bagli gorseller
```

Eski duz `.json` paketleri de dogrudan acilir.

---

## Dosya duzeni

```
Russian_Course_AI.pyw     giris noktasi - yalnizca pencere + sekme kurulumu
rca_common.py             TEK kaynak: baslik, surum, yollar, tema, model varsayilanlari
rca/
  db.py                   SQLite semasi, gocler, repository siniflari
  srs.py                  SM-2 / Leitner  (saf mantik, arayuzden bagimsiz)
  quiz_engine.py          soru uretimi + cevap dogrulama  (saf mantik)
  content.py              gomulu icerik paketleri (alfabe, hal, fiil, hareket, sayi)
  seed_words.py           A1 baslangic destesi
  ai_client.py            OpenAI uyumlu istemci: LM Studio + alternatif uc, saglayici secimi (yalnizca stdlib)
  secrets.py              API anahtari deposu: Windows Credential Manager (ctypes) + dosya yedegi
  tts.py                  seslendirme + konusma tanima sarmalayicilari
  i18n.py                 TR / EN / RU arayuz metinleri + AI sistem yonergeleri
  library.py              acik lisansli kaynak katalogu + indirici + ice aktarici
  ui_util.py              tema, kenar cubugu, yuvarlak kartlar, grafikler, thread kuyrugu
  tabs/                   18 sayfa, her biri tek bir LazyTab sinifi
  dictionary.py           RU<->EN sozluk motoru (gomulu + kullanici + OpenRussian + AI katmanlari)
  dict_data.py            1.360 maddelik gomulu cekirdek sozluk
grammar/*.md              markdown dilbilgisi notlari
assets/app.ico            uygulama simgesi
tools/                    simge ureteci + masaustu kisayolu betigi
build.bat                 exe uretimi + kisayol
Resources/                ders dosyalariniz
Resources/Indirilenler/   Kaynak Merkezinden inen dosyalar + LISANS.txt
tests/                    pytest paketi
PROMPT.md                 bu programi ureten birlestirilmis prompt
KAYNAKLAR.md              kaynak taramasi: lisans dogrulamalari ve elenenler
```

Mimari kurallari:
- Arayuz **asla** dogrudan SQL yazmaz; her erisim repository uzerinden.
- `srs.py` ve `quiz_engine.py` arayuzden tamamen bagimsizdir ve dogrudan test edilir.
- Hicbir modul baska bir modulun ic degiskenine dokunmaz; ortak seyler `rca_common.py`'de.
- Her sekme **tembel yuklenir** - pencere acilisi hizli kalir.
- Uzun islemler thread + kuyruk ile calisir, arayuz kilitlenmez.

---

## Kaynak Merkezi ve lisanslar

**Kaynak Merkezi** sekmesi kuratorlu bir katalog sunar. Katalogda **yalnizca
lisansi acikca dogrulanmis** kaynaklar bulunur: kamu mali (public domain) veya
Creative Commons. Lisansi belirsiz hicbir sey listeye girmez ve program telifli
materyal indirmez. Bu kural bir testle zorlanir
(`tests/test_library.py::test_every_resource_has_a_known_open_license`).

Indirilen her dosyanin yanina, kaynagi ve lisansiyla birlikte bir `LISANS.txt`
yazilir. CC BY-SA kaynaklarini yeniden dagitirken ayni lisansi korumaniz gerekir.

Katalogdaki kaynaklar:

| Kaynak | Tur | Lisans |
|---|---|---|
| FSI Russian FAST - ogrenci kitaplari (Ders 1-5 / 6-8 / 9-11, tarama + OCR) | E-kitap | Kamu mali (ABD devlet eseri) |
| FSI Russian FAST - 8 kaset + ek ses (~125 MB) | Ses | Public Domain Mark 1.0 |
| OpenRussian - isim / fiil / sifat / diger (cekim tablolariyla) | Sozluk verisi | CC BY-SA 4.0 |
| Tatoeba - Rusca cumle derlemi | Derlem | CC BY 2.0 FR |
| Между нами (MSU), Sputnik, LLC Commons, OER Commons, Wikibooks Russian | Web kursu | CC (kaynaga gore) |
| LibriVox Rusca sesli kitaplar, Project Gutenberg Rusca metinler | Okuma / dinleme | Kamu mali |
| Open Culture ders listesi, FSI Language Courses | Video / kurs | CC / kamu mali |

Her kaynagin nereden geldigi, lisansinin nerede dogrulandigi ve hangi adaylarin
neden ELENDIGI [KAYNAKLAR.md](KAYNAKLAR.md) dosyasinda yazilidir.

Depoda `Resources/Indirilenler/` altinda bir baslangic seti hazir gelir
(FSI kitaplari, bir ses kaseti, OpenRussian sozlukleri, Tatoeba derlemi - ~65 MB).
Kalanlari sekmeden tek tikla indirebilirsiniz.

### OpenRussian sozlugunu kelime bankasina aktarma

OpenRussian dosyalari **siklik sirasindadir**. Kaynak Merkezinde indirilmis bir
sozluk dosyasini secip "Aktar" derseniz en sik N kelime bankaya eklenir; vurgu
konumu kaynaktaki isaretlemeden cozulur, isimlerde cinsiyet ve hal ozeti, fiillerde
cekim ozeti ornek alanina yazilir.

Dikkat: bu verideki **ceviriler Ingilizcedir**. Turkce alani varsayilan olarak
Ingilizce ile doldurulur ki kartlar hemen calissin; sonradan duzenleyebilirsiniz.

---

## Testler

```bash
python -m pytest tests -q
```

137 test: SM-2 aralik hesabi, RU<->EN sozluk motoru (veri butunlugu, iki yonlu arama, ice/disa aktarim), AI sozluk katmani (sahte OpenAI uyumlu sunucuyla yapisal sorgu, anahtar basligi, saglayici secimi, gizli anahtar deposu, sema gocu), cevap dogrulama ve harf-harf karsilastirma, veritabani
repositoryleri, metin normalizasyonu (ё / vurgu), gomulu icerik tutarliligi,
uc dilli metin butunlugu, kaynak katalogunun lisans butunlugu, OpenRussian ice aktaricisi ve pencere/sayfa duman testi.
Testler gercek aga, LM Studio'ya ya da Credential Manager'a dokunmaz.

---

## Gizlilik

- Hicbir veri makineden cikmaz; bulut, hesap veya internet gerekmez.
- AI yerelde calisir; modele yalnizca sectiginiz metin gonderilir.
- Token defteri **yalnizca sayaclari** tutar - istek metinleri kaydedilmez.
- Alternatif ucun API anahtari Windows Credential Manager'da tutulur (Windows disinda
  ayar klasorundeki yerel dosyada); `settings.json`'a asla yazilmaz.
- Ag cagrisi yalnizca alternatif AI ucunu (NVIDIA NIM ya da baska bir OpenAI uyumlu
  adres) Ayarlar'dan acikca acarsaniz ya da Kaynak Merkezi'nden indirme yaparsaniz yapilir.
- Kullanici verisi tek yerde: `%APPDATA%\RussianCourseAI` (`data/`, `settings/`,
  `exports/`, `logs/`). Yedeklemek icin bu klasoru kopyalamak yeterlidir.

---

## Baska bir dile uyarlama

`rca_common.py` icindeki `TARGET_LANG` / `TARGET_LANG_NAME` sabitleri tek degistirme
noktasidir. Ardindan `rca/seed_words.py` icindeki desteyi ve `rca/content.py` icindeki
icerik paketlerini hedef dile gore doldurun; arayuz, aralikli tekrar, sinav motoru ve
istatistik katmanlari dilden bagimsiz calisir.
