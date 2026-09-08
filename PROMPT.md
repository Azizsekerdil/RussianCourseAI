# PROMPT — "Russian Course AI" masaüstü Rusça öğrenme programı (birleştirilmiş)

Bu dosya, verdiğin iki prompt'un tek metinde birleştirilmiş halidir.
Bu depodaki çalışan program bu prompt'a göre üretilmiştir.

**Çözülen tek çelişki:** birinci prompt Tkinter/ttk, ikincisi PySide6 istiyordu.
Ana mimari birinciden geldiği ve Tkinter sıfır harici bağımlılık anlamına geldiği için
**Tkinter/ttk** seçildi. İkinci prompt'un tüm somut öğrenme döngüsü (SM-2 kartlar,
4 alıştırma modu, deste + CSV, seed deste, kısayollar, `build.bat`, testler) korundu.

---

## Rolün
Sen kıdemli bir Python masaüstü uygulama geliştiricisisin. Aşağıda tarif edilen
**"Russian Course AI"** adlı, Windows üzerinde **%100 çevrimdışı** çalışan Rusça öğrenme
istasyonunu sıfırdan kuracaksın. Referans mimari: tek pencerede sekmeli çalışma alanları,
gömülü içerik paketleri, yerel LM Studio üzerinden yapay zekâ öğretmen, SQLite tabanlı
öğrenci takibi.

## Ürün tanımı
Rusça'yı sıfırdan (A1) ileri seviyeye (C1 / ТРКИ-3) götürmek için tasarlanmış, tek pencerede
toplanmış bir masaüstü dil öğrenme platformu: PDF ders kitabı okuyucu + not alma, yerel yapay
zekâ öğretmen, Kiril yazı laboratuvarı, dilbilgisi (hal / görünüş / hareket fiilleri)
laboratuvarları, telaffuz & vurgu stüdyosu, kelime bankası + aralıklı tekrar, sınav motoru,
el yazısı çizim tahtası ve çift yönlü TR↔RU sözlük.

**Hiçbir veri makineden çıkmaz.** Yapay zekâ yerelde LM Studio ile çalışır; program dosyaları
kendisi okur ve modele yalnızca **seçili metni / bağlamı** gönderir. Bulut yok, hesap yok,
internet gerekmez.

## Teknik kısıtlar (uyulması zorunlu)
- **Platform:** Windows · **Python 3.11** · **Tkinter/ttk** (harici GUI çatısı yok)
- **Çekirdek bağımlılık sıfır olmalı:** program yalnızca standart kütüphaneyle (tkinter,
  sqlite3, urllib) eksiksiz açılmalı. Diğer her paket isteğe bağlı; yoksa ilgili düğme
  gri kalır, program çalışmaya devam eder.
- **Veri:** SQLite; kullanıcı verisi `%APPDATA%\RussianCourseAI` altında
  (`data/`, `settings/`, `exports/`, `logs/`)
- **AI:** LM Studio OpenAI-uyumlu uç (`http://127.0.0.1:1234`), varsayılan model
  `qwen2.5-7b-instruct`; görsel/OCR için ayrı vision profili; **isteğe bağlı** NVIDIA NIM
  ücretsiz uçları. Model bulunamazsa **özellik çökmesin**, kalite düşsün — profiller kurulu
  modellere karşı çözümlensin.
- **Ses:** çevrimdışı TTS (pyttsx3/SAPI5, yedek olarak Windows System.Speech) ve çevrimdışı
  ASR (Vosk `ru` modeli). Model yoksa ilgili düğmeler gri kalsın, program açılmaya devam etsin.
- **Kütüphaneler (hepsi isteğe bağlı):** pypdfium2 + pypdf (PDF), pymorphy3 (morfoloji), Pillow,
  Tesseract (`rus`) OCR. Grafikler harici kütüphane olmadan tkinter Canvas ile çizilsin.
