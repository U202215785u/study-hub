$ErrorActionPreference = "Stop"

$studyHubDir = Split-Path -Parent $PSScriptRoot
$requirements = Join-Path $studyHubDir "requirements-f2.txt"
$runtimeRequirements = Join-Path $studyHubDir "requirements-f2-runtime.txt"
$vendorDir = Join-Path $studyHubDir ".vendor"
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
$python = Get-Command python -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null
if ($pyLauncher) {
    & $pyLauncher.Source -3 -m pip install --disable-pip-version-check --no-deps --target $vendorDir -r $requirements
    if ($LASTEXITCODE -eq 0) {
        & $pyLauncher.Source -3 -m pip install --disable-pip-version-check --upgrade --target $vendorDir -r $runtimeRequirements
    }
} elseif ($python) {
    & $python.Source -m pip install --disable-pip-version-check --no-deps --target $vendorDir -r $requirements
    if ($LASTEXITCODE -eq 0) {
        & $python.Source -m pip install --disable-pip-version-check --upgrade --target $vendorDir -r $runtimeRequirements
    }
} else {
    throw "Python 3 was not found"
}
if ($LASTEXITCODE -ne 0) {
    throw "F2 isolated installation failed with exit code $LASTEXITCODE"
}

Write-Host "F2 installed in $vendorDir"
