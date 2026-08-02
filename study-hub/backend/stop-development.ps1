# Stop only the Study Hub development backend on port 8742.
$ErrorActionPreference = "SilentlyContinue"
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $BackendDir "data\server-dev.pid"
$Port = 8742

$PortInfo = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
if ($PortInfo) {
    Stop-Process -Id $PortInfo.OwningProcess -Force
    Write-Host "Study Hub development backend stopped (PID=$($PortInfo.OwningProcess))"
} else {
    Write-Host "Study Hub development backend is not running"
}

Remove-Item -LiteralPath $PidFile -Force
