param(
    [string]$InstallRoot = "$env:USERPROFILE\LocalQwenHome",
    [ValidateSet("Classic", "Unified")]
    [string]$Edition = "Unified",
    [ValidateSet("local-only", "tailscale")]
    [string]$AccessMode = "local-only",
    [ValidateSet("balanced", "speed", "video")]
    [string]$Profile = "balanced",
    [string]$SelectedModelId = "",
    [string]$SelectedModelLabel = "",
    [string]$SelectedModelDownloadFile = "",
    [string]$SelectedModelVramClass = "",
    [switch]$SkipDependencies,
    [switch]$SkipOpenCodeInstall,
    [switch]$SkipLlamaSetup,
    [switch]$SkipTurboQuant,
    [switch]$SkipModelDownload,
    [switch]$ShowMoreModelsAfterInstall
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
$assetsDir = Join-Path $workspaceRoot "assets\icons"
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
$recommendedModelsCatalogPath = Join-Path $payloadRoot "install\shared\recommended-models.json"

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

function Get-RecommendedModelCatalog {
    if (-not (Test-Path $recommendedModelsCatalogPath)) {
        return $null
    }

    try {
        return Get-Content -Raw $recommendedModelsCatalogPath | ConvertFrom-Json
    }
    catch {
        Write-InstallLogLine "Unable to parse recommended-models.json, falling back to installer-provided defaults."
        return $null
    }
}

function Resolve-SelectedModelSelection {
    param(
        [string]$RequestedModelId,
        [string]$RequestedLabel,
        [string]$RequestedDownloadFile,
        [string]$RequestedVramClass
    )

    $catalog = Get-RecommendedModelCatalog
    $catalogDefaultModelId = if ($catalog -and $catalog.defaultModelId) { [string]$catalog.defaultModelId } else { "gemma-4-e4b-it-q4-0" }
    $resolvedModelId = [string]$RequestedModelId
    $selectionSource = "wizard"
    if ([string]::IsNullOrWhiteSpace($resolvedModelId)) {
        $resolvedModelId = $catalogDefaultModelId
        $selectionSource = "catalog-default"
    }

    $catalogEntry = $null
    if ($catalog -and $catalog.recommended) {
        $catalogEntry = $catalog.recommended | Where-Object { $_.modelId -eq $resolvedModelId } | Select-Object -First 1
        if (-not $catalogEntry -and $resolvedModelId -ne $catalogDefaultModelId) {
            $resolvedModelId = $catalogDefaultModelId
            $catalogEntry = $catalog.recommended | Where-Object { $_.modelId -eq $resolvedModelId } | Select-Object -First 1
            $selectionSource = "catalog-fallback"
        }
    }

    $resolvedLabel = [string]$RequestedLabel
    $resolvedDownloadFile = [string]$RequestedDownloadFile
    $resolvedVramClass = [string]$RequestedVramClass
    if ($catalogEntry) {
        $resolvedLabel = [string]$catalogEntry.label
        $resolvedDownloadFile = [string]$catalogEntry.downloadFile
        if ($catalogEntry.vramClass -and $catalogEntry.vramClass.label) {
            $resolvedVramClass = [string]$catalogEntry.vramClass.label
        }
    }

    if ([string]::IsNullOrWhiteSpace($resolvedLabel)) {
        $resolvedLabel = $resolvedModelId
    }
    if ([string]::IsNullOrWhiteSpace($resolvedDownloadFile)) {
        $resolvedDownloadFile = ""
    }
    if ([string]::IsNullOrWhiteSpace($resolvedVramClass)) {
        $resolvedVramClass = ""
    }

    return [ordered]@{
        modelId = $resolvedModelId
        label = $resolvedLabel
        downloadFile = $resolvedDownloadFile
        vramClass = $resolvedVramClass
        family = if ($catalogEntry -and $catalogEntry.family) { [string]$catalogEntry.family } else { "" }
        customSource = if ($catalogEntry -and $catalogEntry.customSource) { [string]$catalogEntry.customSource } else { "" }
        repo = if ($catalogEntry -and $catalogEntry.repo) { [string]$catalogEntry.repo } else { "" }
        legacyModelId = ""
        source = $selectionSource
        catalogPath = $recommendedModelsCatalogPath
        defaultModelId = $catalogDefaultModelId
        showMoreModelsAfterInstall = [bool]$ShowMoreModelsAfterInstall
    }
}

function Register-InstallerSelectedModelWithLegacyCatalog {
    param([object]$SelectedModelSelection)

    $customSource = [string]$SelectedModelSelection.customSource
    $repo = [string]$SelectedModelSelection.repo
    $downloadFile = [string]$SelectedModelSelection.downloadFile
    $label = [string]$SelectedModelSelection.label
    $family = [string]$SelectedModelSelection.family

    if ([string]::IsNullOrWhiteSpace($customSource) -or [string]::IsNullOrWhiteSpace($repo) -or [string]::IsNullOrWhiteSpace($downloadFile)) {
        return $SelectedModelSelection
    }

    $legacyCommonScript = Join-Path $legacyLaunchersDir "local-qwen-common.ps1"
    if (-not (Test-Path $legacyCommonScript)) {
        throw "Legacy common skripta nije pronadjena: $legacyCommonScript"
    }

    . $legacyCommonScript
    $registeredModel = switch ($customSource.ToLowerInvariant()) {
        "unsloth" { Add-UnslothCustomModel -Repo $repo -FileName $downloadFile -Label $label -Family $(if ([string]::IsNullOrWhiteSpace($family)) { "Unsloth" } else { $family }) }
        "huggingface" { Add-HuggingFaceCustomModel -Repo $repo -FileName $downloadFile -Label $label -Family $(if ([string]::IsNullOrWhiteSpace($family)) { "Custom" } else { $family }) }
        default { return $SelectedModelSelection }
    }

    $legacyModelId = if ($registeredModel -and $registeredModel.PSObject.Properties["id"]) { [string]$registeredModel.id } else { "" }
    if ([string]::IsNullOrWhiteSpace($legacyModelId)) {
        throw "Registracija legacy modela nije vratila validan id za $downloadFile"
    }

    Write-InstallLogLine "Legacy catalog registration: source=$customSource repo=$repo legacyModelId=$legacyModelId"
    $SelectedModelSelection.legacyModelId = $legacyModelId
    return $SelectedModelSelection
}

function Sync-BootstrappedModelIntoWorkspace {
    param([object]$SelectedModelSelection)

    $downloadFile = [string]$SelectedModelSelection.downloadFile
    if ([string]::IsNullOrWhiteSpace($downloadFile)) {
        return
    }

    $workspaceModelPath = Join-Path (Join-Path $workspaceRoot "models") $downloadFile
    if (Test-Path $workspaceModelPath) {
        return
    }

    $fallbackHome = Join-Path $env:USERPROFILE "LocalQwenHome"
    $candidatePaths = @(
        (Join-Path $fallbackHome "models\$downloadFile"),
        (Join-Path $fallbackHome ("models\\llama-cpp\\{0}\\{1}" -f [System.IO.Path]::GetFileNameWithoutExtension($downloadFile), $downloadFile))
    )

    $resolvedSource = $candidatePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $resolvedSource) {
        $resolvedSource = Get-ChildItem -Path (Join-Path $fallbackHome "models") -Recurse -Filter $downloadFile -File -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName -First 1
    }

    if (-not $resolvedSource) {
        return
    }

    Ensure-Dir (Split-Path -Parent $workspaceModelPath)
    Copy-Item -LiteralPath $resolvedSource -Destination $workspaceModelPath -Force
    Write-InstallLogLine "Synced bootstrapped model into workspace: source=$resolvedSource target=$workspaceModelPath"
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
        [string]$Arguments = "",
        [string]$IconPath = ""
    )
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = Split-Path -Parent $TargetPath
    if ($IconPath -and (Test-Path $IconPath)) {
        $shortcut.IconLocation = "$IconPath,0"
    }
    $shortcut.Save()
}

