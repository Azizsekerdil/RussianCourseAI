#!/usr/bin/env bash
set -eo pipefail

cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "HATA: macOS .app paketi bir Mac üzerinde oluşturulmalıdır."
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

rm -rf build/macos "dist/RussianCourseAI.app"
mkdir -p build/macos

# vosk==0.3.45'in macOS (arm64) icin PyPI dagitimi yok; macOS'ta 0.3.44 kullanilir.
# pyttsx3 GPL-3.0'dir: dagitilan .app saf MIT kalsin diye derleme ortamina hic
# kurulmaz (bkz. THIRD_PARTY_NOTICES.md). macOS'ta seslendirme zaten isletim
# sisteminin `say` komutuyla yapilir, ozellik kaybi yoktur.
sed -e 's/^vosk==0\.3\.45$/vosk==0.3.44/' -e '/^pyttsx3==/d' \
  requirements.txt > build/macos/requirements-macos.txt

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r build/macos/requirements-macos.txt
"$PYTHON_BIN" -m pip install pyinstaller

ICON_ARGS=()
if command -v sips >/dev/null && command -v iconutil >/dev/null && [[ -f assets/app.png ]]; then
  ICONSET="build/macos/RussianCourseAI.iconset"
  mkdir -p "$ICONSET"
  for size in 16 32 128 256 512; do
    sips -z "$size" "$size" assets/app.png --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z "$double" "$double" assets/app.png --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o build/macos/RussianCourseAI.icns
  ICON_ARGS=(--icon "$PROJECT_ROOT/build/macos/RussianCourseAI.icns")
fi

DATA_ARGS=()
[[ -d grammar ]] && DATA_ARGS+=(--add-data "$PROJECT_ROOT/grammar:grammar")
[[ -d assets ]] && DATA_ARGS+=(--add-data "$PROJECT_ROOT/assets:assets")

"$PYTHON_BIN" -m PyInstaller --noconfirm --clean --onedir --windowed \
  --workpath build/macos/pyinstaller --specpath build/macos \
  --name "RussianCourseAI" \
  --osx-bundle-identifier "com.russiancourseai.desktop" \
  "${ICON_ARGS[@]}" "${DATA_ARGS[@]}" \
  --collect-submodules rca \
  --hidden-import rca.secrets \
  --hidden-import rca.dictionary \
  --hidden-import rca.dict_data \
  --hidden-import rca.ai_client \
  --hidden-import rca.pdf_backend \
  --hidden-import rca.tabs.dictionary_tab \
  --hidden-import rca.tabs.vocab_tab \
  --hidden-import rca.tabs.srs_tab \
  --hidden-import rca.tabs.exam_tab \
  --hidden-import rca.tabs.cyrillic_tab \
  --hidden-import rca.tabs.pron_tab \
  --hidden-import rca.tabs.grammar_tab \
  --hidden-import rca.tabs.resources_tab \
  --hidden-import rca.tabs.pdf_tab \
  --hidden-import rca.tabs.library_tab \
  --hidden-import rca.tabs.ai_tab \
  --hidden-import rca.tabs.speaking_tab \
  --hidden-import rca.tabs.writing_tab \
  --hidden-import rca.tabs.progress_tab \
  --hidden-import rca.tabs.packs_tab \
  --hidden-import rca.tabs.tokens_tab \
  --hidden-import rca.tabs.guide_tab \
  --hidden-import rca.tabs.settings_tab \
  --exclude-module pytest --exclude-module matplotlib \
  --exclude-module pyttsx3 \
  "$PROJECT_ROOT/Russian_Course_AI.pyw"

APP_PATH="dist/RussianCourseAI.app"
[[ -d "$APP_PATH" ]] || { echo "HATA: $APP_PATH oluşturulamadı."; exit 1; }

ditto -c -k --keepParent "$APP_PATH" "dist/RussianCourseAI-macOS.zip"
echo "Tamamlandı: $APP_PATH"
echo "Dağıtım ZIP'i: dist/RussianCourseAI-macOS.zip"
