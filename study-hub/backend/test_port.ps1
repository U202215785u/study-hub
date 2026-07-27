try {
    $r = Invoke-WebRequest -Uri "http://localhost:8741/" -UseBasicParsing -TimeoutSec 5
    Write-Host "GET / -> $($r.StatusCode)"
} catch {
    Write-Host "GET / -> $($_.Exception.Response.StatusCode.value__)"
}
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8741/admin" -UseBasicParsing -TimeoutSec 5
    Write-Host "GET /admin -> $($r.StatusCode)"
} catch {
    Write-Host "GET /admin -> $($_.Exception.Response.StatusCode.value__)"
}
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8741/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "GET /health -> $($r.StatusCode) - $($r.Content)"
} catch {
    Write-Host "GET /health -> ERROR"
}
