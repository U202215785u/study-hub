# Study Hub development backend starter
$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = Join-Path $ProjectDir "data"
$PidFile = Join-Path $DataDir "server-dev.pid"
$LogFile = Join-Path $DataDir "app-dev.log"
$Port = 8742
$PythonExe = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

$PortInUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
if ($PortInUse) {
    $ExistingPid = $PortInUse.OwningProcess
    Write-Host "[INFO] Study Hub development backend already uses port $Port (PID=$ExistingPid)" -ForegroundColor Yellow
    Set-Content -Path $PidFile -Value $ExistingPid -NoNewline
    exit 0
}

$InnerCmd = "cd /d `"$ProjectDir`" && `"$PythonExe`" -m uvicorn main:app --host 0.0.0.0 --port $Port > `"$LogFile`" 2>&1"
Write-Host "[INFO] Starting Study Hub development backend..." -ForegroundColor Cyan
Write-Host "[INFO] Working dir: $ProjectDir" -ForegroundColor Gray
Write-Host "[INFO] Data dir: $DataDir" -ForegroundColor Gray
Write-Host "[INFO] Log file: $LogFile" -ForegroundColor Gray

Start-Process -FilePath "cmd.exe" -ArgumentList "/c start /min `"StudyHub Development Backend`" cmd /c `"$InnerCmd`"" | Out-Null
for ($attempt = 1; $attempt -le 15; $attempt++) {
    Start-Sleep -Seconds 1
    $NewPortInfo = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
    if ($NewPortInfo) { break }
}

if ($NewPortInfo) {
    Set-Content -Path $PidFile -Value $NewPortInfo.OwningProcess -NoNewline
    Write-Host "[OK] Study Hub development backend started on port $Port (PID=$($NewPortInfo.OwningProcess))" -ForegroundColor Green
} else {
    Write-Host "[WARN] Service may still be starting. Check $LogFile" -ForegroundColor Yellow
}
