# Builds AI-Meter.exe on Windows. Needs Python 3.11+ (python.org or `winget install Python.Python.3.12`).
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

python -m venv .build-venv
& .\.build-venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.build-venv\Scripts\python.exe -m pip install --quiet "pyinstaller==6.11.1"
& .\.build-venv\Scripts\python.exe -m unittest discover -s tests
& .\.build-venv\Scripts\pyinstaller.exe --noconfirm --clean --onefile --windowed `
    --name AI-Meter --icon ai-meter.ico `
    --add-data "aimeter\web;aimeter\web" `
    run_aimeter.py

$out = Join-Path $PSScriptRoot 'dist\AI-Meter-package'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Copy-Item dist\AI-Meter.exe, ai-meter.ico, install.ps1, README.md -Destination $out -Force
Copy-Item extension -Destination $out -Recurse -Force
Compress-Archive -Path "$out\*" -DestinationPath dist\AI-Meter.zip -Force
Write-Output "Built: $out  and  dist\AI-Meter.zip"
