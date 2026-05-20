param(
    [string]$Version,
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

# Windows hybrid installer builder for local-qwen-control-center-next
# Produces Local-AI-Control-Center-Setup-<version>.exe
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$versionPath = Join-Path $repoRoot "version.json"
$issPath = Join-Path $PSScriptRoot "LocalAIControlCenterSetup.iss"

function Find-StableSupportRepo {
    $envOverride = $env:LOCAL_AI_CONTROL_CENTER_SUPPORT_REPO
    $candidates = @(
        $envOverride,
        (Join-Path (Split-Path $repoRoot -Parent) "Local Qwen 3.635Ba3B on home computer")
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-Path (Join-Path $candidate "config\profiles\defaults.json")) {
            return (Resolve-Path $candidate).Path
        }
    }

    throw "Stable support repo nije pronadjen. Postavi LOCAL_AI_CONTROL_CENTER_SUPPORT_REPO ili drzi stable repo kao sibling direktorijum."
}

function Find-Iscc {
    $candidates = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    if ($candidates) {
        return $candidates | Select-Object -First 1
    }

    $searchRoots = @(
        "C:\Program Files",
        "C:\Program Files (x86)",
        "$env:LOCALAPPDATA\Programs"
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($root in $searchRoots) {
        $match = Get-ChildItem $root -Filter ISCC.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($match) {
            return $match.FullName
        }
    }

    return $null
}

function Ensure-Version {
    if (-not (Test-Path $versionPath)) {
        throw "version.json nije pronadjen."
    }

    $versionData = Get-Content -Raw $versionPath | ConvertFrom-Json
    if ([string]::IsNullOrWhiteSpace($Version)) {
        $Version = [string]$versionData.version
    }

    if ($Version -notmatch '^\d+\.\d+\.\d+$') {
        throw "Version mora biti u obliku a.b.c"
    }

    return $versionData
}

function Copy-IfExists {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
        Copy-Item $Source $Destination -Force -Recurse
    }
}

function Copy-FolderIfExists {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        Copy-Item (Join-Path $Source "*") $Destination -Force -Recurse
    }
}

