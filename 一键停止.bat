@echo off
chcp 65001 >nul
echo ==============================================================================
echo [AgenticCommerce] 正在停止开发环境基础设施...
echo ==============================================================================

docker-compose -f docker-compose.infra.yml down

echo.
echo 基础设施已停止。
pause
