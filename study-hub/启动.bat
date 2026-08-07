@echo off
chcp 65001 >nul
echo ============================================
echo   学习中枢 Study Hub 启动器
echo ============================================
echo.

REM 项目目录
set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "VENV_SITE=%PROJECT_DIR%venv\Lib\site-packages"

REM 找原始 Python（优先系统 Python312，venv 的 python.exe 可能是 GUI 子系统无控制台输出）
set "PYTHON="
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" (
    set "PYTHON=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
) else (
    REM 回退：用 venv 的 python.exe（注意：可能是 GUI 子系统，终端无报错输出）
    if exist "%PROJECT_DIR%venv\Scripts\python.exe" (
        set "PYTHON=%PROJECT_DIR%venv\Scripts\python.exe"
    ) else (
        set "PYTHON=python.exe"
    )
)

echo [1/3] Python: %PYTHON%

REM 检查 venv site-packages
if not exist "%VENV_SITE%" (
    echo [2/3] 创建虚拟环境...
    "%PYTHON%" -m venv "%PROJECT_DIR%venv"
) else (
    echo [2/3] 虚拟环境已就绪
)

REM 设置 PYTHONPATH
set "PYTHONPATH=%VENV_SITE%"
echo [3/3] 包路径: %VENV_SITE%

REM 创建数据目录
if not exist "%BACKEND_DIR%\data\inbox" mkdir "%BACKEND_DIR%\data\inbox"

echo.
echo 🚀 启动服务...
echo    Study Hub 稳定入口: http://localhost:8741
echo    管理后台:  http://localhost:8741/admin
echo    API 文档:  http://localhost:8741/docs
echo    日志文件:  %BACKEND_DIR%\data\app.log
echo --------------------------------------------
echo 按 Ctrl+C 停止服务
echo.

cd /d "%BACKEND_DIR%"
"%PYTHON%" main.py
pause
