$ErrorActionPreference = "Stop"

$script:Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$script:BackendDir = Join-Path $script:Root "backend"
$script:FrontendDir = Join-Path $script:Root "frontend"
$script:VenvDir = Join-Path $script:Root ".venv"
$script:StateDir = Join-Path $script:Root "state"
$script:StateFile = Join-Path $script:StateDir "runtime-state.json"
$script:RuntimeConfigFile = Join-Path $script:StateDir "runtime-config.json"
$script:StartupMutexName = "LocalQwenControlCenterNextStartup"

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

function Read-RuntimeConfig {
    if (-not (Test-Path $script:RuntimeConfigFile)) {
        return $null
    }

    try {
        return Get-Content $script:RuntimeConfigFile -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-RequestedAccessMode {
    if ($env:CONTROL_CENTER_NEXT_ACCESS_MODE) {
        return [string]$env:CONTROL_CENTER_NEXT_ACCESS_MODE
    }

    $config = Read-RuntimeConfig
    if ($config -and $config.accessMode) {
        return [string]$config.accessMode
    }

    return "local-only"
}

function Get-RequestedHost {
    if ($env:CONTROL_CENTER_NEXT_HOST) {
        return [string]$env:CONTROL_CENTER_NEXT_HOST
    }

    if ((Get-RequestedAccessMode) -eq "tailscale") {
        return "0.0.0.0"
    }

    return "127.0.0.1"
}

function Should-ForceRestart {
    return [string]$env:CONTROL_CENTER_NEXT_FORCE_RESTART -eq "1"
}

function Acquire-StartupMutex {
    $mutex = New-Object System.Threading.Mutex($false, $script:StartupMutexName)
    $lockTaken = $false
    try {
        $lockTaken = $mutex.WaitOne(30000)
    }
    catch [System.Threading.AbandonedMutexException] {
        $lockTaken = $true
    }

    if (-not $lockTaken) {
        throw "Nije dobijen startup lock za Control Center Next u predvidjenom roku."
    }

    return $mutex
}

function Reuse-ExistingBackend {
    if (Should-ForceRestart) {
        return $false
    }

    $state = Read-State
    if (-not $state -or -not $state.port) {
        return $false
    }

    $requestedAccessMode = Get-RequestedAccessMode
    if ($state.accessMode -and [string]$state.accessMode -ne $requestedAccessMode) {
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

function Save-State([int]$Port, [int]$ProcessId, [string]$AccessMode, [string]$BindHost) {
    [ordered]@{
        port = $Port
        pid = $ProcessId
        method = "Start-Process"
        accessMode = $AccessMode
        host = $BindHost
    } | ConvertTo-Json | Set-Content -Path $script:StateFile -Encoding utf8
}

function Stop-ExistingBackend {
    $state = Read-State
    if ($state -and $state.pid) {
        try {
            Stop-Process -Id ([int]$state.pid) -Force -ErrorAction SilentlyContinue
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
    $runnerScript = Join-Path $script:Root "run_control_center_next.py"
    $localQwenHome = if ($env:LOCAL_QWEN_HOME) { $env:LOCAL_QWEN_HOME } else { Join-Path $env:USERPROFILE "LocalAIControlCenter" }
    $frontendDist = Join-Path $script:FrontendDir "dist"
    $savedEnv = @{
        CONTROL_CENTER_NEXT_TARGET_PLATFORM = $env:CONTROL_CENTER_NEXT_TARGET_PLATFORM
        CONTROL_CENTER_NEXT_UI_PORT = $env:CONTROL_CENTER_NEXT_UI_PORT
        CONTROL_CENTER_NEXT_ACCESS_MODE = $env:CONTROL_CENTER_NEXT_ACCESS_MODE
        CONTROL_CENTER_NEXT_HOST = $env:CONTROL_CENTER_NEXT_HOST
        CONTROL_CENTER_NEXT_FRONTEND_DIST = $env:CONTROL_CENTER_NEXT_FRONTEND_DIST
        LOCAL_QWEN_HOME = $env:LOCAL_QWEN_HOME
    }
    $accessMode = Get-RequestedAccessMode
    $bindHost = Get-RequestedHost

    try {
        $env:CONTROL_CENTER_NEXT_TARGET_PLATFORM = "windows"
        $env:CONTROL_CENTER_NEXT_UI_PORT = "$Port"
        $env:CONTROL_CENTER_NEXT_ACCESS_MODE = $accessMode
        $env:CONTROL_CENTER_NEXT_HOST = $bindHost
        $env:CONTROL_CENTER_NEXT_FRONTEND_DIST = $frontendDist
        $env:LOCAL_QWEN_HOME = $localQwenHome

        $process = Start-Process -FilePath $pythonExe -ArgumentList @($runnerScript) -WorkingDirectory $script:Root -WindowStyle Hidden -PassThru
    }
    finally {
        foreach ($entry in $savedEnv.GetEnumerator()) {
            if ($null -eq $entry.Value) {
                Remove-Item "Env:$($entry.Key)" -ErrorAction SilentlyContinue
            }
            else {
                Set-Item "Env:$($entry.Key)" -Value $entry.Value
            }
        }
    }

    Save-State -Port $Port -ProcessId $process.Id -AccessMode $accessMode -Host $bindHost
}

Set-Location $script:Root
Ensure-StateDir
Ensure-Venv
Ensure-FrontendBuild

$startupMutex = Acquire-StartupMutex
try {
    if (Should-ForceRestart) {
        Stop-ExistingBackend
    }

    if (Reuse-ExistingBackend) {
        exit 0
    }

    $selectedPort = Get-SelectedPort
    $healthUrl = Get-HealthUrl -Port $selectedPort
    $appUrl = Get-AppUrl -Port $selectedPort

    Write-Output "Starting Local AI Control Center backend on 127.0.0.1."
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
}
finally {
    $startupMutex.ReleaseMutex()
    $startupMutex.Dispose()
}
