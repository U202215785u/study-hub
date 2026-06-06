$python = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
$backendDir = Join-Path $PSScriptRoot "backend"
$mainPy = Join-Path $backendDir "main.py"
$env:PYTHONPATH = Join-Path $PSScriptRoot "venv\Lib\site-packages"

Push-Location $backendDir
& $python -u $mainPy 2>&1
Pop-Location
