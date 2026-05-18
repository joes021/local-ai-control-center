#ifndef MyAppName
  #define MyAppName "Local AI Control Center"
#endif

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

#ifndef MySetupBaseName
  #define MySetupBaseName "Local-AI-Control-Center-Setup"
#endif

#ifndef SourceRoot
  #error "SourceRoot define is required."
#endif

#ifndef SupportRoot
  #error "SupportRoot define is required."
#endif

[Setup]
AppId={{54D4D6B8-A22A-4E0B-B0EF-7B5B6D7A8F01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Local AI Control Center
AppPublisherURL=https://github.com/joes021/local-qwen-control-center-next
DefaultDirName={autopf}\LocalAIControlCenterSetup
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyMemo=yes
DisableReadyPage=no
OutputDir=..\..\dist\windows
OutputBaseFilename={#MySetupBaseName}-{#MyAppVersion}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
Uninstallable=yes
CreateAppDir=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#SourceRoot}\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceRoot}\frontend\dist\*"; DestDir: "{app}\frontend\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceRoot}\launchers\windows\*"; DestDir: "{app}\launchers\windows"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceRoot}\install\windows\*"; DestDir: "{app}\install\windows"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceRoot}\run_control_center_next.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\version.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\release-notes.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SupportRoot}\config\profiles\*"; DestDir: "{app}\config\profiles"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SupportRoot}\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__\*,*.pyc"
Source: "{#SupportRoot}\assets\icons\*"; DestDir: "{app}\assets\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{app}\install\windows\setup-bootstrap.cmd"; DestDir: "{app}"; Flags: external skipifsourcedoesntexist

[Run]
Filename: "{app}\setup-bootstrap.cmd"; Description: "Run Local AI Control Center bootstrap"; Flags: postinstall skipifsilent runascurrentuser
