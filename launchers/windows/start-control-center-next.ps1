$ErrorActionPreference = "Stop"

$script:Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$script:BackendDir = Join-Path $script:Root "backend"
$script:FrontendDir = Join-Path $script:Root "frontend"
$script:VenvDir = Join-Path $script:Root ".venv"
$script:StateDir = Join-Path $script:Root "state"
$script:StateFile = Join-Path $script:StateDir "runtime-state.json"

$script:LocalHost = "127.0.0.1"
$script:StartPort = if ($env:CONTROL_CENTER_NEXT_START_PORT) { [int]$env:CONTROL_CENTER_NEXT_START_PORT } else { 3210 }
$script:EndPort = if ($env:CONTROL_CENTER_NEXT_END_PORT) { [int]$env:CONTROL_CENTER_NEXT_END_PORT } else { 3299 }
$script:HealthPath = "/api/health"

function Ensure-StateDir {
    if (-not (Test-Path $script:StateDir)) {
        New-Item -ItemType Directory -Path $script:StateDir | Out-Null
    }
}

function Get-PythonExe {
    $venvPython = Join-Path $script:VenvDir "Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }
    return "python"
}

function Ensure-Venv {
    $pythonExe = Get-PythonExe
    if (Test-Path $pythonExe) {
        return
    }

    python -m venv $script:VenvDir
    & (Get-PythonExe) -m pip install -q -r (Join-Path $script:BackendDir "requirements.txt")
}

function Ensure-FrontendBuild {
    $indexPath = Join-Path $script:FrontendDir "dist\index.html"
    if (Test-Path $indexPath) {
        return
    }

    Push-Location $script:FrontendDir
    try {
        npm install
        npm run build
    }
    finally {
        Pop-Location
    }
}

function Get-HealthUrl([int]$Port) {
    return "http://$($script:LocalHost):$Port$($script:HealthPath)"
}

function Get-AppUrl([int]$Port) {
    return "http://$($script:LocalHost):$Port/"
}

function Get-SelectedPort {
    $pythonExe = Get-PythonExe
    $command = "from backend.app.port_selection import select_first_free_port; print(select_first_free_port($($script:StartPort), $($script:EndPort)))"
    $output = & $pythonExe -c $command
    return [int]($output | Select-Object -Last 1)
}

function Wait-ForHealth([string]$Url) {
    for ($i = 0; $i -lt 30; $i++) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    return $false
}

function Read-State {
    if (-not (Test-Path $script:StateFile)) {
        return $null
    }

    try {
        return Get-Content $script:StateFile -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Reuse-ExistingBackend {
    $state = Read-State
    if (-not $state -or -not $state.port) {
        return $false
    }

    $healthUrl = Get-HealthUrl -Port ([int]$state.port)
    try {
        Invoke-WebRequest -Uri $healthUrl -UseBasicParsing | Out-Null
    }
    catch {
        return $false
    }

    Open-AppUrl -Url (Get-AppUrl -Port ([int]$state.port))
    return $true
}

function Save-State([int]$Port, [int]$Pid) {
    [ordered]@{
        port = $Port
        pid = $Pid
        method = "Start-Process"
    } | ConvertTo-Json | Set-Content -Path $script:StateFile -Encoding utf8
}

function Get-BrowserPath {
    $candidates = @(
        "${env:ProgramFiles}\BraveSoftware\Brave-Browser\Application\brave.exe",
        "${env:ProgramFiles(x86)}\BraveSoftware\Brave-Browser\Application\brave.exe",
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles}\Mozilla Firefox\firefox.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    return $candidates | Select-Object -First 1
}

function Open-AppUrl([string]$Url) {
    $browserPath = Get-BrowserPath
    if ($browserPath) {
        Start-Process $browserPath $Url | Out-Null
        return
    }

    Start-Process $Url | Out-Null
}

function Start-Backend([int]$Port) {
    $pythonExe = Get-PythonExe
    $frontendDist = Join-Path $script:FrontendDir "dist"
    $uvicornCommand = "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port $Port"
    $psCommand = @"
Set-Location '$($script:Root)'
`$env:CONTROL_CENTER_NEXT_UI_PORT = '$Port'
`$env:CONTROL_CENTER_NEXT_ACCESS_MODE = 'local-only'
`$env:CONTROL_CENTER_NEXT_HOST = '127.0.0.1'
`$env:CONTROL_CENTER_NEXT_FRONTEND_DIST = '$frontendDist'
& '$pythonExe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port $Port
"@
    $process = Start-Process powershell -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-WindowStyle", "Hidden",
        "-Command", $psCommand
    ) -PassThru

    Save-State -Port $Port -Pid $process.Id
}

Set-Location $script:Root
Ensure-StateDir
Ensure-Venv
Ensure-FrontendBuild

if (Reuse-ExistingBackend) {
    exit 0
}

$selectedPort = Get-SelectedPort
$healthUrl = Get-HealthUrl -Port $selectedPort
$appUrl = Get-AppUrl -Port $selectedPort

Write-Output "Starting Local Qwen Control Center Next backend on 127.0.0.1."
Write-Output "Preferred port range: $($script:StartPort)-$($script:EndPort)"
Write-Output "Selected port: $selectedPort"
Write-Output "Health check endpoint: $healthUrl"

Start-Backend -Port $selectedPort

if (-not (Wait-ForHealth -Url $healthUrl)) {
    Write-Error "Backend nije postao healthy na vreme. Otvori rucno: $appUrl"
    exit 1
}

Open-AppUrl -Url $appUrl
Write-Output "Control Center Next je dostupan na: $appUrl"
