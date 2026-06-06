# Study Hub Backend - Stop background service
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectDir "backend"
$pidFile    = Join-Path $backendDir "data\server.pid"

# Try PID file first
if (Test-Path $pidFile) {
    $targetPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($targetPid) {
        Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

# Fallback: kill by command-line pattern
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object {
    $_.CommandLine -like "*main.py*"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "Study Hub backend stopped"