function Write-DesktopFolderMetadata {
    param(
        [string]$FolderPath,
        [string]$IconPath
    )

    if (-not (Test-Path $FolderPath) -or -not (Test-Path $IconPath)) {
        return
    }

    $desktopIniPath = Join-Path $FolderPath "desktop.ini"
    $desktopIniContent = @(
        "[.ShellClassInfo]",
        "IconResource=$IconPath,0",
        "ConfirmFileOp=0"
    ) -join "`r`n"
    Set-Content -Path $desktopIniPath -Value $desktopIniContent -Encoding ascii
    attrib +h +s $desktopIniPath | Out-Null
    attrib +r $FolderPath | Out-Null
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

function Get-ModelBootstrapState {
    param(
        [object]$SelectedModelSelection,
        [string]$InstalledModelFile = "",
        [string]$BootstrapStatus = "",
        [string]$BootstrapMessage = ""
    )

    $selectedModelId = [string]$SelectedModelSelection.modelId
    $selectedModelDownloadFile = [string]$SelectedModelSelection.downloadFile
    $selectedModelPath = if ($selectedModelDownloadFile) { Join-Path (Join-Path $workspaceRoot "models") $selectedModelDownloadFile } else { "" }
    $selectedModelDownloaded = $false
    if ($selectedModelPath -and (Test-Path $selectedModelPath)) {
        $selectedModelDownloaded = $true
    }
    elseif ($InstalledModelFile -and $selectedModelDownloadFile -and ((Split-Path $InstalledModelFile -Leaf) -eq $selectedModelDownloadFile)) {
        $selectedModelDownloaded = $true
    }

    $effectiveStatus = $BootstrapStatus
    if ([string]::IsNullOrWhiteSpace($effectiveStatus)) {
        if ([string]::IsNullOrWhiteSpace($selectedModelId) -or [string]::IsNullOrWhiteSpace($selectedModelDownloadFile)) {
            $effectiveStatus = "selection-missing"
        }
        elseif ($selectedModelDownloaded) {
            $effectiveStatus = "ready"
        }
        else {
            $effectiveStatus = "download-required"
        }
    }

    $bootstrapReady = $selectedModelDownloaded -and -not ([string]::IsNullOrWhiteSpace($selectedModelId)) -and -not ([string]::IsNullOrWhiteSpace($selectedModelDownloadFile))
    if ([string]::IsNullOrWhiteSpace($BootstrapMessage)) {
        switch ($effectiveStatus) {
            "selection-missing" { $BootstrapMessage = "Installer nema kompletan selected model selection za model bootstrap fazu." }
            "ready" { $BootstrapMessage = "Selected model je spreman za model bootstrap fazu." }
            "download-required" { $BootstrapMessage = "Selected model jos nije prisutan i mora da prodje model bootstrap/download fazu." }
            "downloaded" { $BootstrapMessage = "Selected model je uspesno preuzet kroz model bootstrap fazu." }
            "download-skipped" { $BootstrapMessage = "Model bootstrap nije kompletan jer je download preskocen." }
            default { $BootstrapMessage = "Model bootstrap status: $effectiveStatus" }
        }
    }

    return [ordered]@{
        selectedModelId = $selectedModelId
        selectedModelDownloadFile = $selectedModelDownloadFile
        selectedModelPath = $selectedModelPath
        selectedModelDownloaded = $selectedModelDownloaded
        modelBootstrap = [ordered]@{
            status = $effectiveStatus
            message = $BootstrapMessage
            bootstrapReady = $bootstrapReady
            selectedModelDownloaded = $selectedModelDownloaded
        }
    }
}

function Invoke-ModelBootstrap {
    param([object]$SelectedModelSelection)

    $installedModelFile = Get-PreferredModelFile
    $bootstrapState = Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile $installedModelFile
    if ($bootstrapState.modelBootstrap.bootstrapReady) {
        return $bootstrapState
    }
    if ([string]::IsNullOrWhiteSpace([string]$bootstrapState.selectedModelId) -or [string]::IsNullOrWhiteSpace([string]$bootstrapState.selectedModelDownloadFile)) {
        return $bootstrapState
    }
    if ($SkipModelDownload) {
        return (Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile $installedModelFile -BootstrapStatus "download-skipped")
    }

    $modelIdToDownload = [string]$bootstrapState.selectedModelId
    if (-not [string]::IsNullOrWhiteSpace([string]$SelectedModelSelection.customSource)) {
        try {
            $SelectedModelSelection = Register-InstallerSelectedModelWithLegacyCatalog -SelectedModelSelection $SelectedModelSelection
            if (-not [string]::IsNullOrWhiteSpace([string]$SelectedModelSelection.legacyModelId)) {
                $modelIdToDownload = [string]$SelectedModelSelection.legacyModelId
            }
        }
        catch {
            return (Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile (Get-PreferredModelFile) -BootstrapStatus "registration-failed" -BootstrapMessage $_.Exception.Message)
        }
    }

    $manageModelsScript = Join-Path $legacyLaunchersDir "manage-models.ps1"
    if (-not (Test-Path $manageModelsScript)) {
        $manageModelsScript = Join-Path $launchersDir "manage-models.ps1"
    }
    if (-not (Test-Path $manageModelsScript)) {
        return (Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile $installedModelFile -BootstrapStatus "download-script-missing")
    }

    Write-InstallLogLine "Model bootstrap start: modelId=$modelIdToDownload"
    try {
        & (Get-WindowsPowerShellExe) -NoProfile -ExecutionPolicy Bypass -File $manageModelsScript -ModelId $modelIdToDownload -Download | Out-Null
    }
    catch {
        return (Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile (Get-PreferredModelFile) -BootstrapStatus "download-failed" -BootstrapMessage $_.Exception.Message)
    }

    Sync-BootstrappedModelIntoWorkspace -SelectedModelSelection $SelectedModelSelection

    return (Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile (Get-PreferredModelFile) -BootstrapStatus "downloaded")
}

function Invoke-FirstRunProbe {
    param(
        [Nullable[int]]$HealthyRuntimePort,
        [object]$ModelBootstrapState
    )

    $probePrompt = "Reply with exactly OK and nothing else."
    if (-not $ModelBootstrapState -or -not $ModelBootstrapState.modelBootstrap.bootstrapReady) {
        return [ordered]@{
            probePrompt = $probePrompt
            probeResponse = ""
            firstRunProbe = [ordered]@{
                status = "bootstrap-not-ready"
                message = "First-run probe nije pokrenut jer model bootstrap nije spreman."
                probeReady = $false
            }
        }
    }
    if (-not $HealthyRuntimePort) {
        return [ordered]@{
            probePrompt = $probePrompt
            probeResponse = ""
            firstRunProbe = [ordered]@{
                status = "runtime-unavailable"
                message = "First-run probe nije pokrenut jer runtime health nije potvrdjen."
                probeReady = $false
            }
        }
    }

    $probeUri = "http://127.0.0.1:$HealthyRuntimePort/v1/chat/completions"
    $probeBody = @{
        messages = @(
            @{
                role = "user"
                content = $probePrompt
            }
        )
        max_tokens = 8
        temperature = 0
    } | ConvertTo-Json -Depth 6

    try {
        $probeResult = Invoke-RestMethod -Uri $probeUri -Method Post -ContentType "application/json" -Body $probeBody -TimeoutSec 30
        $probeContent = [string]($probeResult.choices[0].message.content)
        $probeReasoning = [string]($probeResult.choices[0].message.reasoning_content)
        $normalizedContent = ($probeContent -replace '\s+', ' ').Trim()
        $normalizedReasoning = ($probeReasoning -replace '\s+', ' ').Trim()
        $completionTokens = 0
        if ($probeResult.usage -and $probeResult.usage.completion_tokens) {
            $completionTokens = [int]$probeResult.usage.completion_tokens
        }
        $probeResponse = if (-not [string]::IsNullOrWhiteSpace($normalizedContent)) { $normalizedContent } else { $normalizedReasoning }
        $probeReady = $false
        $probeStatus = "unexpected-response"
        $probeMessage = "First-run probe je dobio neocekivan odgovor od modela."
        if ($normalizedContent -eq "OK" -or $normalizedReasoning -eq "OK") {
            $probeReady = $true
            $probeStatus = "ready"
            $probeMessage = "First-run probe je uspesno potvrdio da model odgovara na upit."
            $probeResponse = "OK"
        }
        elseif (-not [string]::IsNullOrWhiteSpace($probeResponse) -or $completionTokens -gt 0) {
            $probeReady = $true
            $probeStatus = "ready-non-exact"
            $probeMessage = "First-run probe je potvrdio da model odgovara, ali ne striktno sa exact OK."
        }
        return [ordered]@{
            probePrompt = $probePrompt
            probeResponse = $probeResponse
            firstRunProbe = [ordered]@{
                status = $probeStatus
                message = $probeMessage
                probeReady = $probeReady
            }
        }
    }
    catch {
        return [ordered]@{
            probePrompt = $probePrompt
            probeResponse = ""
            firstRunProbe = [ordered]@{
                status = "probe-failed"
                message = $_.Exception.Message
                probeReady = $false
            }
        }
    }
}

function Update-InstallStateAndSettings {
    param(
        [bool]$LlamaReady,
        [string]$LlamaPath,
        [string]$TurboServerPath,
        [object]$SelectedModelSelection,
        [object]$ModelBootstrapState = $null
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
    if ($ModelBootstrapState -and $ModelBootstrapState.selectedModelDownloaded -and $ModelBootstrapState.selectedModelPath -and (Test-Path ([string]$ModelBootstrapState.selectedModelPath))) {
        $modelFile = [string]$ModelBootstrapState.selectedModelPath
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
        selectedModelId = [string]$SelectedModelSelection.modelId
        selectedModelLabel = [string]$SelectedModelSelection.label
        selectedModelDownloadFile = [string]$SelectedModelSelection.downloadFile
        selectedModelVramClass = [string]$SelectedModelSelection.vramClass
        selectedModelSource = [string]$SelectedModelSelection.source
        selectedModelCatalogPath = [string]$SelectedModelSelection.catalogPath
        defaultModelId = [string]$SelectedModelSelection.defaultModelId
        showMoreModelsAfterInstall = [bool]$SelectedModelSelection.showMoreModelsAfterInstall
        selectedModelDownloaded = [bool]($ModelBootstrapState -and $ModelBootstrapState.selectedModelDownloaded)
        modelBootstrapStatus = if ($ModelBootstrapState) { [string]$ModelBootstrapState.modelBootstrap.status } else { "" }
        modelBootstrapMessage = if ($ModelBootstrapState) { [string]$ModelBootstrapState.modelBootstrap.message } else { "" }
        bootstrapReady = [bool]($ModelBootstrapState -and $ModelBootstrapState.modelBootstrap.bootstrapReady)
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
        [object]$SelectedModelSelection,
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
        "Guided model selection: $($SelectedModelSelection.label) [$($SelectedModelSelection.modelId)]",
        "Model bootstrap: $($Components.modelBootstrap.status)",
        "Bootstrap ready: $($Components.modelBootstrap.bootstrapReady)",
        "Selected model downloaded: $($Components.modelBootstrap.selectedModelDownloaded)",
        "First-run probe: $($Components.firstRunProbe.status)",
        "Probe ready: $($Components.firstRunProbe.probeReady)",
        "Probe prompt: $($Components.firstRunProbe.probePrompt)",
        "Model VRAM class: $($SelectedModelSelection.vramClass)",
        "Catalog defaultModelId: $($SelectedModelSelection.defaultModelId)",
        "Prikazi jos modela: $($SelectedModelSelection.showMoreModelsAfterInstall)",
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
$selectedModelSelection = Resolve-SelectedModelSelection `
    -RequestedModelId $SelectedModelId `
    -RequestedLabel $SelectedModelLabel `
    -RequestedDownloadFile $SelectedModelDownloadFile `
    -RequestedVramClass $SelectedModelVramClass
Write-InstallLogLine "Guided model selection: id=$($selectedModelSelection.modelId) source=$($selectedModelSelection.source) showMoreModels=$($selectedModelSelection.showMoreModelsAfterInstall)"

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
Copy-FolderContent -Source (Join-Path $payloadRoot "support\config\profiles") -Destination (Join-Path $workspaceRoot "config\profiles")
Copy-FolderContent -Source (Join-Path $payloadRoot "support\scripts") -Destination (Join-Path $workspaceRoot "scripts")
Copy-FolderContent -Source (Join-Path $payloadRoot "support\assets\icons") -Destination (Join-Path $workspaceRoot "assets\icons")
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
$modelBootstrapState = Invoke-ModelBootstrap -SelectedModelSelection $selectedModelSelection
Write-InstallLogLine "Model bootstrap result: status=$($modelBootstrapState.modelBootstrap.status) selectedModelDownloaded=$($modelBootstrapState.selectedModelDownloaded)"

$launchWrapper = Write-LaunchWrapper
$controlCenterIconPath = Join-Path $assetsDir "control-center.ico"
$openCodeIconPath = Join-Path $assetsDir "opencode-local-qwen.ico"
Write-Shortcut -ShortcutPath (Join-Path $desktopDir "Local AI Control Center.lnk") -TargetPath $launchWrapper -IconPath $controlCenterIconPath
if ($opencodeReady -and (Resolve-OpenCodePath)) {
    Write-Shortcut -ShortcutPath (Join-Path $desktopDir "OpenCode - Local AI Control Center.lnk") -TargetPath (Resolve-OpenCodePath) -IconPath $openCodeIconPath
}
Write-DesktopFolderMetadata -FolderPath $desktopDir -IconPath $controlCenterIconPath

$llamaPath = Join-Path $appsDir "llama.cpp\build\bin\llama-server.exe"
Write-JsonFile -Path $runtimeConfigPath -Payload @{ accessMode = $AccessMode }
Write-InstallLogLine "Wrote runtime-config.json"
Update-InstallStateAndSettings -LlamaReady $llamaReady -LlamaPath $llamaPath -TurboServerPath $turboServerPath -SelectedModelSelection $selectedModelSelection -ModelBootstrapState $modelBootstrapState
$healthyRuntimePort = Start-LegacyRuntimeIfNeeded
Write-InstallLogLine "Legacy runtime probe result: port=$healthyRuntimePort"
Update-InstallStateAndSettings -LlamaReady $llamaReady -LlamaPath $llamaPath -TurboServerPath $turboServerPath -SelectedModelSelection $selectedModelSelection -ModelBootstrapState $modelBootstrapState
$healthyRuntimePort = Find-HealthyRuntimePort
Update-ServiceLifecycle -HealthyPort $healthyRuntimePort
$controlCenterStart = Start-ControlCenterAndWait -LaunchWrapper $launchWrapper
Write-InstallLogLine "Control Center start result: started=$($controlCenterStart.Started) url=$($controlCenterStart.Url)"
$firstRunProbeState = Invoke-FirstRunProbe -HealthyRuntimePort $healthyRuntimePort -ModelBootstrapState $modelBootstrapState
Write-InstallLogLine "First-run probe result: status=$($firstRunProbeState.firstRunProbe.status) probeReady=$($firstRunProbeState.firstRunProbe.probeReady)"
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
    modelBootstrap = $modelBootstrapState.modelBootstrap
    firstRunProbe = [ordered]@{
        status = $firstRunProbeState.firstRunProbe.status
        message = $firstRunProbeState.firstRunProbe.message
        probeReady = [bool]$firstRunProbeState.firstRunProbe.probeReady
        probePrompt = [string]$firstRunProbeState.probePrompt
        probeResponse = [string]$firstRunProbeState.probeResponse
    }
}
Write-JsonFile -Path $installReportPath -Payload @{
    installRoot = $workspaceRoot
    appRoot = $appRoot
    edition = $Edition
    selectedModel = $selectedModelSelection
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
if (-not $components.modelBootstrap.bootstrapReady) { $failedCore += "model bootstrap" }
if (-not $components.firstRunProbe.probeReady) { $failedCore += "first-run probe" }
Write-InstallSummary -Components $components -SelectedModelSelection $selectedModelSelection -ControlCenterStart $controlCenterStart -RuntimePort $healthyRuntimePort -FailedCore $failedCore
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

