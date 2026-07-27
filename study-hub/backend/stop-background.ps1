[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8741
)

$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot
$MainPy = [System.IO.Path]::GetFullPath((Join-Path $ProjectDir "main.py"))
$DataDir = Join-Path $ProjectDir "data"
$PidName = if ($Port -eq 8741) { "server.pid" } else { "server.$Port.pid" }
$PidFile = Join-Path $DataDir $PidName

function Get-Listener {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

function Get-ProcessInfo([int]$ProcessId) {
    Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
}

function Get-ProcessListeners([int]$ProcessId) {
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { [int]$_.OwningProcess -eq $ProcessId }
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

$StoppedProcessIds = @()
$FileProcessId = Read-PidFile
if ($FileProcessId -gt 0) {
    if (Test-StudyHubProcess $FileProcessId) {
        $FileListeners = @(Get-ProcessListeners $FileProcessId)
        $ListensElsewhere = $FileListeners.Count -gt 0 -and -not (
            $FileListeners | Where-Object { [int]$_.LocalPort -eq $Port }
        )
        if ($ListensElsewhere) {
            Write-Host "[WARN] PID $FileProcessId belongs to another Study Hub port; leaving it running." -ForegroundColor Yellow
        } else {
            Write-Host "[INFO] Stopping this Study Hub process (PID=$FileProcessId)." -ForegroundColor Cyan
            Stop-Process -Id $FileProcessId -Force -ErrorAction SilentlyContinue
            $StoppedProcessIds += $FileProcessId
        }
    } else {
        Write-Host "[WARN] Ignoring stale or foreign PID $FileProcessId." -ForegroundColor Yellow
    }
}

$Listener = Get-Listener
if ($Listener) {
    $ListenerId = [int]$Listener.OwningProcess
    if (Test-StudyHubProcess $ListenerId) {
        if ($StoppedProcessIds -notcontains $ListenerId) {
            Write-Host "[INFO] Recovering this Study Hub process from port $Port (PID=$ListenerId)." -ForegroundColor Cyan
            Stop-Process -Id $ListenerId -Force -ErrorAction SilentlyContinue
            $StoppedProcessIds += $ListenerId
        }
    } else {
        Write-Host "[WARN] Port $Port belongs to an unrelated process (PID=$ListenerId); leaving it running." -ForegroundColor Yellow
    }
}

if (Test-Path -LiteralPath $PidFile) {
    Remove-Item -LiteralPath $PidFile -Force
}

foreach ($StoppedId in $StoppedProcessIds) {
    Wait-Process -Id $StoppedId -Timeout 10 -ErrorAction SilentlyContinue
}

for ($Attempt = 0; $Attempt -lt 20; $Attempt++) {
    $RemainingListener = Get-Listener
    if (-not $RemainingListener -or -not (Test-StudyHubProcess ([int]$RemainingListener.OwningProcess))) {
        if ($StoppedProcessIds.Count -gt 0) {
            Write-Host "[OK] Study Hub stopped and PID file cleaned." -ForegroundColor Green
        } else {
            Write-Host "[OK] No owned Study Hub process is running; PID file cleaned." -ForegroundColor Green
        }
        exit 0
    }
    Start-Sleep -Milliseconds 250
}

Write-Host "[ERROR] Study Hub is still listening on port $Port." -ForegroundColor Red
exit 1
