param(
    [string]$InstallRoot = "$env:USERPROFILE\LocalAIControlCenter",
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

# Unified installer overlay for the Local AI Control Center runtime.
# This script keeps backward compatibility with the older runtime layout while deploying control-center-next as the Next shell.
$payloadRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$workspaceRoot = $InstallRoot
$appRoot = Join-Path $workspaceRoot "control-center-next"
$stateDir = Join-Path $workspaceRoot "state"
$appsDir = Join-Path $workspaceRoot "apps"
$binDir = Join-Path $workspaceRoot "bin"
$launchersDir = Join-Path $appRoot "launchers\windows"
$legacyLaunchersPayloadDir = Join-Path $payloadRoot "support\launcher\windows"
$legacyInstallPayloadDir = Join-Path $payloadRoot "support\install\windows"
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
$legacyInstallStatusPath = Join-Path $stateDir "legacy-install-status.ini"
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

function Find-ExistingExecutablePath {
    param(
        [string[]]$CandidatePaths
    )

    foreach ($candidate in $CandidatePaths) {
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-WorkspaceSeedSource {
    param(
        [string]$PrimaryRelativePath,
        [string]$FallbackRelativePath
    )

    $primaryPath = Join-Path $payloadRoot $PrimaryRelativePath
    if (Test-Path $primaryPath) {
        return $primaryPath
    }

    return (Join-Path $payloadRoot $FallbackRelativePath)
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

function Get-ExceptionSummary {
    param([System.Exception]$Exception)

    if ($null -eq $Exception) {
        return "Nepoznata greska."
    }

    $messages = New-Object System.Collections.Generic.List[string]
    $current = $Exception
    while ($null -ne $current) {
        if (-not [string]::IsNullOrWhiteSpace($current.Message)) {
            $messages.Add($current.Message.Trim())
        }
        $current = $current.InnerException
    }

    if ($messages.Count -eq 0) {
        return $Exception.GetType().FullName
    }

    return (($messages | Select-Object -Unique) -join " | ")
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

    $legacyCommonScript = Join-Path $legacyLaunchersDir "local-ai-control-center-common.ps1"
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

function Invoke-LegacyCoreInstall {
    param([object]$SelectedModelSelection)

    $legacyInstallScript = Join-Path $legacyInstallPayloadDir "install.ps1"
    if (-not (Test-Path $legacyInstallScript)) {
        throw "Legacy core installer nije pronadjen: $legacyInstallScript"
    }

    $legacyModelId = if (-not [string]::IsNullOrWhiteSpace([string]$SelectedModelSelection.legacyModelId)) {
        [string]$SelectedModelSelection.legacyModelId
    }
    else {
        [string]$SelectedModelSelection.modelId
    }

    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $legacyInstallScript,
        "-InstallRoot", $workspaceRoot,
        "-DesktopFolder", (Join-Path $env:USERPROFILE "Desktop"),
        "-Profile", $Profile,
        "-ModelId", $legacyModelId,
        "-LogPath", $installLogPath,
        "-SummaryPath", $installSummaryPath,
        "-StatusPath", $legacyInstallStatusPath
    )

    if ($SkipDependencies) { $arguments += "-SkipDependencies" }
    if ($SkipOpenCodeInstall) { $arguments += "-SkipOpenCodeInstall" }
    if ($SkipLlamaSetup) { $arguments += "-SkipLlamaDownload" }
    if ($SkipTurboQuant) { $arguments += "-SkipTurboQuantBuild" }
    if ($SkipModelDownload) { $arguments += "-SkipModelDownload" }

    Write-InstallLogLine "Legacy core install start: modelId=$legacyModelId"
    & (Get-WindowsPowerShellExe) @arguments | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Legacy core installer nije uspeo. Exit code: $LASTEXITCODE"
    }
    Write-InstallLogLine "Legacy core install finished successfully."
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

    $candidateHomes = @(
        (Join-Path $env:USERPROFILE "LocalAIControlCenter")
    ) | Select-Object -Unique
    $candidatePaths = foreach ($candidateHome in $candidateHomes) {
        @(
            (Join-Path $candidateHome "models\$downloadFile"),
            (Join-Path $candidateHome ("models\\llama-cpp\\{0}\\{1}" -f [System.IO.Path]::GetFileNameWithoutExtension($downloadFile), $downloadFile))
        )
    }

    $resolvedSource = $candidatePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $resolvedSource) {
        foreach ($candidateHome in $candidateHomes) {
            $modelsRoot = Join-Path $candidateHome "models"
            if (-not (Test-Path $modelsRoot)) {
                continue
            }
            $resolvedSource = Get-ChildItem -Path $modelsRoot -Recurse -Filter $downloadFile -File -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty FullName -First 1
            if ($resolvedSource) {
                break
            }
        }
    }

    if (-not $resolvedSource) {
        return
    }

    Ensure-Dir (Split-Path -Parent $workspaceModelPath)
    Copy-Item -LiteralPath $resolvedSource -Destination $workspaceModelPath -Force
    Write-InstallLogLine "Synced bootstrapped model into workspace: source=$resolvedSource target=$workspaceModelPath"
}

function Normalize-WorkspaceBranding {
    $windowsLauncherDir = $legacyLaunchersDir
    if (Test-Path $windowsLauncherDir) {
        $newCommon = Join-Path $windowsLauncherDir "local-ai-control-center-common.ps1"
        $oldCommon = Get-ChildItem -Path $windowsLauncherDir -File -Filter "*-common.ps1" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -ne "local-ai-control-center-common.ps1" } |
            Select-Object -First 1
        if ((-not (Test-Path $newCommon)) -and $oldCommon) {
            Move-Item -LiteralPath $oldCommon.FullName -Destination $newCommon -Force
        }

        Get-ChildItem -Path $windowsLauncherDir -Filter *.ps1 -File -ErrorAction SilentlyContinue | ForEach-Object {
            $content = Get-Content -Raw $_.FullName
            $updated = $content -replace '[A-Za-z0-9_-]+-common\.ps1', 'local-ai-control-center-common.ps1'
            if ($updated -ne $content) {
                Set-Content -Path $_.FullName -Value $updated -Encoding UTF8
            }
        }

        if (Test-Path $newCommon) {
            $content = Get-Content -Raw $newCommon
            $updated = $content
            $updated = $updated -replace '@\("opencode\.cmd", "opencode\.ps1", "opencode", "opencode\.exe"\)', '@("opencode.ps1", "opencode.cmd", "opencode", "opencode.exe")'
            $updated = $updated.Replace(
@'
if ($extension -ieq ".cmd") {
        $npmDir = Split-Path -Parent $executablePath
        $binScript = Join-Path $npmDir "node_modules\opencode-ai\bin\opencode"
        if (-not (Test-Path $binScript)) {
            throw "OpenCode bin skripta nije pronadjena: $binScript"
        }

        return [pscustomobject]@{
            mode = "node"
            executablePath = (Get-NodeExecutable)
            scriptPath = $binScript
            displayPath = $executablePath
        }
    }
'@,
@'
if ($extension -ieq ".cmd") {
        $npmDir = Split-Path -Parent $executablePath
        $nativeExe = Join-Path $npmDir "node_modules\opencode-ai\bin\opencode.exe"
        if (Test-Path $nativeExe) {
            return [pscustomobject]@{
                mode = "direct"
                executablePath = $nativeExe
                scriptPath = $null
                displayPath = $executablePath
            }
        }

        $binScript = Join-Path $npmDir "node_modules\opencode-ai\bin\opencode"
        if (-not (Test-Path $binScript)) {
            throw "OpenCode bin skripta nije pronadjena: $binScript"
        }

        return [pscustomobject]@{
            mode = "node"
            executablePath = (Get-NodeExecutable)
            scriptPath = $binScript
            displayPath = $executablePath
        }
    }
'@
            )
            $updated = $updated.Replace(
@'
function Get-LlamaServerExe {
    $state = Get-InstallState
    $candidates = @()

    if ($state.PSObject.Properties["turboServerExe"] -and $state.turboServerExe) {
        $candidates += [string]$state.turboServerExe
    }

    if ($state.PSObject.Properties["llamaBinDir"] -and $state.llamaBinDir) {
        $candidates += (Join-Path $state.llamaBinDir "llama-server.exe")
    }

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "llama-server.exe nije pronadjen ni u TurboQuant ni u upstream bin folderu."
}
'@,
@'
function Get-LlamaServerExe {
    $state = Get-InstallState
    $candidates = New-Object System.Collections.Generic.List[string]

    if ($state.PSObject.Properties["turboServerExe"] -and $state.turboServerExe) {
        $candidates.Add([string]$state.turboServerExe) | Out-Null
    }

    if ($state.PSObject.Properties["llamaServerExe"] -and $state.llamaServerExe) {
        $candidates.Add([string]$state.llamaServerExe) | Out-Null
    }

    if ($state.PSObject.Properties["llamaBinDir"] -and $state.llamaBinDir) {
        $candidates.Add((Join-Path $state.llamaBinDir "llama-server.exe")) | Out-Null
    }

    $installRoot = if ($state.PSObject.Properties["installRoot"] -and $state.installRoot) { [string]$state.installRoot } else { (Get-LocalQwenStateRoot) }
    foreach ($candidate in @(
        (Join-Path $installRoot "apps\llama.cpp\bin\llama-server.exe"),
        (Join-Path $installRoot "apps\llama.cpp\build\bin\llama-server.exe"),
        (Join-Path $installRoot "apps\llama.cpp-turboquant\build-cuda\bin\llama-server.exe")
    )) {
        if ($candidate) {
            $candidates.Add($candidate) | Out-Null
        }
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    $discovered = Get-ChildItem -Path (Join-Path $installRoot "apps") -Recurse -Filter "llama-server.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($discovered) {
        return $discovered.FullName
    }

    throw "llama-server.exe nije pronadjen ni u TurboQuant ni u upstream bin folderu."
}
'@
            )
            $updated = $updated -replace "joes021/Local-Qwen-3\.635Ba3B-on-home-computer", "joes021/local-ai-control-center"
            $updated = $updated -replace "Local Qwen Home Computer", "Local AI Control Center"
            $updated = $updated -replace "Local Qwen Control Center\.lnk", "Local AI Control Center.lnk"
            if ($updated -ne $content) {
                Set-Content -Path $newCommon -Value $updated -Encoding UTF8
            }
        }
    }

    $legacyIcon = Get-ChildItem -Path $assetsDir -File -Filter "opencode-*.ico" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "opencode-control-center.ico" } |
        Select-Object -First 1
    $newIcon = Join-Path $assetsDir "opencode-control-center.ico"
    if ((-not (Test-Path $newIcon)) -and $legacyIcon) {
        Copy-Item -LiteralPath $legacyIcon.FullName -Destination $newIcon -Force
    }
    if ($legacyIcon -and (Test-Path $legacyIcon.FullName) -and ($legacyIcon.FullName -ne $newIcon)) {
        Remove-Item -LiteralPath $legacyIcon.FullName -Force -ErrorAction SilentlyContinue
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
    $pythonPath = Find-ExistingExecutablePath -CandidatePaths @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
        (Join-Path $env:USERPROFILE "AppData\Local\Programs\Python\Python312\python.exe"),
        (Join-Path $env:USERPROFILE "AppData\Local\Programs\Python\Python313\python.exe")
    )
    if ($pythonPath) {
        return $pythonPath
    }
    if (Ensure-Command -Name "python" -WingetId "Python.Python.3.12") {
        return "python"
    }
    throw "Python nije dostupan."
}

