# Russian Course AI

[![release](https://img.shields.io/github/v/release/Azizsekerdil/RussianCourseAI?display_name=tag&sort=semver&label=release&color=2ea44f)](https://github.com/Azizsekerdil/RussianCourseAI/releases/latest)
[![license MIT](https://img.shields.io/github/license/Azizsekerdil/RussianCourseAI?label=license&color=blue)](LICENSE)
[![platform Windows and macOS](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-0078D4)](https://github.com/Azizsekerdil/RussianCourseAI/releases/latest)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/downloads/)

[Türkçe](README.md) | **English**

[Trilingual promotional PDF](output/pdf/Russian-Course-AI-Trilingual.pdf) ·
[Editable PowerPoint](docs/presentation/Russian-Course-AI-Trilingual.pptx)

[User guide (English)](docs/USER_GUIDE.md) - installation, all 20 pages, the dictionary, AI setup, and troubleshooting.

Russian Course AI is a Windows and macOS desktop learning workspace for studying
Russian from A1 through C1. It brings structured review, vocabulary, grammar,
pronunciation, reading, writing, exams, progress tracking, and an optional local
AI tutor into one application.

The interface supports **Türkçe, English, and Русский**. Language changes apply
immediately and are remembered for the next launch.

## Highlights

- Spaced review with SM-2/Leitner scheduling and five practice modes
- Turkish-Russian-English word bank with CSV import and export
- Trilingual Russian-English-Turkish dictionary with a direction selector (Auto / RU→EN / EN→RU / RU→TR / TR→RU): 1,360 stressed built-in entries, 45,000+ with the downloadable OpenRussian data, TTS, CSV/TSV import
- AI dictionary lookup for missing words (and missing Turkish glosses) through LM Studio or an alternative OpenAI-compatible endpoint (NVIDIA NIM by default, or any URL + API key); results are cached into the local dictionary
- Cyrillic, pronunciation, stress, grammar, speaking, and handwriting labs
- Whisper speech recognition (optional, GPU-accelerated): every Whisper model, transcription and translation, language detection, live dictation, pronunciation check, TXT/SRT/VTT/TSV/JSON/LRC export
- PDF reader with notes, annotations, selected-text lookup, and AI explanation
- Audiobook from a PDF textbook: generate and listen to any chapter or page, sentence highlighting with click-to-seek, chapter MP3 + M3U8 export; offline Piper voices by default
- Exams, weak-topic analysis, learning streaks, and weekly progress summaries
- Optional local AI through an OpenAI-compatible LM Studio server
- Multiple learner profiles, light/dark themes, and offline text-to-speech
- Resource library limited to public-domain or Creative Commons material

## Privacy and connectivity

Study data is stored locally in SQLite. The AI tutor can run locally through LM
Studio, so core learning does not require a cloud account. Network access is
used only for features the user explicitly chooses, such as Resource Center
downloads or the optional alternative AI endpoint (off by default).

The audio features add only two network calls, both only when you explicitly use
them: **Edge TTS** (when selected, the narrated text is sent to Microsoft) and
**model downloads** (a Whisper model or Piper voice is fetched once on first use).
After that, Whisper and Piper run fully offline and microphone audio never leaves
the machine.

The alternative endpoint's API key is kept in Windows Credential Manager (a
local file in the settings folder on other systems) and is never written to
`settings.json`. It can also be supplied through the `RUSSIANCOURSEAI_API_KEY`
environment variable.

The token log stores counts, model names, task types, and timing information;
it does not store prompt or response text.

## Download

Ready-made packages are available - **no Python installation is required**. The
links below always point at the
[latest release](https://github.com/Azizsekerdil/RussianCourseAI/releases/latest)
and keep working as new versions are published.

| Package | Download |
|---|---|
| Windows (64-bit) | [RussianCourseAI-Windows.zip](https://github.com/Azizsekerdil/RussianCourseAI/releases/latest/download/RussianCourseAI-Windows.zip) |
| macOS (Apple Silicon) | [RussianCourseAI-macOS.zip](https://github.com/Azizsekerdil/RussianCourseAI/releases/latest/download/RussianCourseAI-macOS.zip) |
| User guide (PDF, Turkish) | [RussianCourseAI-Kullanim-Kilavuzu.pdf](https://github.com/Azizsekerdil/RussianCourseAI/releases/latest/download/RussianCourseAI-Kullanim-Kilavuzu.pdf) |

Unzip the archive and launch the application. The macOS bundle is **not
notarized**: on first launch do not double-click it - **right-click
`RussianCourseAI.app` and choose Open**, then confirm **Open** in the dialog.
Later launches work normally.

To run from source instead, see below.

## Quick start

Run from source with Python 3.11 or newer:

```bash
python Russian_Course_AI.pyw
```

The first launch creates the application data directory, initializes SQLite,
loads the built-in A1 starter vocabulary, and creates a default learner profile.

Install optional features with:

```bash
pip install -r requirements.txt
```

Whisper speech recognition and the audiobook need the optional audio set:

```bash
pip install -r requirements.txt -r requirements-audio.txt
```

## Optional dependencies

Core use needs nothing beyond the Python 3.11 standard library. When an optional
package is missing, the related buttons stay disabled and everything else keeps
working.

| Package | Enables |
|---|---|
| `pypdfium2` / `pypdf` | PDF rendering and text selection / annotated PDF export |
| `pillow` | Handwriting PNG export and the "what did I write?" image query |
| `pymorphy3` | Exact morphology tags (fallback: suffix heuristics) |
| `vosk` + `sounddevice` | Microphone pronunciation comparison (fallback when Whisper is absent) |
| `truststore` or `certifi` | Resource Center downloads |

Audio components live in `requirements-audio.txt`:

| Package | Enables |
|---|---|
| `faster-whisper` (+ `sounddevice`) | Speech Recognition (Whisper) page, Whisper microphone check on the Pronunciation page, audiobook verification |
| `nvidia-cublas-cu12` + `nvidia-cudnn-cu12` | Whisper on an NVIDIA GPU (falls back to CPU otherwise; skipped on macOS) |
| `piper-tts` (GPL-3.0, **not bundled**) | Offline neural voices - the default audiobook engine |
| `edge-tts` (LGPL-3.0, **not bundled**) | Online Microsoft Edge voices (optional engine) |

Word-level speech needs no package (Windows `System.Speech`, macOS `say`); Settings
can switch it to Piper or Edge, falling back to the system voice when the engine is
unavailable. `piper-tts` and `edge-tts` are excluded from the `.exe` / `.app`
(`--exclude-module piper` / `edge_tts`) to keep the distributed binaries MIT-compatible;
install them when running from source.

## Build the Windows application

```bash
build.bat
```

Available build options:

| Command | Result |
|---|---|
| `build.bat` | Single-file executable and desktop shortcut |
| `build.bat /noshortcut` | Single-file executable only |
| `build.bat /onedir` | Folder-based build with faster startup |

The executable is written to `dist/RussianCourseAI.exe`.

## Build the macOS application

```bash
./build_macos.sh
```

The script has to run **on a Mac**. It prepares a macOS-specific requirement set
(`vosk` 0.3.44, no GPL-3.0 `pyttsx3`), builds `dist/RussianCourseAI.app` with
PyInstaller, generates an `.icns` icon from `assets/app.png`, copies `LICENSE`
and `THIRD_PARTY_NOTICES.md` into the bundle's `Contents/Resources`, runs the
MIT licence check (`tools/check_build_licence.py`), and finally packs
`dist/RussianCourseAI-macOS.zip` with `ditto`.

The repository's only workflow, **macOS Paketi**
(`.github/workflows/build-macos.yml`), runs the same script on GitHub's
`macos-latest` runner. It is **manually triggered only** (`workflow_dispatch`):
when a tag is given in the `release_tag` input (for example `v1.3.0`) the
resulting zip is uploaded straight to that release, otherwise the zip is kept
as a workflow artifact.

The bundle is **not notarized**, so first-launch users go through right-click ->
Open.

## Optional local AI setup

1. Install [LM Studio](https://lmstudio.ai).
2. Download an instruction model, for example `qwen2.5-7b-instruct`.
3. Start LM Studio's Local Server at `http://127.0.0.1:1234`.
4. Open Russian Course AI. The AI status indicator turns green when ready.

The rest of the application remains available when no AI model is running.

### Alternative endpoint for the dictionary (optional, internet)

When a word is missing from the local dictionary, the RU-EN-TR Dictionary asks an
AI model and receives a structured entry (headword with stress, part of speech,
gender/aspect, English and Turkish translations, example sentence, note). In the
RU→TR direction an entry without a Turkish gloss triggers the same lookup and the
returned gloss is merged into the existing entry instead of creating a duplicate.
Two providers are available:

| Provider | Address | Key |
|---|---|---|
| LM Studio (local) | `http://127.0.0.1:1234` | not needed |
| Alternative endpoint | NVIDIA NIM `https://integrate.api.nvidia.com/v1` by default; any OpenAI-compatible URL (OpenRouter, Groq, Ollama, ...) | entered in Settings |

The `dict_ai` policy (also selectable from the dictionary toolbar) decides which
one is used: `auto` (LM Studio when reachable, otherwise the alternative
endpoint if enabled), `local`, `alt`, or `off`. AI results are saved into the
local dictionary with source `ai`, so the next lookup is instant and offline;
with autosave disabled, a selected AI entry can be saved with one click.

## Whisper speech recognition (optional)

After `pip install -r requirements-audio.txt` the **Speech Recognition (Whisper)**
page becomes available (faster-whisper / CTranslate2):

- **Models download once**: every model from tiny to large-v3 / large-v3-turbo,
  including distil-* and `.en` variants. A downloaded model is stored under
  `%APPDATA%\RussianCourseAI\models\whisper` and then works fully offline.
- **GPU is automatic**: with device `auto`, an NVIDIA card is used through CUDA,
  otherwise the CPU; the compute type (float16 / int8_float16 / int8 ...) follows the
  device. No CUDA Toolkit is needed - the cuBLAS / cuDNN DLLs come from the
  `nvidia-*-cu12` pip wheels.
- **All options**: transcription and translation to English, language detection with
  probabilities, audio/video file input, microphone recording and live dictation, word
  timestamps, Silero VAD filter, batched inference, pronunciation comparison (wrong /
  missing / extra words), and every decoding option on the Advanced tab (beam_size,
  best_of, patience, temperature fallback, thresholds, initial prompt, prefix, hotwords,
  repetition penalty, no-repeat n-gram, clip timestamps, hallucination silence
  threshold ...).
- **Output**: TXT, SRT, VTT, TSV, JSON, LRC.

The microphone check on the Pronunciation page also uses Whisper (Vosk as fallback).

## Audiobook (optional)

The **Audiobook** page turns a PDF textbook into an audiobook you can listen to
selectively:

1. **Book**: pick a PDF; a chapter tree is built from its table of contents. The book
   lives under `%APPDATA%\RussianCourseAI\audiobooks\<id>\`.
2. **Narration script**: language-tagged parts (ru / tr / en) for every page. A curated
   script folder can be imported; otherwise the script is generated automatically from
   the PDF's text layer. Each part is read with a voice for its own language.
3. **Per-page audio**: `pNNN.mp3` plus sentence timings (`pNNN.json`) for each page.
   Pages whose script, voice, and speed have not changed are not re-rendered; rendering
   runs in parallel.
4. **Listening**: choose any chapter or page; the current sentence is highlighted,
   clicking a sentence seeks to it, and there is sentence repeat, speed, volume,
   continuous play, and resume. A rendered page can be checked with Whisper.
5. **Export**: one MP3 per chapter (ID3-tagged) plus an M3U8 playlist.

Engines: **Piper** is the default and runs offline (voice models download once on
first use to `%APPDATA%\RussianCourseAI\models\piper`). **Edge** is optional and
sounds more natural, but **the text is sent to Microsoft**.

It also works from the command line:

```bash
python tools/make_audiobook.py --pdf Kitap.pdf --script betik/ --engine piper --export
```

See `python tools/make_audiobook.py --help` for `--pages 4-9,15`, `--rate 0.9`,
`--force`, `--workers N`, `--book <id>`, and more.

## Main workspaces

| Area | What it provides |
|---|---|
| Spaced Review | Daily dashboard, flashcards, typing, listening, matching, and multiple choice |
| Word Bank | TR/RU/EN vocabulary, frequency lists, examples, favorites, and CSV tools |
| Dictionary RU-EN-TR | Direction selector (`dict_direction`): Auto (Cyrillic searches RU->EN, Latin picks EN->RU or TR->RU by best match), RU→EN, EN→RU, RU→TR, TR→RU - a fixed direction searches only its source side; Russian / English / Turkish columns (Turkish first in Turkish directions); built-in core plus OpenRussian layer; listen, add to word bank (Turkish gloss becomes the bank's TR field), ask the AI, CSV import/export (`ru, en, tr, pos, extra, source`, legacy `ru, en, pos, extra` accepted) |
| Exam | Multiple question types, automatic scoring, and mistake tracking |
| Cyrillic Lab | All 33 letters, handwriting forms, stroke practice, and confusion drills |
| Pronunciation | Stress, reduction rules, rough IPA, TTS, and optional microphone comparison (Whisper, Vosk fallback) |
| Speech Recognition (Whisper) | File / Microphone / Pronunciation / Advanced: every Whisper model, GPU, transcription + translation, language detection, live dictation, VAD, TXT/SRT/VTT/TSV/JSON/LRC export |
| Grammar Labs | Cases, aspect, verbs of motion, numbers, syntax, notes, and exercises |
| PDF Reader | Zoom, annotations, text selection, vocabulary lookup, and AI explanation |
| Audiobook | Chapter tree from a PDF: render and play any chapter/page, sentence highlight + click-to-seek, repeat, speed, resume, Piper/Edge voices, chapter MP3 + M3U8 export, Whisper verification |
| AI Tutor | Explain, translate, correct writing, and optional image/OCR tasks |
| Progress | Mastery, weak topics, exam trends, and weekly summaries |

## Tests

```bash
python -m pytest tests -q
```

The test suite (244 tests, plus 5 skipped depending on the environment) covers the database and its schema migration, spaced-repetition calculations, quiz engine, the RU-EN-TR dictionary engine
(direction selector, auto direction with Turkish queries, CSV with the `tr` column), the AI dictionary layer (a mock OpenAI-compatible server,
English + Turkish glosses, provider resolution, the secrets store),
content packages, multilingual text integrity, the PDF backend (page count and size, rendering that scales with the zoom, top-left word boxes, and an annotated export that pypdf can reopen), the audio layer (`tests/test_audio.py`: Whisper
options and export formats, pronunciation comparison, the model catalog, the audiobook chapter tree, page rendering and
caching, chapter export, cancellation, player speed and seeking, and the ASR / speech fallbacks), and UI smoke flows.
No test touches the network, LM Studio, or Windows Credential Manager; the audio tests use a fake engine and download
no models.

## Project structure

```text
Russian_Course_AI.pyw   Application entry point and shell
rca/                    Data, AI, content, localization, and UI modules
rca/whisper_engine.py   faster-whisper wrapper: models, GPU, all options, microphone, export formats
rca/audiobook.py        Audiobook engine: book + script, Piper/Edge, page MP3 + timings, chapter export
rca/audio_player.py     Audio player (PyAV + sounddevice): seek, speed, volume
rca/i18n_audio.py       TR / EN / RU strings for the Whisper and Audiobook pages
rca/tabs/               Feature workspaces (20 pages)
grammar/                Built-in grammar notes
tests/                  Unit and UI smoke tests
assets/                 Application icon assets
tools/                  Icon generator, desktop shortcut, and licence checker
tools/make_audiobook.py Command-line audiobook rendering and export
requirements-audio.txt  Optional audio components (Whisper, CUDA, Piper, Edge)
build.bat               Windows build: executable and desktop shortcut
build_macos.sh          macOS build: .app bundle and distribution zip
.github/workflows/      Manually triggered "macOS Paketi" workflow
docs/presentation/      Editable promotional presentation and visual assets
output/pdf/             Final promotional PDF
LICENSE                 MIT licence text
THIRD_PARTY_NOTICES.md  Verified licences of third-party components
```

Downloaded learning resources and generated application builds are intentionally
excluded from version control.

## License

This project is released under the **MIT License** - full text in
[`LICENSE`](LICENSE).

The verified licences of every third-party component that is used or bundled in
the distributed binaries are listed in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). The PDF stack is permissively
licensed (`pypdfium2`: Apache-2.0 / BSD-3-Clause, `pypdf`: BSD-3-Clause) and the
repository contains no AGPL-licensed component. The only copyleft component in
the distributed `.exe` / `.app` is `certifi` (MPL-2.0, which - as long as it is
not modified - only requires carrying its licence text). GPL-3.0 licensed
`pyttsx3` is neither installed by `requirements.txt` nor bundled into the binary
(`--exclude-module pyttsx3`); speech falls back to the operating system's own
engine. For the same reason the optional `piper-tts` (GPL-3.0-or-later) and
`edge-tts` (LGPL-3.0) packages are not bundled either. Material downloaded from the Library is not part of the repository and
keeps its own open licence.
