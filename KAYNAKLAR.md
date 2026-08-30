# Açık Lisanslı Kaynak Taraması

Bu belge, **Kaynak Merkezi** sekmesindeki kataloğun gerekçesidir: her kaynağın
nereden geldiği, lisansının ne olduğu ve bu lisansın nerede doğrulandığı.

**Kural:** katalogda yalnızca lisansı açıkça doğrulanmış kaynaklar bulunur —
kamu malı (public domain) veya Creative Commons. Lisansı belirsiz hiçbir şey
listeye girmez ve program telifli materyal indirmez. Bu kural bir testle
zorlanır: `tests/test_library.py::test_every_resource_has_a_known_open_license`.

İndirilen her dosyanın yanına, kaynağı ve lisansıyla birlikte bir `LISANS.txt`
yazılır.

---

## 1. Ders kitapları ve alıştırmalar — kamu malı

### FSI Russian FAST (US Foreign Service Institute)

ABD Dışişleri Bakanlığı'nın dil enstitüsü tarafından üretilmiştir. ABD telif
yasası uyarınca federal devlet eserleri **kamu malıdır** — serbestçe kullanılır,
çoğaltılır ve dağıtılır.

| Dosya | Boyut | İçerik |
|---|---|---|
| Ders 1-5 (tarama PDF) | 2.3 MB | Diyaloglar, kelime listeleri, alıştırmalar |
| Ders 6-8 (tarama PDF) | 1.5 MB | Devam |
| Ders 9-11 (tarama PDF) | 2.1 MB | Devam |
| Ders 1-5 (OCR metin PDF) | 5.3 MB | Metin katmanlı — program içinde seçip AI'a sorulabilir |
| Ders 6-8 (OCR metin PDF) | 4.0 MB | Metin katmanlı |
| Ders 9-11 (OCR metin PDF) | 5.2 MB | Metin katmanlı |
| Kaset 1-8 + Ek (MP3) | ~125 MB | Ana dili konuşan kayıtlar |

Lisans doğrulaması: Internet Archive öğe meta verisi `licenseurl` alanı —
`Fsi-RussianFastCourse-StudentText` için
`creativecommons.org/licenses/publicdomain/`, `FSIRussianFAST` için
`creativecommons.org/publicdomain/mark/1.0/`.

**Neden bu seçildi:** yapılandırılmış bir kurs (diyalog → kelime → alıştırma),
sesiyle birlikte, hiçbir telif kısıtı olmadan. Türkçe konuşan bir öğrenci için
ara dil İngilizce oluyor; buna karşılık materyalin yoğunluğu ve ses eşleşmesi
onu en iyi ücretsiz seçenek yapıyor.

---

## 2. Sözlük ve derlem verisi — Creative Commons

### OpenRussian (CC BY-SA 4.0)

