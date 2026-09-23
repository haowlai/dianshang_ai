@echo off
chcp 65001 >nul
echo ==============================================================================
echo [AgenticCommerce] 正在启动开发环境...
echo ==============================================================================

echo [1/3] 检查并启动基础设施 (PostgreSQL 16 + Redis 7 + MinIO)...
docker-compose -f docker-compose.infra.yml up -d

echo [2/3] 基础设施就绪检查 (等待 3 秒)...
timeout /t 3 /nobreak >nul

echo [3/3] 启动建议:
echo   - 后端启动: uv run uvicorn main:app --reload --host 0.0.0.0 --port 8002
echo   - 前端启动: cd frontend ^&^& npm run dev
echo.
echo 访问地址:
echo   - 后端 API 文档:  http://localhost:8002/docs
echo   - 前端工作台:    http://localhost:5173
echo   - MinIO 控制台:   http://localhost:9001 (minioadmin / minioadmin)
echo.
pause
