$python = "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
$backendDir = Join-Path $PSScriptRoot "backend"
$mainPy = Join-Path $backendDir "main.py"
$venvSite = Join-Path $PSScriptRoot "venv\Lib\site-packages"
$douyinMcpDir = Join-Path (Split-Path $PSScriptRoot -Parent) "douyin-mcp-server"
$env:PYTHONPATH = "$douyinMcpDir;$venvSite"

Push-Location $backendDir
& $python -u $mainPy 2>&1
Pop-Location
