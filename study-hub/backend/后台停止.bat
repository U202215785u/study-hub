@echo off
chcp 65001 >nul
echo ========================================
echo Study Hub 后端服务 - 停止
echo ========================================
powershell -ExecutionPolicy Bypass -File "%~dp0stop-background.ps1"
echo.
pause
