@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0backend\start-background.ps1"
if errorlevel 1 (
    echo.
    echo Study Hub did not start. Review the message above.
    pause
    exit /b 1
)
start "" "http://127.0.0.1:8741/"
exit /b 0
