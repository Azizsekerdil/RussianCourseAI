# Russian Course AI — User Guide

Version 1.3.0 · Windows and macOS desktop application · Interface languages: Türkçe / English / Русский

- [1. About this guide](#1-about-this-guide)
- [2. Installation](#2-installation)
- [3. First launch](#3-first-launch)
- [4. Screens](#4-screens)
- [5. Dictionary (in detail)](#5-dictionary-in-detail)
- [6. Artificial intelligence](#6-artificial-intelligence)
- [7. Data management](#7-data-management)
- [8. Shortcuts and tips](#8-shortcuts-and-tips)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Release notes summary](#10-release-notes-summary)
- [11. Frequently asked questions](#11-frequently-asked-questions)
- [12. Licence](#12-licence)

---

## 1. About this guide

This document is the user guide for **Russian Course AI 1.3.0**. The program is a desktop workspace for studying Russian from A1 to C1, holding 20 pages in a single window.

How to read it: **if you are starting out**, read sections 2 and 3, then the `Aralikli Tekrar`, `Kelime Bankasi` and `Sozluk RU-EN-TR` pages in section 4 — the program works at full capacity without any AI. **If you will use the dictionary heavily**, go straight to section 5. **If you want to connect the AI**, see section 6.

**A note on spelling.** Labels written `in code style` are quoted **exactly as they appear on screen**. The Turkish locale currently renders most of its text without diacritics (`Kelime Bankasi`, `Sozluk RU-EN-TR`, `Ogrenci Takip`), and this guide keeps page and button names in that Turkish form so you can find them regardless of the interface language you have chosen; the English label follows in parentheses where it helps.

---

## 2. Installation

### 2.1 Windows (zip)

1. Download the Windows zip file from the release archive.
2. Extract the zip **completely** into a folder.
3. Double-click **`RussianCourseAI.exe`**.

No installation is required: there is no administrator prompt, no registry entry and no uninstaller; deleting the folder is enough (your data lives in a separate folder, see 2.4). To build your own exe, run `build.bat` in the repository root; `build.bat /onedir` produces a folder instead of a single file and starts noticeably faster.

### 2.2 macOS (zip)

The macOS package is built for Apple Silicon and is **not notarized**, so Gatekeeper warns you the first time.

1. Open `RussianCourseAI-macOS.zip`.
2. Move `RussianCourseAI.app` into your `Applications` folder.
3. Instead of double-clicking, **right-click → Open**, then press **Open** again in the warning dialog.

You only have to confirm once. You can build your own package on a Mac with `./build_macos.sh`.

### 2.3 Running from source

Python 3.11 or newer is enough:

```bash
python Russian_Course_AI.pyw
```

The core needs no external packages (tkinter, sqlite3, urllib). For the optional features:

```bash
pip install -r requirements.txt
```

A missing package never stops the program; only the related buttons stay greyed out: `pypdfium2` + `pypdf` (PDF), `pillow` (handwriting PNG and image questions), `pymorphy3` (exact morphology), `vosk` + `sounddevice` (microphone pronunciation), `truststore` / `certifi` (Library downloads).

**Audio components (optional).** For the `Konusma Tanima (Whisper)` and `Sesli Kitap` pages and the neural voices, also run:

```bash
pip install -r requirements-audio.txt
```

This installs `faster-whisper` (Whisper speech recognition) and `sounddevice`, plus — on Windows/Linux — the `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` wheels for NVIDIA GPU acceleration; **no CUDA Toolkit is needed**, the program loads the DLLs from those packages. Without a GPU, Whisper falls back to the CPU on its own; on macOS the NVIDIA lines are skipped. The same file installs the audiobook engines: `piper-tts` (offline, GPL-3.0) and `edge-tts` (online, LGPL-3.0). Because of their licences these two packages are **deliberately not bundled** into the distributed `.exe` / `.app`; to use them, run the program from source and install them yourself. If the packages are missing, the page in question prints the reason and the install command, and the rest of the program is unaffected.

### 2.4 Where your data is kept

| System | Data folder |
|---|---|
| Windows | `%APPDATA%\RussianCourseAI` |
| macOS | `~/Library/Application Support/RussianCourseAI` |
| Linux | `~/.russiancourseai` |

Contents: `data/rca.db` (SQLite), `settings/settings.json`, `exports/` (default target for exports), `logs/`; if you use the audio components, also `models/whisper` (Whisper models), `models/piper` (Piper voices) and `audiobooks/` (your audiobooks). The program directory holds read-only content: `Resources/` and `grammar/`. On macOS `Resources/` sits inside the data folder instead, because a signed `.app` bundle cannot be written to.

**Portable use.** If the `RCA_HOME` environment variable is set, the program uses it as the data folder:

```bat
set RCA_HOME=E:\RussianCourseAI-data
RussianCourseAI.exe
```

---

## 3. First launch

There is no setup wizard. On its first run the program creates the data folders, builds the SQLite schema, loads the built-in **A1 deck** (125 words in 9 decks: `A1 Temel`, `Gunluk Hayat`, `Yiyecek`, `Fiiller`, `Hareket Fiilleri`, `Sifatlar`, `Sayilar`, `Zamirler`, `Edatlar`), creates a profile named `Ogrenci` (Learner), and loads the built-in dictionary of 1,360 stress-marked entries with Turkish glosses into memory.

The window has a grouped sidebar on the left, a profile selector, language selector and AI status pill along the top, and a status bar at the bottom showing the path of the data folder.

| Setting | Default | Where |
|---|---|---|
| Interface language | `Türkçe` | The 🌐 selector in the top bar (applies instantly) or `Ayarlar` → `Dil:` |
| Theme | `dark` | `Ayarlar` → `Tema:` (`dark` / `light`) |
| Daily goal | `20` words/day | `Ayarlar` → `Gunluk hedef:` |
| CEFR level | `A1` | `Ayarlar` → `CEFR seviyesi:` (A1–C1) |

A language change applies instantly; a theme change needs a restart to reach everywhere, and `Ayarlar` reminds you of that when you save.

**Profile.** Pick a profile from the list in the top bar; the `+` button creates a new one. Review history, exams and statistics belong to the profile; the word bank and the dictionary are shared by all profiles.

---

## 4. Screens

The order below is the sidebar's own order.

### 4.1 Learn (`Ogren`)

#### Spaced Review (`Aralikli Tekrar`)

**What it is for.** The daily review hub; the SM-2 / Leitner algorithm computes each word's next review date itself, and the dashboard makes no AI call.

**How to use it.** Look at the six cards on the `Bugun` (Today) dashboard (`Bugun tekrar edilecek`, `Yanlislar`, `Denenmemis`, `Ogrenildi`, `Seri`, `Dogruluk`). Choose a format in the `Mod` list (`Kart`, `Coktan secmeli`, `Yazarak`, `Dinleme`, `Eslestirme`), set the length with `Adet`, then press `▶ Tekrar`, `✗ Yanlis drill`, `✚ Yeni kelime` or `★ Favoriler`. In `Kart` mode **Space** flips the card and **1 / 2 / 3** grade it; in `Yazarak` and `Dinleme` type the answer and press **Enter** (or `Kontrol Et`); in `Coktan secmeli` and `Eslestirme` click the right option.

**Tip.** The badge in the sidebar shows how many reviews are due; an empty badge means you are done for the day.

#### Word Bank (`Kelime Bankasi`)

**What it is for.** The permanent store of the words you have learned; review, exam and statistics pages all feed from it.

**How to use it.** Type Turkish, Russian or English into the box and press `Ara`; narrow the list with `Deste` and `Frekans` (`hepsi`, `ilk 100`, `ilk 500`, `ilk 1000`). **Double-click** a word to hear it; the right panel shows IPA, an example sentence, the aspect pair and your statistics. Buttons: `🔊 Dinle`, `★ Favori`, `AI'a sor`, `Sil`, `+ Ekle`, `CSV Ice Aktar`, `CSV Disa Aktar`.

**Tip.** The import format is `kelime;anlam;ornek;deste` (word; meaning; example; deck), and the header row is optional.

#### Dictionary RU-EN-TR (`Sozluk RU-EN-TR`)

**What it is for.** The word bank holds only your own words; this page is a trilingual dictionary for **every** word you meet while reading. Details: [section 5](#5-dictionary-in-detail).

#### Exam (`Sinav`)

**What it is for.** Recognition and production are different skills; the exam measures the second one.

**How to use it.** Tick the question types in the `Sinav kur` box: `Coktan secmeli (RU->TR)`, `Coktan secmeli (TR->RU)`, `Bosluk doldurma`, `Dogru hali sec`, `Fiili cek`, `Ceviri TR->RU`, `Ceviri RU->TR`, `Dinleme`, `Kelime dikte`. Choose `Soru sayisi:` (5–60) and `Kaynak:` (`Karisik`, `Vakti gelenler`, `Yanlislar`, `Yeni kelimeler`), press `▶ Basla`, and confirm each answer with **Enter**. The program tolerates equivalent translations and, when unsure, offers `Dogru say` / `Yanlis say` / `Yine de dogru say`.

**Tip.** Every word you get wrong is marked "wrong" in the bank and joins the `Yanlis drill` queue.

### 4.2 Labs (`Laboratuvar`)

#### Cyrillic Lab (`Kiril Lab`)

**What it is for.** The alphabet is the first wall in Russian, and cursive (курсив) looks nothing like print.

**How to use it.** Four tabs: `Alfabe (33 harf)`, `Yazim / El yazisi`, `Karisan ciftler`, `Alistirma`. In the writing tab pick a letter, press `▶ Yazim sirasini oynat`, write it yourself on the canvas and click `Karsilastir`; `Tuvali temizle` resets it. In the practice tab press `▶ 12 soruluk tur baslat`.

**Tip.** The `Karisan ciftler` tab puts the confusable pairs ш/щ, б/в, и/й, ь/ъ side by side.

#### Pronunciation (`Telaffuz & Vurgu`)

**What it is for.** In Russian the position of the stress changes the meaning, and unstressed `о` is read [a].

**How to use it.** Type a word and press `Coz`, or pick one with `Bankadan sec`; the program shows the syllables, a rough IPA reading and the reduction rules. Correct the stress from the `Vurgulu hece:` list and press `🔊 Dinle` to hear it. When speech recognition is available, `● Kaydet ve karsilastir` appears in the `Mikrofonla tekrar` box: the program records a few seconds and compares what it heard with the target word. Recognition uses **Whisper** first (when at least one model has been downloaded on the `Konusma Tanima (Whisper)` page) and falls back to Vosk otherwise. The engine in use is shown in brackets to the right of the button (`(whisper)` / `(vosk)`).

**Tip.** If the microphone section is disabled, the reason is printed there; either download a Whisper model on the `Konusma Tanima (Whisper)` page or extract the Vosk `ru` model into `%APPDATA%\RussianCourseAI\models\vosk-ru`. For sentence-level, word-by-word coloured feedback, use the `Telaffuz` tab of the Whisper page.

#### Speech Recognition (`Konusma Tanima (Whisper)`)

**What it is for.** Speech recognition with Whisper (faster-whisper) that runs **entirely on your computer**: it transcribes audio and video files or translates them into English, takes dictation from the microphone, and scores a Russian sentence you say word by word. The internet is used only the first time a model is downloaded.

**How to use it.** The top bar is shared by all tabs:

- `Model:` — the sizes `tiny`, `base`, `small`, `medium`, `large-v1` / `large-v2` / `large-v3`, the distilled `distil-*` models and the English-only `.en` variants. The default is **`large-v3-turbo`** (~1.6 GB, close to large accuracy, very fast); the turbo model does **not translate** into English, so pick `large-v3` or `medium` for `Ingilizceye cevir`. The line below shows the selected model's size and whether it is `indirilmis, hazir` (downloaded, ready) or `indirilmedi (ilk kullanimda indirilir)` (not downloaded, downloads on first use).
- `Modeli indir` asks for confirmation and downloads the model **once** into `%APPDATA%\RussianCourseAI\models\whisper`; `Yukle` loads it into memory ahead of time, `Bellekten bosalt` frees GPU memory / RAM, and 📂 opens the model folder.
- `Aygit:` (device) is `auto` (`cuda` when an NVIDIA GPU is present, otherwise `cpu`), `cuda` or `cpu`. `Hesap turu:` (compute type) is `auto`, `float16`, `int8_float16`, `bfloat16`, `int8` or `float32`; `auto` picks `float16` on the GPU and `int8` on the CPU. If the GPU cannot be loaded the program does not stop — it switches to the CPU.
- The status line below reads `GPU hazir (...)` (GPU ready) or `GPU yok - CPU kullanilacak` (no GPU, CPU will be used), and adds the loaded model's name and device/compute type.

There are four inner tabs:

- **`Dosya`** (File) — choose an audio/video file with `Dosya sec...` (mp3, wav, m4a, ogg, opus, flac, mp4, mkv…) or process every file in a folder with `Klasoru toplu isle...` (a `.srt` and a `.txt` are written next to each file). Set `Gorev:` to `Yaziya dok` (transcribe) or `Ingilizceye cevir` (translate to English); `Dil:` is `auto` (detect) or a fixed language. `Dili algila` shows the five most likely languages with their probabilities and selects the first. `▶ Baslat` runs and `■ Durdur` stops; the text streams in segment by segment with timestamps, and at the end the language, duration, speed (real-time factor) and device are summarised. With `Kelime guvenini renklendir` ticked, words Whisper is unsure of are shown in yellow (medium) and red (low). The `TXT`, `SRT`, `VTT`, `TSV`, `JSON` and `LRC` buttons on the `Disa aktar:` row write a file; `Kopyala` copies to the clipboard, and `AI Ogretmen'e gonder` moves the text to the `AI Ogretmen` page for an explanation or translation.
- **`Mikrofon`** (Microphone) — the microphone in use is shown at the top. `● Kaydet` starts recording and `■ Bitir` stops and transcribes; `🎙 Canli dikte` writes the text live while you speak (the not-yet-final part appears dimmed). `Dil:` defaults to `ru`. A level meter and the elapsed time are shown while recording; `Kaydi WAV olarak sakla` writes the last recording to a WAV file.
- **`Telaffuz`** (Pronunciation) — type a target Russian sentence or fetch an example sentence from the word bank with `Bankadan sec`, listen with `🔊 Dinle`, press `● Kaydet`, say it and press `■ Bitir`. Whisper compares what it heard with the target word by word: green = correct, yellow = correct but unclear, red = different (what it heard in brackets), struck through = skipped, blue = extra. `Puan` (score) is out of 100, and the `Duyulan` (heard) line shows Whisper's full text. Every attempt is logged in the `Ogrenci Takip` statistics as pronunciation study (85 and above counts as correct).
- **`Gelismis ayarlar`** (Advanced settings) — every Whisper option, in groups: `Kod cozme` (decoding: `beam_size`, `best_of`, `patience`, `length_penalty`, `repetition_penalty`, `no_repeat_ngram_size`, `temperature` with its fallback list, `prompt_reset_on_temperature`), `Esikler ve dil algilama` (thresholds and language detection: `compression_ratio_threshold`, `log_prob_threshold`, `no_speech_threshold`, `hallucination_silence_threshold`, `language_detection_threshold`, `language_detection_segments`), `Dil, istem ve metin` (language, prompt and text: `Varsayilan dil`, `multilingual`, `initial_prompt`, `prefix`, `hotwords`, `condition_on_previous_text`, `suppress_blank`, `clip_timestamps`), `Zaman damgalari` (timestamps: `word_timestamps`, `without_timestamps`, `max_initial_timestamp`, `chunk_length`), `VAD (konusma algilama, Silero)` (`vad_filter`, `threshold`, `min_speech_duration_ms`, `min_silence_duration_ms`, `speech_pad_ms`, `max_speech_duration_s`) and `Performans` (`batched`, `batch_size`, `cpu_threads`). `Ayarlari kaydet` saves them, and `Varsayilanlara don` resets everything except the model/device choice.

**Tip.** On an NVIDIA card with plenty of VRAM, `large-v3-turbo` + `float16` + `batched` processes long files far faster than real time; on the CPU, `small` or `medium` + `int8` is a better fit. If you see invented text in silent stretches, keep `vad_filter` on. If names or terms come out wrong, add them to `initial_prompt` or `hotwords`.

#### Grammar Labs (`Dilbilgisi Lab`)

**What it is for.** Cases, aspect and verbs of motion are the three hardest areas of Russian for a Turkish speaker.

**How to use it.** Six tabs: `Notlar (.md)`, `Hal Lab (Падежи)`, `Fiil Lab (Вид)`, `Hareket Fiilleri`, `Sayi & Olcu`, `Soz Dizimi`. Every lab follows rule → table → live example → exercise; press `▶ 10 soruluk tur baslat` at the bottom of the page, and in `Soz Dizimi` type a sentence and press `Ayristir`.

**Tip.** The `Notlar (.md)` tab reads the `grammar/*.md` files, so you can add your own notes there.

### 4.3 Read (`Oku`)

#### Course Resources (`Kurs Kaynaklari`)

**What it is for.** Lists your course files as a tree and tracks which ones you have finished.

**How to use it.** `Kok klasor:` defaults to the `Resources` folder; pick another with `Degistir`, and the list filters as you type in the search box. Selecting a file and pressing **Space**, or the `☐/☑ Bitirdim (Space)` button, toggles the mark. Other buttons: `PDF Okuyucuda ac`, `Varsayilan programda ac`, `Klasoru goster`, `Yazdir`.

**Tip.** The marks are stored per profile.

#### PDF Reader (`PDF Okuyucu`)

**What it is for.** Lets you read, annotate and question your textbook without leaving the program.

**How to use it.** Open a file with `📂 PDF ac`, then navigate with `◀` / `▶`, `Git...`, `−` / `+` and `Genislige sigdir`. The tools are `✏ Kalem`, `🖍 Isaretleme`, `🔤 Metin`, `🧽 Silgi` and `⬚ Metin sec`. After selecting text, use `AI'a acikla`, `Sozlukte ara`, `🔊` or `Bankaya ekle` in the right panel. Type into `Sayfa notu` and press `Notlari kaydet`; `Isaretli PDF disa aktar` writes a new PDF with the annotations embedded, and `Sayfayi temizle` clears the current page.

**Tip.** This page needs `pypdfium2` (viewing/text) and `pypdf` (annotated export); the text you select is also available on the `AI Ogretmen` page through `PDF'teki secimi al`.

**Cyrillic and Turkish characters in note text.** In the output of `Isaretli PDF disa aktar` the **full text of your note is always preserved** and shows up complete in your PDF reader's comment/annotation pane. The copy that is **drawn onto the page**, however, uses the built-in Helvetica font and can only show Western European characters: Cyrillic letters and Turkish letters such as `ı`, `ş`, `ğ` and `İ` appear as `?` on the page itself. If you take notes in Cyrillic, read them in the comment pane; highlights, pen strokes and yellow marks are unaffected.

#### Audiobook (`Sesli Kitap`)

**What it is for.** Turns your textbook (for example a Russian beginner's book) into an audiobook page by page, and lets you pick **any section or page** to listen to. Every part is read with a voice for its own language — Russian sentences in Russian, Turkish explanations in Turkish, English parts in English — and the sentence being read is highlighted in the text panel.

**How to use it.**

- **Book.** Choose a book from the `Kitap:` list at the top. For a new one, press `PDF'ten yeni kitap...` (New book from PDF) and pick the PDF; the program asks whether you have a prepared narration script folder (`pNNN.json` files) for this book. Answer **Yes** and point to the folder to use the curated script (missing pages are filled from the PDF); answer **No** and the script is generated automatically from the PDF text (Cyrillic → Russian, Turkish letters/words → Turkish, everything else → English). The line under the book shows the page count, how many pages have been generated with the selected engine and the script source (`elle hazirlanmis betik` curated, `kismen hazir betik` partly curated, `PDF metninden otomatik betik` automatic); 📂 opens the book folder. Books live under `%APPDATA%\RussianCourseAI\audiobooks\`.
- **Contents.** The `Icindekiler` (Contents) tree on the left is built from the PDF's table of contents: chapter → subsection → `Sayfa N`. The `Sayfa` column shows the page range and the last column the generation status for the selected engine: `✓` all ready, a value such as `3/8` partly ready, empty if nothing has been generated yet. **Double-click** a section or page, or press **Enter**, to start playing from there; selecting a section plays its ready pages in order. If the audio does not exist yet, the program offers to generate it now. Use **Ctrl** / **Shift** to select several items.
- **Player.** `⏮` / `⏭` previous / next page, `⏪` / `⏩` previous / next sentence (in the middle of a sentence `⏪` first returns to its start), `−10` / `+10` ten seconds back / forward, `▶` / `⏸` play / pause, `■` stop. Use the scrub bar to jump anywhere in the page. `Hiz:` (speed) ranges from 0.5x to 2x with the **pitch preserved** (slowing down does not deepen the voice). The `Ses:` (volume) slider goes up to 150%.
- **Repeat and continuous play.** With `Cumleyi tekrarla` (repeat sentence) ticked, the current sentence loops until you untick it — ideal for shadowing. With `Surekli cal` (continuous) on, the next generated page follows when a page ends. `⏯ Kaldigim yerden` (resume) brings back the book, page and position you last listened to (saved when you stop, when a page ends and when the program closes).
- **Text panel.** Shows the text of the playing page with the current sentence highlighted; Russian is in the normal colour, Turkish in green, English in dim grey, and headings are bold. **Click** any sentence to jump playback to it.
- **Audio generation.** In the `Ses uretimi` box at the bottom, choose `Motor:` **Piper** (`cevrimdisi` — offline, the default) or **Edge** (`cevrimici, Microsoft` — online); `Varsayilan yap` (make default) makes the selected engine the permanent default. On first use Edge asks for confirmation, warning that the text is sent to Microsoft servers; Piper is fully offline. Each language has its own voice (`Rusça:`, `Türkçe:`, `İngilizce:`; for example `ru_RU-irina-medium`, `tr_TR-dfki-medium`, `en_US-lessac-medium` with Piper, or `ru-RU-SvetlanaNeural`, `tr-TR-EmelNeural`, `en-US-AriaNeural` with Edge). `Sesleri dene` (try voices) plays a short sample with the selected voices; `Konusma hizi:` (speech rate, 0.6–1.5) sets the tempo of the generated audio.
- **Generate buttons.** `Secileni uret` (generate selection) generates the sections/pages selected in the tree and `Tum kitabi uret` (generate whole book) the entire book; `■ Durdur` stops. Generation runs in parallel (several processes with Piper, concurrent requests with Edge) and progress shows as `[k/total] sayfa N`. Pages whose script, voice and rate have not changed are **skipped**; tick `guncel olsa da yeniden uret` (regenerate even if current) to force a rebuild. Audio is stored per engine, so you can generate with both and switch between them with `Motor:` (the playing page switches to the new engine's audio). If a Piper voice you chose is not on the computer, the program offers to download it (`%APPDATA%\RussianCourseAI\models\piper`).
- **Export.** `Bolum MP3'lerini disa aktar...` (export chapter MP3s) asks for a folder and writes one MP3 per top-level chapter named `01 - Chapter title.mp3` (ID3 tags: title, album = book title, track number, page range) plus a `.m3u8` playlist in chapter order — handy for a phone or the car. Pages not yet generated are skipped.
- **Verify with Whisper.** `Whisper ile dogrula` has Whisper listen to the Russian parts of the playing page and compares them with the script. Suspicious sentences (misread or skipped by the speech engine) get a **red underline** in the text panel and are listed in the status line as `«script» → «heard»`. This needs a model downloaded on the `Konusma Tanima (Whisper)` page.

**Tip.** The same work can be done from the command line: `python tools/make_audiobook.py --help` lists every option (`--pdf`, `--script`, `--book`, `--engine piper|edge`, `--pages 4-9,15`, `--rate`, `--force`, `--export`, `--out`, `--workers`). The page needs `piper-tts` and/or `edge-tts` for generation and `av` + `sounddevice` for playback, all of which come with `requirements-audio.txt` (see 2.3).

#### Library (`Kaynak Merkezi`)

**What it is for.** Lists and downloads only openly licensed material (public domain or Creative Commons); nothing with an unclear licence enters the catalogue.

**How to use it.** Filter by kind: `Tumu`, `E-kitap`, `Ses`, `Sozluk / veri`, `Web` or `Video`. The right panel shows the provider, the licence and any attribution requirement. Press `Indir`; the file lands under `Resources/Indirilenler` next to a `LISANS.txt`. A downloaded PDF opens with `📕 PDF Okuyucuda ac`, and a downloaded OpenRussian dictionary goes into the word bank with `Aktar`.

**Tip.** The files the dictionary's OpenRussian layer needs are downloaded from the `Sozluk / veri` kind.

### 4.4 Practice (`Pratik`)

#### AI Tutor (`AI Ogretmen`)

**What it is for.** A tutor running on your own computer that you can ask *why* a sentence is wrong.

**How to use it.** Pick a task in the `Gorev:` list: `Dilbilgisi acikla`, `Ceviri RU -> TR`, `Ceviri TR -> RU`, `Yazi duzelt`, `Serbest soru`. `Model:` defaults to `(otomatik)`; `Modelleri tara` lets you choose one by hand. Type your text and press **Ctrl+Enter** or `▶ Sor`; listen to the answer with `🔊 Yaniti oku` and clear the field with `Temizle`. If a vision model is installed, `🖼 Gorsel / OCR` reads an image.

**Tip.** The `Yazi duzelt` answer has a fixed shape: HATA / KURAL / DOGRU / NEDEN (error / rule / correction / reason).

#### Speaking (`Konusma Pratigi`)

**What it is for.** Role-play dialogues locked to your CEFR level.

**How to use it.** Pick a scenario from `Senaryo:` (`Kafede siparis`, `Otel resepsiyonu`, `Doktorda`, `Magazada alisveris`, `Yol sormak`, `Is gorusmesi`, `Tanisma`, `Telefonda randevu`), choose A1–C1 in `Seviye:` and press `▶ Oturumu baslat`. Write in Russian and press `Gonder`; when you finish, press `⏹ Bitir ve rapor al`.

**Tip.** The end-of-session report lists your mistakes and the five words you should learn.

#### Handwriting (`El Yazisi`)

**What it is for.** Cyrillic cursive needs muscle memory, and this board is where you build it.

**How to use it.** Set the stroke width with the `Kalem:` slider and the colour from `Renk:`; choosing a letter in `Kilavuz:` places a faint template behind your writing. Write with a stylus or the mouse; `Geri al`, `Temizle` and `PNG kaydet` are ready, and `🤖 Ne yazdim?` asks a vision model to read what you wrote.

**Tip.** `PNG kaydet` and `🤖 Ne yazdim?` need `pillow`.

### 4.5 System (`Sistem`)

#### Progress (`Ogrenci Takip`)

**What it is for.** Measures the selected profile's progress; when there is no data it does not guess: the chart says `Bu donemde veri yok`, the trend says `Trend icin en az 2 sinav gerekir`, `Zayif konular` says `Konu verisi yok - dilbilgisi laboratuvarlarindan veya sinavdan alistirma yapin.`, and the mastery table shows `(veri yok)`.

**How to use it.** The cards, the `Son 30 gun - dogru cevap sayisi` chart, the `Sinav puani trendi`, the `Zayif konular` list and the `Kelime ustaligi (en dusuk 25)` table are computed automatically. `Yenile` recomputes them; `📄 Haftalik Ozet` opens a printable A4 report in your browser.

**Tip.** The page refreshes itself when you switch profiles, so two learners' data never mix.

#### Packs (`Paketler`)

**What it is for.** Moves the decks you build to another machine or another person.

**How to use it.** Fill in `Paket adi:` and `Yazar:`, choose `Kaynak deste:`, optionally tick `Kendi ilerlememi de ekle`, then press `📦 .rupack olustur`; `{ } .json olustur` exists for backward compatibility. Open an incoming pack with `📂 Paket ac (.rupack / .json)`.

**Tip.** A `.rupack` is a ZIP holding `paket.json` plus optional `audio/` and `images/` folders.

#### Token Log (`Token Defteri`)

**What it is for.** Makes your AI usage transparent; it keeps only the counters (model name, task type, token counts, duration). Your text is never stored.

**How to use it.** The cards summarise today / 7 days / 30 days / all time. Change the table with `Grupla:` (`Modele gore`, `Ise gore`, `Gune gore`); `CSV Disa Aktar` exports it and `Defteri temizle` deletes the records.

**Tip.** This is the easiest place to see how much traffic leaves your machine once you enable the alternative endpoint.

#### Guide (`Kilavuz`)

**What it is for.** A fully offline guide inside the program, describing every screen as WHY · HOW · BENEFIT.

**How to use it.** Read the page top to bottom; it ends with `Gizlilik` (privacy) notes and a shortcut table. `🖨 Yazdirilabilir surum` opens the same content as HTML formatted for A4.

**Tip.** The document you are reading is more detailed; the in-app guide needs no internet.

#### Settings (`Ayarlar`)

**What it is for.** The single place for interface, sound, AI, profile and data settings.

**How to use it.** The page is a stack of titled sections: `Arayuz` (`Dil:`, `Tema:`, `Gunluk hedef:`, `CEFR seviyesi:`), `Ses` (`Seslendirme acik`, `Hiz:` 80–260, `Test et`, `Kelime seslendirme motoru:`, `Sesli kitap varsayilan motoru:`), `Yapay zeka (yerel)` (`AI ozellikleri acik`, `LM Studio adresi:`, `Baglantiyi dene`, `Varsayilan model:`), `Alternatif uc (OpenAI uyumlu - INTERNET)` (see section 6), `Profiller` (`Yeni profil`, `Secili profili sil`) and `Veri` (`Veri klasorunu ac`, `Ilerlemeyi sifirla (bu profil)`, `Eksik seed kelimeleri geri yukle`). Changes are written when you press `Kaydet`.

**Speech engines.** `Kelime seslendirme motoru:` (word speech engine) decides which voice reads the 🔊 buttons throughout the program (word bank, dictionary, pronunciation, AI answers…): `Sistem sesi` (the operating system's voice, the default), `Piper (cevrimdisi, dogal)` (offline, natural) or `Edge (cevrimici, Microsoft)` (online). If the chosen neural engine is not installed or fails, the program quietly falls back to the system voice. `Sesli kitap varsayilan motoru:` (audiobook default engine: `Piper (cevrimdisi, dogal)` / `Edge (cevrimici, Microsoft)`) is the engine the `Sesli Kitap` page selects when it opens; the `Varsayilan yap` button on that page changes the same setting.

**Tip.** The language changes instantly; the theme needs a restart and the program reminds you.

---

## 5. Dictionary (in detail)

`Sozluk RU-EN-TR` merges four layers into one list: the built-in core, your own entries, downloaded OpenRussian data, and entries returned by the AI. The counter at the bottom of the page always shows that breakdown.

### 5.1 Direction selector

The `Yon:` list offers five options; your choice is stored in the `dict_direction` setting and survives a restart.

| Option | Side that is searched | When to choose it |
|---|---|---|
| `Otomatik` (Auto) | Cyrillic input searches the headword; Latin input scores **both** the English and the Turkish side and the best match wins | Everyday use |
| `RU → EN` | Russian headword only | Looking up the English of a Russian word |
| `EN → RU` | English glosses only | Looking up the Russian of an English word |
| `RU → TR` | Russian headword only, Turkish as target | Looking up the Turkish of a Russian word; a missing gloss is asked of the AI |
| `TR → RU` | Turkish glosses only | Looking up the Russian of a Turkish word |

A fixed direction searches **only** that direction's source side, which keeps the list clean for queries that resemble both Turkish and English. The small label to the right of the search box shows the **effective** direction of the search, so in `Otomatik` you can see what the engine decided.

### 5.2 The Turkish column and the detail panel

The list has six columns: `Rusca`, `Ingilizce`, `Türkçe`, `Tur`, `Cins / Gorunus`, `Kaynak`. When a direction that involves Turkish (`RU → TR` or `TR → RU`) is selected, the `Türkçe` column moves to sit right beside the headword.

The detail panel shows the stress-marked headword, a rough IPA reading, the part of speech and gender/aspect label, the `Ingilizce:` and `Türkçe:` lines, plus the example sentence and note when present. If the same word is in your word bank, a 📚 marker shows its meaning and deck there. Below are `Son aramalar` (your last 12 lookups) and the `AI yaniti` transcript; **double-clicking** a row speaks the word.

### 5.3 Search rules

The engine scores every entry and sorts the results by score:

| Match | Score |
|---|---|
| Exact match (the whole field, or one sense separated by `;`) | 100 |
| Exact match after stripping a leading `to` / `the` / `a` / `an` | 95 |
| Prefix: a sense or the field starts with the query | 60 |
| Inside a word: the query starts a word in the field | 30 |
| Substring (for queries of at least 3 characters) | 10 |
| Match found only through the ASCII / capital-letter fold (Turkish side) | 59% of the direct score: exact 59, prefix 35, inside a word 17, substring 5 |

On equal scores, in the directions that involve Turkish (`RU → TR` and `TR → RU`) the entry that **has** a Turkish gloss comes first, then the shorter headword, then alphabetical order. The folded match is tried only on the Turkish side, and only when the direct comparison finds nothing; that is why the query `ask` puts the English `to ask` ahead of the Turkish `aşk`.

Both the query and the field are normalized before comparison: case is ignored and `İ` folds to a plain `i` (`İstanbul` = `istanbul`); the **stress mark** is ignored (`приве'т` and `привет` reach the same entry); **ё → е** is folded (`ёлка` = `елка`); and the Turkish letters `ç ğ ı ö ş ü` are always shown in their correct spelling but fold to their ASCII equivalents for the comparison, so `sinav`, `SINAV` and `sınav` all reach the same entry (`ç→c`, `ğ→g`, `ı/İ→i`, `ö→o`, `ş→s`, `ü→u`). A query containing Turkish letters is still the hint that pulls `Otomatik` towards the Turkish side. The Cyrillic/Latin distinction only matters in `Otomatik`: as soon as a Cyrillic letter appears, the engine switches to `RU → EN`.

Typing two characters filters the list on its own; **Enter** commits the search, writes it to the history and, if needed, calls the AI. `🎲 Rastgele kelime` opens a random entry from the built-in core.

### 5.4 Source labels

| Label | Meaning |
|---|---|
| `gomulu` | The built-in core of 1,360 stress-marked entries with Turkish glosses |
| `kullanici` | Entries you added with `Madde ekle` or imported from CSV/TSV |
| `OpenRussian` | Openly licensed data you downloaded and loaded (its translations are English) |
| `AI` | An entry from the AI; once saved it becomes part of the local dictionary |

### 5.5 Filling a missing gloss with the AI

Unless the policy is `Kapali`, the dictionary calls the model by itself in two situations:

1. **No result.** The query goes to the model in the background; for each entry the model returns a stress-marked headword, part of speech, gender/aspect, **both an English and a Turkish** gloss, one short Russian example sentence and a note in your interface language. The results are added at the top of the list with the `AI` label.
2. **A missing Turkish gloss.** In the `RU → TR` direction, if the first entry found has no Turkish, the model is asked only to fill that gap; the returned gloss is merged into the existing entry **without creating a duplicate row**.

The `🤖 AI'a sor` button sends the query to the model by hand even when a local result exists. The interface never blocks: the query runs in the background with the `AI'a soruluyor...` waiting text, and if you start a new search the old answer is discarded silently.

**Saving.** `AI sonuclarini sozluge kaydet` is on by default: incoming entries are written to the local database with the `ai` source, so the next search is **instant and offline**. If you turn it off, entries live only on screen and you save the ones you like one by one with `💾 Sozluge kaydet`. That button appears only while an unsaved entry or an unsaved Turkish fill is selected.

### 5.6 Adding to the word bank

`📚 Kelime bankasina ekle` moves the selected entry into your study loop. The meaning written to the bank is the **first sense of the Turkish gloss**; if there is no Turkish, the first English sense is used. The stress position, the part of speech (with the gender merged in for nouns) and any example sentence come along, and the deck is named `Sozluk`. `Kopyala` copies the entry to the clipboard as `headword — English — Turkish`; when there is no Turkish gloss only `headword — English` is copied.

### 5.7 CSV import / export

`CSV disa aktar` writes the **visible results** when the list has any, and otherwise every entry except the OpenRussian layer. The default name is `sozluk_ru_en_tr.csv` and the default folder is `exports` inside your data folder.

| Column | Contents |
|---|---|
| `ru` | Russian headword; the stress is an apostrophe placed **immediately after** the stressed vowel |
| `en` | English gloss(es), separated by `; ` |
| `tr` | Turkish gloss(es), separated by `; ` (may be empty) |
| `pos` | Part of speech: `n v adj adv pron prep conj num part int phr` |
| `extra` | Gender `m f n pl` for nouns, aspect `ipf pf` for verbs, empty otherwise |
| `source` | `builtin` / `user` / `openrussian` / `ai` |

```csv
ru,en,tr,pos,extra,source
дом,house; home,ev; yuva,n,m,user
кни'га,book,kitap,n,f,user
говори'ть,to speak; to talk,konuşmak; söylemek,v,ipf,user
```

`CSV/TSV ice aktar` recognizes both comma and tab separators. If there is a header row the columns are matched **by name** in any order, and synonyms in Turkish, English and Russian are accepted (`Rusça`, `Türkçe`, `English`, `Tur`, `Kaynak`…); without a header the old positional layout applies: `ru, en[, pos[, extra]]`. The Russian and English fields are mandatory, and the program fixes rows written the other way round.

### 5.8 Adding an entry

`+ Madde ekle` opens a small window with the fields `Rusca (вург: приве'т)`, `Ingilizce`, `Türkçe`, `Tur (n/v/adj/...)` and `Cins / Gorunus (m/f/n/ipf/pf)`. Whatever is in the search box is pre-filled into the field matching its language. Russian and English cannot be empty; **Enter** saves and **Esc** closes the window.

### 5.9 Loading OpenRussian

1. On the `Kaynak Merkezi` page choose `Sozluk / veri` in the kind filter.
2. Download the OpenRussian files; they land in `Resources/Indirilenler/Sozluk` as `openrussian_*.tsv`.
3. Press `OpenRussian'i yukle` on the dictionary page. If the files are already there, the page loads them **by itself** when it opens.

Loading runs in the background and pushes the entry count into the tens of thousands. If the files are missing, the program shows `OpenRussian dosyalari yok. Kaynak Merkezi'nden 'Sozluk / veri' bolumunu indirin.`

**Note:** OpenRussian translations are **English**; entries in that layer carry no Turkish gloss. Searching them in the `RU → TR` direction shows an empty Turkish field, and the AI steps in to fill it if it is enabled.

---

## 6. Artificial intelligence

The AI is **optional**; with it switched off everything else — dictionary, review, exams and labs — keeps working.

### 6.1 Installing LM Studio and the local server

1. Install [LM Studio](https://lmstudio.ai).
2. Download a model; `qwen2.5-7b-instruct` is recommended, plus a vision model such as `qwen2-vl-7b-instruct` for image/OCR.
3. Start the **Local Server** inside LM Studio; the default address is `http://127.0.0.1:1234`.
4. The pill in the top bar is ready once it shows a model name; if it says `AI: cevrimdisi`, click it to probe again.
5. `Ayarlar` → `Baglantiyi dene` tests the connection and reports how many models it found.

A local address needs no API key: `localhost`, `127.0.0.1`, `.local`, `.lan` and private network addresses (10.x, 192.168.x, 172.16–31.x) are accepted without one.

### 6.2 Model selection

The program defines a model profile per task and picks the best of the **installed** models itself. The dictionary profile prefers, in order: `qwen2.5-7b-instruct`, `qwen2.5-14b-instruct`, `gemma-4-12b-qat`, `llama-3.1-8b-instruct`, `qwen3.6-35b-a3b`. An **exact match** in the profile wins first, then the same family (qwen, llama…), then general models; on ties, models of **4–16 billion parameters** and names containing `instruct`, `-it`, `chat` or `assistant` come first.

**Specialist models are skipped:** names containing `embed`, `embedding`, `rerank`, `math`, `coder`, `code-`, `vision`, `-vl`, `llava`, `moondream`, `whisper`, `tts`, `audio`, `clip`, `sd-`, `stable-diffusion`, `bio` or `medic` are unsuitable for text tasks and only enter the list when there is no alternative; for the image/OCR task the opposite applies and only a vision model is looked for. If no model is found the feature does not crash — the interface shows a calm warning.

### 6.3 Alternative endpoint

So the dictionary can still ask a model while LM Studio is off, `Ayarlar` has an `Alternatif uc (OpenAI uyumlu - INTERNET)` section. It is **off by default**; a network call happens only if you enable it.

1. Tick `Alternatif ucu kullan (varsayilan kapali)`.
2. Put an OpenAI-compatible address in `Adres (base URL):`; the default is NVIDIA NIM, `https://integrate.api.nvidia.com/v1`. OpenRouter, Groq, Ollama or any other OpenAI-compatible address also works.
3. Enter the model in `Model adi:` (the default is `meta/llama-3.1-8b-instruct`).
4. Paste your key into `API anahtari:`.
5. Test it with `Baglantiyi dene`; on success you see `Baglandi` and the model count. Then press `Kaydet`.

### 6.4 How the key is stored

The API key is **never** written to `settings.json`.

- **On Windows** the key goes into Windows Credential Manager under the target `RussianCourseAI/alt_api_key`.
- On other systems, or if Credential Manager is unavailable, it goes into `secrets.json` in the settings folder, with `0600` permissions where possible.
- If the `RUSSIANCOURSEAI_API_KEY` environment variable is set, it wins, so you can supply a key without storing it anywhere.

The settings page never shows the real key; it only prints `••••• kayitli (degistirmek icin yeni anahtari yazin)` or `anahtar kayitli degil`. `Anahtari sil` removes the key from both stores.

### 6.5 AI policy

The `dict_ai` setting decides which provider the dictionary uses. The same list appears both in the dictionary toolbar (`AI:`) and in `Ayarlar` → `Sozluk AI kaynagi:`, and the two follow each other.

| Policy | Behaviour |
|---|---|
| `Otomatik` (Auto) | Local if LM Studio is reachable, otherwise the alternative endpoint (if enabled) |
| `LM Studio (yerel)` | LM Studio only |
| `Alternatif uc` | The alternative endpoint only (unused if disabled or without a key) |
| `Kapali` (Off) | No AI call at all in the dictionary |

If the `AI ozellikleri acik` box is unticked, no call is made whatever the policy. The status label in the toolbar reports the current state: `LM Studio: bagli`, `Alternatif: hazir`, `AI cevrimdisi` or `AI kapali`. Reachability is checked in the background and cached for about 30 seconds, so no individual search waits on the network.

### 6.6 Token log and privacy

Every AI call writes one row to the `Token Defteri` page: model name, task type, prompt and completion token counts, duration and success. **Neither the request nor the response text is stored.**

The privacy rules: no data leaves the machine during core operation; the AI runs locally and only the text you select is sent to the model; a network call happens only when you enable the alternative endpoint or download from the Library; and the Library downloads only openly licensed material with TLS certificate verification that is never disabled.

---

## 7. Data management

**Profiles.** The `+` in the top bar, or `Ayarlar` → `Yeni profil`, creates a new learner. `Secili profili sil` removes the profile and its progress; the word bank and the dictionary are untouched.

**Backup.** The most reliable route is copying the whole data folder. For partial backups:

| Method | What it saves | Where |
|---|---|---|
| `CSV Disa Aktar` | The word bank (`kelime;anlam;ingilizce;ornek_ru;ornek_tr;deste` — word; meaning; English; Russian example; Turkish example; deck) | `Kelime Bankasi` |
| `CSV disa aktar` | Dictionary entries (`ru,en,tr,pos,extra,source`) | `Sozluk RU-EN-TR` |
| `📦 .rupack olustur` | One deck plus its questions, optionally your progress | `Paketler` |
| `CSV Disa Aktar` | Token usage records | `Token Defteri` |

**Data folder.** `Ayarlar` → `Veri` prints the full path, and `Veri klasorunu ac` opens it in your file manager. The same path is shown at the right end of the status bar.

**Resetting.** `Ilerlemeyi sifirla (bu profil)` deletes all review, exam and topic progress for the selected profile (the word bank is **not** deleted) and asks for confirmation. `Eksik seed kelimeleri geri yukle` restores built-in A1 words you have deleted without duplicating the ones you kept. To reset everything, delete the data folder while the program is closed; it rebuilds all of it on the next launch.

---

## 8. Shortcuts and tips

| Key | Action |
|---|---|
| `Ctrl+1` … `Ctrl+9` | Jump to one of the first nine pages (`Aralikli Tekrar`, `Kelime Bankasi`, `Sozluk RU-EN-TR`, `Sinav`, `Kiril Lab`, `Telaffuz & Vurgu`, `Konusma Tanima (Whisper)`, `Dilbilgisi Lab`, `Kurs Kaynaklari`) |
| `Ctrl+PgDn` / `Ctrl+PgUp` | Next / previous page |
| `F5` | Refresh the visible page |
| `Ctrl+Q` | Quit the program |
| `Space` | Flip the card in `Aralikli Tekrar` card mode |
| `1` / `2` / `3` | After flipping: `Bilmiyorum` / `Emin degilim` / `Biliyorum` (don't know / not sure / I know it) |
| `Enter` | Run the search (dictionary, word bank, pronunciation), check the answer (exam and typing modes), send the message (speaking) |
| `Ctrl+Enter` | Send the question in `AI Ogretmen` |
| `Space` | Toggle the `Bitirdim` mark in `Kurs Kaynaklari` |
| Double-click | Speak the selected word in the word bank and dictionary lists; play the section / page in the `Sesli Kitap` tree |
| `Enter` | Play the selected section / page in the `Sesli Kitap` tree |
| `Esc` | Close the add-entry / add-word window |

**Tips.** Clicking the AI pill in the top bar re-probes the connection. The grey text beside the page title is that page's own hint. In the dictionary the list filters after two characters; press **Enter** for the full result and, if needed, the AI. Text you select in `PDF Okuyucu` is waiting on the `AI Ogretmen` page behind `PDF'teki secimi al`.

---

## 9. Troubleshooting

**LM Studio will not connect.** *Cause:* the Local Server is not running, the address differs, or `AI ozellikleri acik` is off. *Fix:* start the **Local Server** in LM Studio, check that `LM Studio adresi:` is `http://127.0.0.1:1234` and press `Baglantiyi dene`. If the program says `Baglanti yok. LM Studio'yu acip Local Server'i baslatin.` the server really is down; the program still works fully without it.

**The AI returns an empty answer.** *Cause:* "thinking" models (gemma-4, qwen3 and similar) can spend the token budget on reasoning text and leave the content empty, or the chosen model is a specialist one. *Fix:* the program mitigates this **for dictionary queries** — it sends a field that disables thinking to the local server, and retries once with triple the budget when the answer was cut off. The other pages (`AI Ogretmen`, `Konusma Pratigi`) have no such retry. If it is still empty, load an instruction model such as `qwen2.5-7b-instruct`; `Modelleri tara` shows what is installed.

**There is no Turkish gloss.** *Cause:* the entry comes from the OpenRussian layer (its translations are English) or its `tr` field is empty. *Fix:* set the direction to `RU → TR` and press **Enter**; unless the policy is `Kapali`, the program asks the model for the missing gloss and merges it into the existing entry without a duplicate. If you would rather not use the AI, type the Turkish yourself with `+ Madde ekle`.

**macOS says the app "cannot be opened".** *Cause:* the application is not notarized, and Gatekeeper will not open an unrecognized developer's app directly. *Fix:* do not double-click; **right-click → Open** and press **Open** again in the warning. You confirm this only once.

**There is no sound.** *Cause:* `Seslendirme acik` is off, the system has no Russian voice, or the operating system's speech engine cannot be reached. *Fix:* read the status line in `Ayarlar` → `Ses` and press `Test et`; speech needs no extra package (`System.Speech` on Windows, `say` on macOS), but you do have to add a Russian speech package in your operating system's settings.

**Whisper does not use the GPU.** *Cause:* the status line says `GPU yok - CPU kullanilacak` (no GPU, CPU will be used) or the loaded model shows `(cpu/int8)`; the NVIDIA cuBLAS/cuDNN libraries were not found, the driver is old, or `Aygit:` is set to `cpu`. *Fix:* install the `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` wheels with `pip install -r requirements-audio.txt` (no CUDA Toolkit needed), update the NVIDIA driver, set `Aygit:` to `auto` or `cuda`, then press `Bellekten bosalt` → `Yukle`. If the GPU cannot be loaded, the program prints `GPU yuklenemedi, CPU'ya geciliyor...` and carries on with the CPU.

**The first GPU run is very slow.** *Cause:* on new-generation graphics cards the CUDA kernels are compiled for your card on first use (JIT), which can take a few minutes once. If the model is being used for the first time, the download time comes on top. *Fix:* let the first job finish; later runs are fast. To warm up ahead of time, press `Yukle` and transcribe a short file.

**A Piper voice is missing.** *Cause:* the Piper voice you chose (its `.onnx` file) is not in `%APPDATA%\RussianCourseAI\models\piper`. *Fix:* press `Secileni uret` or `Tum kitabi uret`; the program offers to download the missing voices from the internet and, once you confirm, downloads them and carries on generating. If it says `piper-tts kurulu degil` (not installed), run `pip install -r requirements-audio.txt` first.

**The Edge engine reports errors.** *Cause:* Edge voices are online; there is no internet connection, a firewall blocks it, or the Microsoft server is temporarily not answering. *Fix:* check your connection and try again; ready pages are skipped, so only the missing ones are generated. To work without the internet, switch `Motor:` to Piper.

**The audiobook does not play.** *Cause:* there is no audio output device or it is disabled (`ses cikis aygiti yok`), or `av` / `sounddevice` is not installed. *Fix:* connect speakers or headphones and make them the default output device in Windows, then restart the program; if a package is missing, run `pip install -r requirements-audio.txt`. The same applies to the microphone: if the `Mikrofon` tab finds no microphone, its record buttons stay greyed out.

**The exe will not start.** *Cause:* the zip was not fully extracted, an antivirus quarantined the file, or the single-file build is unpacking itself into a temporary folder. *Fix:* extract the zip into a real folder and run `RussianCourseAI.exe` from there; the first launch can take a few seconds. If the database cannot be opened, the program shows the path of the offending file — move it and restart.

**Where is my data.** *Cause:* the program directory and the data directory are deliberately separate, so updating never wipes your progress. *Fix:* `%APPDATA%\RussianCourseAI` on Windows, `~/Library/Application Support/RussianCourseAI` on macOS, `~/.russiancourseai` elsewhere; `Ayarlar` → `Veri klasorunu ac` takes you straight there. If `RCA_HOME` is set, the data lives there instead.

---

## 10. Release notes summary

| Version | Highlights |
|---|---|
| **v1.0.0** | First release: 17 pages, trilingual interface, offline operation, SM-2 spaced review, exam engine, Cyrillic and grammar labs, PDF reader, word bank, openly licensed Library, local LM Studio tutor, macOS package |
| **v1.1.0** | The `Sozluk RU-EN-TR` page: a bidirectional Russian–English dictionary, built-in core data, the OpenRussian layer and an **AI connection** (LM Studio or an alternative OpenAI-compatible endpoint); the API key is kept in Credential Manager |
| **v1.1.1** | Dictionary AI fixes: empty answers from thinking models, task-based model selection, repair of misplaced stress marks |
| **v1.1.2** | Dictionary polish: the `Cins / Gorunus` field, the effective-direction label, policy selection from the toolbar, removal of repeated senses |
| **v1.2.0** | **Direction selection and Turkish as a third language:** the `Otomatik / RU→EN / EN→RU / RU→TR / TR→RU` selector, a `Türkçe` column in the list and detail panel, Turkish glosses for all 1,360 built-in entries, filling a missing Turkish gloss with the AI without creating duplicates, CSV import/export with a `tr` column, and a `tr` column migration for older databases |
| **v1.2.1** | **ASCII and upper-case support in Turkish search:** `sinav`, `SINAV` and `sınav` return the same results; `cok` → `çok`, `ogrenci` → `öğrenci`, `gormek` → `görmek`. Folded matches rank below direct matches, so a user typing `ask` still gets the English gloss first, and the displayed spelling never changes. This **user guide** (`docs/USER_GUIDE.md`, Turkish `docs/KULLANIM_KILAVUZU.md`) was added to the repository, and its PDF is published as a release asset |
| **v1.3.0** | **MIT licence and a permissive PDF stack:** the PDF reader now uses `pypdfium2` (page rendering + text) and `pypdf` (writing annotated PDFs); AGPL-licensed **PyMuPDF** was removed. The project is released under the **MIT License**, `LICENSE` and `THIRD_PARTY_NOTICES.md` were added to the repository and ship inside the zip you download. The packages are built in a clean virtual environment: only the libraries listed in `requirements.txt` enter the bundle, so the download is smaller |

---

## 11. Frequently asked questions

**Can I use the program without the internet?** Yes; core operation is entirely offline. The network is used only when you enable the alternative AI endpoint and when you download a file from the Library.

**Is the program useful without the AI?** Very much so. Spaced review, exams, the word bank, the 1,360-entry built-in dictionary, the labs and progress tracking all work fully without it.

**What is the difference between the word bank and the dictionary?** `Kelime Bankasi` is your personal deck feeding the review and exam queues; `Sozluk RU-EN-TR` is the general dictionary you consult while reading. Move an entry you like into the bank with `📚 Kelime bankasina ekle`.

**Which direction should I choose?** Leave it on `Otomatik` if you are unsure. Choose `RU → TR` for the Turkish of a Russian word and `TR → RU` for the opposite; a fixed direction eliminates mixed matches.

**How do I write the stress mark?** You do not need it when searching. When adding an entry, mark the stress with an apostrophe **immediately after** the stressed vowel: `приве'т`, `кни'га`, `хорошо'`. One-syllable words and words containing `ё` are not marked.

**Will it find the word if I type `е` instead of `ё`?** Yes; `ё` is always folded to `е` before comparison.

**Where is my API key stored?** In Credential Manager on Windows, and in `secrets.json` inside the settings folder elsewhere; it is never written to `settings.json` and never displayed in the interface.

**Is the text I send to the AI stored?** No. The `Token Defteri` keeps only the model name, task type, token counts and duration.

**How do I move my data to another computer?** Copy the data folder as it is; use a `.rupack` for decks alone and `CSV disa aktar` for the dictionary alone.

**Can two people use the same computer?** Yes; create a second profile with `+`. Review history, exams and statistics are separated, while the word bank and dictionary stay shared.

**Do I have to load OpenRussian?** No. The built-in 1,360 entries cover A1–B1 and work instantly; OpenRussian is for those who want tens of thousands of entries.

**Will uninstalling delete my data?** No; deleting the program folder does not touch your data. To remove the data as well, delete the data folder from section 7 by hand.


---

## 12. Licence

Russian Course AI is released under the **MIT License**; the full text is in the
`LICENSE` file at the repository root. You may use, modify and redistribute the
program freely as long as the copyright and licence notice is kept.

The verified licences of every third-party component the program uses or bundles into
the `.exe` / `.app` package are listed in `THIRD_PARTY_NOTICES.md`. The PDF stack is
permissively licensed (`pypdfium2`: Apache-2.0 / BSD-3-Clause, `pypdf`: BSD-3-Clause)
and the project contains no AGPL-licensed component. The only copyleft component in the
package you download is `certifi` (MPL-2.0), which carries no extra obligation as long
as it is not modified. GPL-3.0 licensed `pyttsx3` is deliberately left out; speech uses
`System.Speech` on Windows and the built-in `say` command on macOS.

Material you download from the Library is not covered by the program's licence but by
its own open licence, and a `LISANS.txt` is written next to every download.
