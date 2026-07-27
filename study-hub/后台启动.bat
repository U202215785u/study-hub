@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0backend\start-background.ps1"
exit /b %errorlevel%
