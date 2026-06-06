@echo off
chcp 65001 >nul
echo ========================================
echo Study Hub 后端服务 - 后台启动
echo ========================================
powershell -ExecutionPolicy Bypass -File "%~dp0start-background.ps1"
echo.
echo 按任意键关闭此窗口（服务将继续在后台运行）
pause >nul