function Ensure-Node {
    if ((Get-Command node -ErrorAction SilentlyContinue) -and (Get-Command npm -ErrorAction SilentlyContinue)) {
        return
    }
    $packagesRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $packagesRoot) {
        $nodePackage = Get-ChildItem -Path $packagesRoot -Directory -Filter "OpenJS.NodeJS.LTS_*" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($nodePackage) {
            $nodeExe = Find-ExistingExecutablePath -CandidatePaths @(
                (Join-Path $nodePackage.FullName "node.exe")
            )
            $npmCmd = Find-ExistingExecutablePath -CandidatePaths @(
                (Join-Path $nodePackage.FullName "npm.cmd")
            )
            if ($nodeExe -and $npmCmd) {
                $script:ManualNodeExe = $nodeExe
                $script:ManualNpmCmd = $npmCmd
                return
            }
        }
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
    $npmCommand = if ($script:ManualNpmCmd) { $script:ManualNpmCmd } else { "npm" }
    & $npmCommand install -g opencode-ai
    return [bool](Get-Command opencode -ErrorAction SilentlyContinue)
}

function Get-LegacyCommonScriptPath {
    $candidates = @(
        (Join-Path $legacyLaunchersDir "local-ai-control-center-common.ps1"),
        (Join-Path $legacyLaunchersPayloadDir "local-ai-control-center-common.ps1")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "Common launcher skripta nije pronadjena u Local AI Control Center payload-u."
}

function Resolve-LlamaCppServerPath {
    param([string]$Target)

    if ([string]::IsNullOrWhiteSpace($Target)) {
        return ""
    }

    $directCandidates = @(
        (Join-Path $Target "build\bin\llama-server.exe"),
        (Join-Path $Target "bin\llama-server.exe")
    )
    foreach ($candidate in $directCandidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $resolved = Get-ChildItem -Path $Target -Recurse -Filter "llama-server.exe" -File -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($resolved) {
        return $resolved.FullName
    }

    return ""
}

function Ensure-LlamaCpp {
    $target = Join-Path $appsDir "llama.cpp"
    $existingPath = Resolve-LlamaCppServerPath -Target $target
    if ($existingPath) {
        return $existingPath
    }
    $existingState = Read-JsonFile $installStatePath
    if ($existingState -and $existingState.llamaServerExe -and (Test-Path ([string]$existingState.llamaServerExe))) {
        return [string]$existingState.llamaServerExe
    }
    $running = Get-RunningRuntimeInfo
    if ($running -and $running.ExecutablePath -and (Test-Path ([string]$running.ExecutablePath))) {
        return [string]$running.ExecutablePath
    }
    if (Find-HealthyRuntimePort) {
        return ""
    }
    if ($SkipLlamaSetup) {
        return ""
    }
    if (-not (Test-Path $target)) {
        git clone https://github.com/ggml-org/llama.cpp.git $target
    }
    $llamaExe = Resolve-LlamaCppServerPath -Target $target
    if (-not $llamaExe -and (Get-Command cmake -ErrorAction SilentlyContinue)) {
        $cudaFlag = if (Get-Command nvcc -ErrorAction SilentlyContinue) { "ON" } else { "OFF" }
        $generator = if (Get-Command ninja -ErrorAction SilentlyContinue) { "Ninja" } else { "Visual Studio 17 2022" }
        Write-InstallLogLine "Ensure-LlamaCpp: attempting local build with generator=$generator cuda=$cudaFlag"
        & cmake -G $generator -S $target -B (Join-Path $target "build") "-DGGML_CUDA=$cudaFlag" | Out-Null
        if ($LASTEXITCODE -eq 0) {
            & cmake --build (Join-Path $target "build") --config Release -j | Out-Null
        }
        $llamaExe = Resolve-LlamaCppServerPath -Target $target
    }

    if (-not $llamaExe) {
        try {
            $legacyCommonScript = Get-LegacyCommonScriptPath
            . $legacyCommonScript
            $prebuiltDir = Join-Path $target "bin"
            Write-InstallLogLine "Ensure-LlamaCpp: local build unavailable, downloading prebuilt llama.cpp Windows CUDA binary."
            Download-LlamaCppWindowsCuda -DestinationDir $prebuiltDir
            $llamaExe = Resolve-LlamaCppServerPath -Target $target
        }
        catch {
            Write-InstallLogLine "Ensure-LlamaCpp fallback failed: $(Get-ExceptionSummary -Exception $_.Exception)"
        }
    }

    return $llamaExe
}

function Ensure-TurboQuant {
    if ($SkipTurboQuant) {
        return @{ status = "skipped"; path = ""; reason = "TurboQuant je iskljucen u installer izboru."; details = @() }
    }
    $target = Join-Path $appsDir "llama.cpp-turboquant"
    $details = New-Object System.Collections.Generic.List[string]
    $details.Add("Target: $target") | Out-Null
    if (Test-Path $target) {
        $details.Add("Repo vec postoji.") | Out-Null
    } else {
        $details.Add("Repo ne postoji, pokusavam git clone.") | Out-Null
        & git clone https://github.com/TheTom/llama-cpp-turboquant.git $target | Out-Null
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $target)) {
            return @{
                status = "clone-failed"
                path = ""
                reason = "TurboQuant repo nije uspesno kloniran."
                details = $details
            }
        }
        $details.Add("Git clone uspesan.") | Out-Null
    }
    $turboExe = Join-Path $target "build-cuda\bin\llama-server.exe"
    if (Test-Path $turboExe) {
        $details.Add("TurboQuant binar je vec prisutan.") | Out-Null
        return @{ status = "present"; path = $target; reason = "TurboQuant binar je pronadjen i spreman."; details = $details }
    }

    $cmakeCmd = Get-Command cmake -ErrorAction SilentlyContinue
    $nvccCmd = Get-Command nvcc -ErrorAction SilentlyContinue
    if (-not $cmakeCmd) {
        $details.Add("cmake nije pronadjen u PATH-u.") | Out-Null
        return @{
            status = "missing-cmake"
            path = ""
            reason = "TurboQuant build nije moguc jer cmake nije dostupan."
            details = $details
        }
    }
    if (-not $nvccCmd) {
        $details.Add("nvcc nije pronadjen u PATH-u.") | Out-Null
        return @{
            status = "missing-nvcc"
            path = ""
            reason = "TurboQuant build nije moguc jer CUDA nvcc nije dostupan."
            details = $details
        }
    }

    $generator = if (Get-Command ninja -ErrorAction SilentlyContinue) { "Ninja" } else { "Visual Studio 17 2022" }
    $buildDir = Join-Path $target "build-cuda"
    $details.Add("Generator: $generator") | Out-Null
    $details.Add("Build dir: $buildDir") | Out-Null
    & cmake -G $generator -S $target -B $buildDir -DGGML_CUDA=ON | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $details.Add("cmake configure je vratio non-zero exit code.") | Out-Null
        return @{
            status = "configure-failed"
            path = ""
            reason = "TurboQuant configure korak nije uspeo."
            details = $details
        }
    }

    & cmake --build $buildDir --config Release -j | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $details.Add("cmake build je vratio non-zero exit code.") | Out-Null
        return @{
            status = "build-failed"
            path = ""
            reason = "TurboQuant build korak nije uspeo."
            details = $details
        }
    }

    if (Test-Path $turboExe) {
        $details.Add("TurboQuant build je proizveo llama-server.exe.") | Out-Null
        return @{ status = "present"; path = $target; reason = "TurboQuant je uspesno buildovan i spreman."; details = $details }
    }

    $details.Add("Build je zavrsen bez pronadjenog binara.") | Out-Null
    return @{
        status = "not-installed"
        path = ""
        reason = "TurboQuant nije ostavio startabilan binar posle build koraka."
        details = $details
    }
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

