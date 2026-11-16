; Inno Setup Script for Trip Mo, Trip Ko — Nueva Ecija Travel Desktop App
; Compiles dist\NuevaEcijaTravel\* into a single one-click Setup.exe installer

#define MyAppName "Trip Mo, Trip Ko - Nueva Ecija Travel"
#define MyAppShortName "NuevaEcijaTravel"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Edward Renz Natividad (Edselrenz)"
#define MyAppURL "https://edselrenz.github.io/Itinerary-App/"
#define MyAppExeName "NuevaEcijaTravel.exe"

[Setup]
AppId={{8F9E4A21-5C6D-4B8A-9E12-7D3C5A9B1E04}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; Installs to %LOCALAPPDATA%\Programs\NuevaEcijaTravel by default (no Admin prompt needed, full write access to storage/ and tiles_cache/)
DefaultDirName={autopf}\{#MyAppShortName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist_installer
OutputBaseFilename=NuevaEcijaTravel_Setup_v{#MyAppVersion}
SetupIconFile=..\desktop_client\assets\icon\app_icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}\storage"; Permissions: users-modify
Name: "{app}\storage\exports"; Permissions: users-modify
Name: "{app}\storage\avatars"; Permissions: users-modify
Name: "{app}\assets\tiles_cache"; Permissions: users-modify

[Files]
; Pack the entire compiled PyInstaller + Flet Flutter distribution
Source: "..\dist\NuevaEcijaTravel\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\NuevaEcijaTravel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\storage"
Type: filesandordirs; Name: "{app}\assets\tiles_cache"
