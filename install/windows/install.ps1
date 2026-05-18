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
$configProfilesDir = Join-Path $appRoot "config\profiles"
$scriptsDir = Join-Path $appRoot "scripts"
$assetsDir = Join-Path $appRoot "assets\icons"
$installStatePath = Join-Path $stateDir "install-state.json"
$installReportPath = Join-Path $stateDir "install-report.json"
$settingsPath = Join-Path $stateDir "settings.json"
$runtimeConfigPath = Join-Path $stateDir "runtime-config.json"
$desktopDir = Join-Path $env:USERPROFILE "Desktop\Local AI Control Center"

function Ensure-Dir([string]$Path) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
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
    if ($SkipLlamaSetup) {
        return $false
    }
    $target = Join-Path $appsDir "llama.cpp"
    if (Test-Path (Join-Path $target "build\bin\llama-server.exe")) {
        return $true
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
    $content = @(
        "@echo off",
        "set LOCAL_QWEN_HOME=$workspaceRoot",
        "powershell -NoProfile -ExecutionPolicy Bypass -File `"$launchersDir\start-control-center-next.ps1`""
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

Ensure-Dir $workspaceRoot
Ensure-Dir $stateDir
Ensure-Dir $appsDir
Ensure-Dir $binDir
Ensure-Dir $desktopDir

if (-not $SkipDependencies) {
    Ensure-Command -Name "git" -WingetId "Git.Git" | Out-Null
    $pythonExe = Ensure-Python
    Ensure-Node
} else {
    $pythonExe = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "" }
}

Copy-FolderContent -Source (Join-Path $payloadRoot "backend") -Destination (Join-Path $appRoot "backend")
Copy-FolderContent -Source (Join-Path $payloadRoot "frontend") -Destination (Join-Path $appRoot "frontend")
Copy-FolderContent -Source (Join-Path $payloadRoot "launchers") -Destination (Join-Path $appRoot "launchers")
Copy-FolderContent -Source (Join-Path $payloadRoot "install") -Destination (Join-Path $appRoot "install")
Copy-FolderContent -Source (Join-Path $payloadRoot "config") -Destination (Join-Path $appRoot "config")
Copy-FolderContent -Source (Join-Path $payloadRoot "scripts") -Destination (Join-Path $appRoot "scripts")
Copy-FolderContent -Source (Join-Path $payloadRoot "assets") -Destination (Join-Path $appRoot "assets")
foreach ($file in @("run_control_center_next.py", "README.md", "version.json", "release-notes.txt")) {
    $source = Join-Path $payloadRoot $file
    if (Test-Path $source) {
        Copy-Item $source (Join-Path $appRoot $file) -Force
        if ($file -in @("version.json", "release-notes.txt")) {
            Copy-Item $source (Join-Path $workspaceRoot $file) -Force
        }
    }
}

$opencodeReady = Ensure-OpenCode
$llamaReady = Ensure-LlamaCpp
$turboInfo = Ensure-TurboQuant

$launchWrapper = Write-LaunchWrapper
Write-Shortcut -ShortcutPath (Join-Path $desktopDir "Local AI Control Center.lnk") -TargetPath $launchWrapper
if ($opencodeReady -and (Get-Command opencode -ErrorAction SilentlyContinue)) {
    Write-Shortcut -ShortcutPath (Join-Path $desktopDir "OpenCode - Local AI Control Center.lnk") -TargetPath (Get-Command opencode).Source
}

$llamaPath = Join-Path $appsDir "llama.cpp\build\bin\llama-server.exe"
$installState = [ordered]@{
    edition = $Edition
    profile = "balanced"
    modelId = if ($SkipModelDownload) { "none" } else { "installer-default" }
    modelFile = ""
    port = 8091
    llamaServerExe = if (Test-Path $llamaPath) { $llamaPath } else { "" }
    turboServerExe = ""
}
Write-JsonFile -Path $installStatePath -Payload $installState

$settingsPayload = [ordered]@{
    edition = $Edition
    profile = $Profile
    context = 262144
    outputTokens = 8192
    accessMode = $AccessMode
}
Write-JsonFile -Path $settingsPath -Payload $settingsPayload
Write-JsonFile -Path $runtimeConfigPath -Payload @{ accessMode = $AccessMode }

$components = [ordered]@{
    controlCenter = @{ ok = (Test-Path (Join-Path $appRoot "frontend\dist\index.html")); path = $appRoot }
    llamaCppRuntime = @{ ok = $llamaReady; path = $llamaPath }
    openCode = @{ ok = $opencodeReady; path = if ($opencodeReady) { (Get-Command opencode).Source } else { "" } }
    turboQuantRuntime = @{ ok = ($turboInfo.status -eq "present"); path = $turboInfo.path; status = $turboInfo.status }
}
Write-JsonFile -Path $installReportPath -Payload @{
    installRoot = $workspaceRoot
    appRoot = $appRoot
    edition = $Edition
    launchWrapper = $launchWrapper
    localUrl = "http://127.0.0.1:3210"
    components = $components
}

$failedCore = @()
if (-not $components.controlCenter.ok) { $failedCore += "Control Center" }
if (-not $components.llamaCppRuntime.ok) { $failedCore += "llama.cpp" }
if (-not $components.openCode.ok) { $failedCore += "OpenCode" }

Write-Host "Install report:" -ForegroundColor Cyan
Write-Host "Edition: $Edition"
Write-Host "Control Center: $($components.controlCenter.ok)"
Write-Host "llama.cpp: $($components.llamaCppRuntime.ok)"
Write-Host "OpenCode: $($components.openCode.ok)"
Write-Host "TurboQuant: $($components.turboQuantRuntime.status)"
Write-Host "Access mode: $AccessMode"
Write-Host "Install root: $workspaceRoot"
Write-Host "Launcher: $launchWrapper"

if ($failedCore.Count -gt 0) {
    throw ("Instalacija nije uspela za obavezne komponente: " + ($failedCore -join ", "))
}
