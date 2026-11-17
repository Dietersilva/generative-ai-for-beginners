# Builds AI-Meter.exe on Windows. Needs Python 3.11+ (python.org or `winget install Python.Python.3.12`).
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Check($what) { if ($LASTEXITCODE -ne 0) { throw "$what failed (exit $LASTEXITCODE)" } }

python -m venv .build-venv; Check "venv"
& .\.build-venv\Scripts\python.exe -m pip install --quiet --upgrade pip; Check "pip"
& .\.build-venv\Scripts\python.exe -m pip install --quiet "pyinstaller==6.11.1"; Check "install PyInstaller"
& .\.build-venv\Scripts\python.exe -m unittest discover -s tests; Check "tests"
& .\.build-venv\Scripts\pyinstaller.exe --noconfirm --clean --onedir --windowed --noupx `
    --name AI-Meter --icon ai-meter.ico `
    --add-data "aimeter\web;aimeter\web" `
    run_aimeter.py
Check "PyInstaller"

$out = Join-Path $PSScriptRoot 'dist\AI-Meter-package'
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Force -Path $out | Out-Null
# Folder build (exe + _internal): no self-extracting to %TEMP%, far fewer antivirus false positives.
Copy-Item dist\AI-Meter -Destination (Join-Path $out 'app') -Recurse -Force
Copy-Item ai-meter.ico, install.ps1, README.md -Destination $out -Force
Get-FileHash (Join-Path $out 'app\AI-Meter.exe') -Algorithm SHA256 | Format-List
Copy-Item extension -Destination $out -Recurse -Force
Compress-Archive -Path "$out\*" -DestinationPath dist\AI-Meter.zip -Force
Write-Output "Built: $out  and  dist\AI-Meter.zip"
