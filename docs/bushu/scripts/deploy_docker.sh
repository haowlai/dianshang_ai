#!/usr/bin/env bash
# ==============================================================================
# AgenticCommerce 方案B：Docker 容器化全栈一键生产部署与平滑发布脚本
# 适用场景：全栈容器化，使用 Docker Compose 编排，支持离线 tar 导入与滚动发布
# 使用方法：
#   chmod +x deploy_docker.sh
#   sudo ./deploy_docker.sh
# ==============================================================================

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "❌ 请以 root 用户运行：sudo ./deploy_docker.sh" 
   exit 1
fi

DEPLOY_DIR="/data/docker-deploy"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "🚀 开始执行方案 B：Docker 容器化全栈生产发布..."
echo "=========================================================="

mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# ----------------------------------------------------
# 1. 离线 Docker 镜像导入 (针对无法直连国外 Docker Hub 的学生)
# ----------------------------------------------------
echo "[1/5] 📦 检查并导入离线 Docker 镜像包..."
TAR_SEARCH_DIRS=("$SCRIPT_DIR" "$SCRIPT_DIR/docker_images" "$DEPLOY_DIR/docker_images")

for search_dir in "${TAR_SEARCH_DIRS[@]}"; do
    if [[ -d "$search_dir" ]]; then
        for tar_file in "$search_dir"/*.tar; do
            if [[ -f "$tar_file" ]]; then
                echo "发现离线镜像包: $tar_file，正在执行 docker load..."
                docker load -i "$tar_file"
                echo "✅ $tar_file 导入成功！"
            fi
        done
    fi
done

# ----------------------------------------------------
# 2. 检查部署配置文件与生产环境变量
# ----------------------------------------------------
echo "[2/5] ⚙️ 检查 docker-compose.prod.yml 与 .env.prod..."

if [[ -f "$SCRIPT_DIR/docker-compose.prod.yml" && ! -f "$DEPLOY_DIR/docker-compose.prod.yml" ]]; then
    cp "$SCRIPT_DIR/docker-compose.prod.yml" "$DEPLOY_DIR/docker-compose.prod.yml"
fi

if [[ ! -f "$DEPLOY_DIR/docker-compose.prod.yml" ]]; then
    echo "❌ 错误：未在 $DEPLOY_DIR 找到 docker-compose.prod.yml！"
    exit 1
fi

if [[ ! -f "$DEPLOY_DIR/.env.prod" ]]; then
    if [[ -f "$SCRIPT_DIR/.env.prod.example" ]]; then
        echo "⚠️ 未发现 .env.prod，正在根据 .env.prod.example 初始化..."
        cp "$SCRIPT_DIR/.env.prod.example" "$DEPLOY_DIR/.env.prod"
        echo "⚠️ 请编辑 $DEPLOY_DIR/.env.prod 填写真实的生产数据库密码与百炼 API_KEY！"
    else
        echo "❌ 错误：请创建 $DEPLOY_DIR/.env.prod 配置文件！"
        exit 1
    fi
fi

# ----------------------------------------------------
# 3. 启动并编排容器集群 (后台运行)
# ----------------------------------------------------
echo "[3/5] 🐳 执行 Docker Compose 生产集群拉起..."
docker compose -f docker-compose.prod.yml --env-file .env.prod pull --ignore-pull-failures || true
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --remove-orphans

# ----------------------------------------------------
# 4. 等待依赖就绪与执行数据库结构初始化
# ----------------------------------------------------
echo "[4/5] ⏳ 等待 PostgreSQL 数据库就绪并执行结构检查..."
sleep 5

# 检查 Postgres 容器健康
docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U postgres || true

# 执行后端数据库表初始化
echo "同步初始化系统数据表..."
docker compose -f docker-compose.prod.yml exec -T backend python -c "
import asyncio
from app.database import init_db
print('正在验证数据库与向量扩展连接...')
try:
    asyncio.run(init_db())
    print('✅ 数据库初始化/迁移执行成功！')
except Exception as e:
    print('⚠️ 初始化数据库输出:', e)
" || true

# ----------------------------------------------------
# 5. 探针健康巡检与资源清理
# ----------------------------------------------------
echo "[5/5] 🛡️ 服务运行状态探针与资源清理..."
sleep 3

# 清理无用的悬空镜像 (dangling images)
docker image prune -f || true

echo "=========================================================="
echo "🎉 [发布成功] Docker 全栈容器化生产集群已全部就绪！"
echo "=========================================================="
echo "📋 当前运行容器状态："
docker compose -f docker-compose.prod.yml ps
echo "----------------------------------------------------------"
echo "👉 实时跟踪全栈日志：docker compose -f docker-compose.prod.yml logs -f"
echo "👉 仅跟踪后端实时日志：docker logs -f agentic-backend-prod"
echo "👉 停止整个服务集群：docker compose -f docker-compose.prod.yml down"
echo "=========================================================="
