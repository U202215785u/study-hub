[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8741
)

$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot
$MainPy = [System.IO.Path]::GetFullPath((Join-Path $ProjectDir "main.py"))
$DataDir = Join-Path $ProjectDir "data"
$PidFile = Join-Path $DataDir "server.pid"
$AppLog = Join-Path $DataDir "app.log"

function Get-Listener {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

function Get-ProcessInfo([int]$ProcessId) {
    Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
}

function Test-StudyHubProcess([int]$ProcessId) {
    $ProcessInfo = Get-ProcessInfo $ProcessId
    if (-not $ProcessInfo -or -not $ProcessInfo.CommandLine) {
        return $false
    }
    return $ProcessInfo.CommandLine.IndexOf(
        $MainPy,
        [System.StringComparison]::OrdinalIgnoreCase
    ) -ge 0
}

function Read-PidFile {
    if (-not (Test-Path -LiteralPath $PidFile)) {
        return 0
    }
    $PidText = Get-Content -LiteralPath $PidFile -Raw -ErrorAction SilentlyContinue
    if ($PidText -and $PidText.Trim() -match '^\d+$') {
        return [int]$PidText.Trim()
    }
    return 0
}

function Resolve-SystemPython {
    $Launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
    if (-not $Launcher) {
        throw "Python launcher py.exe was not found. Install Python 3 first."
    }

    $PythonOutput = @(& $Launcher.Source -3 -c "import sys; print(sys.executable)" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $PythonOutput.Count -eq 0) {
        throw "py -3 could not resolve a working Python interpreter."
    }
    $PythonExe = $PythonOutput[-1].Trim()
    if (-not [System.IO.Path]::IsPathRooted($PythonExe) -or
        -not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
        throw "py -3 returned an invalid Python path: $PythonExe"
    }

    $ProbeOutput = @(& $PythonExe -c "print('STUDY_HUB_PYTHON_OK')" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $ProbeOutput[-1].Trim() -ne "STUDY_HUB_PYTHON_OK") {
        throw "Resolved Python interpreter failed its execution probe: $PythonExe"
    }
    return [System.IO.Path]::GetFullPath($PythonExe)
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

$Listener = Get-Listener
if ($Listener) {
    $ListenerId = [int]$Listener.OwningProcess
    if (Test-StudyHubProcess $ListenerId) {
        Write-Host "[INFO] Restarting this Study Hub process (PID=$ListenerId)." -ForegroundColor Cyan
        Stop-Process -Id $ListenerId -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $ListenerId -Timeout 10 -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
        for ($Attempt = 0; $Attempt -lt 20 -and (Get-Listener); $Attempt++) {
            Start-Sleep -Milliseconds 250
        }
        if (Get-Listener) {
            Write-Host "[ERROR] The previous Study Hub process did not release port $Port." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERROR] Port $Port is occupied by an unrelated process (PID=$ListenerId)." -ForegroundColor Red
        exit 2
    }
}

$FileProcessId = Read-PidFile
if ($FileProcessId -gt 0 -and (Test-StudyHubProcess $FileProcessId)) {
    Write-Host "[INFO] Stopping an owned process that no longer listens (PID=$FileProcessId)." -ForegroundColor Cyan
    Stop-Process -Id $FileProcessId -Force -ErrorAction SilentlyContinue
    Wait-Process -Id $FileProcessId -Timeout 5 -ErrorAction SilentlyContinue
}
if (Test-Path -LiteralPath $PidFile) {
    Remove-Item -LiteralPath $PidFile -Force
}

try {
    $PythonExe = Resolve-SystemPython
} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
    exit 3
}

Write-Host "[INFO] Starting Study Hub with $PythonExe" -ForegroundColor Cyan
Write-Host "[INFO] Working directory: $ProjectDir" -ForegroundColor Gray

$PreviousPort = $env:PORT
$PreviousUnbuffered = $env:PYTHONUNBUFFERED
try {
    $env:PORT = [string]$Port
    $env:PYTHONUNBUFFERED = "1"
    $LaunchArguments = '/d /c start "" /min "{0}" -u "{1}"' -f $PythonExe, $MainPy
    Start-Process `
        -FilePath "cmd.exe" `
        -ArgumentList $LaunchArguments `
        -WorkingDirectory $ProjectDir `
        -WindowStyle Hidden | Out-Null
} finally {
    $env:PORT = $PreviousPort
    $env:PYTHONUNBUFFERED = $PreviousUnbuffered
}

$Healthy = $false
$ActualProcessId = 0
for ($Attempt = 0; $Attempt -lt 60; $Attempt++) {
    Start-Sleep -Milliseconds 500
    $CurrentListener = Get-Listener
    if (-not $CurrentListener) {
        continue
    }
    $CurrentProcessId = [int]$CurrentListener.OwningProcess
    if (-not (Test-StudyHubProcess $CurrentProcessId)) {
        Write-Host "[ERROR] Port $Port was taken by an unrelated process during startup." -ForegroundColor Red
        break
    }
    try {
        $Health = Invoke-WebRequest `
            -Uri "http://127.0.0.1:$Port/health" `
            -UseBasicParsing `
            -TimeoutSec 1
        if ($Health.StatusCode -eq 200) {
            $Healthy = $true
            $ActualProcessId = $CurrentProcessId
            break
        }
    } catch {
        # The service can bind before the application is ready to answer.
    }
}

if ($Healthy) {
    Set-Content -LiteralPath $PidFile -Value $ActualProcessId -NoNewline -Encoding ASCII
    Write-Host "[OK] Study Hub started (PID=$ActualProcessId, port=$Port)" -ForegroundColor Green
    exit 0
}

Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { Test-StudyHubProcess ([int]$_.ProcessId) } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
if (Test-Path -LiteralPath $PidFile) {
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}
Write-Host "[ERROR] Study Hub did not become healthy on port $Port." -ForegroundColor Red
if (Test-Path -LiteralPath $AppLog) {
    Get-Content -LiteralPath $AppLog -Tail 20 -ErrorAction SilentlyContinue
}
exit 4
