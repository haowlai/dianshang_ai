#!/usr/bin/env bash
# ==============================================================================
# AgenticCommerce 阿里云 ECS 生产服务器一键初始化脚本 (Ubuntu 22.04 LTS)
# 作用：全新买入的阿里云 ECS，一键完成防 OOM Swap 创建、Docker环境、Nginx、系统基础库配置
# 使用方法：
#   chmod +x init_ecs_server.sh
#   sudo ./init_ecs_server.sh
# ==============================================================================

set -euo pipefail

# 必须以 root 权限运行
if [[ $EUID -ne 0 ]]; then
   echo "❌ 错误：请以 root 用户或使用 sudo ./init_ecs_server.sh 执行此脚本！" 
   exit 1
fi

echo "=========================================================="
echo "🚀 开始初始化阿里云 ECS 生产环境 (Target: Ubuntu 22.04 LTS)"
echo "=========================================================="

# ----------------------------------------------------
# 1. 配置 4GB 虚拟内存 Swap (防 2核4G 服务器 OOM 绝招)
# ----------------------------------------------------
echo "[1/6] 🧠 正在检查并配置虚拟内存 Swap (4GB)..."
if grep -q "swapfile" /proc/swaps; then
    echo "✅ Swap 已存在，跳过创建。"
else
    echo "创建 4GB /swapfile 文件..."
    fallocate -l 4G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=4096
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # 写入永久挂载
    if ! grep -q "/swapfile" /etc/fstab; then
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
    fi
    
    # 调优虚拟内存积极度 (swappiness = 20)
    sysctl vm.swappiness=20
    echo 'vm.swappiness=20' >> /etc/sysctl.conf
    echo "✅ 4GB Swap 创建并挂载成功！"
fi

# ----------------------------------------------------
# 2. 系统升级与基础工具安装
# ----------------------------------------------------
echo "[2/6] 📦 正在更新系统源并安装必要基础软件包..."
export DEBIAN_FRONTEND=noninteractive
apt update -y
apt install -y \
    curl \
    wget \
    git \
    htop \
    unzip \
    tar \
    jq \
    rsync \
    net-tools \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release \
    nginx \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev

echo "✅ 系统基础依赖安装完成！"

# ----------------------------------------------------
# 3. 安装最新 Docker Engine 与 Docker Compose
# ----------------------------------------------------
echo "[3/6] 🐳 正在安装与配置 Docker 运行环境..."
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装，版本: $(docker --version)"
else
    # 官方安装脚本
    curl -fsSL https://get.docker.com | bash -s docker
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker 安装成功！"
fi

# ----------------------------------------------------
# 4. 配置 Docker 日志轮转 (严防容器日志撑爆磁盘)
# ----------------------------------------------------
echo "[4/6] ⚙️ 配置 Docker 日志轮转与守护进程参数..."
mkdir -p /etc/docker
cat <<EOF > /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  },
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://mirror.ccs.tencentyun.com"
  ]
}
EOF
systemctl daemon-reload
systemctl restart docker
echo "✅ Docker 日志轮转上限已设为 50MB x 3，再不用担心日志占满磁盘！"

# ----------------------------------------------------
# 5. 初始化项目标准化数据与部署目录
# ----------------------------------------------------
echo "[5/6] 📁 创建标准化生产目录骨架..."
mkdir -p /data/agentic-web/dist
mkdir -p /data/agentic-backend
mkdir -p /data/docker-deploy/data/postgres
mkdir -p /data/docker-deploy/data/redis
mkdir -p /data/docker-deploy/data/minio
mkdir -p /data/docker-deploy/backups
mkdir -p /data/logs
chmod -R 755 /data
echo "✅ 生产根目录 /data 初始化完成！"

# ----------------------------------------------------
# 6. 安全防火墙状态提示
# ----------------------------------------------------
echo "[6/6] 🛡️ 检查防火墙与网络端口..."
echo "当前公网 IP: $(curl -s ifconfig.me || curl -s ip.sb || echo '请在控制台查看')"
echo ""
echo "=========================================================="
echo "🎉 阿里云 ECS 服务器基础环境初始化全部成功！"
echo "=========================================================="
echo "📊 资源状态看板："
free -h
echo "----------------------------------------------------------"
df -h /
echo "----------------------------------------------------------"
echo "👉 后续部署选项："
echo "  - 原生部署模式：运行 sudo ./deploy_native.sh"
echo "  - Docker 模式： 运行 sudo ./deploy_docker.sh"
echo "=========================================================="
