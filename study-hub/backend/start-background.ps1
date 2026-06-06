# Study Hub Backend Background Starter
# Fix: PowerShell Start-Process child process killed by parent session Job Object
# Use cmd /c start /min to create truly independent process
# DEC-021 / DEC-023

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = Join-Path $ProjectDir "data"
$PidFile = Join-Path $ProjectDir "data\server.pid"
$LogFile = Join-Path $ProjectDir "data\app.log"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

# Check if port already in use (only check LISTENING state, ignore TIME_WAIT)
$PortInUse = Get-NetTCPConnection -LocalPort 8741 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } | Select-Object -First 1
if ($PortInUse) {
    $ExistingPid = $PortInUse.OwningProcess
    Write-Host "[WARN] Port 8741 already used by PID=$ExistingPid" -ForegroundColor Yellow
    if (Test-Path $PidFile) {
        $FilePidStr = Get-Content $PidFile -Raw -ErrorAction SilentlyContinue
        $FilePid = 0
        if ($FilePidStr -and ($FilePidStr -match '^\s*(\d+)\s*$')) {
            $FilePid = [int]$Matches[1]
        }
        if ($FilePid -eq $ExistingPid) {
            Write-Host "[INFO] Backend already running (PID=$ExistingPid)" -ForegroundColor Green
            exit 0
        }
    }
    Write-Host "[ERROR] Port 8741 occupied by another process" -ForegroundColor Red
    exit 1
}

# Clean stale PID file
if (Test-Path $PidFile) {
    $OldPidStr = Get-Content $PidFile -Raw -ErrorAction SilentlyContinue
    $OldPid = 0
    if ($OldPidStr -and ($OldPidStr -match '^\s*(\d+)\s*$')) {
        $OldPid = [int]$Matches[1]
    }
    if ($OldPid -gt 0) {
        $OldProcess = Get-Process -Id $OldPid -ErrorAction SilentlyContinue
        if (-not $OldProcess) {
            Write-Host "[INFO] Cleaning stale PID file (PID=$OldPid dead)" -ForegroundColor Cyan
            Remove-Item $PidFile -Force
        } else {
            Write-Host "[INFO] Backend already running (PID=$OldPid)" -ForegroundColor Green
            exit 0
        }
    } else {
        Write-Host "[INFO] Cleaning invalid PID file" -ForegroundColor Cyan
        Remove-Item $PidFile -Force
    }
}

$PythonExe = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
$UvicornCmd = "-m uvicorn main:app --host 0.0.0.0 --port 8741"

Write-Host "[INFO] Starting Study Hub backend in background..." -ForegroundColor Cyan
Write-Host "[INFO] Working dir: $ProjectDir" -ForegroundColor Gray
Write-Host "[INFO] Log file: $LogFile" -ForegroundColor Gray

# Build command: cd to project, start uvicorn, write PID to file
$InnerCmd = "cd /d `"$ProjectDir`" && `"$PythonExe`" $UvicornCmd > `"$LogFile`" 2>&1 & echo %! > `"$PidFile`""

# Use cmd /c start /min to launch independent window
$proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c start /min `"StudyHub Backend`" cmd /c `"$InnerCmd`"" -PassThru

Start-Sleep -Seconds 3

# Find actual PID by port (only LISTENING state)
$NewPortInfo = Get-NetTCPConnection -LocalPort 8741 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } | Select-Object -First 1
if ($NewPortInfo) {
    $ActualPid = $NewPortInfo.OwningProcess
    Set-Content -Path $PidFile -Value $ActualPid -NoNewline
    Write-Host "[OK] Backend started (PID=$ActualPid, port=8741)" -ForegroundColor Green
} else {
    Write-Host "[WARN] Service may still be starting, check port 8741 later" -ForegroundColor Yellow
}
