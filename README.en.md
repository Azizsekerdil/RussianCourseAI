# Russian Course AI

[Türkçe](README.md) | **English**

[Trilingual promotional PDF](output/pdf/Russian-Course-AI-Trilingual.pdf) ·
[Editable PowerPoint](docs/presentation/Russian-Course-AI-Trilingual.pptx)

[User guide (English)](docs/USER_GUIDE.md) - installation, all 18 pages, the dictionary, AI setup, and troubleshooting.

Russian Course AI is a Windows desktop learning workspace for studying Russian
from A1 through C1. It brings structured review, vocabulary, grammar,
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
- PDF reader with notes, annotations, selected-text lookup, and AI explanation
- Exams, weak-topic analysis, learning streaks, and weekly progress summaries
- Optional local AI through an OpenAI-compatible LM Studio server
- Multiple learner profiles, light/dark themes, and offline text-to-speech
- Resource library limited to public-domain or Creative Commons material

## Privacy and connectivity

Study data is stored locally in SQLite. The AI tutor can run locally through LM
Studio, so core learning does not require a cloud account. Network access is
used only for features the user explicitly chooses, such as Resource Center
downloads or the optional alternative AI endpoint (off by default).

The alternative endpoint's API key is kept in Windows Credential Manager (a
local file in the settings folder on other systems) and is never written to
`settings.json`. It can also be supplied through the `RUSSIANCOURSEAI_API_KEY`
environment variable.

The token log stores counts, model names, task types, and timing information;
it does not store prompt or response text.

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

## Main workspaces

| Area | What it provides |
|---|---|
| Spaced Review | Daily dashboard, flashcards, typing, listening, matching, and multiple choice |
| Word Bank | TR/RU/EN vocabulary, frequency lists, examples, favorites, and CSV tools |
| Dictionary RU-EN-TR | Direction selector (`dict_direction`): Auto (Cyrillic searches RU->EN, Latin picks EN->RU or TR->RU by best match), RU→EN, EN→RU, RU→TR, TR→RU - a fixed direction searches only its source side; Russian / English / Turkish columns (Turkish first in Turkish directions); built-in core plus OpenRussian layer; listen, add to word bank (Turkish gloss becomes the bank's TR field), ask the AI, CSV import/export (`ru, en, tr, pos, extra, source`, legacy `ru, en, pos, extra` accepted) |
| Exam | Multiple question types, automatic scoring, and mistake tracking |
| Cyrillic Lab | All 33 letters, handwriting forms, stroke practice, and confusion drills |
| Pronunciation | Stress, reduction rules, rough IPA, TTS, and optional microphone comparison |
| Grammar Labs | Cases, aspect, verbs of motion, numbers, syntax, notes, and exercises |
| PDF Reader | Zoom, annotations, text selection, vocabulary lookup, and AI explanation |
| AI Tutor | Explain, translate, correct writing, and optional image/OCR tasks |
| Progress | Mastery, weak topics, exam trends, and weekly summaries |

## Tests

```bash
python -m pytest -q
```

The test suite (177 tests) covers the database and its schema migration, spaced-repetition calculations, quiz engine, the RU-EN-TR dictionary engine
(direction selector, auto direction with Turkish queries, CSV with the `tr` column), the AI dictionary layer (a mock OpenAI-compatible server,
English + Turkish glosses, provider resolution, the secrets store),
content packages, multilingual text integrity, the PDF backend (page count and size, rendering that scales with the zoom, top-left word boxes, and an annotated export that pypdf can reopen), and UI smoke flows. No test touches the network,
LM Studio, or Windows Credential Manager.

## Project structure

```text
Russian_Course_AI.pyw   Application entry point and shell
rca/                    Data, AI, content, localization, and UI modules
rca/tabs/               Feature workspaces
grammar/                Built-in grammar notes
tests/                  Unit and UI smoke tests
assets/                 Application icon assets
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
engine. Material downloaded from the Library is not part of the repository and
keeps its own open licence.
