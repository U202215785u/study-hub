@echo off
chcp 65001 >nul
echo Stopping Study Hub backend...
powershell -ExecutionPolicy Bypass -File "%~dp0stop-background.ps1"
echo.
pause
