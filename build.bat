@echo off
REM ==========================================================================
REM  Russian Course AI - Windows .exe uretimi + masaustu kisayolu
REM
REM  Kullanim:
REM      build.bat              -> exe uret ve masaustune kisayol koy
REM      build.bat /noshortcut  -> yalnizca exe uret
REM      build.bat /onedir      -> tek dosya yerine klasor olarak uret (daha hizli acilir)
REM
REM  Cikti: dist\RussianCourseAI.exe
REM ==========================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul

set MODE=--onefile
set SHORTCUT=1
for %%A in (%*) do (
    if /I "%%A"=="/onedir" set MODE=--onedir
    if /I "%%A"=="/noshortcut" set SHORTCUT=0
)

echo.
echo  ============================================
echo   Russian Course AI - derleme
echo  ============================================
echo.

echo [1/5] Python kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo      HATA: python PATH uzerinde bulunamadi.
    goto :hata
)
python --version

echo [2/5] PyInstaller kontrol ediliyor...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo      PyInstaller bulunamadi, kuruluyor...
    python -m pip install --quiet pyinstaller
    if errorlevel 1 goto :hata
)

echo [3/5] Simge hazirlaniyor...
if not exist assets\app.ico (
    python tools\make_icon.py
)
set ICONARG=
if exist assets\app.ico set ICONARG=--icon assets\app.ico

echo [4/5] Derleniyor... (birkac dakika surebilir)
REM  pyttsx3 GPL-3.0 lisanslidir. Ikili paket MIT kosullariyla dagitildigi icin
REM  --exclude-module pyttsx3 ile disarida birakilir; seslendirme Windows'un
REM  System.Speech (PowerShell) yedegine duser, ozellik kaybi olmaz.
REM  Ayrintili gerekce: THIRD_PARTY_NOTICES.md, "pyttsx3 hakkinda".
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist RussianCourseAI.spec del /q RussianCourseAI.spec

python -m PyInstaller ^
    --noconfirm --clean %MODE% --windowed ^
    --name RussianCourseAI ^
    %ICONARG% ^
    --add-data "grammar;grammar" ^
    --add-data "assets;assets" ^
    --collect-submodules rca ^
    --hidden-import rca.secrets ^
    --hidden-import rca.dictionary ^
    --hidden-import rca.dict_data ^
    --hidden-import rca.ai_client ^
    --hidden-import rca.pdf_backend ^
    --hidden-import rca.tabs.dictionary_tab ^
    --hidden-import rca.tabs.vocab_tab ^
    --hidden-import rca.tabs.srs_tab ^
    --hidden-import rca.tabs.exam_tab ^
    --hidden-import rca.tabs.cyrillic_tab ^
    --hidden-import rca.tabs.pron_tab ^
    --hidden-import rca.tabs.grammar_tab ^
    --hidden-import rca.tabs.resources_tab ^
    --hidden-import rca.tabs.pdf_tab ^
    --hidden-import rca.tabs.library_tab ^
    --hidden-import rca.tabs.ai_tab ^
    --hidden-import rca.tabs.speaking_tab ^
    --hidden-import rca.tabs.writing_tab ^
    --hidden-import rca.tabs.progress_tab ^
    --hidden-import rca.tabs.packs_tab ^
    --hidden-import rca.tabs.tokens_tab ^
    --hidden-import rca.tabs.guide_tab ^
    --hidden-import rca.tabs.settings_tab ^
    --exclude-module pytest ^
    --exclude-module matplotlib ^
    --exclude-module pyttsx3 ^
    Russian_Course_AI.pyw
if errorlevel 1 goto :hata

if not exist dist\RussianCourseAI.exe (
    if not exist dist\RussianCourseAI\RussianCourseAI.exe goto :hata
)

echo [5/5] Masaustu kisayolu...
if "%SHORTCUT%"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\make_shortcut.ps1
) else (
    echo      atlandi ^(/noshortcut^)
)

echo.
echo  ============================================
echo   BITTI
echo  ============================================
if exist dist\RussianCourseAI.exe echo   Cikti : %cd%\dist\RussianCourseAI.exe
if exist dist\RussianCourseAI\RussianCourseAI.exe echo   Cikti : %cd%\dist\RussianCourseAI\RussianCourseAI.exe
echo   Veri  : %%APPDATA%%\RussianCourseAI
echo.
goto :son

:hata
echo.
echo  HATA: derleme basarisiz oldu. Yukaridaki ciktiya bakin.
endlocal
exit /b 1

:son
endlocal
