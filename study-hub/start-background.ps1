# Study Hub Backend - Start in background (no console window, survives CLI timeout)
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectDir "backend"
$venvSite   = Join-Path $projectDir "venv\Lib\site-packages"
$douyinMcpDir = Join-Path (Split-Path $projectDir -Parent) "douyin-mcp-server"
$pidFile    = Join-Path $backendDir "data\server.pid"

# Find Python interpreter
$python = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $python)) {
    $python = Join-Path $projectDir "venv\Scripts\python.exe"
}

# Ensure data directory exists
$dataDir = Join-Path $backendDir "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

# Stop any existing instance first
if (Test-Path $pidFile) {
    $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($oldPid) {
        Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object {
    $_.CommandLine -like "*main.py*"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Get-NetTCPConnection -LocalPort 8741 -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

# Set PYTHONPATH and start hidden process via cmd /c start
# Using cmd /c start ensures the process truly detaches from the parent session
$env:PYTHONPATH = "$douyinMcpDir;$venvSite"
$mainPy = Join-Path $backendDir "main.py"

Push-Location $backendDir
cmd /c "start /min `"`" `"$python`" `"$mainPy`""
Pop-Location

Start-Sleep 2

# Query PID and save
$proc = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
    $_.CommandLine -like "*main.py*"
} | Select-Object -First 1

if ($proc) {
    $proc.ProcessId | Out-File $pidFile -Encoding utf8
    Write-Host "Study Hub backend started in background"
    Write-Host "PID: $($proc.ProcessId)"
    Write-Host "Main page:    http://localhost:8741"
    Write-Host "Admin panel:  http://localhost:8741/admin"
} else {
    Write-Host "Study Hub backend started"
    Write-Host "Main page:    http://localhost:8741"
}