function Get-DetectedGpuMemoryMiBForInstaller {
    try {
        $controllers = Get-CimInstance Win32_VideoController -ErrorAction Stop |
            Where-Object { $_.AdapterRAM -and [int64]$_.AdapterRAM -gt 0 }
        if (-not $controllers) {
            return 0
        }
        $maxBytes = ($controllers | Measure-Object -Property AdapterRAM -Maximum).Maximum
        if (-not $maxBytes) {
            return 0
        }
        return [int][math]::Floor(([double]$maxBytes) / 1MB)
    }
    catch {
        return 0
    }
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
    $installedModelLeaf = if ($InstalledModelFile) { Split-Path $InstalledModelFile -Leaf } else { "" }
    $hasExistingInstalledModel = -not [string]::IsNullOrWhiteSpace($InstalledModelFile) -and (Test-Path $InstalledModelFile)
    $selectedModelMatchesInstalledModel = $InstalledModelFile -and $selectedModelDownloadFile -and ($installedModelLeaf -eq $selectedModelDownloadFile)
    if ($selectedModelPath -and (Test-Path $selectedModelPath)) {
        $selectedModelDownloaded = $true
    }
    elseif ($selectedModelMatchesInstalledModel) {
        $selectedModelDownloaded = $true
        $selectedModelPath = $InstalledModelFile
    }

    $effectiveStatus = $BootstrapStatus
    if ([string]::IsNullOrWhiteSpace($effectiveStatus)) {
        if ([string]::IsNullOrWhiteSpace($selectedModelId) -or [string]::IsNullOrWhiteSpace($selectedModelDownloadFile)) {
            $effectiveStatus = "selection-missing"
        }
        elseif ($selectedModelDownloaded) {
            $effectiveStatus = "ready"
        }
        elseif ($hasExistingInstalledModel) {
            $effectiveStatus = "different-model-active"
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
            "different-model-active" { $BootstrapMessage = "Na masini postoji drugi aktivni model, ali installer i dalje mora da potvrdi ili preuzme bas izabrani model." }
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

    $resolvedBootstrapState = Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile (Get-PreferredModelFile) -BootstrapStatus "downloaded"
    if (-not $resolvedBootstrapState.modelBootstrap.bootstrapReady) {
        return (Get-ModelBootstrapState -SelectedModelSelection $SelectedModelSelection -InstalledModelFile (Get-PreferredModelFile) -BootstrapStatus "download-failed" -BootstrapMessage "Selected model nije pronadjen posle download koraka.")
    }

    return $resolvedBootstrapState
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

    $detectedGpuMiB = Get-DetectedGpuMemoryMiBForInstaller
    $defaultContextSize = 262144
    $defaultMaxOutputTokens = 8192
    $defaultContextCustomized = $false
    $defaultMaxOutputCustomized = $false
    if ($detectedGpuMiB -gt 0) {
        if ($detectedGpuMiB -le 8192) {
            $defaultContextSize = 4096
            $defaultMaxOutputTokens = 2048
            $defaultContextCustomized = $true
            $defaultMaxOutputCustomized = $true
        }
        elseif ($detectedGpuMiB -le 12288) {
            $defaultContextSize = 8192
            $defaultMaxOutputTokens = 2048
            $defaultContextCustomized = $true
            $defaultMaxOutputCustomized = $true
        }
        else {
            $defaultContextSize = 16384
            $defaultMaxOutputTokens = 4096
            $defaultContextCustomized = $true
            $defaultMaxOutputCustomized = $true
        }
    }

    $settingsPayload = [ordered]@{
        edition = if ($existingSettings -and $existingSettings.edition) { [string]$existingSettings.edition } else { $Edition }
        profile = if ($existingSettings -and $existingSettings.profile) { [string]$existingSettings.profile } else { $Profile }
        accessMode = $AccessMode
        llama = [ordered]@{
            contextSize = if ($existingSettings -and $existingSettings.llama -and $existingSettings.llama.contextSize) { [int]$existingSettings.llama.contextSize } else { $defaultContextSize }
            maxOutputTokens = if ($existingSettings -and $existingSettings.llama -and $existingSettings.llama.maxOutputTokens) { [int]$existingSettings.llama.maxOutputTokens } else { $defaultMaxOutputTokens }
            contextSizeCustomized = if ($existingSettings -and $existingSettings.llama) { [bool]$existingSettings.llama.contextSizeCustomized } else { $defaultContextCustomized }
            maxOutputTokensCustomized = if ($existingSettings -and $existingSettings.llama) { [bool]$existingSettings.llama.maxOutputTokensCustomized } else { $defaultMaxOutputCustomized }
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

    Start-Process -FilePath (Get-WindowsPowerShellExe) `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $startServerScript, "-Profile", $Profile) `
        -WindowStyle Hidden | Out-Null

    for ($i = 0; $i -lt 45; $i++) {
        $healthyPort = Find-HealthyRuntimePort
        if ($healthyPort) {
            return $healthyPort
        }
        Start-Sleep -Seconds 2
    }

    return $null
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
        $startControlCenterScript = Join-Path $launchersDir "start-control-center-next.ps1"
        Start-Process -FilePath (Get-WindowsPowerShellExe) -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            $startControlCenterScript
        ) -WindowStyle Hidden | Out-Null
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
        "TurboQuant explanation: $($Components.turboQuantRuntime.reason)",
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
if (-not [string]::IsNullOrWhiteSpace([string]$selectedModelSelection.customSource)) {
    $selectedModelSelection = Register-InstallerSelectedModelWithLegacyCatalog -SelectedModelSelection $selectedModelSelection
}
Invoke-LegacyCoreInstall -SelectedModelSelection $selectedModelSelection

if (-not $SkipDependencies) {
    Write-InstallLogLine "Dependency bootstrap started."
    try {
        Ensure-Command -Name "git" -WingetId "Git.Git" | Out-Null
        Write-InstallLogLine "Dependency bootstrap: git ready."
        $pythonExe = Ensure-Python
        Write-InstallLogLine "Dependency bootstrap: python ready at $pythonExe"
        Ensure-Node
        Write-InstallLogLine "Dependency bootstrap: node/npm ready. node=$script:ManualNodeExe npm=$script:ManualNpmCmd"
        Write-InstallLogLine "Dependency bootstrap finished."
    }
    catch {
        $exceptionSummary = Get-ExceptionSummary -Exception $_.Exception
        Write-InstallLogLine "Dependency bootstrap failed: $exceptionSummary"
        throw
    }
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
Normalize-WorkspaceBranding
Copy-FolderContent -Source (Get-WorkspaceSeedSource -PrimaryRelativePath "support\config\profiles" -FallbackRelativePath "config\profiles") -Destination (Join-Path $workspaceRoot "config\profiles")
Copy-FolderContent -Source (Get-WorkspaceSeedSource -PrimaryRelativePath "support\scripts" -FallbackRelativePath "scripts") -Destination (Join-Path $workspaceRoot "scripts")
Copy-FolderContent -Source (Get-WorkspaceSeedSource -PrimaryRelativePath "support\assets\icons" -FallbackRelativePath "assets\icons") -Destination (Join-Path $workspaceRoot "assets\icons")
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
try {
    $opencodeReady = Ensure-OpenCode
    Write-InstallLogLine "Component check: OpenCode=$opencodeReady"
    $llamaPath = Ensure-LlamaCpp
    $llamaReady = -not [string]::IsNullOrWhiteSpace($llamaPath)
    Write-InstallLogLine "Component check: llamaReady=$llamaReady path=$llamaPath"
    $turboInfo = Ensure-TurboQuant
    Write-InstallLogLine "Component check: TurboQuant=$($turboInfo.status) reason=$($turboInfo.reason)"
    foreach ($detailLine in ($turboInfo.details | Where-Object { $_ })) {
        Write-InstallLogLine "TurboQuant detail: $detailLine"
    }
}
catch {
    $exceptionSummary = Get-ExceptionSummary -Exception $_.Exception
    Write-InstallLogLine "Component check failed: $exceptionSummary"
    throw
}
$turboServerPath = if ($turboInfo.status -eq "present") { (Resolve-LlamaCppServerPath -Target (Join-Path $appsDir "llama.cpp-turboquant")) } else { "" }
Write-InstallLogLine "Component check finished: OpenCode=$opencodeReady llamaReady=$llamaReady TurboQuant=$($turboInfo.status)"

$launchWrapper = Write-LaunchWrapper
$controlCenterIconPath = Join-Path $assetsDir "control-center.ico"
$openCodeIconPath = Join-Path $assetsDir "opencode-control-center.ico"
Write-Shortcut -ShortcutPath (Join-Path $desktopDir "Local AI Control Center.lnk") -TargetPath $launchWrapper -IconPath $controlCenterIconPath
if ($opencodeReady -and (Resolve-OpenCodePath)) {
    Write-Shortcut -ShortcutPath (Join-Path $desktopDir "OpenCode - Local AI Control Center.lnk") -TargetPath (Resolve-OpenCodePath) -IconPath $openCodeIconPath
}
Write-DesktopFolderMetadata -FolderPath $desktopDir -IconPath $controlCenterIconPath

Write-JsonFile -Path $runtimeConfigPath -Payload @{ accessMode = $AccessMode }
Write-InstallLogLine "Wrote runtime-config.json"
Update-InstallStateAndSettings -LlamaReady $llamaReady -LlamaPath $llamaPath -TurboServerPath $turboServerPath -SelectedModelSelection $selectedModelSelection -ModelBootstrapState $null
Write-InstallLogLine "Wrote initial install-state.json before model bootstrap."
$modelBootstrapState = Invoke-ModelBootstrap -SelectedModelSelection $selectedModelSelection
Write-InstallLogLine "Model bootstrap result: status=$($modelBootstrapState.modelBootstrap.status) selectedModelDownloaded=$($modelBootstrapState.selectedModelDownloaded)"
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
    turboQuantRuntime = @{
        ok = ($turboInfo.status -eq "present")
        path = $effectiveTurboPath
        status = $turboInfo.status
        reason = $turboInfo.reason
        details = $turboInfo.details
    }
    modelBootstrap = $modelBootstrapState.modelBootstrap
    firstRunProbe = [ordered]@{
        status = $firstRunProbeState.firstRunProbe.status
        message = $firstRunProbeState.firstRunProbe.message
        probeReady = [bool]$firstRunProbeState.firstRunProbe.probeReady
        probePrompt = [string]$firstRunProbeState.probePrompt
        probeResponse = [string]$firstRunProbeState.probeResponse
    }
}
$turboQuantRequired = -not $SkipTurboQuant
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
if ($turboQuantRequired -and -not $components.turboQuantRuntime.ok) { $failedCore += "TurboQuant" }
Write-InstallSummary -Components $components -SelectedModelSelection $selectedModelSelection -ControlCenterStart $controlCenterStart -RuntimePort $healthyRuntimePort -FailedCore $failedCore
Write-InstallLogLine "Install summary written."

Write-Host "Install report:" -ForegroundColor Cyan
Write-Host "Edition: $Edition"
Write-Host "Control Center: $($components.controlCenter.ok)"
Write-Host "llama.cpp: $($components.llamaCppRuntime.ok)"
Write-Host "OpenCode: $($components.openCode.ok)"
Write-Host "TurboQuant: $($components.turboQuantRuntime.status)"
Write-Host "TurboQuant detail: $($components.turboQuantRuntime.reason)"
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
exit 0

