$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot '..\start-background-helpers.ps1')

$projectDir = Split-Path -Parent $PSScriptRoot

if (-not (Test-StudyHubBackendProcess -CommandLine '"C:\Python\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8741' -ProjectDir $projectDir)) {
    throw 'Expected the Study Hub uvicorn command to be recognized as the existing backend.'
}

if (Test-StudyHubBackendProcess -CommandLine '"C:\Python\python.exe" -m uvicorn other:app --port 8741' -ProjectDir $projectDir) {
    throw 'Expected a different uvicorn application to be rejected.'
}

Write-Output 'PASS: existing backend process detection'