- **Kod düzeni:** tek dev dosya yok. Giriş `Russian_Course_AI.pyw` (yalnız pencere + sekme
  kurulumu), ortak sabitler `rca_common.py` (`APP_NAME`, `VERSION`, yollar, tema, model
  varsayılanları — **tek kaynak**, hiçbir yerde başlık string'i tekrarlanmaz).
- **Hedef dil parametrik:** `rca_common.TARGET_LANG` tek değiştirme noktası olsun.
- **Arayüz dili:** Türkçe / İngilizce / Rusça — üçü de **aynı derinlikte**; AI'a giden sistem
  yönergesi de seçilen dile göre değişsin.
- **Tema:** koyu + açık tema, tek bir `THEME` sözlüğünden.
- **Test:** `tests/` altında pytest paketi; GUI'siz mantık ayrık tutulsun ve doğrudan test
  edilsin. En az 10 anlamlı test — özellikle SM-2 aralık hesabı ve cevap doğrulama için.
- **Kodlama:** her şey UTF-8; tüm public fonksiyonlara type hint ve kısa docstring.

## Modüller (sekme sekme)

1. **Kurs Kaynakları** — `Resources/` altını ağaç görünümünde gez (📘 Dersler / 📝 Alıştırmalar),
   "☐ Bitirdim" tiki, arama, klasör konumunu aç, yazdır.
2. **PDF Okuyucu / Not Alma** — zoom, sayfa gezinme, Fit Width, Kalem/İşaretleme/Metin/Silgi,
   notları kaydet, işaretli PDF dışa aktar. **Kiril metin seçimi** ve seçili parçayı doğrudan
   AI'a / sözlüğe gönderme.
3. **AI Öğretmen** — seçili metni/soruyu yerel modele sor; göreve göre model yönlendirme
   (dilbilgisi açıklama / çeviri / diyalog / düzeltme / görsel-OCR). **Yazı düzeltici:** kullanıcı
   Rusça cümle yazar, model *hatayı işaretler + kuralı adlandırır + doğrusunu verir*.
4. **Kiril Laboratuvarı** — 33 harf: basılı/el yazısı (курсив) formları, ses değeri, sık karışan
   çiftler (ш/щ, б/в, и/й, ь/ъ). Harf harf animasyonlu yazım sırası; kullanıcı tabletle yazar,
   program şekli karşılaştırır. Ayrıca harf→ses alıştırma turu.
5. **Telaffuz & Vurgu Stüdyosu** — kelimenin **vurgusu (ударение)**, редукция (о→а) kuralının
   gösterimi, IPA, çevrimdışı TTS ile dinleme; mikrofonla tekrar → Vosk ile karşılaştırma +
   hangi hecenin kaydığını gösteren geri bildirim.
6. **Dilbilgisi Laboratuvarları** (her biri *kural → tablo → canlı örnek → alıştırma* akışında):
   - **Hal Lab (Падежи):** 6 hal, isim/sıfat/zamir çekim tabloları, cinsiyet + sayı,
     edat–hal eşleşmeleri; girilen cümlede halleri renklendirerek gösterir.
   - **Fiil Lab (Вид / Спряжение):** tamamlanmış–tamamlanmamış görünüş çiftleri, 1./2. çekim,
     geçmiş–şimdi–gelecek, emir kipi, dönüşlü fiiller.
   - **Hareket Fiilleri Lab:** идти/ходить, ехать/ездить ve ön ekli türevleri; hareket şemasıyla
     görselleştirme.
   - **Sayı & Ölçü Lab:** sayı–isim uyumu (1 / 2–4 / 5+), tarih, saat, para, yaş kalıpları.
   - **Söz Dizimi Lab:** cümle ayrıştırma — pymorphy3 ile her kelimenin kök/çekim etiketi,
     ağaç görünümü (pymorphy3 yoksa sonek tabanlı yaklaşık etiketleme).
   - **Notlar:** `grammar/*.md` dosyalarını okuyan basit markdown görüntüleyici.
   Her lab **gömülü içerik paketi** olarak yazılsın: modül içinde veri sözlüğü + tek bir
   `build()` finalizer'ı; harici dosya bağımlılığı yok.
7. **Kelime Bankası & Sözlük** — SQLite TR↔RU↔EN; frekans listeleri (ilk 100/500/1000),
   kök ailesi, görünüş çiftleri, örnek cümle, ses. PDF'ten kelime tarayıcı, görsel/OCR çeviri,
   favoriler, "bu kelimeyi AI'a sor". **CSV içe/dışa aktarma** (`kelime;anlam;örnek;deste`).
   İlk açılışta ~100+ kelimelik hazır A1 destesi (kod içinde seed verisi) gelsin.
8. **Aralıklı Tekrar (Leitner/SM-2)** — "Bugün" panosu: tekrar vakti gelenler, yanlışlar,
   denenmemişler, doğruluk kartları; tek tıkla hedefli oturum (**Tekrar / Yanlış Drill /
   Yeni Kelime / Favoriler**). Çalışma modları: **Kart · Çoktan seçmeli · Yazarak · Dinleme ·
   Eşleştirme**. Yazarak modunda harf harf karşılaştırma, yanlış harfler kırmızı.
   **Kural tabanlı, AI çağrısı yok** — pano anında açılsın; veri yetersizse tahmin üretme,
   "yeterli veri yok" de.
   Kısayollar: `Space` kartı çevir, `1/2/3` değerlendir, `Enter` kontrol et.
9. **Sınav Motoru** — soru tipleri: çoktan seçmeli (RU→TR / TR→RU), boşluk doldurma,
   **doğru hali seç**, **fiili çek**, TR→RU / RU→TR çeviri, dinleme (TTS), kelime dikte.
   Otomatik puanlama; çeviride *eşdeğer cevap* toleransı (büyük/küçük harf, vurgu işareti,
   ё/е farkı) ama son kararı kullanıcı verir. Sınavdaki yanlışlar bankada otomatik "Yanlış" olur.
10. **Konuşma Pratiği** — yerel modelle rol-yapma senaryoları (kafede sipariş, otel, doktor,
    iş görüşmesi); CEFR seviyesine (A1–C1) göre kelime sınırlaması; oturum sonunda
    *hata dökümü + öğrenilecek 5 kelime* çıktısı.
11. **El Yazısı Tahtası** — tablet/kalem ile Kiril el yazısı çalış, kılavuz harf şablonu,
    PNG kaydet, "ne yazdım?" diye AI'a sor.
12. **Öğrenci Takip** — birden çok profil; kelime/dilbilgisi ustalık tablosu, zayıf konular
    (örn. "родительный падеж %48"), sınav puanı trendi, **📄 Haftalık Özet** (tarayıcıda açılan
    tek sayfa, A4 yazdırılabilir rapor). Veri yoksa boş grafik çizme, "bu hafta veri yok" yaz.
13. **Paket Sistemi** — kendi kelime/soru paketlerini **`.rupack`** (ZIP: `paket.json` +
    `audio/` + `images/`) olarak dışa aktar/paylaş; düz `.json` geriye dönük uyumlu kalsın.
14. **Token Kullanım Defteri** — AI'a giden her isteğin kaydı: bugün / 7 gün / 30 gün / tüm
    zamanlar kartları; modele·işe·güne göre gruplu tablolar, CSV dışa aktarma.
    **İstek metinleri saklanmaz.**
15. **Eğitim & Tanıtım Modülü** — her ekranı *neden → nasıl → fayda* biçiminde anlatan,
    çevrimdışı tek sayfa kılavuz; renkli/gri yazdırılabilir.
16. **Kaynak Merkezi** — küratörlü, **yalnızca açık lisanslı** (kamu malı veya Creative
    Commons) e-kitap / ses dersi / sözlük verisi / web kursu kataloğu. Tür ve arama
    filtresi, sağ panelde lisans ve atıf zorunluluğu, arka planda iptal edilebilir
    indirme, her indirmenin yanına `LISANS.txt`. İndirilen PDF tek tıkla PDF Okuyucuda
    açılır; indirilen OpenRussian sözlüğü (sıklık sıralı, vurgu işaretli, çekim tablolu)
    kelime bankasına aktarılır. **Lisansı belirsiz hiçbir kaynak katalogda yer almaz ve
    program telifli materyal indirmez** — bu kural bir testle zorlanır.
17. **Ayarlar** — arayüz dili, tema, günlük hedef (kelime/gün), CEFR seviyesi, ses açık-kapalı
    ve konuşma hızı, LM Studio adresi ve varsayılan model, profil yönetimi, veri klasörü,
    ilerlemeyi sıfırlama, eksik seed kelimeleri geri yükleme, kullanılan TLS sertifika deposu.

## Arayüz gereksinimleri
- Üst sekme şeridi değil, **gruplu bir kenar çubuğu** (Öğren · Laboratuvar · Oku · Pratik ·
  Sistem); etkin öğede vurgu çubuğu, fare üzerinde geçiş rengi, bekleyen tekrar sayısı için
  rozet.
- Üst barda sayfa başlığı + kısayol ipucu, profil seçici ve LM Studio durum işareti;
  altta durum çubuğu.
- Kartlar, rozetler ve grafikler **harici arayüz kütüphanesi olmadan** tkinter Canvas ile
  yuvarlak köşeli çizilsin; renkler tek bir `THEME` sözlüğünden gelsin (koyu + açık).
- Veri yokken boş grafik çizilmesin; duruma göre yönlendiren **boş durum ekranı** gösterilsin.
- `Ctrl+1..9` sayfa geçişi, `Ctrl+PgUp/PgDn` sıradaki sayfa, `F5` tazele.

## Dağıtım
- `build.bat`: PyInstaller'ı kontrol et (yoksa kur), `assets/app.ico` simgesini üret,
  tek dosyalık `dist\RussianCourseAI.exe` derle ve **masaüstüne kısayol koy**.
  `/noshortcut` ve `/onedir` seçenekleri olsun.
- `tools/make_shortcut.ps1`: exe varsa onu, yoksa `pythonw.exe` + `.pyw` hedefleyen
  kısayol üretsin — böylece derlemeden de kullanılabilsin.
- `tools/make_icon.py`: Pillow varsa çok boyutlu `.ico` üretsin, yoksa sessizce geçsin.

## Veri modeli (asgari tablolar)
`profiles`, `words(id, ru, ru_norm, tr, en, stress_pos, pos, aspect_pair_id, freq_rank, audio,
tags, example_ru, example_tr)`, `word_progress(profile_id, word_id, box, easiness, interval,
repetition, due_date, correct, wrong, last_seen, starred)`, `grammar_topics`, `topic_progress`,
`questions`, `exams`, `exam_answers`, `packs`, `pdf_notes`, `resource_state`, `study_log`,
`token_log`.

## Kalite kuralları
- Her özellik **çevrimdışı çalışmalı**; ağ çağrısı yalnızca kullanıcı NIM'i açıkça açarsa veya Kaynak Merkezinden bir dosya indirmeyi kendisi başlatırsa yapılsın.
- TLS sertifika doğrulaması **hiçbir koşulda kapatılmasın**. Python'un gömülü kök deposu eskiyse `truststore` (işletim sistemi deposu) veya `certifi` denensin, hangisinin kullanıldığı Ayarlar'da yazsın.
- API anahtarı Windows Credential Manager'da tutulsun, **diske düz metin yazılmasın**.
- AI'ın ürettiği kod/komut **yalnızca onay penceresinden geçerek**, yalıtılmış alt süreçte çalışsın.
- Uzun işlemler arayüzü kilitlemesin (thread + kuyruk); her panel **tembel yüklensin**.
- Rusça metin her yerde UTF-8; `ё` ve vurgu işaretleri arama sırasında normalize edilsin.
- Hiçbir modül başka bir modülün iç değişkenine dokunmasın; ortak şeyler `rca_common.py`'de.
- Arayüz doğrudan SQL yazmasın; her erişim repository sınıfları üzerinden olsun.
- Hata yönetimi: DB bozuksa, ses motoru yoksa, PDF kütüphanesi eksikse program **çökmesin**,
  kullanıcıya anlaşılır mesaj göstersin.
- `requirements.txt` sürüm sabitli (pinned) olsun; `README.md` kurulum, çalıştırma, exe alma,
  CSV formatı, paket formatı ve kısayolları anlatsın.

## Teslim sırası (adım adım uygula, her adımda çalışan program bırak)
1. `rca_common.py` + `Russian_Course_AI.pyw` iskeleti: pencere, tema, sekme çerçeveleri, ayarlar.
2. SQLite şeması + profil yönetimi + `app_paths` göçü.
3. Kelime Bankası & Sözlük → Aralıklı Tekrar → Sınav Motoru (öğrenme döngüsünü kapat).
4. PDF Okuyucu + annotation.
5. LM Studio istemcisi + AI Öğretmen + token defteri.
6. Kiril Lab → Telaffuz Stüdyosu → Dilbilgisi Laboratuvarları.
7. Konuşma Pratiği, El Yazısı Tahtası, Öğrenci Takip raporları.
8. Paket dışa/içe aktarma, çok dilli arayüz, kılavuz modülü, `tests/` seti.
9. Kaynak Merkezi: katalog + indirici + lisans manifesti + sözlük içe aktarıcı.
10. Simge, `build.bat` ile exe üretimi ve masaüstü kısayolu.

Her adımın sonunda: değişen dosyaları özetle, testleri çalıştır, sonucu raporla.
