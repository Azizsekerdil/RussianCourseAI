# Russian Course AI — Kullanım Kılavuzu

Sürüm 1.3.0 · Windows ve macOS masaüstü uygulaması · Arayüz dilleri: Türkçe / English / Русский

- [1. Bu kılavuz hakkında](#1-bu-kılavuz-hakkında)
- [2. Kurulum](#2-kurulum)
- [3. Programın ilk açılışı](#3-programın-ilk-açılışı)
- [4. Ekranlar](#4-ekranlar)
- [5. Sözlük (ayrıntılı)](#5-sözlük-ayrıntılı)
- [6. Yapay zeka](#6-yapay-zeka)
- [7. Veri yönetimi](#7-veri-yönetimi)
- [8. Kısayollar ve ipuçları](#8-kısayollar-ve-ipuçları)
- [9. Sorun giderme](#9-sorun-giderme)
- [10. Sürüm notları özeti](#10-sürüm-notları-özeti)
- [11. Sık sorulan sorular](#11-sık-sorulan-sorular)
- [12. Lisans](#12-lisans)

---

## 1. Bu kılavuz hakkında

Bu belge **Russian Course AI 1.3.0** sürümünün kullanım kılavuzudur. Program, Rusçayı A1'den C1'e çalışmak için tasarlanmış, tek pencerede 18 sayfa barındıran bir masaüstü çalışma istasyonudur.

Nasıl okunur: **yeni başlıyorsanız** 2. ve 3. bölümü, sonra 4. bölümdeki `Aralikli Tekrar`, `Kelime Bankasi` ve `Sozluk RU-EN-TR` sayfalarını okuyun — program yapay zekâ olmadan da tam kapasite çalışır. **Sözlüğü yoğun kullanacaksanız** doğrudan 5. bölüme geçin. **Yapay zekâyı bağlayacaksanız** 6. bölüme bakın.

**Yazım notu.** Anlatım dili tam Türkçedir; `kod biçiminde` yazılmış etiketler ise ekranda **göründüğü gibi** aktarılmıştır. Arayüzün Türkçe metinlerinin çoğu şu an aksansız harflerle görüntülenir (`Kelime Bankasi`, `Sozluk RU-EN-TR`, `Ogrenci Takip`); düğmeleri ararken bu yazımı esas alın.

---

## 2. Kurulum

### 2.1 Windows (zip)

1. Sürüm arşivindeki Windows zip dosyasını indirin.
2. Zip'i bir klasöre **tam olarak** açın.
3. **`RussianCourseAI.exe`** dosyasını çift tıklayın.

Kurulum gerekmez: yönetici hakkı, kayıt defteri girdisi ve kaldırma işlemi yoktur; klasörü silmeniz yeterlidir (verileriniz ayrı klasörde durur, bkz. 2.4). Kendi exe'nizi üretmek isterseniz depo kökünde `build.bat` çalıştırın; `build.bat /onedir` tek dosya yerine belirgin biçimde daha hızlı açılan bir klasör üretir.

### 2.2 macOS (zip)

macOS paketi Apple Silicon için üretilir ve **notarize edilmemiştir**; ilk açılışta Gatekeeper uyarısı görürsünüz.

1. `RussianCourseAI-macOS.zip` dosyasını açın.
2. `RussianCourseAI.app` uygulamasını `Uygulamalar` klasörüne taşıyın.
3. Çift tıklamak yerine **sağ tıklayın → Aç**, çıkan uyarıda yine **Aç**'a basın.

Bu onayı bir kez vermeniz yeterlidir. Kendi paketinizi bir Mac üzerinde `./build_macos.sh` ile üretebilirsiniz.

### 2.3 Kaynaktan çalıştırma

Python 3.11 veya üzeri yeterlidir:

```bash
python Russian_Course_AI.pyw
```

Çekirdek için harici paket gerekmez (tkinter, sqlite3, urllib). İsteğe bağlı özellikler için:

```bash
pip install -r requirements.txt
```

Eksik paket programı durdurmaz, yalnızca ilgili düğmeler gri kalır: `pypdfium2` + `pypdf` (PDF), `pillow` (el yazısı PNG ve görsel soru), `pymorphy3` (kesin morfoloji), `vosk` + `sounddevice` (mikrofonla telaffuz), `truststore` / `certifi` (Kaynak Merkezi indirmeleri).

### 2.4 Verileriniz nerede tutulur

| Sistem | Veri klasörü |
|---|---|
| Windows | `%APPDATA%\RussianCourseAI` |
| macOS | `~/Library/Application Support/RussianCourseAI` |
| Linux | `~/.russiancourseai` |

İçerik: `data/rca.db` (SQLite), `settings/settings.json`, `exports/` (dışa aktarımların varsayılan hedefi), `logs/`. Program dizininde ise salt okunur `grammar/` klasörü bulunur; ders dosyalarının tutulduğu `Resources/` de program dizinindedir — yalnız macOS'ta, imzalı `.app` paketinin içine yazılamayacağı için veri klasörünün altındadır.

**Taşınabilir kullanım.** `RCA_HOME` ortam değişkeni tanımlıysa program veri klasörü olarak onu kullanır:

```bat
set RCA_HOME=E:\RussianCourseAI-veri
RussianCourseAI.exe
```

---

## 3. Programın ilk açılışı

Kurulum sihirbazı yoktur. Program ilk açılışta veri klasörlerini oluşturur, SQLite şemasını kurar, gömülü **A1 destesini** yükler (9 destede 125 kelime: `A1 Temel`, `Gunluk Hayat`, `Yiyecek`, `Fiiller`, `Hareket Fiilleri`, `Sifatlar`, `Sayilar`, `Zamirler`, `Edatlar`), `Ogrenci` adlı bir profil açar ve 1.360 maddelik vurgu işaretli, Türkçe karşılıklı gömülü sözlüğü belleğe alır.

Pencerede solda gruplu kenar çubuğu, üstte profil seçici, dil seçici ve yapay zekâ durum rozeti, altta veri klasörünün yolunu gösteren durum çubuğu vardır.

| Ayar | Varsayılan | Nerede |
|---|---|---|
| Arayüz dili | `Türkçe` | Üst çubuktaki 🌐 seçici (anında uygulanır) veya `Ayarlar` → `Dil:` |
| Tema | `dark` | `Ayarlar` → `Tema:` (`dark` / `light`) |
| Günlük hedef | `20` kelime/gün | `Ayarlar` → `Gunluk hedef:` |
| CEFR seviyesi | `A1` | `Ayarlar` → `CEFR seviyesi:` (A1–C1) |

Dil değişikliği anında uygulanır; tema değişikliğinin her yere işlemesi için program yeniden başlatılmalıdır ve `Ayarlar` bunu kaydettiğinizde hatırlatır.

**Profil.** Üst çubuktaki listeden profil seçilir, `+` düğmesi yeni profil açar. Tekrar geçmişi, sınavlar ve istatistikler profile özeldir; kelime bankası ve sözlük tüm profillerde ortaktır.

---

## 4. Ekranlar

Aşağıdaki sıra kenar çubuğunun kendi sırasıdır.

### 4.1 Öğren (`Ogren`)

#### Aralıklı Tekrar (`Aralikli Tekrar`)

**Ne işe yarar.** Günlük tekrar merkezi; SM-2 / Leitner algoritması her kelimenin bir sonraki tekrar gününü kendisi hesaplar ve pano yapay zekâ çağırmaz.

**Nasıl kullanılır.** `Bugun` panosundaki altı karta bakın (`Bugun tekrar edilecek`, `Yanlislar`, `Denenmemis`, `Ogrenildi`, `Seri`, `Dogruluk`). `Mod` listesinden biçimi seçin (`Kart`, `Coktan secmeli`, `Yazarak`, `Dinleme`, `Eslestirme`), `Adet` ile uzunluğu belirleyin, sonra `▶ Tekrar`, `✗ Yanlis drill`, `✚ Yeni kelime` ya da `★ Favoriler`'e basın. `Kart` modunda **Space** çevirir, **1 / 2 / 3** değerlendirir; `Yazarak` ve `Dinleme` modlarında cevabı yazıp **Enter**'a (ya da `Kontrol Et`'e) basın; `Coktan secmeli` ve `Eslestirme` modlarında doğru seçeneğe tıklayın.

**İpucu.** Kenar çubuğundaki rozet bekleyen tekrar sayısını gösterir; boşsa o gün bitmiştir.

#### Kelime Bankası (`Kelime Bankasi`)

**Ne işe yarar.** Öğrendiğiniz kelimelerin kalıcı deposu; tekrar, sınav ve istatistik sayfaları buradan beslenir.

**Nasıl kullanılır.** Kutuya Türkçe, Rusça veya İngilizce yazıp `Ara`'ya basın; `Deste` ve `Frekans` (`hepsi`, `ilk 100`, `ilk 500`, `ilk 1000`) ile daraltın. Kelimeye **çift tıklayarak** dinleyin; sağ panelde IPA, örnek cümle, görünüş çifti ve istatistik görünür. Düğmeler: `🔊 Dinle`, `★ Favori`, `AI'a sor`, `Sil`, `+ Ekle`, `CSV Ice Aktar`, `CSV Disa Aktar`.

**İpucu.** İçe aktarma biçimi `kelime;anlam;ornek;deste`, başlık satırı isteğe bağlıdır.

#### Sözlük RU-EN-TR (`Sozluk RU-EN-TR`)

**Ne işe yarar.** Kelime bankası yalnızca sizin kelimelerinizi tutar; bu sayfa okurken karşılaştığınız **her** kelime için üç dilli sözlüktür. Ayrıntı: [5. bölüm](#5-sözlük-ayrıntılı).

#### Sınav (`Sinav`)

**Ne işe yarar.** Tanıma ile üretme farklı becerilerdir; sınav ikincisini ölçer.

**Nasıl kullanılır.** `Sinav kur` kutusunda soru tiplerini işaretleyin: `Coktan secmeli (RU->TR)`, `Coktan secmeli (TR->RU)`, `Bosluk doldurma`, `Dogru hali sec`, `Fiili cek`, `Ceviri TR->RU`, `Ceviri RU->TR`, `Dinleme`, `Kelime dikte`. `Soru sayisi:` (5–60) ve `Kaynak:` (`Karisik`, `Vakti gelenler`, `Yanlislar`, `Yeni kelimeler`) seçip `▶ Basla`'ya basın; cevabı **Enter** ile onaylayın. Program eşdeğer çevirileri tolere eder, kararsız kalınca `Dogru say` / `Yanlis say` / `Yine de dogru say` sunar.

**İpucu.** Yanlış yaptığınız kelime bankada "yanlış" işaretlenir ve `Yanlis drill` kuyruğuna girer.

### 4.2 Laboratuvar (`Laboratuvar`)

#### Kiril Lab (`Kiril Lab`)

**Ne işe yarar.** Rusçadaki ilk duvar alfabedir; el yazısı (курсив) basılı harflere benzemez.

**Nasıl kullanılır.** Dört sekme: `Alfabe (33 harf)`, `Yazim / El yazisi`, `Karisan ciftler`, `Alistirma`. Yazım sekmesinde harfi seçip `▶ Yazim sirasini oynat`'a basın, tuvale kendiniz yazın, `Karsilastir`'a tıklayın; `Tuvali temizle` sıfırlar. Alıştırmada `▶ 12 soruluk tur baslat` deyin.

**İpucu.** `Karisan ciftler` sekmesi ш/щ, б/в, и/й, ь/ъ çiftlerini yan yana gösterir.

#### Telaffuz & Vurgu (`Telaffuz & Vurgu`)

**Ne işe yarar.** Rusçada vurgunun yeri anlamı değiştirir ve vurgusuz `о` [a] okunur.

**Nasıl kullanılır.** Kelimeyi yazıp `Coz`'e basın ya da `Bankadan sec` ile seçin; program heceleri, kaba IPA okunuşunu ve indirgeme kurallarını gösterir. `Vurgulu hece:` listesinden vurguyu düzeltin, `🔊 Dinle` ile seslendirin. Vosk modeli kuruluysa `● Kaydet ve karsilastir` çıkar.

**İpucu.** Mikrofon bölümü kapalıysa nedeni orada yazar; Vosk `ru` modelini `%APPDATA%\RussianCourseAI\models\vosk-ru` klasörüne açın.

#### Dilbilgisi Lab (`Dilbilgisi Lab`)

**Ne işe yarar.** Hâl, görünüş ve hareket fiilleri Türkçe konuşan biri için Rusçanın en zor üç bölgesidir.

**Nasıl kullanılır.** Altı sekme: `Notlar (.md)`, `Hal Lab (Падежи)`, `Fiil Lab (Вид)`, `Hareket Fiilleri`, `Sayi & Olcu`, `Soz Dizimi`. Her lab kural → tablo → canlı örnek → alıştırma akışını izler; sayfa altındaki `▶ 10 soruluk tur baslat` ile deneyin, `Soz Dizimi`'nde cümle yazıp `Ayristir`'a basın.

**İpucu.** `Notlar (.md)` sekmesi `grammar/*.md` dosyalarını okur; kendi notlarınızı oraya ekleyebilirsiniz.

### 4.3 Oku (`Oku`)

#### Kurs Kaynakları (`Kurs Kaynaklari`)

**Ne işe yarar.** Ders dosyalarınızı ağaç görünümünde listeler ve hangilerini bitirdiğinizi takip eder.

**Nasıl kullanılır.** `Kok klasor:` varsayılan olarak `Resources` klasörüdür; `Degistir` ile başkasını seçin, arama kutusuna yazdıkça liste süzülür. Dosyayı seçip **Space**'e basmak ya da `☐/☑ Bitirdim (Space)` işareti değiştirir. Diğer düğmeler: `PDF Okuyucuda ac`, `Varsayilan programda ac`, `Klasoru goster`, `Yazdir`.

**İpucu.** İşaretler profile göre saklanır.

#### PDF Okuyucu (`PDF Okuyucu`)

**Ne işe yarar.** Ders kitabını programdan çıkmadan okumanızı, işaretlemenizi ve seçtiğiniz parçayı yapay zekâya sormanızı sağlar.

**Nasıl kullanılır.** `📂 PDF ac` ile dosyayı açın; `◀` / `▶`, `Git...`, `−` / `+` ve `Genislige sigdir` ile gezinin. Araçlar: `✏ Kalem`, `🖍 Isaretleme`, `🔤 Metin`, `🧽 Silgi`, `⬚ Metin sec`. Metin seçince sağ panelden `AI'a acikla`, `Sozlukte ara`, `🔊` veya `Bankaya ekle` deyin. `Sayfa notu` yazıp `Notlari kaydet`'e basın; `Isaretli PDF disa aktar` işaretleri gömülü yeni bir PDF yazar, `Sayfayi temizle` o sayfayı sıfırlar.

**İpucu.** Bu sayfa `pypdfium2` (görüntüleme/metin) ve `pypdf` (işaretli dışa aktarma) gerektirir; seçtiğiniz metni `AI Ogretmen` sayfasında `PDF'teki secimi al` ile de kullanabilirsiniz.

**Not metinlerinde Kiril ve Türkçe harfler.** `Isaretli PDF disa aktar` çıktısında notunuzun **tam metni her zaman korunur** ve PDF okuyucunuzun yorum/açıklama panelinde eksiksiz görünür. Sayfanın **üzerine çizilen** kopya ise gömülü Helvetica yazı tipiyle yazıldığı için yalnızca Batı Avrupa harflerini gösterebilir: Kiril harfleri ile `ı`, `ş`, `ğ`, `İ` gibi Türkçe harfler sayfa üzerinde `?` görünür. Kiril not alacaksanız notu yorum panelinden okuyun; işaretleme, kalem çizimi ve sarı vurgular bundan etkilenmez.

#### Kaynak Merkezi (`Kaynak Merkezi`)

**Ne işe yarar.** Yalnızca açık lisanslı (kamu malı veya Creative Commons) materyali listeler ve indirir; lisansı belirsiz hiçbir şey kataloğa girmez.

**Nasıl kullanılır.** Tür süzgecinden `Tumu`, `E-kitap`, `Ses`, `Sozluk / veri`, `Web` ya da `Video` seçin. Sağ panelde sağlayıcı, lisans ve atıf zorunluluğu yazar. `Indir`'e basın; dosya `Resources/Indirilenler` altına, yanında `LISANS.txt` ile iner. İndirilmiş bir PDF'i `📕 PDF Okuyucuda ac` ile açar, bir OpenRussian sözlüğünü `Aktar` ile kelime bankasına alırsınız.

**İpucu.** Sözlüğün OpenRussian katmanı için gereken dosyalar `Sozluk / veri` türünden indirilir.

### 4.4 Pratik (`Pratik`)

#### AI Öğretmen (`AI Ogretmen`)

**Ne işe yarar.** Bir cümlenin *neden* yanlış olduğunu soracağınız, bilgisayarınızda çalışan öğretmen.

**Nasıl kullanılır.** `Gorev:` listesinden seçin: `Dilbilgisi acikla`, `Ceviri RU -> TR`, `Ceviri TR -> RU`, `Yazi duzelt`, `Serbest soru`. `Model:` varsayılan `(otomatik)`'tir; `Modelleri tara` ile elle de seçebilirsiniz. Metni yazıp **Ctrl+Enter**'a ya da `▶ Sor`'a basın; yanıtı `🔊 Yaniti oku` ile dinleyin, `Temizle` ile alanı boşaltın. Görme modeli kuruluysa `🖼 Gorsel / OCR` resim okutur.

**İpucu.** `Yazi duzelt` yanıtı sabit düzendedir: HATA / KURAL / DOGRU / NEDEN.

#### Konuşma Pratiği (`Konusma Pratigi`)

**Ne işe yarar.** CEFR seviyenize kilitlenmiş rol yapma diyaloglarıyla konuşma pratiği yaptırır.

**Nasıl kullanılır.** `Senaryo:` listesinden birini seçin (`Kafede siparis`, `Otel resepsiyonu`, `Doktorda`, `Magazada alisveris`, `Yol sormak`, `Is gorusmesi`, `Tanisma`, `Telefonda randevu`), `Seviye:` kutusundan A1–C1 seçin, `▶ Oturumu baslat`'a basın. Rusça yazıp `Gonder`'e basın; bitirince `⏹ Bitir ve rapor al` deyin.

**İpucu.** Oturum sonu raporu hata dökümünü ve öğrenmeniz gereken 5 kelimeyi verir.

#### El Yazısı (`El Yazisi`)

**Ne işe yarar.** Kiril el yazısı kas hafızası ister; bu tahta onu çalışmak içindir.

**Nasıl kullanılır.** `Kalem:` kaydırıcısıyla kalınlığı, `Renk:` listesinden rengi ayarlayın; `Kilavuz:` listesinden bir harf seçerseniz arkada soluk şablon belirir. Kalemle ya da fareyle yazın; `Geri al`, `Temizle` ve `PNG kaydet` hazırdır, `🤖 Ne yazdim?` yazdığınızı görme modeline okutur.

**İpucu.** `PNG kaydet` ve `🤖 Ne yazdim?` için `pillow` gerekir.

### 4.5 Sistem (`Sistem`)

#### Öğrenci Takip (`Ogrenci Takip`)

**Ne işe yarar.** Seçili profilin ilerlemesini ölçer; veri yoksa tahmin yürütmez: grafikte `Bu donemde veri yok`, trendde `Trend icin en az 2 sinav gerekir`, `Zayif konular` bölümünde `Konu verisi yok - dilbilgisi laboratuvarlarindan veya sinavdan alistirma yapin.` ve ustalık tablosunda `(veri yok)` yazar.

**Nasıl kullanılır.** Kartlar, `Son 30 gun - dogru cevap sayisi` grafiği, `Sinav puani trendi`, `Zayif konular` ve `Kelime ustaligi (en dusuk 25)` tablosu otomatik hesaplanır. `Yenile` yeniden hesaplar; `📄 Haftalik Ozet` tarayıcıda A4 yazdırılabilir rapor açar.

**İpucu.** Profil değiştirince sayfa kendini tazeler; iki öğrencinin verisi karışmaz.

#### Paketler (`Paketler`)

**Ne işe yarar.** Hazırladığınız desteleri başka bir makineye ya da başka birine taşır.

**Nasıl kullanılır.** `Paket adi:` ve `Yazar:` alanlarını doldurun, `Kaynak deste:` seçin, isterseniz `Kendi ilerlememi de ekle` işaretleyip `📦 .rupack olustur`'a basın; eski uyumluluk için `{ } .json olustur` vardır. Gelen paketi `📂 Paket ac (.rupack / .json)` ile alın.

**İpucu.** `.rupack`, içinde `paket.json` ile isteğe bağlı `audio/` ve `images/` bulunan bir ZIP dosyasıdır.

#### Token Defteri (`Token Defteri`)

**Ne işe yarar.** Yapay zekâ kullanımınızı şeffaf gösterir; yalnızca sayaçları tutar (model adı, görev türü, token sayıları, süre). Metinler kaydedilmez.

**Nasıl kullanılır.** Kartlar bugün / 7 gün / 30 gün / tüm zamanlar özetini verir. `Grupla:` seçenekleriyle (`Modele gore`, `Ise gore`, `Gune gore`) tabloyu değiştirin; `CSV Disa Aktar` dışa aktarır, `Defteri temizle` kayıtları siler.

**İpucu.** Alternatif uç noktayı açtığınızda dışarıya ne kadar istek gittiğini buradan görürsünüz.

#### Kılavuz (`Kilavuz`)

**Ne işe yarar.** Program içinde, tamamen çevrimdışı bir rehber; her ekranı NEDEN · NASIL · FAYDA düzeninde anlatır.

**Nasıl kullanılır.** Sayfayı yukarıdan aşağı okuyun; sonunda `Gizlilik` maddeleri ve kısayol tablosu vardır. `🖨 Yazdirilabilir surum` aynı içeriği A4 için biçimlenmiş HTML olarak açar.

**İpucu.** Elinizdeki belge daha ayrıntılıdır; program içi kılavuz internet gerektirmez.

#### Ayarlar (`Ayarlar`)

**Ne işe yarar.** Arayüz, ses, yapay zekâ, profil ve veri ayarlarının tek yeri.

**Nasıl kullanılır.** Sayfa başlıklı bölümlerden oluşur: `Arayuz` (`Dil:`, `Tema:`, `Gunluk hedef:`, `CEFR seviyesi:`), `Ses` (`Seslendirme acik`, `Hiz:` 80–260, `Test et`), `Yapay zeka (yerel)` (`AI ozellikleri acik`, `LM Studio adresi:`, `Baglantiyi dene`, `Varsayilan model:`), `Alternatif uc (OpenAI uyumlu - INTERNET)` (bkz. 6. bölüm), `Profiller` (`Yeni profil`, `Secili profili sil`) ve `Veri` (`Veri klasorunu ac`, `Ilerlemeyi sifirla (bu profil)`, `Eksik seed kelimeleri geri yukle`). Değişiklikler `Kaydet` ile yazılır.

**İpucu.** Dil anında değişir; tema için yeniden başlatma gerekir ve program bunu hatırlatır.

---

## 5. Sözlük (ayrıntılı)

`Sozluk RU-EN-TR` dört katmanı tek listede birleştirir: gömülü çekirdek, sizin maddeleriniz, indirilmiş OpenRussian verisi ve yapay zekâdan gelen maddeler. Sayfa altındaki sayaç bu dağılımı sürekli gösterir.

### 5.1 Yön seçici

`Yon:` listesi beş seçenek sunar; seçiminiz `dict_direction` ayarına kaydedilir ve sonraki açılışta korunur.

| Seçenek | Aranan taraf | Ne zaman seçmeli |
|---|---|---|
| `Otomatik` | Kiril yazarsanız başlık; Latin yazarsanız İngilizce **ve** Türkçe taraf puanlanır, en iyi eşleşen kazanır | Günlük kullanım |
| `RU → EN` | Yalnızca Rusça başlık | Rusça kelimenin İngilizcesini ararken |
| `EN → RU` | Yalnızca İngilizce karşılıklar | İngilizce kelimenin Rusçasını ararken |
| `RU → TR` | Yalnızca Rusça başlık, hedef Türkçe | Rusça kelimenin Türkçesini isterken; eksik karşılık yapay zekâya sorulur |
| `TR → RU` | Yalnızca Türkçe karşılıklar | Türkçe kelimenin Rusçasını ararken |

Sabit yönde **yalnızca** o yönün kaynak tarafı taranır; bu, hem Türkçeye hem İngilizceye benzeyen sorgularda listeyi temiz tutar. Arama kutusunun sağındaki küçük etiket aramanın **etkin** yönünü gösterir; `Otomatik`'te motorun kararını oradan görürsünüz.

### 5.2 Türkçe sütunu ve detay paneli

Liste altı sütunludur: `Rusca`, `Ingilizce`, `Türkçe`, `Tur`, `Cins / Gorunus`, `Kaynak`. Türkçe içeren bir yön (`RU → TR` ya da `TR → RU`) seçiliyse `Türkçe` sütunu başlığın hemen sağına alınır.

Detay paneli vurgu işaretli başlığı, kaba IPA okunuşunu, tür ve cins/görünüş etiketini, `Ingilizce:` ve `Türkçe:` satırlarını, varsa örnek cümleyi ve notu gösterir. Kelime bankanızda aynı kelime varsa 📚 işaretiyle bankadaki anlam ve deste görünür. Altta `Son aramalar` (son 12 sorgu) ve `AI yaniti` dökümü bulunur; listeye **çift tıklamak** kelimeyi seslendirir.

### 5.3 Arama kuralları

Motor her maddeye puan verir ve sonuçları puana göre sıralar:

| Eşleşme | Puan |
|---|---|
| Tam eşleşme (alanın tamamı ya da `;` ile ayrılmış tek bir anlam) | 100 |
| Baştaki `to` / `the` / `a` / `an` atıldıktan sonra tam eşleşme | 95 |
| Önek: bir anlam ya da alan sorguyla başlıyorsa | 60 |
| Kelime içinde: sorgu bir kelimenin başında geçiyorsa | 30 |
| Alt dize (en az 3 harflik sorgu için) | 10 |
| Yalnızca ASCII / büyük harf katlamasıyla eşleşme (Türkçe taraf) | doğrudan puanın %59'u: tam 59, önek 35, kelime içinde 17, alt dize 5 |

Eşit puanda, Türkçe içeren yönlerde (`RU → TR` ve `TR → RU`) **Türkçe karşılığı olan** madde öne gelir, sonra kısa başlık, sonra alfabetik sıra. Katlanmış eşleşme yalnızca Türkçe tarafta ve yalnızca doğrudan karşılaştırma boş dönerse denenir; bu yüzden `ask` sorgusu İngilizce `to ask` maddesini Türkçe `aşk`ın önüne koyar.

Karşılaştırma öncesi hem sorgu hem alan normalleştirilir: büyük/küçük harf farkı yok sayılır ve `İ` düz `i`ye indirgenir (`İstanbul` = `istanbul`); **vurgu işareti** yok sayılır (`приве'т` de `привет` de aynı maddeye ulaşır); **ё → е** eşitlenir (`ёлка` = `елка`); Türkçeye özgü `ç ğ ı ö ş ü` harfleri ekranda hep doğru yazımıyla görünür, ama karşılaştırmada ASCII karşılıklarına katlanır: `sinav`, `SINAV` ve `sınav` aynı maddeye ulaşır (`ç→c`, `ğ→g`, `ı/İ→i`, `ö→o`, `ş→s`, `ü→u`). Türkçe harf içeren sorgu yine `Otomatik` yönde Türkçe tarafına yönelmenin ipucudur. Kiril/Latin ayrımı yalnızca `Otomatik` yönde anlamlıdır: Kiril harf görülünce motor `RU → EN` tarafına geçer.

İki harf yazdığınızda liste kendiliğinden süzülür; **Enter** aramayı kesinleştirir, geçmişe yazar ve gerekirse yapay zekâyı devreye sokar. `🎲 Rastgele kelime` gömülü çekirdekten rastgele bir madde açar.

### 5.4 Kaynak etiketleri

| Etiket | Anlamı |
|---|---|
| `gomulu` | Programla gelen, vurgu işaretli, Türkçe karşılıklı 1.360 maddelik çekirdek |
| `kullanici` | `Madde ekle` ile girdiğiniz ya da CSV/TSV ile aktardığınız maddeler |
| `OpenRussian` | İndirilip yüklenen açık lisanslı veri (çevirileri İngilizcedir) |
| `AI` | Yapay zekâdan gelen madde; kaydedilince yerel sözlüğe geçer |

### 5.5 AI ile eksik karşılığın doldurulması

Politika `Kapali` değilse sözlük iki durumda kendiliğinden modele başvurur:

1. **Sonuç yoksa.** Sorgu arka planda modele gider; model her madde için vurgu işaretli başlık, tür, cins/görünüş, **hem İngilizce hem Türkçe** karşılık, kısa bir Rusça örnek cümle ve arayüz dilinizde bir not döndürür. Gelen maddeler listenin başına `AI` etiketiyle eklenir.
2. **Türkçe karşılık eksikse.** `RU → TR` yönünde bulunan ilk maddenin Türkçesi boşsa, model yalnızca o boşluğu doldurmak için sorulur; gelen karşılık **kopya satır oluşturmadan** mevcut maddeye işlenir.

`🤖 AI'a sor` düğmesi, yerel sonuç bulunsa bile aramayı elle modele gönderir. Arayüz kilitlenmez: sorgu arka planda çalışır, `AI'a soruluyor...` bekleme metni görünür ve yeni bir arama başlatırsanız eski yanıt sessizce atılır.

**Kaydetme.** `AI sonuclarini sozluge kaydet` varsayılan olarak açıktır: gelen maddeler `ai` kaynağıyla yerel veritabanına yazılır ve bir sonraki arama **anında ve çevrimdışı** çalışır. Kapatırsanız maddeler yalnızca ekranda kalır; beğendiğinizi `💾 Sozluge kaydet` ile tek tek kaydedersiniz. Bu düğme yalnızca kaydedilmemiş bir madde ya da Türkçe dolgu seçiliyken görünür.

### 5.6 Kelime bankasına ekleme

`📚 Kelime bankasina ekle` seçili maddeyi çalışma dolaşımınıza alır. Bankaya yazılan anlam **Türkçe karşılığın ilk anlamıdır**; Türkçe yoksa İngilizcenin ilki kullanılır. Vurgu konumu, tür (isimlerde cinsiyet birleştirilerek) ve varsa örnek cümle birlikte aktarılır, deste adı `Sozluk` olur. `Kopyala` maddeyi `başlık — İngilizce — Türkçe` biçiminde panoya alır; Türkçe karşılık yoksa yalnızca `başlık — İngilizce` kopyalanır.

### 5.7 CSV içe / dışa aktarma

`CSV disa aktar`, listede sonuç varsa **görünen sonuçları**, yoksa OpenRussian dışındaki tüm maddeleri yazar. Varsayılan ad `sozluk_ru_en_tr.csv`, varsayılan klasör veri klasörünüzün `exports` altıdır.

| Sütun | İçerik |
|---|---|
| `ru` | Rusça başlık; vurgu, vurgulu sesliden **hemen sonra** gelen kesme işaretiyle |
| `en` | İngilizce karşılık(lar), `; ` ile ayrılmış |
| `tr` | Türkçe karşılık(lar), `; ` ile ayrılmış (boş olabilir) |
| `pos` | Tür: `n v adj adv pron prep conj num part int phr` |
| `extra` | İsimlerde cins `m f n pl`, fiillerde görünüş `ipf pf`, diğerlerinde boş |
| `source` | `builtin` / `user` / `openrussian` / `ai` |

```csv
ru,en,tr,pos,extra,source
дом,house; home,ev; yuva,n,m,user
кни'га,book,kitap,n,f,user
говори'ть,to speak; to talk,konuşmak; söylemek,v,ipf,user
```

`CSV/TSV ice aktar` hem virgül hem sekme ayırıcısını tanır. Başlık satırı varsa sütunlar **adıyla** eşlenir, sıra serbesttir ve eş anlamlı başlıklar kabul edilir (`Rusça`, `Türkçe`, `English`, `Tur`, `Kaynak`…); başlık yoksa eski konumsal düzen geçerlidir: `ru, en[, pos[, extra]]`. Rusça ve İngilizce alanları zorunludur, ters yazılmışsa program düzeltir.

### 5.8 Madde ekleme

`+ Madde ekle` küçük bir pencere açar. Alanlar: `Rusca (вург: приве'т)`, `Ingilizce`, `Türkçe`, `Tur (n/v/adj/...)`, `Cins / Gorunus (m/f/n/ipf/pf)`. Arama kutusundaki sorgu, diline göre uygun alana kendiliğinden yazılır. Rusça ve İngilizce boş bırakılamaz; **Enter** kaydeder, **Esc** kapatır.

### 5.9 OpenRussian yükleme

1. `Kaynak Merkezi` sayfasında tür süzgecinden `Sozluk / veri`'yi seçin.
2. OpenRussian dosyalarını indirin; `Resources/Indirilenler/Sozluk` klasörüne `openrussian_*.tsv` adıyla inerler.
3. Sözlük sayfasında `OpenRussian'i yukle`'ye basın. Dosyalar zaten oradaysa sayfa açılırken **kendiliğinden** yüklenir.

Yükleme arka planda çalışır ve toplam madde sayısını on binlere çıkarır. Dosya yoksa program `OpenRussian dosyalari yok. Kaynak Merkezi'nden 'Sozluk / veri' bolumunu indirin.` uyarısını verir.

**Dikkat:** OpenRussian çevirileri **İngilizcedir**; bu katmanın maddeleri Türkçe karşılık taşımaz. `RU → TR` yönünde ararsanız Türkçe boş görünür ve yapay zekâ açıksa boşluğu doldurmak için devreye girer.

---

## 6. Yapay zeka

Yapay zekâ **isteğe bağlıdır**; kapalıyken sözlük, tekrar, sınav ve laboratuvarlar dâhil her şey çalışmaya devam eder.

### 6.1 LM Studio kurulumu ve yerel sunucu

1. [LM Studio](https://lmstudio.ai) kurun.
2. Bir model indirin; önerilen `qwen2.5-7b-instruct`. Görsel/OCR için ayrıca `qwen2-vl-7b-instruct` gibi bir görme modeli.
3. LM Studio içinde **Local Server**'ı başlatın; varsayılan adres `http://127.0.0.1:1234`.
4. Üst çubuktaki rozet model adına dönünce hazırdır; `AI: cevrimdisi` yazıyorsa üzerine tıklayarak yeniden yoklayın.
5. `Ayarlar` → `Baglantiyi dene` bağlantıyı sınar ve kaç model bulduğunu yazar.

Yerel adres API anahtarı istemez: `localhost`, `127.0.0.1`, `.local`, `.lan` ve özel ağ adresleri (10.x, 192.168.x, 172.16–31.x) anahtarsız kabul edilir.

### 6.2 Model seçimi

Program her göreve bir model profili tanımlar ve **kurulu** modeller arasından en uygununu kendisi seçer. Sözlük profilinin tercih sırası: `qwen2.5-7b-instruct`, `qwen2.5-14b-instruct`, `gemma-4-12b-qat`, `llama-3.1-8b-instruct`, `qwen3.6-35b-a3b`. Profildeki **tam eşleşme** önce gelir, sonra aynı aile (qwen, llama…), sonra genel modeller; eşitlikte **4–16 milyar parametreli** ve adında `instruct`, `-it`, `chat`, `assistant` geçen modeller öne alınır.

**Uzman modeller atlanır:** adında `embed`, `embedding`, `rerank`, `math`, `coder`, `code-`, `vision`, `-vl`, `llava`, `moondream`, `whisper`, `tts`, `audio`, `clip`, `sd-`, `stable-diffusion`, `bio`, `medic` geçenler metin görevlerine uygun değildir ve ancak başka seçenek yoksa listeye girer; görsel/OCR görevinde ise yalnızca görme modeli aranır. Model bulunamazsa özellik çökmez, arayüz sakin bir uyarı gösterir.

### 6.3 Alternatif uç nokta

LM Studio kapalıyken sözlüğün yine de soru sorabilmesi için `Ayarlar` → `Alternatif uc (OpenAI uyumlu - INTERNET)` bölümü vardır. **Varsayılan olarak kapalıdır**; yalnızca siz açarsanız ağ çağrısı yapılır.

1. `Alternatif ucu kullan (varsayilan kapali)` kutusunu işaretleyin.
2. `Adres (base URL):` alanına OpenAI uyumlu bir adres yazın; varsayılan NVIDIA NIM `https://integrate.api.nvidia.com/v1`. OpenRouter, Groq, Ollama gibi herhangi bir OpenAI uyumlu adres de olur.
3. `Model adi:` alanına modeli yazın (varsayılan `meta/llama-3.1-8b-instruct`).
4. `API anahtari:` alanına anahtarınızı yapıştırın.
5. `Baglantiyi dene` ile sınayın; başarılıysa `Baglandi` ve model sayısı görünür. Sonra `Kaydet`'e basın.

### 6.4 Anahtarın saklanması

API anahtarı `settings.json` dosyasına **asla** yazılmaz.

- **Windows'ta** anahtar Windows Credential Manager'a `RussianCourseAI/alt_api_key` hedefiyle kaydedilir.
- Diğer sistemlerde ya da Credential Manager erişilemezse ayar klasöründeki `secrets.json` dosyasına, mümkün olan yerde `0600` izniyle yazılır.
- `RUSSIANCOURSEAI_API_KEY` ortam değişkeni tanımlıysa o kazanır; hiçbir yere yazmadan anahtar verebilirsiniz.

Ayarlar sayfası gerçek anahtarı göstermez; yalnızca `••••• kayitli (degistirmek icin yeni anahtari yazin)` ya da `anahtar kayitli degil` yazar. `Anahtari sil` anahtarı her iki depodan kaldırır.

### 6.5 AI politikası

Sözlüğün hangi sağlayıcıyı kullanacağını `dict_ai` ayarı belirler. Aynı liste hem sözlük araç çubuğunda (`AI:`) hem `Ayarlar` → `Sozluk AI kaynagi:` alanında görünür ve ikisi birbirini izler.

| Politika | Davranış |
|---|---|
| `Otomatik` | LM Studio ulaşılabiliyorsa yerel, değilse (açıksa) alternatif uç |
| `LM Studio (yerel)` | Yalnızca LM Studio |
| `Alternatif uc` | Yalnızca alternatif uç (kapalıysa ya da anahtar yoksa kullanılmaz) |
| `Kapali` | Sözlükte hiç yapay zekâ çağrısı yapılmaz |

`AI ozellikleri acik` kutusu kapalıysa politika ne olursa olsun çağrı yapılmaz. Araç çubuğundaki durum etiketi geçerli durumu söyler: `LM Studio: bagli`, `Alternatif: hazir`, `AI cevrimdisi`, `AI kapali`. Erişilebilirlik denetimi arka planda yapılır ve yaklaşık 30 saniye önbellekte tutulur; bu yüzden her arama ağ beklemesine takılmaz.

### 6.6 Token defteri ve gizlilik

Her yapay zekâ çağrısı `Token Defteri` sayfasına bir satır yazar: model adı, görev türü, istem ve yanıt token sayıları, süre, başarı durumu. **İstek ya da yanıt metni saklanmaz.**

Gizlilik kuralları: çekirdek işleyişte hiçbir veri makineden çıkmaz; yapay zekâ yerelde çalışır ve modele yalnızca seçtiğiniz metin gönderilir; ağ çağrısı yalnızca alternatif uç noktayı açtığınızda ya da Kaynak Merkezi'nden indirme yaptığınızda olur; Kaynak Merkezi yalnızca açık lisanslı kaynak indirir ve TLS sertifika doğrulaması hiçbir koşulda kapatılmaz.

---

## 7. Veri yönetimi

**Profiller.** Üst çubuktaki `+` ya da `Ayarlar` → `Yeni profil` yeni öğrenci açar. `Secili profili sil` profili ve ona bağlı ilerlemeyi kaldırır; kelime bankası ve sözlük etkilenmez.

**Yedekleme.** En sağlam yol veri klasörünün tamamını kopyalamaktır. Parça parça yedek için:

| Yöntem | Ne yedekler | Nerede |
|---|---|---|
| `CSV Disa Aktar` | Kelime bankası (`kelime;anlam;ingilizce;ornek_ru;ornek_tr;deste`) | `Kelime Bankasi` |
| `CSV disa aktar` | Sözlük maddeleri (`ru,en,tr,pos,extra,source`) | `Sozluk RU-EN-TR` |
| `📦 .rupack olustur` | Bir deste + soruları, isteğe bağlı olarak ilerlemeniz | `Paketler` |
| `CSV Disa Aktar` | Token kullanım kayıtları | `Token Defteri` |

**Veri klasörü.** `Ayarlar` → `Veri` bölümünde tam yol yazar; `Veri klasorunu ac` onu dosya yöneticisinde açar. Aynı yol durum çubuğunun sağ ucunda da görünür.

**Sıfırlama.** `Ilerlemeyi sifirla (bu profil)` seçili profildeki tüm tekrar, sınav ve konu ilerlemesini siler (kelime bankası **silinmez**) ve onay ister. `Eksik seed kelimeleri geri yukle` sildiğiniz gömülü A1 kelimelerini geri koyar, var olanları çoğaltmaz. Her şeyi sıfırlamak için program kapalıyken veri klasörünü silin; program bir sonraki açılışta hepsini yeniden kurar.

---

## 8. Kısayollar ve ipuçları

| Tuş | İşlev |
|---|---|
| `Ctrl+1` … `Ctrl+9` | İlk dokuz sayfaya doğrudan geç (`Aralikli Tekrar`, `Kelime Bankasi`, `Sozluk RU-EN-TR`, `Sinav`, `Kiril Lab`, `Telaffuz & Vurgu`, `Dilbilgisi Lab`, `Kurs Kaynaklari`, `PDF Okuyucu`) |
| `Ctrl+PgDn` / `Ctrl+PgUp` | Sonraki / önceki sayfa |
| `F5` | Görünen sayfayı tazele |
| `Ctrl+Q` | Programı kapat |
| `Space` | `Aralikli Tekrar`'da kart modunda kartı çevir |
| `1` / `2` / `3` | Kart çevrildikten sonra `Bilmiyorum` / `Emin degilim` / `Biliyorum` |
| `Enter` | Aramayı çalıştır (sözlük, kelime bankası, telaffuz), cevabı kontrol et (sınav ve yazma modları), mesajı gönder (konuşma pratiği) |
| `Ctrl+Enter` | `AI Ogretmen`'de soruyu gönder |
| `Space` | `Kurs Kaynaklari`'nda `Bitirdim` işaretini değiştir |
| Çift tık | Kelime bankası ve sözlük listelerinde seçili kelimeyi dinle |
| `Esc` | Madde / kelime ekleme penceresini kapat |

**İpuçları.** Üst çubuktaki yapay zekâ rozetine tıklamak bağlantıyı yeniden yoklar. Sayfa başlığının yanındaki gri metin o sayfaya özgü ipucudur. Sözlükte iki harf yazınca liste süzülür; tam sonuç ve gerekirse yapay zekâ için **Enter**'a basın. `PDF Okuyucu`'da seçtiğiniz metin `AI Ogretmen` sayfasında `PDF'teki secimi al` ile hazır gelir.

---

## 9. Sorun giderme

**LM Studio'ya bağlanılmıyor.** *Neden:* Local Server başlatılmamış, adres farklı ya da `AI ozellikleri acik` kapalı. *Çözüm:* LM Studio'da **Local Server**'ı başlatın, `LM Studio adresi:` alanının `http://127.0.0.1:1234` olduğunu doğrulayıp `Baglantiyi dene`'ye basın. Program `Baglanti yok. LM Studio'yu acip Local Server'i baslatin.` derse sunucu gerçekten kapalıdır; bağlantı olmadan da program tam çalışır.

**AI boş yanıt veriyor.** *Neden:* "Düşünen" modeller (gemma-4, qwen3 gibi) akıl yürütme metnini token bütçesine yazıp içeriği boş bırakabilir; ya da seçilen model uzman bir modeldir. *Çözüm:* Program bunu **sözlük sorgularında** hafifletir — yerel sunucuya düşünmeyi kapatan bir alan gönderir, yanıt kesilmişse bütçeyi üç katına çıkarıp bir kez daha dener. Diğer sayfalarda (`AI Ogretmen`, `Konusma Pratigi`) böyle bir yeniden deneme yoktur. Yine boşsa `qwen2.5-7b-instruct` gibi bir yönerge modeli yükleyin; `Modelleri tara` kurulu modelleri gösterir.

**Türkçe karşılık yok.** *Neden:* Madde OpenRussian katmanındandır (çevirileri İngilizce) ya da `tr` alanı boştur. *Çözüm:* Yönü `RU → TR` yapıp **Enter**'a basın; politika `Kapali` değilse program eksik karşılığı modele sorar ve kopya oluşturmadan mevcut maddeye işler. Yapay zekâ istemiyorsanız `+ Madde ekle` ile Türkçesini kendiniz yazın.

**macOS "açılamıyor" uyarısı.** *Neden:* Uygulama notarize edilmemiştir; Gatekeeper tanımadığı geliştiricinin uygulamasını doğrudan açmaz. *Çözüm:* Çift tıklamayın; **sağ tıklayın → Aç**, çıkan uyarıda yine **Aç**'a basın. Onay bir kez verilir.

**Ses çıkmıyor.** *Neden:* `Seslendirme acik` kapalı, sistemde Rusça ses paketi yok ya da işletim sisteminin konuşma motoruna erişilemiyor. *Çözüm:* `Ayarlar` → `Ses` bölümündeki durum satırını okuyup `Test et`'e basın; seslendirme ek paket istemez (Windows'ta `System.Speech`, macOS'ta `say`), ancak Rusça konuşma paketini işletim sisteminizin ayarlarından eklemeniz gerekir.

**exe açılmıyor.** *Neden:* Zip tam açılmamış, antivirüs dosyayı karantinaya almış ya da tek dosyalık paket kendini geçici klasöre açıyor. *Çözüm:* Zip'i gerçekten bir klasöre çıkarıp `RussianCourseAI.exe`'yi oradan çalıştırın; ilk açılış birkaç saniye sürebilir. Veritabanı açılamazsa program hatalı dosyanın yolunu gösterir; o dosyayı taşıyıp yeniden başlatın.

**Veriler nerede.** *Neden:* Program dizini ile veri dizini bilinçli olarak ayrıdır; böylece güncelleme ilerlemenizi silmez. *Çözüm:* Windows'ta `%APPDATA%\RussianCourseAI`, macOS'ta `~/Library/Application Support/RussianCourseAI`, diğer sistemlerde `~/.russiancourseai`; `Ayarlar` → `Veri klasorunu ac` doğrudan oraya götürür. `RCA_HOME` tanımlıysa veriler orada tutulur.

---

## 10. Sürüm notları özeti

| Sürüm | Öne çıkanlar |
|---|---|
| **v1.0.0** | İlk sürüm: 17 sayfa, üç dilli arayüz, çevrimdışı çalışma, SM-2 aralıklı tekrar, sınav motoru, Kiril ve dilbilgisi laboratuvarları, PDF okuyucu, kelime bankası, açık lisanslı Kaynak Merkezi, yerel LM Studio öğretmeni, macOS paketi |
| **v1.1.0** | `Sozluk RU-EN-TR` sayfası: iki yönlü Rusça–İngilizce sözlük, gömülü çekirdek veri, OpenRussian katmanı ve **yapay zekâ bağlantısı** (LM Studio ya da alternatif OpenAI uyumlu uç); API anahtarı Credential Manager'da saklanır |
| **v1.1.1** | Sözlük yapay zekâ düzeltmeleri: düşünen modellerde boş yanıt, görev bazlı model seçimi, vurgu işaretinin onarımı |
| **v1.1.2** | Sözlük cilası: `Cins / Gorunus` alanı, etkin yön etiketi, araç çubuğundan politika seçimi, tekrar eden anlamların ayıklanması |
| **v1.2.0** | **Yön seçimi ve Türkçe üçüncü dil:** `Otomatik / RU→EN / EN→RU / RU→TR / TR→RU` seçicisi, listede ve detay panelinde `Türkçe` sütunu, gömülü 1.360 maddenin tamamına Türkçe karşılık, eksik Türkçenin kopya oluşturmadan doldurulması, `tr` sütunlu CSV aktarımı ve eski veritabanlarına `tr` sütunu göçü |
| **v1.2.1** | **Türkçe aramada ASCII ve büyük harf desteği:** `sinav`, `SINAV` ve `sınav` aynı sonucu verir; `cok` → `çok`, `ogrenci` → `öğrenci`, `gormek` → `görmek`. Katlanarak bulunan eşleşmeler doğrudan eşleşmelerin altına sıralanır, böylece `ask` yazan kullanıcı önce İngilizce karşılığı görür; gösterilen yazım değişmez. Ayrıca bu **kullanım kılavuzu** (`docs/KULLANIM_KILAVUZU.md`, İngilizcesi `docs/USER_GUIDE.md`) depoya eklendi ve PDF sürümü sürüm ek dosyası olarak yayımlandı |
| **v1.3.0** | **MIT lisansı ve izin verici PDF katmanı:** PDF okuyucu artık `pypdfium2` (sayfa çizimi + metin) ve `pypdf` (işaretli PDF yazma) kullanıyor; AGPL lisanslı **PyMuPDF** kaldırıldı. Proje **MIT lisansı** altında yayımlandı, `LICENSE` ve `THIRD_PARTY_NOTICES.md` depoya eklendi ve indirdiğiniz zip'in içinde geliyor. Paketler temiz bir sanal ortamda derlendi: yalnızca `requirements.txt`'teki kütüphaneler pakete girer, böylece dosya boyutu küçülür |

---

## 11. Sık sorulan sorular

**Programı internetsiz kullanabilir miyim?** Evet; çekirdek işleyişin tamamı çevrimdışıdır. Ağ yalnızca alternatif yapay zekâ uç noktasını açtığınızda ve Kaynak Merkezi'nden dosya indirdiğinizde kullanılır.

**Yapay zekâ olmadan program işe yarar mı?** Fazlasıyla. Aralıklı tekrar, sınav, kelime bankası, 1.360 maddelik gömülü sözlük, laboratuvarlar ve ilerleme takibi yapay zekâsız tam çalışır.

**Kelime bankası ile sözlük arasındaki fark nedir?** `Kelime Bankasi` tekrar ve sınav kuyruğunu besleyen kişisel destenizdir; `Sozluk RU-EN-TR` ise okurken başvurduğunuz genel sözlüktür. Beğendiğiniz maddeyi `📚 Kelime bankasina ekle` ile bankaya taşırsınız.

**Hangi yönü seçmeliyim?** Emin değilseniz `Otomatik` bırakın. Rusça bir kelimenin Türkçesini istiyorsanız `RU → TR`, tersi için `TR → RU` seçin; sabit yön karışık eşleşmeleri eler.

**Vurgu işaretini nasıl yazmalıyım?** Aramada gerekmez. Madde eklerken vurguyu, vurgulu sesli harften **hemen sonra** bir kesme işaretiyle belirtin: `приве'т`, `кни'га`, `хорошо'`. Tek heceli kelimeler ve içinde `ё` geçenler işaretlenmez.

**`ё` yerine `е` yazarsam bulur mu?** Bulur; karşılaştırma öncesi `ё` her zaman `е`ye indirgenir.

**API anahtarım nerede saklanıyor?** Windows'ta Credential Manager'da, diğer sistemlerde ayar klasöründeki `secrets.json` dosyasında; `settings.json`'a asla yazılmaz ve arayüzde görüntülenmez.

**Yapay zekâya gönderdiğim metinler saklanıyor mu?** Hayır. `Token Defteri` yalnızca model adını, görev türünü, token sayılarını ve süreyi tutar.

**Verilerimi başka bir bilgisayara nasıl taşırım?** Veri klasörünü olduğu gibi kopyalayın; yalnızca desteler için `.rupack`, yalnızca sözlük için `CSV disa aktar` kullanın.

**Aynı bilgisayarda iki kişi çalışabilir mi?** Evet; `+` ile ikinci profil açın. Tekrar geçmişi, sınavlar ve istatistikler ayrılır, kelime bankası ve sözlük ortak kalır.

**OpenRussian'i yüklemek zorunda mıyım?** Hayır. Gömülü 1.360 madde A1–B1'i karşılar ve anında çalışır; OpenRussian on binlerce madde isteyenler içindir.

**Programı kaldırırsam verilerim silinir mi?** Hayır; program klasörünü silmek verilerinize dokunmaz. Verileri de silmek isterseniz 7. bölümdeki veri klasörünü elle kaldırın.


---

## 12. Lisans

Russian Course AI **MIT Lisansi** ile dagitilir; tam metin deponun kokundeki `LICENSE`
dosyasindadir. Programi serbestce kullanabilir, degistirebilir ve dagitabilirsiniz;
tek kosul telif ve lisans bildiriminin korunmasidir.

Programin kullandigi ve `.exe` / `.app` paketine gomulen ucuncu taraf bilesenlerin
dogrulanmis lisanslari `THIRD_PARTY_NOTICES.md` dosyasindadir. PDF katmani izin verici
lisanslidir (`pypdfium2`: Apache-2.0 / BSD-3-Clause, `pypdf`: BSD-3-Clause) ve projede
AGPL lisansli hicbir bilesen yoktur. Indirdiginiz pakette tek copyleft bilesen `certifi`
(MPL-2.0) olup degistirilmedigi surece ek bir yukumluluk getirmez. GPL-3.0 lisansli
`pyttsx3` paketi bilerek disarida birakilmistir; seslendirme Windows'ta `System.Speech`,
macOS'ta yerlesik `say` komutuyla yapilir.

Kaynak Merkezi'nden indirdiginiz materyal programin lisansina degil, kendi acik
lisansina tabidir ve her indirmenin yaninda bir `LISANS.txt` olusturulur.
