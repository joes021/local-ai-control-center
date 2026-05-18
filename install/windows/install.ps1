param(
    [string]$InstallRoot = "$env:USERPROFILE\LocalQwenHome",
    [ValidateSet("Classic", "Unified")]
    [string]$Edition = "Unified",
    [ValidateSet("local-only", "tailscale")]
    [string]$AccessMode = "local-only",
    [ValidateSet("balanced", "speed", "video")]
    [string]$Profile = "balanced",
    [switch]$SkipDependencies,
    [switch]$SkipOpenCodeInstall,
    [switch]$SkipLlamaSetup,
    [switch]$SkipTurboQuant,
    [switch]$SkipModelDownload
)

$ErrorActionPreference = "Stop"

# Unified installer overlay for legacy Local Qwen 3.635Ba3B on home computer.
# This script keeps legacy runtime expectations and deploys control-center-next as the Next shell.
$payloadRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$workspaceRoot = $InstallRoot
$appRoot = Join-Path $workspaceRoot "control-center-next"
$stateDir = Join-Path $workspaceRoot "state"
$appsDir = Join-Path $workspaceRoot "apps"
$binDir = Join-Path $workspaceRoot "bin"
$launchersDir = Join-Path $appRoot "launchers\windows"
$legacyLaunchersPayloadDir = Join-Path $payloadRoot "support\launcher\windows"
$legacyLaunchersDir = Join-Path $workspaceRoot "launchers"
$configProfilesDir = Join-Path $appRoot "config\profiles"
$scriptsDir = Join-Path $appRoot "scripts"
$assetsDir = Join-Path $appRoot "assets\icons"
$installStatePath = Join-Path $stateDir "install-state.json"
$installReportPath = Join-Path $stateDir "install-report.json"
$installSummaryPath = Join-Path $stateDir "install-summary.txt"
$installLogPath = Join-Path $stateDir "install.log"
$settingsPath = Join-Path $stateDir "settings.json"
$runtimeConfigPath = Join-Path $stateDir "runtime-config.json"
$runtimeStatePath = Join-Path $stateDir "runtime-state.json"
$serviceLifecyclePath = Join-Path $stateDir "server-lifecycle.json"
$opencodeWorkspaceDir = Join-Path $workspaceRoot "opencode-workspace"
$desktopDir = Join-Path $env:USERPROFILE "Desktop\Local AI Control Center"

function Ensure-Dir([string]$Path) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-WindowsPowerShellExe {
    $path = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    if (-not (Test-Path $path)) {
        throw "Windows PowerShell nije pronadjen na ocekivanoj putanji: $path"
    }
    return $path
}

function Copy-FolderContent {
    param(
        [string]$Source,
        [string]$Destination
    )
    if (-not (Test-Path $Source)) {
        return
    }
    Ensure-Dir $Destination
    Copy-Item (Join-Path $Source "*") $Destination -Force -Recurse
}

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Payload
    )
    Ensure-Dir (Split-Path -Parent $Path)
    $Payload | ConvertTo-Json -Depth 8 | Set-Content -Path $Path -Encoding utf8
}

function Write-InstallLogLine {
    param([string]$Message)

    $timestamp = (Get-Date).ToString("s")
    Ensure-Dir (Split-Path -Parent $installLogPath)
    Add-Content -Path $installLogPath -Value "[$timestamp] $Message" -Encoding utf8
}

function Read-JsonFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return $null
    }

    try {
        return Get-Content -Raw $Path | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Ensure-Command {
    param(
        [string]$Name,
        [string]$WingetId = ""
    )
    if (Get-Command $Name -ErrorAction SilentlyContinue) {
        return $true
    }
    if (-not $WingetId) {
        return $false
    }
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        & winget install --id $WingetId --silent --accept-package-agreements --accept-source-agreements
    }
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    if (Ensure-Command -Name "python" -WingetId "Python.Python.3.12") {
        return "python"
    }
    throw "Python nije dostupan."
}

