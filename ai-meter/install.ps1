# AI-Meter installer for this Windows user (no admin rights needed).
# Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 [-StartWithWindows]
param([switch]$StartWithWindows)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\AI-Meter'

# Stop a running copy so the exe can be replaced.
Get-Process -Name 'AI-Meter' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

# Replace the program files only. Your settings and history live elsewhere
# (%APPDATA%\AI-Meter and %LOCALAPPDATA%\AI-Meter) and are kept.
if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item (Join-Path $here 'app\*') -Destination $installDir -Recurse -Force
Copy-Item (Join-Path $here 'ai-meter.ico') -Destination $installDir -Force -ErrorAction SilentlyContinue
$extDst = Join-Path $installDir 'extension'
if (Test-Path $extDst) { Remove-Item $extDst -Recurse -Force }
Copy-Item (Join-Path $here 'extension') -Destination $extDst -Recurse -Force

$target = Join-Path $installDir 'AI-Meter.exe'
$icon = Join-Path $installDir 'ai-meter.ico'
$shell = New-Object -ComObject WScript.Shell
$links = @((Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\AI-Meter.lnk'),
           (Join-Path ([Environment]::GetFolderPath('Desktop')) 'AI-Meter.lnk'))
foreach ($lnkPath in $links) {
    $lnk = $shell.CreateShortcut($lnkPath)
    $lnk.TargetPath = $target
    $lnk.WorkingDirectory = $installDir
    if (Test-Path $icon) { $lnk.IconLocation = "$icon,0" }
    $lnk.Description = 'AI-Meter - AI subscription usage and cost per job'
    if ($lnkPath -like '*Start Menu*') { $lnk.Hotkey = 'CTRL+ALT+M' }
    $lnk.Save()
    Write-Output "shortcut: $lnkPath"
}
$startup = Join-Path ([Environment]::GetFolderPath('Startup')) 'AI-Meter.lnk'
if ($StartWithWindows) {
    $lnk = $shell.CreateShortcut($startup)
    $lnk.TargetPath = $target
    $lnk.WorkingDirectory = $installDir
    $lnk.Save()
    Write-Output "starts with Windows: $startup"
}

Write-Output ""
Write-Output "Installed: $target"
Write-Output "Browser extension folder: $extDst"
Write-Output "Next: Chrome/Edge -> Extensions -> Developer mode -> Load unpacked -> pick the folder above."
Start-Process $target -ArgumentList '--dashboard'
