param(
    [string]$Version,
    [switch]$SkipBuild,
    [switch]$SkipGitPush,
    [switch]$SkipReleasePublish
)

$ErrorActionPreference = "Stop"

# Expected artifact patterns:
# - Local-AI-Control-Center-Setup-<version>.exe
# - Local-AI-Control-Center-Setup-linux-x86_64-<version>.run
# - Local-AI-Control-Center-Setup-linux-arm64-<version>.run
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$versionPath = Join-Path $repoRoot "version.json"
$windowsBuildScript = Join-Path $repoRoot "packaging\windows\build-setup.ps1"
$linuxBuildScript = Join-Path $repoRoot "packaging\linux\build-run-installer.sh"
$releaseNotesPath = Join-Path $repoRoot "release-notes.txt"
$supportMatrixTemplatePath = Join-Path $repoRoot "packaging\release\support-matrix.template.json"
$distWindows = Join-Path $repoRoot "dist\windows"
$distLinux = Join-Path $repoRoot "dist\linux"
$tempReleaseDir = Join-Path $repoRoot "dist\release-meta"

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

$windowsArtifact = Join-Path $distWindows "$($versionData.windowsSetupBaseName)-$Version.exe"
$linuxX64Artifact = Join-Path $distLinux "$($versionData.windowsSetupBaseName)-linux-x86_64-$Version.run"
$linuxArm64Artifact = Join-Path $distLinux "$($versionData.windowsSetupBaseName)-linux-arm64-$Version.run"
$checksumsPath = Join-Path $tempReleaseDir "checksums.txt"
$supportMatrixPath = Join-Path $tempReleaseDir "support-matrix.json"
$releaseSummaryPath = Join-Path $tempReleaseDir "release-summary-v$Version.md"

function Get-ReleaseSection {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Version
    )

    $content = Get-Content -Raw $Path
    $pattern = "(?ms)^v$([regex]::Escape($Version))\s*\r?\n(?<body>.*?)(?=^\s*v\d+\.\d+\.\d+\s*$|\z)"
    $match = [regex]::Match($content, $pattern)
    if (-not $match.Success) {
        return "v$Version`r`n- Release notes nisu jos detaljno zapisane."
    }
    return ("v{0}`r`n{1}" -f $Version, $match.Groups["body"].Value.Trim())
}

function Get-FileHashLine {
    param([string]$Path)
    $hash = Get-FileHash -Algorithm SHA256 -Path $Path
    return "{0} *{1}" -f $hash.Hash.ToLowerInvariant(), [System.IO.Path]::GetFileName($Path)
}

if (-not $SkipBuild) {
    & powershell -ExecutionPolicy Bypass -File $windowsBuildScript -Version $Version
    if ($LASTEXITCODE -ne 0) {
        throw "Windows build nije uspeo."
    }

    & bash $linuxBuildScript $Version all
    if ($LASTEXITCODE -ne 0) {
        throw "Linux build nije uspeo."
    }
}

foreach ($artifact in @($windowsArtifact, $linuxX64Artifact, $linuxArm64Artifact)) {
    if (-not (Test-Path $artifact)) {
        throw "Artefakt nije pronadjen: $artifact"
    }
}

New-Item -ItemType Directory -Force -Path $tempReleaseDir | Out-Null

@(
    Get-FileHashLine -Path $windowsArtifact
    Get-FileHashLine -Path $linuxX64Artifact
    Get-FileHashLine -Path $linuxArm64Artifact
) | Set-Content -Path $checksumsPath -Encoding UTF8

if (Test-Path $supportMatrixTemplatePath) {
    Copy-Item $supportMatrixTemplatePath $supportMatrixPath -Force
}

$releaseSection = Get-ReleaseSection -Path $releaseNotesPath -Version $Version
$releaseSummary = @(
    "v$Version",
    "",
    "- Windows installer: $([System.IO.Path]::GetFileName($windowsArtifact))",
    "- Ubuntu x86_64 installer: $([System.IO.Path]::GetFileName($linuxX64Artifact))",
    "- Ubuntu arm64 installer: $([System.IO.Path]::GetFileName($linuxArm64Artifact))",
    "- Attached metadata: checksums.txt and support-matrix.json",
    "",
    $releaseSection
) -join "`r`n"
Set-Content -Path $releaseSummaryPath -Value $releaseSummary -Encoding UTF8

if (-not $SkipGitPush) {
    & git -C $repoRoot push origin "codex/windows-control-center-next-adapter"
    if ($LASTEXITCODE -ne 0) {
        throw "git push nije uspeo."
    }
}

if (-not $SkipReleasePublish) {
    & gh release create "v$Version" `
        $windowsArtifact `
        $linuxX64Artifact `
        $linuxArm64Artifact `
        $checksumsPath `
        $supportMatrixPath `
        --title "v$Version" `
        --notes-file $releaseSummaryPath

    if ($LASTEXITCODE -ne 0) {
        throw "gh release create nije uspeo."
    }
}

Write-Host "Release automation zavrsena:" -ForegroundColor Green
Write-Host "Version: $Version"
Write-Host "Windows:      $windowsArtifact"
Write-Host "Linux x86_64: $linuxX64Artifact"
Write-Host "Linux arm64:  $linuxArm64Artifact"
Write-Host "Checksums:    $checksumsPath"
Write-Host "Support:      $supportMatrixPath"
