# Üçüncü Taraf Bildirimleri / Third-Party Notices

**Russian Course AI** kendi kaynak kodu için MIT lisanslıdır (bkz. [`LICENSE`](LICENSE)).
Bu dosya, programın kullandığı veya dağıtılan ikili paketlere (`.exe` / `.app`) gömülen
üçüncü taraf bileşenlerini, gerçek lisanslarıyla birlikte listeler.

Her lisans, sabitlenen sürümün **yayımcı meta verisinden** doğrulanmıştır: paket kurulu
olduğunda `importlib.metadata` ile okunan `License` / `License-Expression` alanından ve
paketle gelen lisans dosyalarından, kurulu olmadığında ise PyPI'ın aynı sürüm için
yayımladığı meta veriden. Kurulu paketler için bu doğrulama tekrar edilebilir:
`tests/test_licenses.py` her satırı kurulu dağıtımın meta verisiyle karşılaştırır ve
kurulu olmayan paketleri atlar (`python -m pytest tests/test_licenses.py -v` çıktısı
hangi satırın gerçekten doğrulandığını, hangisinin atlandığını gösterir).

> **Not.** Programın çekirdeği hiçbir harici pakete ihtiyaç duymaz; aşağıdakilerin
> tamamı isteğe bağlıdır. Kurulu olmayan bir paket yalnızca ilgili düğmeleri devre dışı
> bırakır. Bir bileşeni ikili pakete gömmek istemiyorsanız, derlemeden önce onu
> kurmamanız (veya PyInstaller'dan hariç tutmanız) yeterlidir.

---

## 1. İzin verici (permissive) lisanslar — MIT / BSD / Apache-2.0 / PSF

Bu grupta yalnızca telif ve lisans metnini koruma yükümlülüğü vardır; MIT lisanslı bir
proje bunları sorunsuz dağıtabilir.

| Bileşen | Sürüm | Lisans | Ne için kullanılır |
|---|---|---|---|
| [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) | 5.13.0 | Apache-2.0 **VEYA** BSD-3-Clause (paketin kendi kodu; belgeleri CC-BY-4.0) | PDF Okuyucu: sayfa çizimi, sayfa ölçüsü ve metin/karakter kutuları |
| [pypdf](https://github.com/py-pdf/pypdf) | 6.13.2 | BSD-3-Clause | İşaretlemeleri gömülü "işaretli PDF" kopyasını yazmak |
| [Pillow](https://python-pillow.org) | 10.4.0 | HPND (Pillow 10.x meta verisi; 12.x aynı metni MIT-CMU olarak adlandırır) | Simge üretimi, el yazısı PNG kaydı, çizilen sayfanın PPM'e çevrilmesi |
| [pymorphy3](https://github.com/no-plagiarism/pymorphy3) | 2.0.2 | MIT | Rusça morfoloji etiketleri (hâl, görünüş, şahıs) |
| [DAWG-Python](https://github.com/pymorphy2-fork/DAWG-Python) | ≥ 0.7.1 | MIT | pymorphy3'ün sözlük dosyalarını okuyan zorunlu bağımlılığı |
| [Vosk](https://github.com/alphacep/vosk-api) | 0.3.45 | Apache-2.0 | Çevrimdışı konuşma tanıma (telaffuz karşılaştırması) |
| [sounddevice](https://github.com/spatialaudio/python-sounddevice) | 0.5.0 | MIT | Mikrofon kaydı (PortAudio bağlaması) |
| [PortAudio](https://www.portaudio.com) | sounddevice ile gömülü (`libportaudio64bit.dll`) | MIT | Platformlar arası ses giriş/çıkışı |
| [CFFI](https://cffi.readthedocs.io) | sounddevice/vosk ile gelir | MIT | Yerel kütüphane bağlaması |
| [truststore](https://github.com/sethmlarson/truststore) | 0.10.4 | MIT | Kaynak Merkezi indirmelerinde işletim sistemi kök sertifika deposunu kullanmak |
| [pytest](https://pytest.org) | 8.3.3 | MIT | Yalnızca geliştirme/test; ikili pakete **girmez** (`--exclude-module pytest`) |
| [CPython](https://www.python.org) + standart kütüphane (tkinter, sqlite3, urllib) | 3.11 | Python Software Foundation License 2.0 | Çalışma zamanı; PyInstaller tarafından ikili pakete gömülür |
| [Tcl/Tk](https://www.tcl-lang.org) | CPython ile gelir | Tcl/Tk lisansı (BSD tarzı) | tkinter arayüzünün altyapısı; ikili pakete gömülür |
| [SQLite](https://sqlite.org) | CPython ile gelir | Kamu malı (public domain) | Yerel çalışma verisi |

### pypdfium2'nin gömdüğü yerel kütüphane

pypdfium2, Google'ın **PDFium** motorunu önceden derlenmiş `pdfium.dll` / `libpdfium`
olarak taşır. Bu ikili dosyanın içindeki bileşenlerin lisansları paketle birlikte
`pypdfium2-<sürüm>.dist-info/licenses/data/.../BUILD_LICENSES/` altında dağıtılır:

| Bileşen | Lisans |
|---|---|
| PDFium | BSD-3-Clause (Copyright 2014 The PDFium Authors) |
| pdfium-binaries derleme betikleri | MIT (Copyright 2014-2025 Benoit Blanchon) |
| FreeType | FreeType Project License (BSD tarzı) |
| ICU | Unicode License v3 |
| Little CMS (lcms) | MIT |
| libjpeg-turbo | IJG + BSD tarzı iki uyumlu lisans |
| OpenJPEG | BSD-2-Clause |
| libpng | PNG Reference Library License v2 |
| libtiff | libtiff (BSD tarzı) lisansı |
| zlib | zlib lisansı |
| Abseil | Apache-2.0 |
| LLVM libc | Apache-2.0 with LLVM Exceptions |
| simdutf | MIT (paketle gelen lisans metni) |
| fast_float | MIT |
| AGG 2.3 | Anti-Grain Geometry 2.3 lisansı (izin verici: telif bildirimi korunmak koşuluyla kopyalama/değiştirme/satma serbest) |

**Yükümlülük:** Bu lisansların tamamı yalnızca telif/lisans bildiriminin korunmasını
ister. `pypdfium2` paketi bu metinleri kendi içinde taşıdığı için, paketi olduğu gibi
dağıtmak yükümlülüğü karşılar.

### Vosk'un gömdüğü yerel kütüphaneler

Vosk tekerleği `libvosk.dll` ile birlikte MinGW-w64 çalışma zamanı kitaplıklarını
(`libgcc_s_seh-1.dll`, `libstdc++-6.dll`, `libwinpthread-1.dll`) taşır. GCC çalışma
zamanı kitaplıkları **GPL-3.0 + GCC Runtime Library Exception** ile dağıtılır; bu
istisna, kitaplığın kapalı veya farklı lisanslı programlarla bağlanmasına açıkça izin
verir. Vosk kurulu değilse bu dosyaların hiçbiri ikili pakete girmez.

---

## 2. Copyleft — dikkat gerektirenler

| Bileşen | Sürüm | Lisans | Ne için kullanılır |
|---|---|---|---|
| [pyttsx3](https://github.com/nateshmbhat/pyttsx3) | 2.90 (artık `requirements.txt`'te **sabitlenmez**) | **GPL-3.0** (paketin içindeki `LICENSE` dosyası GNU GPL v3 metnidir; PyPI sınıflandırıcısı da GPLv3 der) | İsteğe bağlı seslendirme sarmalayıcısı — **dağıtılan pakete GİRMEZ** |
| [certifi](https://github.com/certifi/python-certifi) | 2026.5.20 | **MPL-2.0** | Kaynak Merkezi indirmelerinde yedek kök sertifika deposu |

**pyttsx3 hakkında.** Bu depo MIT lisanslıdır ve MIT kaynak kodunu GPL'li bir kitaplıkla
birlikte kullanmak serbesttir; ancak **ikisini tek bir çalıştırılabilir dosyada
birleştirip dağıtırsanız**, o birleşik ikili paketin GPL-3.0 koşullarına uyması gerekir
(kaynak kodun sunulması dâhil). Depo kaynağının MIT kalması etkilenmez.

Bu yüzden pyttsx3 dağıtılan `.exe` / `.app` paketlerinin **dışında tutulur**; bu, iki
yerde birden zorlanır:

1. `requirements.txt` pyttsx3'ü kurmaz (yalnızca yorum satırında anlatır), bu yüzden
   `build_macos.sh`'in kurduğu ortamda paket bulunmaz;
2. `build.bat` ve `build_macos.sh` PyInstaller'a `--exclude-module pyttsx3` verir, yani
   derleme makinesinde paket ayrıca kurulu olsa bile pakete alınmaz;
3. her iki betik de (ve macOS iş akışı, yüklemeden hemen önce)
   `tools/check_build_licence.py` ile üretilen paketin baytlarını tarar. Pakette
   pyttsx3'ün ya da kaldırılmış AGPL PDF katmanının izi bulunursa derleme
   **başarısız olur** — böylece eski bir `dist/` ağacı yanlışlıkla yayımlanamaz.

Seslendirme bu durumda işletim sisteminin kendi motoruyla yapılır: Windows'ta
`System.Speech` (PowerShell), macOS'ta yerleşik `say` komutu (bkz. `rca/tts.py`).
pyttsx3'ü kendi makinenize kurarsanız program onu kullanır — ama o zaman ürettiğiniz
ikili paketi **MIT değil GPL-3.0** koşullarıyla dağıtmanız gerekir.

**certifi hakkında.** MPL-2.0 dosya bazlı bir copyleft'tir: yalnızca certifi'nin kendi
dosyalarında yaptığınız **değişiklikler** aynı lisansla paylaşılmak zorundadır. Paketi
değiştirmeden kullanmak/dağıtmak, MPL-2.0 metnini ve kaynağının nereden alınabileceğini
belirtmek dışında bir yükümlülük getirmez. Bu depo certifi'yi değiştirmez.

---

## 3. Veri lisansları

| Bileşen | Lisans | Not |
|---|---|---|
| [pymorphy3-dicts-ru](https://github.com/no-plagiarism/pymorphy3-dicts) 2.4.417150.4580142 | Python kodu **MIT**; **sözlük verisi CC BY-SA 3.0** (OpenCorpora'dan türetilmiştir) | Sözlük verisini yeniden dağıtırken atıf zorunlu ve türetilmiş veri aynı lisansla paylaşılmalıdır. Program bu veriyi değiştirmez, paketi olduğu gibi kullanır. |

---

## 4. Paketleme aracı

| Bileşen | Sürüm | Lisans |
|---|---|---|
| [PyInstaller](https://pyinstaller.org) | 6.10.0+ | **GPL-2.0-or-later WITH bootloader istisnası** |

PyInstaller'ın kendi meta verisi lisansını şöyle tanımlar: "GPLv2-or-later with a special
exception which allows to use PyInstaller to build and distribute non-free programs
(including commercial ones)". Bu istisna sayesinde PyInstaller ile üretilen **dondurulmuş
uygulama** istediğiniz lisansla (burada MIT) dağıtılabilir; GPL yalnızca PyInstaller'ın
kendi kaynak kodunu ve değiştirilmiş bootloader'ları bağlar. PyInstaller yalnızca bir
derleme aracıdır, uygulamanın kaynak koduna karışmaz.

---

## 5. Çalışma zamanında indirilen materyal (depoya dâhil DEĞİLDİR)

**Kaynak Merkezi** sayfası, yalnızca lisansı açıkça doğrulanmış açık materyali listeler ve
kullanıcı istediğinde indirir. İndirilen hiçbir dosya bu depoda veya ikili pakette
bulunmaz; her dosya kendi lisansını korur ve yanına o lisansı yazan bir `LISANS.txt`
kaydedilir. Katalog `rca/library.py` içindedir ve lisans bütünlüğü
`tests/test_library.py::test_every_resource_has_a_known_open_license` ile zorlanır.

| Kaynak | Sağlayıcı | Lisans |
|---|---|---|
| FSI Russian FAST ders kitapları ve sesleri | US Foreign Service Institute | Kamu malı (ABD devlet eseri) / Public Domain Mark 1.0 |
| OpenRussian sözlük verisi (isim / fiil / sıfat / diğer) | OpenRussian.org | CC BY-SA 4.0 |
| Wikibooks - Russian | Wikibooks | CC BY-SA 4.0 |
| Tatoeba Rusça cümle derlemi | Tatoeba | CC BY 2.0 FR (bazı cümleler CC0) |
| LibriVox sesli kitaplar, Project Gutenberg metinleri | LibriVox / Project Gutenberg | Public Domain Mark 1.0 |
| Между нами, LLC Commons, Sputnik, OER Commons, Open Culture | çeşitli | Creative Commons - her materyalin lisansı kendi sayfasında belirtilir |

**Yükümlülük:** CC BY-SA materyalini yeniden dağıtırken atıf vermeniz ve türetilmiş eseri
aynı lisansla paylaşmanız gerekir. Program bu materyali kendi sürümüne gömmez.

Ayrıca Vosk'un Rusça konuşma tanıma modeli (`vosk-ru`) kullanıcı tarafından ayrıca
indirilir, uygulama veri klasörüne (`%APPDATA%\RussianCourseAI\models\vosk-ru`) açılır ve
depoya dâhil edilmez; modelin lisansı Vosk projesinin model sayfasında belirtilmiştir.

---

## 6. Yapay zekâ uçları

Program hiçbir model ağırlığını içermez ve varsayılan olarak modelleri yerelde
([LM Studio](https://lmstudio.ai)) çalıştırır. LM Studio, indirdiğiniz model dosyaları ve
isteğe bağlı alternatif OpenAI uyumlu uç noktalar (varsayılan öneri: NVIDIA NIM) bu
deponun parçası değildir ve kendi koşullarına tabidir.

---

## Kaldırılan bağımlılık

1.2.1 sürümüne kadar PDF sayfası **PyMuPDF** ile çiziliyordu. PyMuPDF ve gömdüğü MuPDF
kitaplığı AGPL-3.0 / ticari çift lisanslıdır; AGPL, dondurulmuş `.exe` içine giren yerel
kitaplık nedeniyle projenin MIT olarak yayımlanmasını engelliyordu. Bu yüzden görüntüleme
ve metin **pypdfium2**'ye (Apache-2.0 / BSD-3-Clause), işaretli PDF yazımı ise
**pypdf**'e (BSD-3-Clause) taşındı. Depoda artık AGPL lisanslı hiçbir bileşen yoktur.
