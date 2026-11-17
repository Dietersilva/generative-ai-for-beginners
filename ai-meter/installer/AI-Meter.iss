; Inno Setup script: builds AI-Meter-Setup.exe (no admin rights needed).
#define AppVersion "2.1.0"

[Setup]
AppId={{6F2B8C1E-4A7D-4E3B-9C55-2D8E61A0B7F4}
AppName=AI-Meter
AppVersion={#AppVersion}
AppVerName=AI-Meter {#AppVersion}
AppPublisher=AI-Meter (self-built)
DefaultDirName={localappdata}\Programs\AI-Meter
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=AI-Meter-Setup
SetupIconFile=..\ai-meter.ico
UninstallDisplayIcon={app}\AI-Meter.exe
UninstallDisplayName=AI-Meter
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
RestartApplications=no

[Tasks]
Name: "startup"; Description: "Start AI-Meter when I sign in to Windows"
Name: "desktopicon"; Description: "Create a desktop shortcut"

[InstallDelete]
; remove files from older versions (settings and history live elsewhere and are kept)
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\extension"
Type: filesandordirs; Name: "{app}\dashboard"

[Files]
Source: "..\dist\AI-Meter\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\extension\*"; DestDir: "{app}\extension"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\ai-meter.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\AI-Meter"; Filename: "{app}\AI-Meter.exe"; IconFilename: "{app}\ai-meter.ico"; HotKey: ctrl+alt+m
Name: "{userdesktop}\AI-Meter"; Filename: "{app}\AI-Meter.exe"; IconFilename: "{app}\ai-meter.ico"; Tasks: desktopicon
Name: "{userstartup}\AI-Meter"; Filename: "{app}\AI-Meter.exe"; IconFilename: "{app}\ai-meter.ico"; Tasks: startup

[Run]
Filename: "{app}\AI-Meter.exe"; Parameters: "--dashboard"; Description: "Start AI-Meter and open the dashboard"; Flags: nowait postinstall
Filename: "{app}\extension"; Description: "Open the browser extension folder (for Chrome/Edge 'Load unpacked')"; Flags: postinstall shellexec skipifsilent unchecked

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /IM AI-Meter.exe /F"; Flags: runhidden; RunOnceId: "StopAIMeter"