function New-StagingPayload {
    param(
        [string]$SupportRepoRoot,
        [object]$VersionData,
        [string]$ResolvedVersion
    )

    $stageRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("local-ai-control-center-stage-" + [guid]::NewGuid().ToString("N"))
    $payloadRoot = Join-Path $stageRoot "payload"
    $supportRoot = Join-Path $stageRoot "support"
    New-Item -ItemType Directory -Force -Path $payloadRoot, $supportRoot | Out-Null

    foreach ($dir in @("backend", "frontend", "launchers", "install", "state", "docs")) {
        Copy-FolderIfExists -Source (Join-Path $repoRoot $dir) -Destination (Join-Path $payloadRoot $dir)
    }

    foreach ($file in @("README.md", "run_control_center_next.py", "version.json", "release-notes.txt")) {
        Copy-IfExists -Source (Join-Path $repoRoot $file) -Destination (Join-Path $payloadRoot $file)
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $supportRoot "config\profiles"), (Join-Path $supportRoot "scripts"), (Join-Path $supportRoot "assets\icons"), (Join-Path $supportRoot "launcher\windows"), (Join-Path $supportRoot "install\windows") | Out-Null
    Copy-FolderIfExists -Source (Join-Path $SupportRepoRoot "config\profiles") -Destination (Join-Path $supportRoot "config\profiles")
    Copy-FolderIfExists -Source (Join-Path $SupportRepoRoot "scripts") -Destination (Join-Path $supportRoot "scripts")
    Copy-FolderIfExists -Source (Join-Path $SupportRepoRoot "assets\icons") -Destination (Join-Path $supportRoot "assets\icons")
    Copy-FolderIfExists -Source (Join-Path $SupportRepoRoot "launcher\windows") -Destination (Join-Path $supportRoot "launcher\windows")
    Copy-FolderIfExists -Source (Join-Path $SupportRepoRoot "install\windows") -Destination (Join-Path $supportRoot "install\windows")

    $supportLauncherDir = Join-Path $supportRoot "launcher\windows"
    $legacyCommon = Join-Path $supportLauncherDir "local-qwen-common.ps1"
    $newCommon = Join-Path $supportLauncherDir "local-ai-control-center-common.ps1"
    if ((Test-Path $legacyCommon) -and (-not (Test-Path $newCommon))) {
        Move-Item -LiteralPath $legacyCommon -Destination $newCommon -Force
    }

    $legacyIcon = Join-Path $supportRoot "assets\icons\opencode-local-qwen.ico"
    $newIcon = Join-Path $supportRoot "assets\icons\opencode-control-center.ico"
    if ((Test-Path $legacyIcon) -and (-not (Test-Path $newIcon))) {
        Copy-Item -LiteralPath $legacyIcon -Destination $newIcon -Force
    }

    if (Test-Path $supportLauncherDir) {
        Get-ChildItem -Path $supportLauncherDir -Filter *.ps1 -File -ErrorAction SilentlyContinue | ForEach-Object {
            $content = Get-Content -Raw $_.FullName
            $updated = $content `
                -replace '[A-Za-z0-9_-]+-common\.ps1', 'local-ai-control-center-common.ps1' `
                -replace 'Local Qwen Home Computer', 'Local AI Control Center' `
                -replace 'joes021/Local-Qwen-3\.635Ba3B-on-home-computer', 'joes021/local-ai-control-center' `
                -replace 'Local Qwen Control Center\.lnk', 'Local AI Control Center.lnk' `
                -replace 'opencode-local-qwen\.ico', 'opencode-control-center.ico'
            if ($updated -ne $content) {
                Set-Content -Path $_.FullName -Value $updated -Encoding UTF8
            }
        }
    }

    $supportInstallDir = Join-Path $supportRoot "install\windows"
    if (Test-Path $supportInstallDir) {
        Get-ChildItem -Path $supportInstallDir -File -ErrorAction SilentlyContinue | ForEach-Object {
            $content = Get-Content -Raw $_.FullName
            $updated = $content `
                -replace 'LocalQwenHome', 'LocalAIControlCenter' `
                -replace 'Local Qwen Home Computer', 'Local AI Control Center' `
                -replace 'Local Qwen', 'Local AI' `
                -replace 'local-qwen', 'local-ai-control-center'
            if ($updated -ne $content) {
                Set-Content -Path $_.FullName -Value $updated -Encoding UTF8
            }
        }
    }

    if (Test-Path $legacyCommon) {
        Remove-Item -LiteralPath $legacyCommon -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $legacyIcon) {
        Remove-Item -LiteralPath $legacyIcon -Force -ErrorAction SilentlyContinue
    }

    return @{
        StageRoot = $stageRoot
        PayloadRoot = $payloadRoot
        SupportRoot = $supportRoot
        ArtifactName = "$($VersionData.windowsSetupBaseName)-$ResolvedVersion.exe"
    }
}

$supportRepoRoot = Find-StableSupportRepo
$versionData = Ensure-Version
$resolvedVersion = if ([string]::IsNullOrWhiteSpace($Version)) { [string]$versionData.version } else { $Version }
$OutputDir = if ($OutputDir) { $OutputDir } else { Join-Path $repoRoot "dist\windows" }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$iscc = Find-Iscc
if (-not $iscc) {
    throw "ISCC.exe nije pronadjen. Instaliraj Inno Setup 6."
}

$stage = New-StagingPayload -SupportRepoRoot $supportRepoRoot -VersionData $versionData -ResolvedVersion $resolvedVersion

try {
    $defines = @(
        "/DMyAppName=$($versionData.displayName)",
        "/DMyAppVersion=$resolvedVersion",
        "/DMySetupBaseName=$($versionData.windowsSetupBaseName)",
        "/DSourceRoot=$($stage.PayloadRoot)",
        "/DSupportRoot=$($stage.SupportRoot)",
        "/O$OutputDir",
        $issPath
    )

    & $iscc @defines
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup build nije uspeo."
    }

    $artifact = Join-Path $OutputDir $stage.ArtifactName
    if (-not (Test-Path $artifact)) {
        throw "Ocekivani setup artefakt nije pronadjen: $artifact"
    }

    Write-Host "Windows hybrid installer spreman za Local AI Control Center:" -ForegroundColor Green
    Write-Host $artifact
}
finally {
    if (Test-Path $stage.StageRoot) {
        Remove-Item -LiteralPath $stage.StageRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