function Ensure-Node {
    if (Get-Command node -ErrorAction SilentlyContinue -and Get-Command npm -ErrorAction SilentlyContinue) {
        return
    }
    if (-not (Ensure-Command -Name "node" -WingetId "OpenJS.NodeJS.LTS")) {
        throw "Node.js nije dostupan."
    }
}

function Ensure-OpenCode {
    if ($SkipOpenCodeInstall) {
        return $false
    }
    if (Get-Command opencode -ErrorAction SilentlyContinue) {
        return $true
    }
    npm install -g opencode-ai
    return [bool](Get-Command opencode -ErrorAction SilentlyContinue)
}

function Ensure-LlamaCpp {
    $target = Join-Path $appsDir "llama.cpp"
    if (Test-Path (Join-Path $target "build\bin\llama-server.exe")) {
        return $true
    }
    $existingState = Read-JsonFile $installStatePath
    if ($existingState -and $existingState.llamaServerExe -and (Test-Path ([string]$existingState.llamaServerExe))) {
        return $true
    }
    if (Find-HealthyRuntimePort) {
        return $true
    }
    if ($SkipLlamaSetup) {
        return $false
    }
    if (-not (Test-Path $target)) {
        git clone https://github.com/ggml-org/llama.cpp.git $target
    }
    $llamaExe = Join-Path $target "build\bin\llama-server.exe"
    if (-not (Test-Path $llamaExe) -and (Get-Command cmake -ErrorAction SilentlyContinue)) {
        $cudaFlag = if (Get-Command nvcc -ErrorAction SilentlyContinue) { "ON" } else { "OFF" }
        $generator = if (Get-Command ninja -ErrorAction SilentlyContinue) { "Ninja" } else { "Visual Studio 17 2022" }
        & cmake -G $generator -S $target -B (Join-Path $target "build") "-DGGML_CUDA=$cudaFlag" | Out-Null
        if ($LASTEXITCODE -eq 0) {
            & cmake --build (Join-Path $target "build") --config Release -j | Out-Null
        }
    }
    return [bool](Test-Path $llamaExe)
}

function Ensure-TurboQuant {
    if ($SkipTurboQuant) {
        return @{ status = "skipped"; path = "" }
    }
    $target = Join-Path $appsDir "llama.cpp-turboquant"
    if (-not (Test-Path $target)) {
        git clone https://github.com/TheTom/llama-cpp-turboquant.git $target | Out-Null
    }
    $turboExe = Join-Path $target "build-cuda\bin\llama-server.exe"
    if (-not (Test-Path $turboExe) -and (Get-Command cmake -ErrorAction SilentlyContinue) -and (Get-Command nvcc -ErrorAction SilentlyContinue)) {
        $generator = if (Get-Command ninja -ErrorAction SilentlyContinue) { "Ninja" } else { "Visual Studio 17 2022" }
        & cmake -G $generator -S $target -B (Join-Path $target "build-cuda") -DGGML_CUDA=ON | Out-Null
        if ($LASTEXITCODE -eq 0) {
            & cmake --build (Join-Path $target "build-cuda") --config Release -j | Out-Null
        }
    }
    if (Test-Path $turboExe) {
        return @{ status = "present"; path = $target }
    }
    return @{ status = "not-installed"; path = "" }
}

function Write-LaunchWrapper {
    $wrapperPath = Join-Path $binDir "launch-local-ai-control-center.cmd"
    $powershellExe = Get-WindowsPowerShellExe
    $content = @(
        "@echo off",
        "set LOCAL_QWEN_HOME=$workspaceRoot",
        "`"$powershellExe`" -NoProfile -ExecutionPolicy Bypass -File `"$launchersDir\start-control-center-next.ps1`""
    ) -join "`r`n"
    Set-Content -Path $wrapperPath -Value $content -Encoding ascii
    return $wrapperPath
}

function Write-Shortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$Arguments = ""
    )
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = Split-Path -Parent $TargetPath
    $shortcut.Save()
}

function Resolve-OpenCodePath {
    $command = Get-Command opencode -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }
    return ""
}

function Find-HealthyRuntimePort {
    foreach ($port in @(8091, 8081, 8080)) {
        try {
            Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
            return $port
        }
        catch {
        }
    }
    return $null
}

