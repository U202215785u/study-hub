@echo off
echo ================================
echo   学习中枢 Study Hub
echo ================================
echo.
echo 启动方式 (任选一种):
echo.
echo [1] Docker 启动 (推荐):
echo     docker compose up -d
echo     然后访问 http://localhost:8741
echo.
echo [2] 本地 Python 启动:
echo     cd backend
echo     pip install -r requirements.txt
echo     python main.py
echo.
echo API 文档: http://localhost:8741/docs
echo 健康检查: http://localhost:8741/health
echo.
echo 复制 .env.example 为 .env 并填入你的 API Key 再启动
echo.
pause
