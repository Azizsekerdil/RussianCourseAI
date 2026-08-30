# Russian Course AI

[Türkçe](README.md) | **English**

[Trilingual promotional PDF](output/pdf/Russian-Course-AI-Trilingual.pdf) ·
[Editable PowerPoint](docs/presentation/Russian-Course-AI-Trilingual.pptx)

Russian Course AI is a Windows desktop learning workspace for studying Russian
from A1 through C1. It brings structured review, vocabulary, grammar,
pronunciation, reading, writing, exams, progress tracking, and an optional local
AI tutor into one application.

The interface supports **Türkçe, English, and Русский**. Language changes apply
immediately and are remembered for the next launch.

## Highlights

- Spaced review with SM-2/Leitner scheduling and five practice modes
- Turkish-Russian-English word bank with CSV import and export
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
downloads or the optional NVIDIA NIM endpoint.

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

## Main workspaces

| Area | What it provides |
|---|---|
| Spaced Review | Daily dashboard, flashcards, typing, listening, matching, and multiple choice |
| Word Bank | TR/RU/EN vocabulary, frequency lists, examples, favorites, and CSV tools |
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

The test suite covers the database, spaced-repetition calculations, quiz engine,
content packages, multilingual text integrity, and UI smoke flows.

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
```

Downloaded learning resources and generated application builds are intentionally
excluded from version control.
