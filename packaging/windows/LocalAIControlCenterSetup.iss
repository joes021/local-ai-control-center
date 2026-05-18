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
Source: "{#SourceRoot}\install\shared\*"; DestDir: "{app}\install\shared"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceRoot}\install\windows\*"; DestDir: "{app}\install\windows"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceRoot}\run_control_center_next.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\version.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceRoot}\release-notes.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SupportRoot}\config\profiles\*"; DestDir: "{app}\config\profiles"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SupportRoot}\scripts\*"; DestDir: "{app}\scripts"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__\*,*.pyc"
Source: "{#SupportRoot}\assets\icons\*"; DestDir: "{app}\assets\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SupportRoot}\launcher\windows\*"; DestDir: "{app}\support\launcher\windows"; Flags: ignoreversion recursesubdirs createallsubdirs

[Code]
var
  EditionPage: TInputOptionWizardPage;
  ModelSelectionPage: TInputOptionWizardPage;
  MoreModelsPage: TInputOptionWizardPage;
  AccessModePage: TInputOptionWizardPage;
  RuntimePage: TInputOptionWizardPage;
  SummaryPage: TOutputMsgMemoWizardPage;
  InstallRunExitCode: Integer;
  InstallRunStarted: Boolean;

function GetWizardFallbackDefaultModelId(): string;
begin
  Result := 'gemma-4-e4b-it-q4-0';
end;

function GetPreferredModelOptionIndex(): Integer;
var
  vramHintText: string;
  vramHintGiB: Integer;
begin
  Result := 0;
  vramHintText := GetEnv('LOCAL_AI_INSTALLER_VRAM_GIB');
  vramHintGiB := StrToIntDef(vramHintText, 0);

  if vramHintGiB >= 24 then
    Result := 2
  else if vramHintGiB >= 12 then
    Result := 1
  else if GetWizardFallbackDefaultModelId() = 'qwen3.6-35b-a3b-ud-iq2-xxs' then
    Result := 1
  else if GetWizardFallbackDefaultModelId() = 'qwen3.6-35b-a3b-mtp-ud-q4-k-xl' then
    Result := 2;
end;

function GetModelOptionCount(): Integer;
begin
  Result := 3;
end;

function GetModelField(ModelIndex: Integer; FieldName: string): string;
begin
  Result := '';

  if ModelIndex = 0 then begin
    if FieldName = 'id' then
      Result := 'gemma-4-e4b-it-q4-0'
    else if FieldName = 'label' then
      Result := 'Gemma 4 E4B Instruct Q4_0'
    else if FieldName = 'download' then
      Result := 'gemma-4-E4B-it-Q4_0.gguf'
    else if FieldName = 'vram' then
      Result := '6 GB'
    else if FieldName = 'option' then
      Result := 'Gemma 4 E4B Instruct Q4_0 - 6 GB VRAM class - safest default';
    exit;
  end;

  if ModelIndex = 1 then begin
    if FieldName = 'id' then
      Result := 'qwen3.6-35b-a3b-ud-iq2-xxs'
    else if FieldName = 'label' then
      Result := 'Qwen3.6 35B A3B UD IQ2_XXS'
    else if FieldName = 'download' then
      Result := 'Qwen3.6-35B-A3B-UD-IQ2_XXS.gguf'
    else if FieldName = 'vram' then
      Result := '12 GB'
    else if FieldName = 'option' then
      Result := 'Qwen3.6 35B A3B UD IQ2_XXS - 12 GB VRAM class - balanced Qwen pick';
    exit;
  end;

  if ModelIndex = 2 then begin
    if FieldName = 'id' then
      Result := 'qwen3.6-35b-a3b-mtp-ud-q4-k-xl'
    else if FieldName = 'label' then
      Result := 'Qwen3.6 35B A3B MTP UD Q4_K_XL'
    else if FieldName = 'download' then
      Result := 'Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf'
    else if FieldName = 'vram' then
      Result := '24 GB'
    else if FieldName = 'option' then
      Result := 'Qwen3.6 35B A3B MTP UD Q4_K_XL - 24 GB VRAM class - high-end profile';
    exit;
  end;
