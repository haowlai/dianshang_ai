@echo off
chcp 65001 >nul
:: ==============================================================================
:: AgenticCommerce 离线全量生产发布打包脚本 (Windows 专用)
:: 适用场景：本地开发完成，一键打包前端静态包、后端纯净源码与 Docker 离线镜像
:: 输出目录：d:\code\dianshang\docs\bushu\release_bundle\
:: ==============================================================================

echo [1/5] 🚀 开始初始化发布构建目录...
set ROOT_DIR=%~dp0..\..\..
cd /d "%ROOT_DIR%"

set BUNDLE_DIR=%ROOT_DIR%\docs\bushu\release_bundle
if exist "%BUNDLE_DIR%" (
    echo 清理历史构建包...
    rmdir /s /q "%BUNDLE_DIR%"
)
mkdir "%BUNDLE_DIR%"
mkdir "%BUNDLE_DIR%\frontend"
mkdir "%BUNDLE_DIR%\backend"
mkdir "%BUNDLE_DIR%\docker_images"

echo.
echo [2/5] 📦 构建前端 Vue 3 生产静态产物 (npm run build)...
cd /d "%ROOT_DIR%"
if exist "dist" rmdir /s /q "dist"

call npm run build
if %errorlevel% neq 0 (
    echo ❌ 前端构建失败，请检查前端代码与类型报错！
    pause
    exit /b %errorlevel%
)

echo 打包前端 dist 目录...
powershell -Command "Compress-Archive -Path '%ROOT_DIR%\dist\*' -DestinationPath '%BUNDLE_DIR%\frontend\dist.zip' -Force"
echo ✅ 前端静态产物已压缩至 %BUNDLE_DIR%\frontend\dist.zip

echo.
echo [3/5] 🐍 准备后端代码与运行依赖清单...
cd /d "%ROOT_DIR%"

:: 生成生产级冻结依赖 requirements.txt
if exist ".venv\Scripts\python.exe" (
    echo 导出冻结依赖清单...
    .venv\Scripts\python.exe -m pip freeze > "%BUNDLE_DIR%\backend\requirements-prod.txt"
) else (
    copy "%ROOT_DIR%\requirements.txt" "%BUNDLE_DIR%\backend\requirements-prod.txt"
)

:: 排除缓存与虚拟环境，归档后端代码
echo 打包后端核心源码...
powershell -Command "Get-ChildItem -Path '%ROOT_DIR%' -Exclude '.venv', 'dist', 'node_modules', '.git', '__pycache__', 'docs', 'release_bundle' | Compress-Archive -DestinationPath '%BUNDLE_DIR%\backend\backend_src.zip' -Force"
echo ✅ 后端核心源码已打包至 %BUNDLE_DIR%\backend\backend_src.zip

echo.
echo [4/5] 🐳 构建并导出 Docker 生产镜像包...
where docker >nul 2>nul
if %errorlevel% equ 0 (
    echo 正在构建后端 Docker 镜像 (dianshang-backend:v1.0.0)...
    docker build -t dianshang-backend:v1.0.0 -f Dockerfile .
    if %errorlevel% equ 0 (
        echo 导出后端 Docker 镜像为 tar 包...
        docker save -o "%BUNDLE_DIR%\docker_images\dianshang-backend-v1.0.0.tar" dianshang-backend:v1.0.0
        echo ✅ 后端 Docker 镜像已导出至 %BUNDLE_DIR%\docker_images\dianshang-backend-v1.0.0.tar
    ) else (
        echo ⚠️ Docker 后端镜像构建失败，跳过镜像打包步骤。
    )

    :: 检查本地是否存在 minio 镜像
    if exist "%ROOT_DIR%\minio_image.tar" (
        echo 复制现成的 minio_image.tar 离线包...
        copy "%ROOT_DIR%\minio_image.tar" "%BUNDLE_DIR%\docker_images\minio_image.tar"
    )
) else (
    echo ⚠️ 未检测到 Docker 守护进程，跳过 Docker 镜像导出。
)

echo.
echo [5/5] 📋 生成部署部署说明与一键发布清单...
copy "%ROOT_DIR%\docs\bushu\04_方案B_Docker容器化一键生产部署.md" "%BUNDLE_DIR%\README_DEPLOY.md"
copy "%ROOT_DIR%\docker-compose.prod.yml" "%BUNDLE_DIR%\docker-compose.prod.yml" 2>nul
copy "%ROOT_DIR%\.env.prod.example" "%BUNDLE_DIR%\.env.prod.example" 2>nul

echo ==============================================================================
echo 🎉 [恭喜] 离线生产发布打包全部完成！
echo 📦 产物路径：%BUNDLE_DIR%
echo 包含内容：
echo   - frontend\dist.zip                    (前端静态页面)
echo   - backend\backend_src.zip              (后端纯净代码)
echo   - backend\requirements-prod.txt        (Python依赖清单)
echo   - docker_images\*.tar                  (Docker离线镜像)
echo.
echo 👉 下一步：使用 WinSCP / FileZilla 将整个 release_bundle 上传至阿里云 ECS 服务器即可发布！
echo ==============================================================================
pause