function Get-RunningRuntimeInfo {
    $healthyPort = Find-HealthyRuntimePort
    $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -eq "llama-server.exe"
    }

    foreach ($process in $processes) {
        $commandLine = [string]$process.CommandLine
        if (-not $commandLine) {
            continue
        }
        if ($healthyPort -and $commandLine -notmatch "--port\s+$healthyPort\b") {
            continue
        }
        $modelFile = ""
        if ($commandLine -match '-m\s+"([^"]+)"') {
            $modelFile = $matches[1]
        }
        elseif ($commandLine -match '-m\s+([^\s]+)') {
            $modelFile = $matches[1]
        }

        return [pscustomobject]@{
            Port = $healthyPort
            ExecutablePath = [string]$process.ExecutablePath
            ModelFile = $modelFile
        }
    }

    return [pscustomobject]@{
        Port = $healthyPort
        ExecutablePath = ""
        ModelFile = ""
    }
}

function Get-PreferredModelFile {
    $modelsDir = Join-Path $workspaceRoot "models"
    $preferred = Join-Path $modelsDir "qwen36-35b-a3b-IQ2_M.gguf"
    if (Test-Path $preferred) {
        return $preferred
    }
    if (-not (Test-Path $modelsDir)) {
        return ""
    }
    $largest = Get-ChildItem -Path $modelsDir -Filter *.gguf -File -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending |
        Select-Object -First 1
    if ($largest) {
        return $largest.FullName
    }
    return ""
}

