; Script generated for Inno Setup
#define MyAppName "MSA"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "Studio Tai"
#define MyAppURL "https://studiotai.com"
#define MyAppExeName "MSA.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{D374B08C-8F92-4E86-9C31-3F6D43997A21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; "ArchitecturesAllowed=x64" specifies that Setup cannot run on anything but x64.
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Output locations
OutputDir=..\dist
OutputBaseFilename=MSA_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; The main executable and all dependencies from the PyInstaller build
Source: "..\dist\MSA\MSA.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\MSA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
