# Study Hub Backend Background Stopper
# Fix: 统一停止逻辑，优先按端口查找，回退到 PID 文件 (ISS-018)

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = Join-Path $ProjectDir "data"
$PidFile = Join-Path $DataDir "server.pid"
$LockFile = Join-Path $DataDir "server.lock"

$Stopped = $false

# ── 1. 优先：按端口 8741 查找并停止 ──
$PortProc = Get-NetTCPConnection -LocalPort 8741 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } | Select-Object -First 1
if ($PortProc) {
    $ProcId = $PortProc.OwningProcess
    Write-Host "[INFO] Found process on port 8741, PID=$ProcId, stopping..." -ForegroundColor Cyan
    try {
        Stop-Process -Id $ProcId -Force -ErrorAction Stop
        Write-Host "[OK] Process stopped" -ForegroundColor Green
        $Stopped = $true
    } catch {
        Write-Host "[WARN] Failed to stop PID=$ProcId : $_" -ForegroundColor Yellow
    }
}

# ── 2. 回退：按 PID 文件停止 ──
if (-not $Stopped -and (Test-Path $PidFile)) {
    $FilePidStr = Get-Content $PidFile -Raw -ErrorAction SilentlyContinue
    $FilePid = 0
    if ($FilePidStr -and ($FilePidStr -match '^\s*(\d+)\s*$')) {
        $FilePid = [int]$Matches[1]
    }

    if ($FilePid -gt 0) {
        $Proc = Get-Process -Id $FilePid -ErrorAction SilentlyContinue
        if ($Proc) {
            Write-Host "[INFO] Stopping backend by PID file (PID=$FilePid)..." -ForegroundColor Cyan
            try {
                Stop-Process -Id $FilePid -Force -ErrorAction Stop
                Write-Host "[OK] Process stopped" -ForegroundColor Green
                $Stopped = $true
            } catch {
                Write-Host "[WARN] Failed to stop PID=$FilePid : $_" -ForegroundColor Yellow
            }
        } else {
            Write-Host "[INFO] PID=$FilePid from file does not exist" -ForegroundColor Yellow
        }
    }
}

# ── 3. 最后手段：按命令行模式查找 python main.py ──
if (-not $Stopped) {
    $PyProcs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object {
        $_.CommandLine -like "*main.py*"
    }
    if ($PyProcs) {
        foreach ($p in $PyProcs) {
            Write-Host "[INFO] Stopping python main.py (PID=$($p.ProcessId))..." -ForegroundColor Cyan
            try {
                Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
                Write-Host "[OK] Process stopped" -ForegroundColor Green
                $Stopped = $true
            } catch {
                Write-Host "[WARN] Failed to stop PID=$($p.ProcessId) : $_" -ForegroundColor Yellow
            }
        }
    }
}

# ── 4. 清理文件 ──
if (Test-Path $PidFile) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] PID file cleaned" -ForegroundColor Green
}
if (Test-Path $LockFile) {
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Lock file cleaned" -ForegroundColor Green
}

if (-not $Stopped) {
    Write-Host "[INFO] No running backend found" -ForegroundColor Green
}
