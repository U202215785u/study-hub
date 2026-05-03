@echo off
echo Study Hub Backend - http://localhost:8741
echo 代码修改后自动重启，关闭此窗口即停止服务
echo.
cd /d "%~dp0"
C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8741 --reload
