# Russian Course AI - masaustu kisayolu olusturur.
#
# Once derlenmis exe aranir (dist\...). Bulunamazsa python + .pyw ile
# calisan bir kisayol yapilir, boylece exe olmadan da calisir.
#
# Kullanim:  powershell -ExecutionPolicy Bypass -File tools\make_shortcut.ps1

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$linkPath = Join-Path $desktop 'Russian Course AI.lnk'
$icon = Join-Path $root 'assets\app.ico'

$exeOneFile = Join-Path $root 'dist\RussianCourseAI.exe'
$exeOneDir = Join-Path $root 'dist\RussianCourseAI\RussianCourseAI.exe'

if (Test-Path $exeOneFile) {
    $target = $exeOneFile
    $arguments = ''
    $workdir = Split-Path -Parent $exeOneFile
    $kind = 'exe (tek dosya)'
}
elseif (Test-Path $exeOneDir) {
    $target = $exeOneDir
    $arguments = ''
    $workdir = Split-Path -Parent $exeOneDir
    $kind = 'exe (klasor)'
}
else {
    # exe yok - pythonw ile kaynaktan calistir
    $pyw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue)
    if ($null -eq $pyw) {
        $pyw = (Get-Command python.exe -ErrorAction SilentlyContinue)
    }
    if ($null -eq $pyw) {
        Write-Host '      HATA: ne exe ne de python bulundu; kisayol olusturulamadi.'
        exit 1
    }
    $target = $pyw.Source
    $arguments = '"' + (Join-Path $root 'Russian_Course_AI.pyw') + '"'
    $workdir = $root
    $kind = 'python + .pyw (kaynaktan)'
}

$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut($linkPath)
$link.TargetPath = $target
if ($arguments -ne '') { $link.Arguments = $arguments }
$link.WorkingDirectory = $workdir
$link.Description = 'Russian Course AI - cevrimdisi Rusca ogrenme istasyonu'
if (Test-Path $icon) { $link.IconLocation = $icon }
$link.Save()

Write-Host "      Kisayol olusturuldu: $linkPath"
Write-Host "      Hedef: $kind"