end;

function GetSelectedModelIndex(): Integer;
var
  i: Integer;
begin
  Result := 0;
  for i := 0 to GetModelOptionCount() - 1 do begin
    if ModelSelectionPage.Values[i] then begin
      Result := i;
      exit;
    end;
  end;
end;

function GetSelectedEdition(): string;
begin
  if EditionPage.Values[0] then
    Result := 'Unified'
  else
    Result := 'Classic';
end;

function GetSelectedAccessMode(): string;
begin
  if AccessModePage.Values[0] then
    Result := 'local-only'
  else
    Result := 'tailscale';
end;

function GetSelectedModelId(): string;
begin
  Result := GetModelField(GetSelectedModelIndex(), 'id');
end;

function GetSelectedModelLabel(): string;
begin
  Result := GetModelField(GetSelectedModelIndex(), 'label');
end;

function GetSelectedModelDownloadFile(): string;
begin
  Result := GetModelField(GetSelectedModelIndex(), 'download');
end;

function GetSelectedModelVramLabel(): string;
begin
  Result := GetModelField(GetSelectedModelIndex(), 'vram');
end;

function ShouldShowMoreModelsAfterInstall(): Boolean;
begin
  Result := MoreModelsPage.Values[0];
end;

function GetInstallScriptParameters(): string;
var
  turboSwitch: string;
  opencodeSwitch: string;
  moreModelsSwitch: string;
begin
  turboSwitch := '';
  opencodeSwitch := '';
  moreModelsSwitch := '';
  if not RuntimePage.Values[1] then
    turboSwitch := ' -SkipTurboQuant';
  if not RuntimePage.Values[0] then
    opencodeSwitch := ' -SkipOpenCodeInstall';
  if ShouldShowMoreModelsAfterInstall() then
    moreModelsSwitch := ' -ShowMoreModelsAfterInstall';

  Result :=
    '-NoProfile -ExecutionPolicy Bypass -File "' + ExpandConstant('{app}\install\windows\install.ps1') + '"' +
    ' -InstallRoot "' + ExpandConstant('{userprofile}\LocalQwenHome') + '"' +
    ' -Edition "' + GetSelectedEdition() + '"' +
    ' -AccessMode "' + GetSelectedAccessMode() + '"' +
    ' -SelectedModelId "' + GetSelectedModelId() + '"' +
    ' -SelectedModelLabel "' + GetSelectedModelLabel() + '"' +
    ' -SelectedModelDownloadFile "' + GetSelectedModelDownloadFile() + '"' +
    ' -SelectedModelVramClass "' + GetSelectedModelVramLabel() + '"' +
    ' -Profile "balanced"' +
    opencodeSwitch + turboSwitch + moreModelsSwitch;
end;

procedure InitializeWizard();
var
  preferredModelIndex: Integer;
  modelIndex: Integer;
