@echo off
chcp 65001 >nul
echo Starting Study Hub backend in background...
powershell -ExecutionPolicy Bypass -File "%~dp0start-background.ps1"
echo.
pause