function Update-InstallStateAndSettings {
    param(
        [bool]$LlamaReady,
        [string]$LlamaPath,
        [string]$TurboServerPath
    )

    $existingState = Read-JsonFile $installStatePath
    $existingSettings = Read-JsonFile $settingsPath
    $running = Get-RunningRuntimeInfo

    $modelFile = ""
    if ($existingState -and $existingState.modelFile) {
        $modelFile = [string]$existingState.modelFile
    }
    if (-not $modelFile -and $running.ModelFile) {
        $modelFile = [string]$running.ModelFile
    }
    if (-not $modelFile) {
        $modelFile = Get-PreferredModelFile
    }

    $modelId = if ($modelFile) { Split-Path $modelFile -Leaf } else { "none" }
    $runtimePort = if ($running.Port) { [int]$running.Port } elseif ($existingState -and $existingState.port) { [int]$existingState.port } else { 8091 }
    $llamaServerExe = if ($running.ExecutablePath) { [string]$running.ExecutablePath } elseif ($LlamaReady -and (Test-Path $LlamaPath)) { $LlamaPath } elseif ($existingState -and $existingState.llamaServerExe) { [string]$existingState.llamaServerExe } else { "" }
    $turboServerExe = if ($TurboServerPath -and (Test-Path $TurboServerPath)) { $TurboServerPath } elseif ($existingState -and $existingState.turboServerExe) { [string]$existingState.turboServerExe } else { "" }

    $installState = [ordered]@{
        edition = if ($existingState -and $existingState.edition) { [string]$existingState.edition } else { $Edition }
        profile = if ($existingState -and $existingState.profile) { [string]$existingState.profile } else { $Profile }
        modelId = $modelId
        modelFile = $modelFile
        port = $runtimePort
        llamaServerExe = $llamaServerExe
        turboServerExe = $turboServerExe
        llamaBinDir = if ($llamaServerExe) { Split-Path -Parent $llamaServerExe } else { "" }
        turboDir = if ($turboServerExe) { Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $turboServerExe)) } else { "" }
        threads = if ($existingState -and $existingState.threads) { [int]$existingState.threads } else { 8 }
        installRoot = $workspaceRoot
        noMmap = if ($existingState) { [bool]$existingState.noMmap } else { $false }
        mlock = if ($existingState) { [bool]$existingState.mlock } else { $false }
        defaultProfile = if ($existingState -and $existingState.defaultProfile) { [string]$existingState.defaultProfile } else { $Profile }
    }
    Write-JsonFile -Path $installStatePath -Payload $installState

    $settingsPayload = [ordered]@{
        edition = if ($existingSettings -and $existingSettings.edition) { [string]$existingSettings.edition } else { $Edition }
        profile = if ($existingSettings -and $existingSettings.profile) { [string]$existingSettings.profile } else { $Profile }
        accessMode = $AccessMode
        llama = [ordered]@{
            contextSize = if ($existingSettings -and $existingSettings.llama -and $existingSettings.llama.contextSize) { [int]$existingSettings.llama.contextSize } else { 262144 }
            maxOutputTokens = if ($existingSettings -and $existingSettings.llama -and $existingSettings.llama.maxOutputTokens) { [int]$existingSettings.llama.maxOutputTokens } else { 8192 }
            contextSizeCustomized = if ($existingSettings -and $existingSettings.llama) { [bool]$existingSettings.llama.contextSizeCustomized } else { $false }
            maxOutputTokensCustomized = if ($existingSettings -and $existingSettings.llama) { [bool]$existingSettings.llama.maxOutputTokensCustomized } else { $false }
        }
        opencode = [ordered]@{
            buildSteps = if ($existingSettings -and $existingSettings.opencode -and $existingSettings.opencode.buildSteps) { [int]$existingSettings.opencode.buildSteps } else { 120 }
            planSteps = if ($existingSettings -and $existingSettings.opencode -and $existingSettings.opencode.planSteps) { [int]$existingSettings.opencode.planSteps } else { 80 }
            generalSteps = if ($existingSettings -and $existingSettings.opencode -and $existingSettings.opencode.generalSteps) { [int]$existingSettings.opencode.generalSteps } else { 100 }
            exploreSteps = if ($existingSettings -and $existingSettings.opencode -and $existingSettings.opencode.exploreSteps) { [int]$existingSettings.opencode.exploreSteps } else { 60 }
            workingDirectory = if ($existingSettings -and $existingSettings.opencode -and $existingSettings.opencode.workingDirectory) { [string]$existingSettings.opencode.workingDirectory } else { $opencodeWorkspaceDir }
        }
        threads = if ($existingSettings -and $existingSettings.threads) { [int]$existingSettings.threads } else { 8 }
        gpuLayers = if ($existingSettings -and $existingSettings.gpuLayers) { [int]$existingSettings.gpuLayers } else { 99 }
        batch = if ($existingSettings -and $existingSettings.batch) { [int]$existingSettings.batch } else { 2048 }
        ubatch = if ($existingSettings -and $existingSettings.ubatch) { [int]$existingSettings.ubatch } else { 512 }
        temperature = if ($existingSettings -and $existingSettings.temperature) { [double]$existingSettings.temperature } else { 0.7 }
        topP = if ($existingSettings -and $existingSettings.topP) { [double]$existingSettings.topP } else { 0.95 }
        minP = if ($existingSettings -and $existingSettings.minP) { [double]$existingSettings.minP } else { 0.05 }
        topK = if ($existingSettings -and $existingSettings.topK) { [int]$existingSettings.topK } else { 40 }
    }
    Write-JsonFile -Path $settingsPath -Payload $settingsPayload
}

function Start-LegacyRuntimeIfNeeded {
    $healthyPort = Find-HealthyRuntimePort
    if ($healthyPort) {
        return $healthyPort
    }

    $state = Read-JsonFile $installStatePath
    if (-not $state -or -not $state.modelFile) {
        return $null
    }

    $startServerScript = Join-Path $legacyLaunchersDir "start-server.ps1"
    if (-not (Test-Path $startServerScript)) {
        return $null
    }

    & powershell -NoProfile -ExecutionPolicy Bypass -File $startServerScript -Profile $Profile | Out-Null
    return Find-HealthyRuntimePort
}

function Stop-ExistingControlCenter {
    $runtimeState = Read-JsonFile $runtimeStatePath
    if ($runtimeState -and $runtimeState.pid) {
        try {
            Stop-Process -Id ([int]$runtimeState.pid) -Force -ErrorAction SilentlyContinue
        }
        catch {
        }
    }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^python(?:w)?\.exe$' -and
            $_.CommandLine -and
            $_.CommandLine -like '*run_control_center_next.py*'
        } |
        ForEach-Object {
            try {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
            catch {
            }
        }
}

