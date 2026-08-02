@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0backend\start-development.ps1"
if errorlevel 1 (
    echo.
    echo Study Hub development version did not start. Review the message above.
    pause
    exit /b 1
)
start "" "http://127.0.0.1:8742/"
exit /b 0
