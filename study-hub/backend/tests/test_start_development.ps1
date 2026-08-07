$script = Get-Content (Join-Path $PSScriptRoot '..\start-development.ps1') -Raw

if ($script -notmatch 'Test-StudyHubBackendProcess') {
    throw 'development launcher must validate the existing listener'
}

if ($script -notmatch 'Port 8742 occupied by another process') {
    throw 'development launcher must explain foreign port conflicts'
}

Write-Host 'Development port ownership check passed'