function Start-ControlCenterAndWait {
    param([string]$LaunchWrapper)

    Stop-ExistingControlCenter
    $saved = @{
        CONTROL_CENTER_NEXT_ACCESS_MODE = $env:CONTROL_CENTER_NEXT_ACCESS_MODE
        CONTROL_CENTER_NEXT_SKIP_OPEN = $env:CONTROL_CENTER_NEXT_SKIP_OPEN
        CONTROL_CENTER_NEXT_FORCE_RESTART = $env:CONTROL_CENTER_NEXT_FORCE_RESTART
    }
    try {
        $env:CONTROL_CENTER_NEXT_ACCESS_MODE = $AccessMode
        $env:CONTROL_CENTER_NEXT_SKIP_OPEN = "1"
        $env:CONTROL_CENTER_NEXT_FORCE_RESTART = "1"
        & (Get-WindowsPowerShellExe) -NoProfile -ExecutionPolicy Bypass -File (Join-Path $launchersDir "start-control-center-next.ps1") | Out-Null
    }
    finally {
        foreach ($entry in $saved.GetEnumerator()) {
            if ($null -eq $entry.Value) {
                Remove-Item "Env:$($entry.Key)" -ErrorAction SilentlyContinue
            }
            else {
                Set-Item "Env:$($entry.Key)" -Value $entry.Value
            }
        }
    }

    $runtimeState = Read-JsonFile $runtimeStatePath
    $port = if ($runtimeState -and $runtimeState.port) { [int]$runtimeState.port } else { 3210 }
    $localUrl = "http://127.0.0.1:$port"
    for ($i = 0; $i -lt 45; $i++) {
        try {
            Invoke-WebRequest -Uri "$localUrl/api/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
            return [pscustomobject]@{
                Started = $true
                Url = $localUrl
                Port = $port
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    return [pscustomobject]@{
        Started = $false
        Url = $localUrl
        Port = $port
    }
}

function Update-ServiceLifecycle {
    param([Nullable[int]]$HealthyPort)

    if ($HealthyPort) {
        Write-JsonFile -Path $serviceLifecyclePath -Payload ([ordered]@{
            state = "active"
            profile = $Profile
            stdout = $null
            stderr = $null
            reason = "Health endpoint returned OK."
            updatedAt = (Get-Date).ToString("s")
        })
    }
    elseif (Test-Path $serviceLifecyclePath) {
        Remove-Item $serviceLifecyclePath -Force
    }
}

function Write-InstallSummary {
    param(
        [hashtable]$Components,
        [pscustomobject]$ControlCenterStart,
        [Nullable[int]]$RuntimePort,
        [string[]]$FailedCore
    )

    $tailscaleUrl = ""
    if ($AccessMode -eq "tailscale") {
        $tailscaleIp = ""
        try {
            $tailscaleIp = (& tailscale ip -4 2>$null | Select-Object -First 1)
        }
        catch {
            $tailscaleIp = ""
        }
        if ($tailscaleIp) {
            $tailscaleUrl = "http://${tailscaleIp}:$($ControlCenterStart.Port)"
        }
    }

    $lines = @(
        "Edition: $Edition",
        "Access mode: $AccessMode",
        "Control Center: $(if ($Components.controlCenter.ok) { 'OK' } else { 'FAILED' })",
        "llama.cpp: $(if ($Components.llamaCppRuntime.ok) { 'OK' } else { 'FAILED' })",
        "OpenCode: $(if ($Components.openCode.ok) { 'OK' } else { 'FAILED' })",
        "TurboQuant: $($Components.turboQuantRuntime.status)",
        "Runtime port: $(if ($RuntimePort) { $RuntimePort } else { 'nije potvrdjen' })",
        "Install root: $workspaceRoot",
        "Launcher: $launchWrapper"
    )
    if ($ControlCenterStart.Started) {
        $lines += "Control Center URL: $($ControlCenterStart.Url)"
    }
    else {
        $lines += "Control Center URL: start nije potvrdjen automatski"
    }
    if ($tailscaleUrl) {
        $lines += "Tailscale URL: $tailscaleUrl"
    }
    $lines += "Install log: $installLogPath"
    if ($FailedCore.Count -gt 0) {
        $lines += "Next step: otvori Repair > Repair runtime ili proveri install log."
    }
    else {
        $lines += "Next step: pokreni Local AI Control Center preko desktop shortcut-a ili URL-a iznad."
    }
    $lines -join "`r`n" | Set-Content -Path $installSummaryPath -Encoding utf8
}

Ensure-Dir $workspaceRoot
Ensure-Dir $stateDir
Ensure-Dir $appsDir
Ensure-Dir $binDir
Ensure-Dir $desktopDir
Ensure-Dir $opencodeWorkspaceDir
if (Test-Path $installLogPath) {
    Remove-Item $installLogPath -Force
}
Write-InstallLogLine "Installer start: edition=$Edition accessMode=$AccessMode profile=$Profile"

if (-not $SkipDependencies) {
    Write-InstallLogLine "Dependency bootstrap started."
    Ensure-Command -Name "git" -WingetId "Git.Git" | Out-Null
    $pythonExe = Ensure-Python
    Ensure-Node
    Write-InstallLogLine "Dependency bootstrap finished."
} else {
    $pythonExe = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "" }
    Write-InstallLogLine "Dependency bootstrap skipped by flag."
}

Write-InstallLogLine "Copying payload into install root."
Copy-FolderContent -Source (Join-Path $payloadRoot "backend") -Destination (Join-Path $appRoot "backend")
Copy-FolderContent -Source (Join-Path $payloadRoot "frontend") -Destination (Join-Path $appRoot "frontend")
Copy-FolderContent -Source (Join-Path $payloadRoot "launchers") -Destination (Join-Path $appRoot "launchers")
Copy-FolderContent -Source (Join-Path $payloadRoot "install") -Destination (Join-Path $appRoot "install")
Copy-FolderContent -Source (Join-Path $payloadRoot "config") -Destination (Join-Path $appRoot "config")
Copy-FolderContent -Source (Join-Path $payloadRoot "scripts") -Destination (Join-Path $appRoot "scripts")
Copy-FolderContent -Source (Join-Path $payloadRoot "assets") -Destination (Join-Path $appRoot "assets")
Copy-FolderContent -Source $legacyLaunchersPayloadDir -Destination $legacyLaunchersDir
foreach ($file in @("run_control_center_next.py", "README.md", "version.json", "release-notes.txt")) {
    $source = Join-Path $payloadRoot $file
    if (Test-Path $source) {
        Copy-Item $source (Join-Path $appRoot $file) -Force
        if ($file -in @("version.json", "release-notes.txt")) {
            Copy-Item $source (Join-Path $workspaceRoot $file) -Force
        }
    }
}

Write-InstallLogLine "Checking runtime components."
$opencodeReady = Ensure-OpenCode
$llamaReady = Ensure-LlamaCpp
$turboInfo = Ensure-TurboQuant
$turboServerPath = if ($turboInfo.status -eq "present") { Join-Path $appsDir "llama.cpp-turboquant\build-cuda\bin\llama-server.exe" } else { "" }
Write-InstallLogLine "Component check finished: OpenCode=$opencodeReady llamaReady=$llamaReady TurboQuant=$($turboInfo.status)"

$launchWrapper = Write-LaunchWrapper
Write-Shortcut -ShortcutPath (Join-Path $desktopDir "Local AI Control Center.lnk") -TargetPath $launchWrapper
if ($opencodeReady -and (Resolve-OpenCodePath)) {
    Write-Shortcut -ShortcutPath (Join-Path $desktopDir "OpenCode - Local AI Control Center.lnk") -TargetPath (Resolve-OpenCodePath)
}

$llamaPath = Join-Path $appsDir "llama.cpp\build\bin\llama-server.exe"
Write-JsonFile -Path $runtimeConfigPath -Payload @{ accessMode = $AccessMode }
Write-InstallLogLine "Wrote runtime-config.json"
Update-InstallStateAndSettings -LlamaReady $llamaReady -LlamaPath $llamaPath -TurboServerPath $turboServerPath
$healthyRuntimePort = Start-LegacyRuntimeIfNeeded
Write-InstallLogLine "Legacy runtime probe result: port=$healthyRuntimePort"
Update-InstallStateAndSettings -LlamaReady $llamaReady -LlamaPath $llamaPath -TurboServerPath $turboServerPath
$healthyRuntimePort = Find-HealthyRuntimePort
Update-ServiceLifecycle -HealthyPort $healthyRuntimePort
$controlCenterStart = Start-ControlCenterAndWait -LaunchWrapper $launchWrapper
Write-InstallLogLine "Control Center start result: started=$($controlCenterStart.Started) url=$($controlCenterStart.Url)"
$installState = Read-JsonFile $installStatePath
$effectiveLlamaPath = if ($installState -and $installState.llamaServerExe) { [string]$installState.llamaServerExe } else { $llamaPath }
$effectiveTurboPath = if ($installState -and $installState.turboServerExe) { [string]$installState.turboServerExe } else { $turboServerPath }
$runtimeReady = [bool]$healthyRuntimePort
$llamaComponentReady = $runtimeReady -or $llamaReady -or ($effectiveLlamaPath -and (Test-Path $effectiveLlamaPath))

$components = [ordered]@{
    controlCenter = @{ ok = (Test-Path (Join-Path $appRoot "frontend\dist\index.html")); path = $appRoot; started = $controlCenterStart.Started; url = $controlCenterStart.Url }
    llamaCppRuntime = @{ ok = $llamaComponentReady; path = $effectiveLlamaPath }
    openCode = @{ ok = $opencodeReady; path = if ($opencodeReady) { (Resolve-OpenCodePath) } else { "" } }
    turboQuantRuntime = @{ ok = ($turboInfo.status -eq "present"); path = $effectiveTurboPath; status = $turboInfo.status }
}
Write-JsonFile -Path $installReportPath -Payload @{
    installRoot = $workspaceRoot
    appRoot = $appRoot
    edition = $Edition
    launchWrapper = $launchWrapper
    localUrl = $controlCenterStart.Url
    controlCenterStarted = $controlCenterStart.Started
    runtimePort = $healthyRuntimePort
    components = $components
}
$failedCore = @()
if (-not $components.controlCenter.ok) { $failedCore += "Control Center" }
if (-not $controlCenterStart.Started) { $failedCore += "Control Center startup" }
if (-not $components.llamaCppRuntime.ok) { $failedCore += "llama.cpp" }
if (-not $healthyRuntimePort) { $failedCore += "runtime health" }
if (-not $components.openCode.ok) { $failedCore += "OpenCode" }
Write-InstallSummary -Components $components -ControlCenterStart $controlCenterStart -RuntimePort $healthyRuntimePort -FailedCore $failedCore
Write-InstallLogLine "Install summary written."

Write-Host "Install report:" -ForegroundColor Cyan
Write-Host "Edition: $Edition"
Write-Host "Control Center: $($components.controlCenter.ok)"
Write-Host "llama.cpp: $($components.llamaCppRuntime.ok)"
Write-Host "OpenCode: $($components.openCode.ok)"
Write-Host "TurboQuant: $($components.turboQuantRuntime.status)"
Write-Host "Access mode: $AccessMode"
Write-Host "Install root: $workspaceRoot"
Write-Host "Launcher: $launchWrapper"
Write-Host "Control Center URL: $($controlCenterStart.Url)"
Write-Host "Runtime port: $(if ($healthyRuntimePort) { $healthyRuntimePort } else { 'nije potvrdjen' })"

if ($failedCore.Count -gt 0) {
    Write-InstallLogLine ("Installer failed for required components: " + ($failedCore -join ", "))
    throw ("Instalacija nije uspela za obavezne komponente: " + ($failedCore -join ", "))
}

Write-InstallLogLine "Installer finished successfully."