`github.com/Badestrand/russian-dictionary` — OpenRussian.org sözlüğünün veri
dökümü. Tab ile ayrılmış dosyalar (uzantısı `.csv` olsa da içerik TSV'dir).

| Dosya | Boyut | Sütunlar |
|---|---|---|
| `nouns.csv` | 8.0 MB | vurgu işaretli biçim, cinsiyet, canlılık, 6 halin tekil/çoğul çekimi |
| `verbs.csv` | 5.4 MB | görünüş, görünüş çifti, emir kipi, geçmiş, şimdi/gelecek çekimleri |
| `adjectives.csv` | 8.0 MB | uzun/kısa biçimler, karşılaştırma |
| `others.csv` | 0.3 MB | zarf, edat, bağlaç, zamir, ünlem |

Vurgu, vurgulu sesli harften **sonra** gelen tek tırnakla gösterilir
(`челове'к`). Program bunu `stress_pos` indeksine çevirir
(`library._stress_from_accented`), böylece kelime kartlarında vurgu doğru
görünür ve telaffuz stüdyosunda çalışır.

Dosyalar **sıklık sırasındadır** — bu yüzden "en sık N kelimeyi içe aktar"
özelliği anlamlıdır.

**Atıf zorunluluğu:** OpenRussian.org, CC BY-SA 4.0. Örnek cümleler Tatoeba
projesindendir. Türetilmiş eser aynı lisansla paylaşılmalıdır.

**Dikkat:** çeviriler İngilizce ve Almancadır, Türkçe yoktur. İçe aktarıcı
Türkçe alanını varsayılan olarak İngilizce ile doldurur ki kartlar hemen
çalışsın; sonradan düzenlenebilir.

### Tatoeba (CC BY 2.0 FR)

`downloads.tatoeba.org` — 429 dilde 13 milyondan fazla cümle. Rusça dökümü
14.7 MB (bz2). Bazı cümleler CC0'dır.

**Atıf zorunluluğu:** Tatoeba.org katkıcıları, CC BY 2.0 FR.

---

## 3. Web kursları — Creative Commons

İndirilmez, katalogdan tarayıcıda açılır. Her birinin lisansı kendi sayfasında
belirtilir; bu yüzden `CC-VARIES` olarak işaretlenmiştir.

| Kaynak | Yayıncı | Not |
|---|---|---|
| **Между нами** | Michigan State University | Açık erişim ders kitabı + indirilebilir alıştırma ve ödev PDF'leri |
| **Sputnik** | sputniktextbook.org | Giriş düzeyi çevrimiçi kurs |
| **LLC Commons** | Less Commonly Taught Languages Partnership | CC lisanslı ders planları; Mellon Foundation destekli |
| **OER Commons** | oercommons.org | Açık eğitim kaynağı araması; her kaydın lisansı listede görünür |
| **Wikibooks Russian** | Wikibooks | CC BY-SA, topluluk yazımı tam ders kitabı |

---

## 4. Okuma ve dinleme — kamu malı

| Kaynak | Not |
|---|---|
| **LibriVox** | 60'tan fazla Rusça sesli kitap; kamu malındaki eserlerin gönüllü seslendirmeleri |
| **Project Gutenberg** | Telifi düşmüş Rus klasikleri (PDF/EPUB/TXT). PDF Okuyucuda açıp not alınabilir |

Bunlar B1+ seviyesi içindir; A1'de kullanışlı değildir.

---

## 5. Video

| Kaynak | Not |
|---|---|
| **Open Culture** | Ücretsiz Rusça video/ses ders listesi; her dersin lisansı kendi sayfasında |
| **FSI Language Courses** | FSI materyallerinin çevrimiçi sunumu — kamu malı |

---

## Elenen kaynaklar

Aramada çıkan ama katalogda **yer almayan** şeyler ve nedenleri:

| Kaynak | Neden elendi |
|---|---|
| `archive.org/details/russian-phonetics` | Öğe meta verisinde `licenseurl` yok — lisans belirsiz |
| Ticari sitelerdeki "ücretsiz" PDF ders kitapları | Ücretsiz erişim ≠ açık lisans; yeniden dağıtım hakkı yok |
| Scribd, benzeri paylaşım siteleri | Yükleyenin dağıtım hakkı doğrulanamıyor |
| YouTube ders kanalları | İçerik açık lisanslı değil; program video indirmez |
| OpenSubtitles altyazı derlemleri | Altyazıların telif durumu kaynağına göre değişiyor, toplu doğrulanamıyor |

---

## Yeni kaynak eklemek

`rca/library.py` içindeki `CATALOG` listesine bir `Resource` ekleyin. Zorunlu
alanlar: `license` (mutlaka `LICENSES` sözlüğünde tanımlı bir anahtar),
`url` (https), indirilebilirse `filename` ve `size_mb`. CC BY / CC BY-SA
kaynakları için `attribution` alanı **zorunludur** — test bunu kontrol eder.

Lisansı doğrulamadan ekleme yapmayın. Internet Archive için hızlı yol:

```bash
curl -s https://archive.org/metadata/<item-id> | python -c "import sys,json;print(json.load(sys.stdin)['metadata'].get('licenseurl'))"
```
