@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0backend\stop-background.ps1"
exit /b %errorlevel%
