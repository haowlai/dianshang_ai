#!/usr/bin/env bash
# ==============================================================================
# AgenticCommerce 方案A：原生裸机一键生产部署与更新脚本
# 适用场景：不使用 Docker，使用 Systemd 守护 Python 进程，Nginx 托管前端与反代
# 使用方法：
#   chmod +x deploy_native.sh
#   sudo ./deploy_native.sh
# ==============================================================================

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "❌ 请以 root 用户运行：sudo ./deploy_native.sh" 
   exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="/data/agentic-backend"
WEB_DIR="/data/agentic-web/dist"

echo "=========================================================="
echo "🚀 开始执行方案 A：原生裸机生产发布..."
echo "=========================================================="

# ----------------------------------------------------
# 1. 部署/更新前端静态页面
# ----------------------------------------------------
echo "[1/4] 🎨 部署前端静态产物..."
mkdir -p "$WEB_DIR"

if [[ -f "$SCRIPT_DIR/dist.zip" ]]; then
    echo "解压 $SCRIPT_DIR/dist.zip 到 $WEB_DIR..."
    unzip -o "$SCRIPT_DIR/dist.zip" -d "$WEB_DIR"
    chmod -R 755 "$WEB_DIR"
    echo "✅ 前端静态产物解压更新成功！"
elif [[ -d "$SCRIPT_DIR/dist" ]]; then
    echo "拷贝 $SCRIPT_DIR/dist 到 $WEB_DIR..."
    cp -r "$SCRIPT_DIR/dist/"* "$WEB_DIR/"
    chmod -R 755 "$WEB_DIR"
    echo "✅ 前端静态产物同步成功！"
else
    echo "⚠️ 未在当前目录找到 dist.zip 或 dist 文件夹，保留原有前端静态文件。"
fi

# ----------------------------------------------------
# 2. 部署/更新后端 Python 虚拟环境与依赖
# ----------------------------------------------------
echo "[2/4] 🐍 部署后端 Python 业务环境..."
mkdir -p "$BACKEND_DIR"

# 如果当前目录有 backend_src.zip 则解压
if [[ -f "$SCRIPT_DIR/backend_src.zip" ]]; then
    echo "解压后端核心代码至 $BACKEND_DIR..."
    unzip -o "$SCRIPT_DIR/backend_src.zip" -d "$BACKEND_DIR"
fi

cd "$BACKEND_DIR"

# 检查虚拟环境
if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
    echo "创建 Python 3 独立虚拟环境..."
    python3 -m venv "$BACKEND_DIR/.venv"
fi

echo "升级 pip 并安装生产依赖..."
"$BACKEND_DIR/.venv/bin/pip" install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

if [[ -f "$BACKEND_DIR/requirements-prod.txt" ]]; then
    "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements-prod.txt" -i https://mirrors.aliyun.com/pypi/simple/
elif [[ -f "$BACKEND_DIR/requirements.txt" ]]; then
    "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt" -i https://mirrors.aliyun.com/pypi/simple/
fi

# 确保 gunicorn 与 uvicorn 安装
"$BACKEND_DIR/.venv/bin/pip" install gunicorn uvicorn -i https://mirrors.aliyun.com/pypi/simple/

echo "✅ 后端 Python 环境与依赖配置完成！"

# ----------------------------------------------------
# 3. 注册并重启 Systemd 进程守护
# ----------------------------------------------------
echo "[3/4] ⚙️ 配置并启动 Systemd 后端守护进程..."
cat <<EOF > /etc/systemd/system/agentic-backend.service
[Unit]
Description=AgenticCommerce Backend Production Server
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/data/agentic-backend
EnvironmentFile=/data/agentic-backend/.env
ExecStart=/data/agentic-backend/.venv/bin/gunicorn main:app \\
    --workers 2 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --bind 127.0.0.1:8002 \\
    --timeout 300 \\
    --keep-alive 75 \\
    --access-logfile /data/logs/backend_access.log \\
    --error-logfile /data/logs/backend_error.log

Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable agentic-backend.service
systemctl restart agentic-backend.service
echo "✅ agentic-backend.service 已启动并在后台守护运行！"

# ----------------------------------------------------
# 4. 配置并重载 Nginx 反向代理
# ----------------------------------------------------
echo "[4/4] 🌐 校验并重载 Nginx 服务..."
# 检查 Nginx 语法
if nginx -t; then
    systemctl reload nginx
    echo "✅ Nginx 重载成功！"
else
    echo "❌ Nginx 语法测试失败，请检查 /etc/nginx/sites-available 中的配置！"
    exit 1
fi

# ----------------------------------------------------
# 5. 探针健康检查
# ----------------------------------------------------
echo "正在等待后端服务启动就绪 (5秒)..."
sleep 5

HEALTH_CHECK_URL="http://127.0.0.1:8002/api/v1/health"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" || true)

if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "404" ]]; then
    echo "=========================================================="
    echo "🎉 [发布成功] 原生裸机模式部署并启动成功！"
    echo "👉 前端静态目录：$WEB_DIR"
    echo "👉 后端运行端口：127.0.0.1:8002"
    echo "👉 运行状态检测：sudo systemctl status agentic-backend"
    echo "👉 查看实时日志：sudo journalctl -u agentic-backend -f"
    echo "=========================================================="
else
    echo "⚠️ 警告：后端服务可能未正常启动，返回 HTTP 状态码: $HTTP_STATUS"
    echo "排查日志：sudo journalctl -u agentic-backend -n 30 --no-pager"
fi