begin
  InstallRunExitCode := 0;
  InstallRunStarted := False;

  EditionPage := CreateInputOptionPage(
    wpWelcome,
    'Choose installer edition',
    'Classic or Unified',
    'Unified installs the full local runtime plus the Control Center Next shell. Classic keeps only the legacy shell.',
    True,
    False
  );
  EditionPage.Add('Unified - full stack + Control Center Next');
  EditionPage.Add('Classic - legacy shell only');
  EditionPage.Values[0] := True;

  ModelSelectionPage := CreateInputOptionPage(
    EditionPage.ID,
    'Guided model selection',
    'Choose a starter model from the recommended installer picks',
    'The installer exposes three recommended models. Wizard preselection currently uses a local fallback plus optional LOCAL_AI_INSTALLER_VRAM_GIB hint. The authoritative shared catalog is read later by install.ps1.',
    True,
    False
  );
  for modelIndex := 0 to GetModelOptionCount() - 1 do
    ModelSelectionPage.Add(GetModelField(modelIndex, 'option'));
  preferredModelIndex := GetPreferredModelOptionIndex();
  ModelSelectionPage.Values[preferredModelIndex] := True;

  MoreModelsPage := CreateInputOptionPage(
    ModelSelectionPage.ID,
    'More model options',
    'Lightweight placeholder hook',
    'Prikazi jos modela does not open a browser inside setup. It only saves a post-install handoff so the app can later guide the user to Browser > Models.',
    False,
    False
  );
  MoreModelsPage.Add('Prikazi jos modela posle instalacije');

  AccessModePage := CreateInputOptionPage(
    MoreModelsPage.ID,
    'Access mode',
    'Choose how the installer should expose the control center',
    'Access mode changes how the service binds after setup. local-only is safest. tailscale exposes the UI through your tailscale network.',
    True,
    False
  );
  AccessModePage.Add('local-only');
  AccessModePage.Add('tailscale');
  AccessModePage.Values[0] := True;

  RuntimePage := CreateInputOptionPage(
    AccessModePage.ID,
    'Runtime components',
    'Choose optional components',
    'OpenCode and TurboQuant can be installed together with llama.cpp. OpenCode is recommended. TurboQuant needs CUDA-compatible build tools.',
    False,
    False
  );
  RuntimePage.Add('Install OpenCode');
  RuntimePage.Add('Install TurboQuant');
  RuntimePage.Values[0] := True;
  RuntimePage.Values[1] := True;

  SummaryPage := CreateOutputMsgMemoPage(
    wpFinished,
    'Installer summary',
    'Review the Windows setup result',
    'Read the installer output before pressing Finish.',
    ''
  );
end;

function LoadInstallSummary(): string;
var
  SummaryPath: string;
  SummaryContent: AnsiString;
begin
  SummaryPath := ExpandConstant('{userprofile}\LocalQwenHome\state\install-summary.txt');
  SummaryContent := '';
  if FileExists(SummaryPath) and LoadStringFromFile(SummaryPath, SummaryContent) then
    Result := SummaryContent
  else
    Result := 'Installer summary nije pronadjen.';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  Executed: Boolean;
  SummaryText: string;
begin
  if CurStep = ssPostInstall then begin
    InstallRunStarted := True;
    SummaryText :=
      'Edition: ' + GetSelectedEdition() + #13#10 +
      'Guided model selection: ' + GetSelectedModelLabel() + ' [' + GetSelectedModelId() + ']' + #13#10 +
      'Model VRAM class: ' + GetSelectedModelVramLabel() + #13#10 +
      'Prikazi jos modela: ' + IntToStr(Integer(ShouldShowMoreModelsAfterInstall())) + #13#10 +
      'Access mode: ' + GetSelectedAccessMode() + #13#10 +
      'OpenCode: ' + IntToStr(Integer(RuntimePage.Values[0])) + #13#10 +
      'TurboQuant: ' + IntToStr(Integer(RuntimePage.Values[1]));

    Executed := Exec(
      ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
      GetInstallScriptParameters(),
      ExpandConstant('{app}'),
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode
    );
    if Executed then
      InstallRunExitCode := ResultCode
    else
      InstallRunExitCode := -1;

    SummaryText := SummaryText + #13#10 + #13#10 + LoadInstallSummary();
    if InstallRunExitCode = 0 then
      SummaryText := SummaryText + #13#10 + #13#10 + 'Setup finished successfully.'
    else
      SummaryText := SummaryText + #13#10 + #13#10 + 'Setup finished with exit code ' + IntToStr(InstallRunExitCode) + '.';

    SummaryPage.RichEditViewer.Text := SummaryText;
  end;
end;
