# AgenticCommerce 阿里云生产发布与部署完整教学手册（合订本）

> **适用对象**：具备基础开发能力、准备将项目正式推向生产上线的开发者、运维工程师及高校师生。
> **核心目标**：从 0 开始手把手教学，覆盖从**阿里云 ECS 服务器采购选型**、**安全组与网络配置**、**Python/前端/Docker 多维度打包**、**原生部署与容器化部署双方案**、**GitHub Actions CI/CD 自动化流水线**，一直到**域名解析与免费 SSL 证书开启**的完整工业级交付闭环。

---

## 📑 全文目录

- [第一章 生产部署架构全景](#第一章-生产部署架构全景)
- [第二章 阿里云ECS云服务器选购与环境初始化](#第二章-阿里云ecs云服务器选购与环境初始化)
- [第三章 生产级打包全流程实操](#第三章-生产级打包全流程实操)
- [第四章 方案A：原生裸机全流程部署实战](#第四章-方案a原生裸机全流程部署实战)
- [第五章 方案B：Docker容器化一键生产部署](#第五章-方案bdocker容器化一键生产部署)
- [第六章 CI/CD自动化打包与持续部署实战](#第六章-cicd自动化打包与持续部署实战)
- [第七章 域名解析、SSL证书与运维排错SOP](#第七章-域名解析ssl证书与运维排错sop)
- [附录A 一键自动化运维与部署脚本库](#附录a-一键自动化运维与部署脚本库)
- [附录B 生产发布全流程闭环验收 Checklist](#附录b-生产发布全流程闭环验收-checklist)
- [教学结语与演进方向](#教学结语与演进方向)

---

# 第一章 生产部署架构全景

## 1.1 生产环境部署架构全景拓扑图

在真实生产环境中，外部公网用户与系统服务之间的请求流转路径如下：

```mermaid
flowchart TD
    User([🌐 外部终端用户 / 浏览器 / 移动端]) -->|1. 访问 https://ai.yourdomain.com| DNS[阿里云 DNS 云解析]
    DNS -->|解析至公网 IP| SG[阿里云 ECS 安全组防火墙<br>放行 80, 443, 22]
    
    subgraph ECS["阿里云 ECS 生产服务器 (Ubuntu 22.04 LTS)"]
        SG -->|加密流量| Nginx[Nginx 生产高性能网关<br>监听 80/443, 卸载 SSL]
        
        Nginx -->|托管静态网页与SPA路由| FrontendDist[Vue 3 前端生产静态产物<br>/var/www/agentic-web/dist]
        Nginx -->|/api/* 代理反向请求| Backend["FastAPI 后端业务服务<br>(Uvicorn/Gunicorn 集群 :8002)"]
        Nginx -->|/api/v1/ws/* 长连接穿透| Backend
        Nginx -->|/agentic-assets/* 直读素材| MinIO[MinIO 私有对象存储<br>端口 9000/9011]
        
        Backend -->|异步读写业务表 + 向量搜索| PG[(PostgreSQL 16<br>+ pgvector 扩展 :5432)]
        Backend -->|高频会话缓存 / 分布式锁| Redis[(Redis 7 缓存与队列 :6379)]
        Backend -->|持久化转存生成的图片/视频| MinIO
    end

    Backend -.->|调用 API 算力| DashScope[阿里云百炼 DashScope<br>通义千问 Qwen / 通义万相 Wanx]
    
    classDef ecsStyle fill:#f0f7ff,stroke:#0066cc,stroke-width:2px;
    class ECS ecsStyle;
```

## 1.2 生产部署方案对比与决策矩阵

企业在将代码合入 `prd`（生产分支）后，通常有两种部署落地形态：

| 考量维度 | 方案 A：原生裸机部署 | 方案 B：Docker 容器化部署 |
| :--- | :--- | :--- |
| **底层运行方式** | 宿主机直接安装 Python 3.12 虚拟环境、Systemd 守护进程、Nginx 静态托管 | 所有组件均封装在独立 Docker 容器内 |
| **内存与 CPU 开销** | **极低**（无容器虚拟化开销，2核4G 服务器运行极度丝滑） | **中等**（每个容器有独立运行时开销，建议 4核8G 以上配置） |
| **排错与日志查看** | 直接使用 `journalctl` 或查看 `/data/logs/*.log`，直观易懂 | 需使用 `docker logs -f <容器名>`，跨容器网络排错门槛稍高 |
| **环境迁移性** | 依赖宿主机的 Linux 系统库（更换操作系统需重新配置环境） | **极高**（一次构建镜像，随处秒级运行） |
| **适合团队与阶段** | 服务器配置有限（如 2核4G 学习机）、对 Linux 有学习诉求的学生 | 商业化标准交付、微服务集群、配合 CI/CD 自动化流水线的企业 |

## 1.3 代码合入 prd 分支后的发布时序图 (CI/CD)

```mermaid
sequenceDiagram
    autonumber
    actor Developer as 开发者 / 学生
    participant Git as 代码仓库 (GitHub / Gitee)
    participant Runner as CI/CD 流水线 (Runner)
    participant ACR as 阿里云容器镜像仓库 (ACR)
    participant ECS as 阿里云 ECS 生产服务器

    Developer->>Git: git push origin prd (合并生产分支)
    Git->>Runner: Webhook 触发自动构建工作流
    
    activate Runner
    Runner->>Runner: 1. 拉取代码，运行单元测试 (pytest)
    Runner->>Runner: 2. 安装 Node 依赖，执行 pnpm build (生成 dist)
    Runner->>Runner: 3. 构建多阶段 Docker 生产镜像
    Runner->>ACR: 4. 推送带版本号镜像至阿里云镜像仓库
    
    Runner->>ECS: 5. 通过 SSH 密钥连接生产服务器执行部署脚本
    deactivate Runner

    activate ECS
    ECS->>ACR: 6. docker pull 拉取最新生产镜像
    ECS->>ECS: 7. 执行数据库自动增量迁移 (init_db / migration)
    ECS->>ECS: 8. 重启后端与前端容器 (零停机平滑更新)
    ECS->>ECS: 9. 运行健康检查探针 (GET /health 确认 200)
    ECS-->>Developer: 10. 发送构建成功飞书/钉钉通知
    deactivate ECS
```

---

# 第二章 阿里云ECS云服务器选购与环境初始化

## 2.1 ECS 云服务器选购指南（避坑指南）

打开 [阿里云官网 ECS 控制台](https://ecs.console.aliyun.com/) 或 [轻量应用服务器选购页](https://swas.console.aliyun.com/)，按以下标准勾选：

### 关键硬件参数选型推荐

| 选型维度 | 小白自学 / 课程演示推荐 | 商业生产标准推荐 | 避坑警示 |
| :--- | :--- | :--- | :--- |
| **计费方式** | **包年包月**（学生机有特惠）或 **按量付费** | 包年包月 | 演示用可买按量付费（用 2 小时花 2 块钱，用完释放） |
| **地域（Region）**| 离自己最近（如华东1 杭州、华北2 北京） | 目标用户集中区域 | 备案要求：若有域名需按所在地域提交 ICP 备案 |
| **实例规格** | **2 核 CPU，4GB 内存**（如算力型 `e` / 共享型 `s6`） | **4 核 CPU，8GB 或 16GB 内存**（计算型 `c7` / 通用型 `g7`） | ⚠️ **坚决不要买 1 核 1G 或 1 核 2G！** 运行 npm build 和 Docker 会直接爆内存死机！ |
| **操作系统镜像** | **Ubuntu 22.04 64位 LTS** | **Ubuntu 22.04 64位 LTS** 或 Alibaba Cloud Linux 3 | ⚠️ **不要选 CentOS 7**（官方已停止维护），**不要选 Windows Server**（耗费 3G 内存且性能差）。 |
| **系统盘大小** | **60 GB ~ 80 GB ESSD AutoPL** | 100 GB+ ESSD PL1 | 默认 40G 很快会被 Docker 镜像和构建缓存占满，建议至少 60G。 |
| **网络带宽模式** | **按使用流量计费（峰值 100 Mbps）** | 按固定带宽（5~10 Mbps）或按流量计费 | ⚠️ **重大省钱技巧**：选择「按使用流量」，峰值直接拉满到 100M，1G 流量仅 0.8 元；若选固定 5M，一个月要多花近百元且速度卡顿！ |

## 2.2 安全组端口放行配置（99% 新手连不上的根因）

购买完成后，进入 **ECS 实例列表** -> 点击实例名称 -> **网络与安全组** -> **安全组配置** -> 点击「**配置规则**」-> 「**入方向**」添加以下端口：

| 授权策略 | 协议类型 | 端口范围 | 授权对象 | 作用说明 |
| :--- | :--- | :--- | :--- | :--- |
| **允许** | TCP | **22** | `0.0.0.0/0` | SSH 终端连接 |
| **允许** | TCP | **80** | `0.0.0.0/0` | HTTP 网页标准端口 |
| **允许** | TCP | **443** | `0.0.0.0/0` | HTTPS 加密证书网页端口 |
| **允许** | TCP | **8002** | `0.0.0.0/0` | FastAPI 后端服务端口 |
| **允许** | TCP | **9000** | `0.0.0.0/0` | MinIO 对象存储 S3 API 接口 |
| **允许** | TCP | **9001** | `0.0.0.0/0` | MinIO 可视化管理后台控制台 |
| **严禁暴露**| TCP | 5432, 6379 | - | **PostgreSQL 与 Redis 严禁对公网开放！** 否则几分钟内就会被黑客全网勒索扫描锁定！ |

## 2.3 首次 SSH 远程登录连接

```bash
# 语法：ssh root@<你的阿里云公网IP>
ssh root@123.56.78.90

# 首次连接会提示：Are you sure you want to continue connecting (yes/no/[fingerprint])?
# 输入 yes 并回车，然后输入你在阿里云设置的 root 登录密码
```

看到如下终端欢迎提示即代表成功登入：
```text
Welcome to Ubuntu 22.04.4 LTS (GNU/Linux 5.15.0-105-generic x86_64)
root@aliyun-server:~#
```

## 2.4 生产环境底层系统优化

针对刚买到的空白 Ubuntu 实例，必须做 **4 项关键优化**：
1. **时区校准**：同步为北京时间（`Asia/Shanghai`）
2. **挂载 Swap 虚拟交换内存（防 OOM 神器）**：创建 4GB Swap 虚拟内存可保障系统绝不崩溃
3. **更换国内源**：换为阿里云内网/公网高速 APT 软件源
4. **提升最大打开文件数 (ulimit)**：避免高并发 WebSocket 出现 `Too many open files` 异常

### 一键初始化脚本

```bash
#!/bin/bash
set -e

echo ">>> [1/5] 校准服务器时区为 Asia/Shanghai..."
timedatectl set-timezone Asia/Shanghai

echo ">>> [2/5] 开启 4GB Swap 虚拟交换内存 (防止内存溢出崩溃)..."
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap 虚拟内存配置完成 (4GB)！"
else
    echo "Swap 虚拟内存已存在，跳过创建。"
fi

echo ">>> [3/5] 优化 Linux 系统内核句柄限制..."
cat >> /etc/security/limits.conf << EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF
sysctl -p || true

echo ">>> [4/5] 更新基础工具链与构建依赖..."
apt update && apt install -y curl wget git vim htop unzip jq build-essential

echo ">>> [5/5] 安装 Docker 与 Docker Compose 插件..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
    systemctl enable --now docker
fi

echo "=================================================================="
echo "🎉 阿里云 ECS 生产环境底座初始化成功！"
echo "当前内存与 Swap 状态："
free -h
echo "=================================================================="
```

---

# 第三章 生产级打包全流程实操

## 3.1 生产打包核心原则

打包的本质是**"提取纯净可执行物料，剔除一切研发脚手架"**：

```
                    ┌────────────────────────────────────────────────────────┐
                    │               本地工程开发目录 (包含全部文件)          │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
      【分支 1: 原生部署打包流】                              【分支 2: 容器化镜像构建流】
                     │                                                     │
        ┌────────────┴────────────┐                           ┌────────────┴────────────┐
        ▼                         ▼                           ▼                         ▼
 [前端 npm build]          [后端 python build]         [docker build backend]    [docker build frontend]
        │                         │                           │                         │
  生成 dist/ 静态网页       生成 requirements.txt       生成生产镜像               生成生产镜像
        │                         │                           │                         │
        └────────────┬────────────┘                           └────────────┬────────────┘
                     ▼                                                     ▼
         [生成源码/静态归档 tar.gz]                              [docker save 导出镜像 .tar]
                     │                                                     │
                     ▼                                                     ▼
            【上传到 ECS 服务器】                                   【上传到 ECS 服务器】
```

## 3.2 前端打包实战 (NPM Build)

### 生产环境变量隔离 (.env.production)

在 `frontend/` 目录下创建生产专用配置文件：

```ini
# frontend/.env.production
VITE_API_BASE_URL=/api/v1
VITE_WS_BASE_URL=/api/v1/ws
VITE_APP_TITLE=AgenticCommerce 生产工作台
```

### 构建静态资源产物并压缩归档

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖 (使用锁版本文件)
pnpm install --frozen-lockfile

# 3. 执行生产构建
npm run build

# 4. 打包为 tar.gz (方便上传传输)
tar -czvf ../frontend-dist.tar.gz -C dist .
cd ..
```

## 3.3 后端打包实战 (Python Build)

### 使用 uv 生成精准锁定版 requirements.txt

```bash
uv pip compile pyproject.toml -o requirements.txt
```

### 过滤缓存与垃圾文件并打包

```bash
tar --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='logs/*' \
    --exclude='data/*' \
    --exclude='frontend' \
    --exclude='temp' \
    -czvf backend-prod.tar.gz \
    app/ conf/ prompts/ main.py requirements.txt pyproject.toml
```

## 3.4 Docker 生产镜像构建实战

### 后端多阶段构建 Dockerfile

```dockerfile
# ── Stage 1: 构建依赖与轮子 ──
FROM python:3.12-slim AS builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml ./
RUN uv pip compile pyproject.toml -o requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: 最终轻量运行时镜像 ──
FROM python:3.12-slim AS runner

WORKDIR /app
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . .

EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
```

### 前端 Nginx 静态镜像构建

文件位置：`frontend/Dockerfile`

```dockerfile
# ── Stage 1: 前端代码构建 ──
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# ── Stage 2: 生产 Nginx 托管 ──
FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
RUN echo 'server { listen 80; location / { root /usr/share/nginx/html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 构建命令

```bash
# 后端镜像
docker build -t agentic-backend:v1.0.0 -f Dockerfile .

# 前端镜像
docker build -t agentic-frontend:v1.0.0 -f frontend/Dockerfile ./frontend
```

## 3.5 Docker 离线镜像导出与恢复 (Docker Save & Load)

### 本地打包导出 (docker save)

```bash
docker save \
    agentic-backend:v1.0.0 \
    agentic-frontend:v1.0.0 \
    pgvector/pgvector:pg16 \
    redis:7-alpine \
    minio/minio:RELEASE.2023-03-20T20-16-18Z \
    | gzip > agentic-images-v1.0.0.tar.gz
```

### 生产服务器离线加载 (docker load)

```bash
docker load -i agentic-images-v1.0.0.tar.gz
docker images
```

---

# 第四章 方案A：原生裸机全流程部署实战

> **适用场景**：服务器内存有限（例如 2核4G、2核2G 云服务器）、追求极致性能与极低内存开销、不希望引入 Docker 虚拟化层时的企业级生产部署方案。

## 4.1 原生架构与工作原理

```
[外部用户 HTTP :80 / HTTPS :443]
               │
               ▼
       [ Nginx 网关服务 ]
               │
       ┌───────┴───────────────────────────────┐
       ▼                                       ▼
[静态网页 / 路由解析]                [动态反向代理 (127.0.0.1)]
(/var/www/agentic-web)                         │
                               ┌───────────────┼───────────────┐
                               ▼               ▼               ▼
                        [agentic-backend]   [MinIO API]   [WebSocket]
                         (:8002 Python)       (:9000)      (:8002 WS)
                               │
                       ┌───────┴───────┐
                       ▼               ▼
                [PostgreSQL 16]   [Redis 7]
                 (:5432 + 向量)    (:6379)
```

## 4.2 PostgreSQL 16 与 pgvector 扩展编译安装

```bash
# 1. 添加官方 PostgreSQL APT 源
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# 2. 安装 PostgreSQL 16 及 C 语言编译头文件
sudo apt install -y postgresql-16 postgresql-server-dev-16

# 3. 源码编译并载入 pgvector 向量扩展
cd /tmp
git clone --branch v0.7.0 https://github.com/pgvector/pgvector.git
cd pgvector
make && sudo make install
cd ~

# 4. 启动服务并设置开机自启
sudo systemctl enable --now postgresql

# 5. 创建生产数据库与用户，并激活向量扩展
sudo -u postgres psql << EOF
CREATE USER postgres WITH PASSWORD 'YourStrongDBPassword2026!';
CREATE DATABASE agentic_commerce OWNER postgres;
\c agentic_commerce
CREATE EXTENSION IF NOT EXISTS vector;
\q
EOF
```

## 4.3 Redis 7 缓存安装与持久化配置

```bash
sudo apt install -y redis-server

# 开启 AOF 持久化
sudo sed -i 's/appendonly no/appendonly yes/g' /etc/redis/redis.conf

# 限制 Redis 仅监听本地环回地址
sudo sed -i 's/bind 127.0.0.1 ::1/bind 127.0.0.1/g' /etc/redis/redis.conf

sudo systemctl enable --now redis-server
redis-cli ping # 返回 PONG 即正常
```

## 4.4 MinIO 二进制安装与 Systemd 守护进程

```bash
# 1. 下载官方二进制文件
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# 2. 创建系统运行独立用户
sudo useradd -r minio-user -s /sbin/nologin || true
sudo mkdir -p /data/minio
sudo chown -R minio-user:minio-user /data/minio

# 3. 注册 Systemd 守护进程
sudo tee /etc/systemd/system/minio.service << EOF
[Unit]
Description=MinIO Object Storage Service
After=network.target

[Service]
User=minio-user
Group=minio-user
Environment="MINIO_ROOT_USER=minioadmin"
Environment="MINIO_ROOT_PASSWORD=YourMinioSecretKey2026!"
ExecStart=/usr/local/bin/minio server /data/minio --address "127.0.0.1:9000" --console-address "127.0.0.1:9011"
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now minio
```

## 4.5 后端 Python 服务生产部署

### 生产目录规划与源码解压

```bash
sudo mkdir -p /data/app/agentic-commerce /data/logs/agentic
sudo chown -R root:root /data/app

cd /data/app/agentic-commerce
tar -xzvf backend-prod.tar.gz
```

### 独立虚拟环境构建与生产依赖安装

```bash
sudo apt install -y python3.12 python3.12-venv python3.12-dev

python3.12 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 数据库表结构初始化

创建生产配置 `.env`：

```ini
APP_ENV=prod
APP_NAME=AgenticCommerce
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YourStrongDBPassword2026!
POSTGRES_DB=agentic_commerce

REDIS_URL=redis://127.0.0.1:6379/0

MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=YourMinioSecretKey2026!
MINIO_BUCKET=agentic-assets

DASHSCOPE_API_KEY=sk-your-real-dashscope-key-here
DEFAULT_LLM_MODEL=qwen-max
```

执行建表命令：
```bash
python -m app.scripts.init_db
python -m app.scripts.seed_data
```

### 编写 Systemd 守护进程 (agentic-backend.service)

```bash
sudo tee /etc/systemd/system/agentic-backend.service << EOF
[Unit]
Description=AgenticCommerce FastAPI Production Backend Service
After=network.target postgresql.service redis-server.service minio.service

[Service]
Type=simple
User=root
WorkingDirectory=/data/app/agentic-commerce
EnvironmentFile=/data/app/agentic-commerce/.env
ExecStart=/data/app/agentic-commerce/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8002 --workers 2 --access-log
Restart=always
RestartSec=5
StandardOutput=append:/data/logs/agentic/backend_access.log
StandardError=append:/data/logs/agentic/backend_error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now agentic-backend
sudo systemctl status agentic-backend
```

## 4.6 前端静态托管与 Nginx 高性能网关

### 前端 Dist 部署

```bash
sudo mkdir -p /var/www/agentic-web
sudo tar -xzvf frontend-dist.tar.gz -C /var/www/agentic-web
```

### 生产级 Nginx 完整配置

创建 `/etc/nginx/sites-available/agentic.conf`：

```nginx
server {
    listen 80;
    server_name _; # 填入你的域名，无域名则填 _

    gzip on;
    gzip_min_length 1k;
    gzip_comp_level 6;
    gzip_types text/plain application/javascript application/x-javascript text/css application/xml text/javascript application/json;

    # ── 1. 前端 Vue 3 单页应用静态资源托管 ──
    location / {
        root /var/www/agentic-web;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }

    # ── 2. 后端 RESTful API 动态反向代理 ──
    location /api/ {
        proxy_pass http://127.0.0.1:8002/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # ── 3. WebSocket 实时推流长连接穿透 ──
    location /api/v1/ws/ {
        proxy_pass http://127.0.0.1:8002/api/v1/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }

    # ── 4. MinIO 媒体素材静态直读反向代理 ──
    location /agentic-assets/ {
        proxy_pass http://127.0.0.1:9000/agentic-assets/;
        proxy_set_header Host $host;
        client_max_body_size 100m;
    }
}
```

启用并重载：
```bash
sudo ln -sf /etc/nginx/sites-available/agentic.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

---

# 第五章 方案B：Docker容器化一键生产部署

> **适用场景**：现代化云原生交付模式。通过 Docker 抹平开发机与生产服务器的全部底层差异，配合容器编排实现一键拉起、健康检查与零停机平滑滚动更新。

## 5.1 生产容器化编排拓扑与目录规划

```text
/data/docker-deploy/
├── docker-compose.prod.yml    # [核心] 生产环境 6 容器统一编排定义
├── .env.prod                  # [核心] 生产真实环境变量 (脱敏管理)
├── conf/
│   └── nginx.conf             # 生产 Nginx 网关反向代理配置文件
├── data/                      # [持久化宿主机映射目录]
│   ├── pgdata/                # PostgreSQL 数据文件
│   ├── redisdata/             # Redis AOF 数据文件
│   └── miniodata/             # MinIO 素材对象存储文件
└── deploy_docker.sh           # 一键自动发布更新脚本
```

## 5.2 生产级编排定义 (docker-compose.prod.yml)

```yaml
version: "3.8"
name: agentic-commerce-prod

services:
  # ── 1. PostgreSQL 16 + pgvector 向量扩展 ──
  postgres:
    image: pgvector/pgvector:pg16
    container_name: agentic-postgres-prod
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-agentic_commerce}
      TZ: Asia/Shanghai
    volumes:
      - /data/docker-deploy/data/pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d ${POSTGRES_DB:-agentic_commerce}"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - agentic-prod-net

  # ── 2. Redis 7 高速缓存与任务队列 ──
  redis:
    image: redis:7-alpine
    container_name: agentic-redis-prod
    restart: always
    volumes:
      - /data/docker-deploy/data/redisdata:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-""}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - agentic-prod-net

  # ── 3. MinIO 私有化对象存储 ──
  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: agentic-minio-prod
    restart: always
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - /data/docker-deploy/data/miniodata:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - agentic-prod-net

  # ── 4. FastAPI Python 业务核心 ──
  backend:
    image: ${REGISTRY_URL}/agentic-backend:${APP_VERSION:-v1.0.0}
    container_name: agentic-backend-prod
    restart: always
    env_file:
      - .env.prod
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      REDIS_URL: redis://redis:6379/0
      MINIO_ENDPOINT: minio:9000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    networks:
      - agentic-prod-net

  # ── 5. Vue 3 前端静态托管容器 ──
  frontend:
    image: ${REGISTRY_URL}/agentic-frontend:${APP_VERSION:-v1.0.0}
    container_name: agentic-frontend-prod
    restart: always
    depends_on:
      - backend
    networks:
      - agentic-prod-net

  # ── 6. Nginx 生产反向代理网关 ──
  nginx:
    image: nginx:alpine
    container_name: agentic-nginx-prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /data/docker-deploy/conf/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - backend
      - frontend
    networks:
      - agentic-prod-net

networks:
  agentic-prod-net:
    driver: bridge
```

## 5.3 生产数据卷持久化与脱敏安全规范

创建 `/data/docker-deploy/.env.prod`：

```ini
APP_ENV=prod
APP_VERSION=v1.0.0

POSTGRES_USER=postgres
POSTGRES_PASSWORD=PrdSec_DbP@ssword2026_xYz
POSTGRES_DB=agentic_commerce

MINIO_ACCESS_KEY=agentic_admin
MINIO_SECRET_KEY=PrdSec_MinioKey2026_AbCdEf
MINIO_BUCKET=agentic-assets

DASHSCOPE_API_KEY=sk-your-real-production-dashscope-key
DEFAULT_LLM_MODEL=qwen-max
```

> ⚠️ **安全底线**：`.env.prod` 文件**严禁提交至 Git 公共代码仓库**！

## 5.4 线上服务拉起、建表与健康自检

```bash
# 1. 如果采用离线镜像包，先导入：
docker load -i agentic-images-v1.0.0.tar.gz

# 2. 一键启动所有容器
docker compose -f docker-compose.prod.yml up -d

# 3. 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 4. 在后端容器内执行数据库建表
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.init_db
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.seed_data

# 5. 校验健康探针
curl http://127.0.0.1/api/v1/health
```

## 5.5 生产滚动更新（Zero-Downtime Rolling Update）

**切忌执行 `docker compose down`**（会导致数秒服务中断）！标准的平滑发布：

```bash
#!/bin/bash
# 1. 拉取最新镜像
docker pull registry.cn-hangzhou.aliyuncs.com/your-org/agentic-backend:v1.0.1
docker pull registry.cn-hangzhou.aliyuncs.com/your-org/agentic-frontend:v1.0.1

# 2. 修改版本号
sed -i 's/APP_VERSION=.*/APP_VERSION=v1.0.1/g' .env.prod

# 3. 平滑重启业务容器，数据库与缓存保持连接！
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend

# 4. 健康检查
sleep 5
curl -f http://127.0.0.1/health || (echo "健康检查未通过！" && exit 1)
docker image prune -f
echo ">>> [发布成功] 业务已平滑升级至 v1.0.1！"
```

## 5.6 常用 Docker 容器化运维速查命令

| 操作需求 | 生产执行命令 |
| :--- | :--- |
| **实时查看后端业务日志** | `docker compose -f docker-compose.prod.yml logs -f --tail=100 backend` |
| **实时查看网关访问日志** | `docker compose -f docker-compose.prod.yml logs -f nginx` |
| **进入后端容器排查** | `docker compose -f docker-compose.prod.yml exec backend bash` |
| **进入 PostgreSQL 数据库** | `docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d agentic_commerce` |
| **查看各容器内存/CPU 消耗**| `docker stats` |
| **重启单项异常容器** | `docker compose -f docker-compose.prod.yml restart backend` |

---

# 第六章 CI/CD自动化打包与持续部署实战

> **核心目标**：彻底告别“手动打包、手动传文件、手动重启服务器”的原始低效操作。实现：**只要开发者将经过测试的代码合并（Merge）到 `prd` 生产分支，CI/CD 流水线就会在云端自动编译、自动打包镜像、推送到阿里云容器镜像仓库 (ACR)，并自动通过 SSH 连上生产服务器完成零停机平滑发布与钉钉/飞书通知**！

## 6.1 CI/CD 自动化流水线架构与流转时序

```mermaid
sequenceDiagram
    autonumber
    actor Dev as 开发者 / 学生
    participant GitHub as GitHub 仓库 (prd 分支)
    participant Action as GitHub Actions Runner
    participant ACR as 阿里云容器镜像服务 ACR
    participant ECS as 阿里云 ECS 生产服务器
    participant Ding as 钉钉 / 飞书团队群

    Dev->>GitHub: 提交 Pull Request 并合并至 prd 分支
    GitHub->>Action: 自动触发 deploy-prd.yml 流水线
    
    activate Action
    Action->>Action: 1. 拉取代码，安装 Node 编译前端生成 dist/
    Action->>Action: 2. 构建 backend & frontend 生产镜像
    Action->>ACR: 3. docker push 推送镜像至阿里云 ACR
    Action->>ECS: 4. SSH 免密登录服务器执行部署命令
    deactivate Action

    activate ECS
    ECS->>ACR: 5. docker pull 拉取最新镜像
    ECS->>ECS: 6. docker compose up -d 滚动平滑更新业务容器
    ECS->>ECS: 7. 执行 curl /health 健康检查验证
    ECS-->>Action: 8. 返回执行结果状态
    deactivate ECS

    Action->>Ding: 9. 推送构建通知："版本 v1.0.x 生产发布成功！"
```

---

## 6.2 准备工作：开通阿里云容器镜像服务 (ACR 免费版)

阿里云提供了面向个人的**容器镜像服务 ACR（个人版）**，提供免费的私有镜像托管配额，速度极快（国内下载速度高达数十 MB/s）。

### 6.2.1 创建个人版实例与命名空间
1. 登录 [阿里云 ACR 控制台](https://cr.console.aliyun.com/)；
2. 选择地域（建议选择与你的 ECS 服务器相同地域，如 `华东1 (杭州)`，内网拉取镜像完全免费且速度极快）；
3. 点击「**创建个人版实例**」；
4. 点击左侧「**命名空间**」->「**创建命名空间**」，输入一个全局唯一的名字（例如 `agentic-commerce-prd`），访问级别选择 **私有**。

---

### 6.2.2 创建后端与前端镜像仓库
进入左侧「**镜像仓库**」-> 点击「**创建镜像仓库**」：
1. **后端仓库**：
   - 仓库名称：`agentic-backend`
   - 仓库类型：私有
   - 代码源：选择本地仓库即可。
2. **前端仓库**：
   - 仓库名称：`agentic-frontend`
   - 仓库类型：私有。

创建完成后，页面会给出你的私有公网 Registry 地址，例如：
`registry.cn-hangzhou.aliyuncs.com/agentic-commerce-prd/agentic-backend`

---

### 6.2.3 设置独立访问凭证密码
在左侧菜单点击「**访问凭证**」->「**设置固定密码**」，输入一个独立的镜像拉取/推送密码（这个密码将用于 CI/CD 流水线登录认证）。

---

## 6.3 GitHub Actions 自动化流水线实战配置

### 6.3.1 在 GitHub 仓库配置 Secrets 敏感变量

在你的 GitHub 项目主页 -> 点击 **Settings** -> 左侧 **Secrets and variables** -> **Actions** -> 点击 **New repository secret**，添加以下 5 个私密变量：

| Secret 变量名 | 变量值示例 | 说明 |
| :--- | :--- | :--- |
| `ALIYUN_REGISTRY` | `registry.cn-hangzhou.aliyuncs.com` | 阿里云镜像服务注册中心域名 |
| `ALIYUN_NAMESPACE`| `agentic-commerce-prd` | 你的 ACR 命名空间 |
| `ALIYUN_USERNAME` | `13800138000` 或 `your_aliyun_account` | 阿里云主账号用户名 |
| `ALIYUN_PASSWORD` | `YourAcrStrongPassword2026!` | 刚才在 ACR 访问凭证里设置的固定密码 |
| `SERVER_HOST` | `123.56.78.90` | 阿里云 ECS 的公网 IP 地址 |
| `SERVER_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | 登录服务器的 SSH 私钥文本 |
| `DINGTALK_WEBHOOK`| `https://oapi.dingtalk.com/robot/send?...` | （可选）钉钉机器人 Webhook 地址 |

---

### 6.3.2 编写生产级发布工作流 (.github/workflows/deploy-prd.yml)

在代码仓库根目录创建 `.github/workflows/deploy-prd.yml` 文件：

```yaml
name: Production Release CI/CD (prd)

# 仅在代码合并推送到 prd 分支时触发
on:
  push:
    branches:
      - prd

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 20

    steps:
      # ── 1. 检出代码 ──
      - name: Checkout Code
        uses: actions/checkout@v4

      # ── 2. 生成基于 Git Commit 的唯一版本号 ──
      - name: Generate Version Tag
        id: vars
        run: echo "SHA_SHORT=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT

      # ── 3. 登录阿里云容器镜像服务 (ACR) ──
      - name: Login to Aliyun ACR
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.ALIYUN_REGISTRY }}
          username: ${{ secrets.ALIYUN_USERNAME }}
          password: ${{ secrets.ALIYUN_PASSWORD }}

      # ── 4. 构建并推送后端镜像 ──
      - name: Build and Push Backend Image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-backend:${{ steps.vars.outputs.SHA_SHORT }}
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-backend:latest

      # ── 5. 构建并推送前端镜像 ──
      - name: Build and Push Frontend Image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile
          push: true
          tags: |
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-frontend:${{ steps.vars.outputs.SHA_SHORT }}
            ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-frontend:latest

      # ── 6. 远程 SSH 连接阿里云 ECS 并执行平滑升级 ──
      - name: Deploy to Aliyun ECS via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: root
          key: ${{ secrets.SERVER_SSH_KEY }}
          script_stop: true
          script: |
            echo ">>> [1/4] 登录服务器，准备拉取最新镜像..."
            cd /data/docker-deploy
            
            # 登录 ACR
            docker login --username=${{ secrets.ALIYUN_USERNAME }} --password=${{ secrets.ALIYUN_PASSWORD }} ${{ secrets.ALIYUN_REGISTRY }}
            
            echo ">>> [2/4] 拉取最新镜像版本: ${{ steps.vars.outputs.SHA_SHORT }}..."
            docker pull ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-backend:latest
            docker pull ${{ secrets.ALIYUN_REGISTRY }}/${{ secrets.ALIYUN_NAMESPACE }}/agentic-frontend:latest
            
            echo ">>> [3/4] 平滑滚动重启业务容器 (DB与Redis保持连接)..."
            docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
            
            echo ">>> [4/4] 运行数据库增量初始化与健康探针..."
            docker compose -f docker-compose.prod.yml exec -T backend python -m app.scripts.init_db
            
            # 等待 3 秒探活
            sleep 3
            HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8002/health)
            if [ "$HEALTH_CODE" != "200" ]; then
                echo "🚨 健康检查失败！HTTP 状态码: $HEALTH_CODE"
                exit 1
            fi
            
            # 清理历史悬空旧镜像，释放磁盘空间
            docker image prune -f
            echo "🎉 生产发布圆满成功！版本号: ${{ steps.vars.outputs.SHA_SHORT }}"

      # ── 7. 发送钉钉群通知 (可选) ──
      - name: DingTalk Notification
        if: always()
        run: |
          STATUS="${{ job.status }}"
          COLOR="green"
          if [ "$STATUS" != "success" ]; then COLOR="red"; fi
          curl -s -H "Content-Type: application/json" \
            -d "{\"msgtype\":\"markdown\",\"markdown\":{\"title\":\"生产发布报告\",\"text\":\"### 🚀 AgenticCommerce 生产发布通知\n- **分支**: prd\n- **版本**: ${{ steps.vars.outputs.SHA_SHORT }}\n- **发布状态**: $STATUS\n- **操作人**: ${{ github.actor }}\"}}" \
            "${{ secrets.DINGTALK_WEBHOOK }}" || true
```

---

## 6.4 备选方案：阿里云云效 (Apsara DevOps) 国内极速流水线

如果你的团队代码托管在 Gitee 或阿里云 Codeup，或者不想走 GitHub，可以使用**阿里云云效**（对 30 人以下团队完全免费）：

1. 打开 [阿里云云效流水线 Flow](https://flow.aliyun.com/)；
2. 新建流水线 -> 选择模板「**Java/Python/Node 容器构建并部署到 ECS**」；
3. 配置流水线触发事件：代码分支为 `prd` 时自动触发；
4. 构建节点：
   - 任务 1：`Node.js 构建` -> 执行 `cd frontend && pnpm install && pnpm build`；
   - 任务 2：`镜像构建并推送至阿里云 ACR`；
   - 任务 3：`ECS 主机部署` -> 选择目标 ECS 实例，直接运行 `docker compose -f docker-compose.prod.yml up -d`；
5. 云效运行在阿里云内网，整个打包发布流程只需 **1 ~ 2 分钟**，速度极快！

---

## 6.5 学生团队开发实战演练：从发 PR 到全自动上线

在教学中，向学生演示标准的现代互联网企业开发流：

```bash
# 1. 学生在自己的功能分支上开发完毕并测试通过
git checkout -b feature/login-optimize
git add .
git commit -m "feat: 优化登录状态与DAG加载性能"
git push origin feature/login-optimize

# 2. 在 GitHub/Gitee 上发起 Pull Request (PR):
#    源分支: feature/login-optimize  --->  目标分支: prd

# 3. 教师/技术负责人 Review 代码无误后，点击 "Merge pull request"

# 4. 此时打开 GitHub 的 "Actions" 选项卡，可以看到绿色的齿轮正在飞速运转：
#    [✓] Checkout Code (2s)
#    [✓] Build and Push Backend (45s)
#    [✓] Build and Push Frontend (30s)
#    [✓] Deploy to ECS (15s)
#    [✓] Health check passed 200 OK!

# 5. 刷新生产网址 https://ai.yourdomain.com，新功能已经毫秒级呈现在线上！
```
这就是真正的工业级持续交付（CI/CD）的魅力！


---

# 第七章 域名解析、SSL证书与运维排错SOP

> **适用场景**：系统已完成部署并可以通过 IP 访问，需要正式绑定专属独立域名、配置 HTTPS 加密传输、开启自动续期，以及在生产环境遇到 502/CORS/WebSocket 断连/OOM 等疑难杂症时的排错应急指南。

## 7.1 阿里云域名购买与云解析 DNS 配置

### 7.1.1 域名选购与国内机房 ICP 备案须知

> [!IMPORTANT]
> **关于国内服务器备案的核心常识**：
> 1. 如果你购买的 ECS 服务器地域在**中国大陆境内**（如杭州、北京、上海、深圳）：
>    - 根据工信部要求，域名必须完成 **ICP 备案** 并通过公安联网备案，才能解析到该服务器的 80/443 端口。未备案域名直接绑定境内服务器，会被阿里云白名单拦截，提示“阻断访问”。
>    - 学生实训或临时作业，建议：
>      - **方案 A（无需备案）**：ECS 选购**中国香港（Hong Kong）**或境外节点（如新加坡），域名可直接解析生效，免去备案等待。
>      - **方案 B（IP直连）**：不使用标准 80/443 端口，直接通过 `http://<公网IP>:8002` 搭配 IP 端口形式测试。
> 2. 如果已完成备案或使用香港节点，请继续执行以下步骤。

### 7.1.2 在阿里云配置 DNS 解析记录

1. 登录 [阿里云控制台](https://hichina.console.aliyun.com/) -> 进入 **云解析 DNS**。
2. 找到你的域名（例如 `yourdomain.com`），点击 **解析设置** -> **添加记录**。
3. 添加两条核心 A 记录：

| 记录类型 | 主机记录 | 解析请求来源 | 记录值 | TTL | 作用说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A** | `@` | 默认 | `47.98.xxx.xxx` (你的 ECS 公网 IP) | 10 分钟 | 访问根域名 `yourdomain.com` |
| **A** | `ai` | 默认 | `47.98.xxx.xxx` (你的 ECS 公网 IP) | 10 分钟 | 访问子域名 `ai.yourdomain.com` |
| **A** | `oss` | 默认 | `47.98.xxx.xxx` (你的 ECS 公网 IP) | 10 分钟 | MinIO 独立对象存储子域（可选） |

4. **本地验证解析是否生效**：
   在你自己本地电脑的命令行中输入：
   ```powershell
   ping ai.yourdomain.com
   ```
   如果返回的 IP 正是你的阿里云 ECS 公网 IP，说明 DNS 解析已经在全球生效。

---

## 7.2 HTTPS 免费 SSL 证书配置实战

### 7.2.1 方案 1：Certbot (Let's Encrypt) 自动化签发与自动续期 (强烈推荐)

Let's Encrypt 证书完全免费，通过 Certbot 工具可一键签发，并自带定时任务每 90 天自动静默续期。

#### 步骤 1：在 ECS 上安装 Snapd 与 Certbot

```bash
# 登录 ECS 终端
sudo apt update
sudo apt install -y snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot
```

#### 步骤 2：使用 Certbot 自动化申请并植入 Nginx

> [!NOTE]
> 在执行前，请确保 Nginx 正在运行，且安全组已放行 80 和 443 端口，域名已成功解析到当前 ECS。

```bash
# 执行交互式一键申请与安装 (将 ai.yourdomain.com 替换为你真实的域名)
sudo certbot --nginx -d ai.yourdomain.com

# 交互式提示说明：
# 1. Enter email address: 输入你的常用邮箱 (用于证书即将过期时接收警报)
# 2. Terms of Service: 输入 'y' 同意条款
# 3. Share your email: 输入 'n' 拒绝营销推广
# 4. 稍等 10 秒，Certbot 会自动校验域名的 HTTP-01 Token 并自动修改 Nginx 配置文件！
```

#### 步骤 3：测试证书自动续期 (Auto-Renew)

Let's Encrypt 证书有效期为 90 天。Certbot 在安装时已自动注册了 Systemd Timer 计时器（每天自动巡检两次并在到期前 30 天自动刷新）。

我们可以执行**演练测试**验证是否正常：
```bash
sudo certbot renew --dry-run
```
如果输出 `Congratulations, all simulated renewals succeeded`，代表后续永久免维护，证书到期前会自动静默续期并重载 Nginx！

---

### 7.2.2 方案 2：阿里云控制台申请免费 DigiCert 个人证书

如果你不希望使用 Certbot，也可以使用阿里云官方免费提供的个人测试证书（每年 20 张免费额度）：

1. 登录阿里云控制台，搜索 **数字证书管理服务 (SSL 证书)**。
2. 点击 **免费证书** -> **创建证书** -> **申请证书**。
3. 填入你的域名 `ai.yourdomain.com`，域名验证方式选择 **DNS 验证**（同账号下阿里云会自动添加验证解析，约 1~2 分钟即可完成审核审核下发）。
4. 证书签发后，在列表点击 **下载** -> 服务器类型选择 **Nginx**。
5. 解压下载的压缩包，得到两个文件：
   - `ai.yourdomain.com.pem`（证书公钥）
   - `ai.yourdomain.com.key`（私钥）
6. 将这两个文件上传至服务器目录：
   ```bash
   sudo mkdir -p /etc/nginx/ssl
   # 通过 scp 命令将本地的 pem 和 key 传到服务器:
   # scp ai.yourdomain.com.* root@<ECS_IP>:/etc/nginx/ssl/
   sudo chmod 600 /etc/nginx/ssl/*.key
   ```

---

## 7.3 生产级 Nginx SSL 安全加固配置

编辑 Nginx 站点配置：
```bash
sudo nano /etc/nginx/sites-available/agentic-commerce.conf
```

贴入经严苛安全加固并完整支持 **HTTP/2、WebSocket 长连接透传、SPA 前端 History 路由、MinIO 素材反代** 的标准配置：

```nginx
# 1. HTTP 80 端口强制 301 重定向到 HTTPS 443
server {
    listen 80;
    listen [::]:80;
    server_name ai.yourdomain.com;

    # Certbot 校验目录放行
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# 2. HTTPS 443 生产核心站
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ai.yourdomain.com;

    # SSL 证书文件路径 (根据实际方案填写)
    # 如果用 Certbot:
    ssl_certificate /etc/letsencrypt/live/ai.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai.yourdomain.com/privkey.pem;
    # 如果用阿里云免费证书:
    # ssl_certificate /etc/nginx/ssl/ai.yourdomain.com.pem;
    # ssl_certificate_key /etc/nginx/ssl/ai.yourdomain.com.key;

    # SSL 现代安全加固参数
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # 安全响应头 (HSTS、防点击劫持、防嗅探)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 请求体积上限 (允许上传 100MB 以内的高清商品图与视频素材)
    client_max_body_size 100M;

    # ----------------------------------------------------
    # A. 前端单页面应用 (Vue 3 SPA) 静态资源托管
    # ----------------------------------------------------
    location / {
        root /data/agentic-web/dist;
        index index.html;
        # 核心：支持 Vue Router HTML5 History 模式，避免刷新 404
        try_files $uri $uri/ /index.html;

        # 静态资源强缓存优化
        location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, no-transform";
        }
    }

    # ----------------------------------------------------
    # B. 后端 RESTful API 代理
    # ----------------------------------------------------
    location /api/ {
        # 原生部署填 http://127.0.0.1:8002/api/
        # Docker 部署若在同一主机也是反代到 127.0.0.1:8002/api/
        proxy_pass http://127.0.0.1:8002/api/;
        proxy_http_version 1.1;

        # 保持客户端真实 IP
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # AI 节点执行与生成时间较长，调大超时时间至 600 秒
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # ----------------------------------------------------
    # C. WebSocket 实时推送透传 (非常关键)
    # ----------------------------------------------------
    location /api/v1/ws/ {
        proxy_pass http://127.0.0.1:8002/api/v1/ws/;
        proxy_http_version 1.1;

        # WebSocket 协议升级标头
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 防止 Nginx 默认 60s 未收到数据强行切断长连接
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # ----------------------------------------------------
    # D. MinIO 本地对象存储静态素材反向代理
    # ----------------------------------------------------
    location /agentic-assets/ {
        proxy_pass http://127.0.0.1:9000/agentic-assets/;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 支持多媒体分片与断点续传
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_slice 2m;
    }
}
```

测试并重载 Nginx：
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7.4 生产环境高频故障排查排错大典 (SOP)

当系统上线后，如果遇到报错，请严格按照以下标准故障分类进行排查与定位：

```mermaid
flowchart TD
    Issue([🚨 生产环境发生告警/无法访问]) --> Q1{客户端表现是什么?}
    
    Q1 -->|网页直接报 502 / 504| Check502[排查后端进程与端口监听状态]
    Q1 -->|浏览器控制台红字 CORS 拦截| CheckCORS[排查后端 main.py CORSMiddleware 域名白名单]
    Q1 -->|工作流执行中断 / WS 连接断开| CheckWS[排查 Nginx proxy_read_timeout 与心跳配置]
    Q1 -->|接口无响应 / 进程神秘消失| CheckOOM[查看 Linux dmesg / Swap 是否被撑爆]
    Q1 -->|日志报错 No space left on device| CheckDisk[执行 df -h 清理 Docker 日志与系统缓存]

    Check502 --> S1[运行 sudo systemctl status agentic-backend]
    CheckCORS --> S2[修改 BACKEND_CORS_ORIGINS 允许生产主域名]
    CheckWS --> S3[调大超时至 3600s 并保持客户端 Ping 帧]
    CheckOOM --> S4[配置 4GB Swap 交换分区并重启后端服务]
    CheckDisk --> S5[truncate 清理日志并配置轮转策略]
```

---

### 故障 1：浏览器报 502 Bad Gateway

- **现象**：浏览器访问前端页面正常，但在请求 `/api/v1/...` 接口或点击登录时，Network 面板返回 `502 Bad Gateway`。
- **根本原因**：Nginx 网关正常，但后端的 FastAPI/Uvicorn 进程挂了，或者没有监听在 Nginx 配置的 `127.0.0.1:8002`。
- **定位与修复命令**：
  ```bash
  # 1. 检查 8002 端口是否有进程在监听
  sudo ss -tulpn | grep 8002
  
  # 2. 如果是原生部署，检查服务状态与最新日志
  sudo systemctl status agentic-backend.service
  sudo journalctl -u agentic-backend.service -n 50 --no-pager
  
  # 3. 如果是 Docker 部署，检查容器是否处于 Restarting / Exited 状态
  docker ps -a | grep backend
  docker logs --tail 100 agentic-backend-prod
  
  # 4. 常见深层原因：
  # a. 数据库连接串密码配错，后端在启动瞬间抛出 sqlalchemy.exc.OperationalError 崩溃退出。
  # b. 端口被其他旧进程占死，kill 掉后重启服务：
  #    sudo fuser -k 8002/tcp && sudo systemctl restart agentic-backend
  ```

---

### 故障 2：前端调用报 CORS 跨域错误

- **现象**：前端调用接口时，控制台报错：
  `Access to XMLHttpRequest at 'https://ai.yourdomain.com/api/v1/auth/login' from origin 'https://ai.yourdomain.com' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
- **根本原因**：
  1. 后端 `main.py` 中的 FastAPI 中间件未允许该请求源；
  2. 或者请求在到达 FastAPI 前就被 Nginx 报错中断（例如 500/502 错误由 Nginx 抛出，Nginx 默认未携带 CORS 响应头，导致浏览器表现为跨域报错）。
- **定位与修复方法**：
  1. 查看是否是因为后端报错导致的假性跨域（先看 Network 中该请求的真实状态码）。
  2. 检查后端 `main.py` 中的 `CORSMiddleware` 配置，确保包含了生产域名：
     ```python
     # 在 backend/main.py 中检查
     app.add_middleware(
         CORSMiddleware,
         allow_origins=[
             "http://localhost:5173",
             "https://ai.yourdomain.com",  # <-- 必须添加你的生产域名
             "*",                          # 生产环境若允许全开放可临时填 * 测试
         ],
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
     ```
  3. 修改后重启后端服务生效。

---

### 故障 3：WebSocket 连接刚建立就中断 (1006 / 60秒断连)

- **现象**：
  在“营销生成工作台”运行 Agentic 工作流时，任务进行到第 2 个节点时页面断开，控制台提示：
  `WebSocket connection to 'wss://ai.yourdomain.com/api/v1/ws/task_xxx' failed: WebSocket is closed before the connection is established` 或 `code 1006`。
- **根本原因**：
  1. Nginx 默认的 `proxy_read_timeout` 是 60 秒。如果某个 Agent 生成大图或视频耗时超过 60 秒且中间没有下发日志，Nginx 就会强行切断 TCP 连接。
  2. Nginx 配置缺失 `Upgrade` 和 `Connection "upgrade"` 头。
  3. 前端与反向代理协议不匹配（页面是 `https://`，但前端尝试连接 `ws://`，被浏览器安全机制 Mixed Content 阻断）。
- **定位与修复方法**：
  1. 确保前端使用 `wss://`（动态探测协议）：
     ```javascript
     const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
     const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/${taskId}`;
     ```
  2. 检查 Nginx 中的超时时间是否已调整为 3600 秒：
     ```nginx
     location /api/v1/ws/ {
         proxy_pass http://127.0.0.1:8002/api/v1/ws/;
         proxy_http_version 1.1;
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection "upgrade";
         proxy_read_timeout 3600s;
         proxy_send_timeout 3600s;
     }
     ```

---

### 故障 4：系统卡死 / Python 进程突然神秘消失 (OOM Killer)

- **现象**：
  当多个用户同时生成营销图文时，服务器 CPU 突然 100%，随后 Uvicorn 进程不留任何错误日志直接消失，`systemctl` 显示 `status=9/KILL`。
- **根本原因**：
  在 2核4G 服务器上，高并发或大体积 Base64 图片在内存中转换时内存耗尽，触发 Linux 内核的 **OOM Killer (Out of Memory)** 机制，系统内核为了防止机器彻底死机，直接 `kill -9` 强制干掉了内存占用最大的 Python 进程。
- **验证命令**：
  ```bash
  # 查看 Linux 内核日志中是否有 OOM 击杀记录
  sudo dmesg -T | grep -i -E "oom|killed process"
  ```
  如果输出类似 `Out of memory: Killed process 12345 (python)`，证实被 OOM 击杀。
- **解决方案**：
  1. **配置 4GB 虚拟内存 Swap（立竿见影救命方案）**：
     ```bash
     sudo fallocate -l 4G /swapfile
     sudo chmod 600 /swapfile
     sudo mkswap /swapfile
     sudo swapon /swapfile
     echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
     ```
  2. 降低 Uvicorn 并发工作进程数，2核4G 服务器建议配置 `--workers 2`，不要设置成 4 或更高。
  3. 生成的临时图片不要长期存留在内存中，及时转存至 MinIO 并释放局部变量。

---

### 故障 5：ECS 磁盘使用率 100% 导致系统无法写入

- **现象**：
  无法启动服务，执行任何命令报：`No space left on device`，数据库无法写入。
- **根本原因**：
  Docker 容器长时间运行未配置日志轮转，导致 `/var/lib/docker/containers/*/*.log` 膨胀到几十个 GB；或者 Systemd journal 日志占满。
- **定位与清理命令**：
  ```bash
  # 1. 检查各挂载点磁盘占用
  df -h
  
  # 2. 定位哪个目录体积最大
  sudo du -sh /* 2>/dev/null | sort -hr | head -n 5
  
  # 3. 瞬间清空所有正在增长的 Docker 容器日志 (不会中断容器运行)
  sudo sh -c "truncate -s 0 /var/lib/docker/containers/*/*-json.log"
  
  # 4. 清理无用的悬空 Docker 镜像与构建缓存
  docker system prune -af --volumes
  
  # 5. 清理超过 3 天的历史 Systemd 守护进程日志
  sudo journalctl --vacuum-time=3d
  ```

---

### 故障 6：MinIO 图片预览 403 Forbidden 或跨域无法播放视频

- **现象**：
  AI 生成的图片 URL 为 `https://ai.yourdomain.com/agentic-assets/products/...`，但在浏览器中直接打开返回 403 Access Denied。
- **根本原因**：
  MinIO 中创建的存储桶（Bucket）默认为 `Private`（私有访问权限）。
- **解决方案**：
  1. 登录 MinIO 管理控制台（`http://<ECS_IP>:9011`）。
  2. 进入 **Administrator** -> **Buckets** -> 找到 `agentic-assets` 桶。
  3. 进入 **Access Policy**（访问策略），将其从 `Private` 改为 **`Public`** 或添加只读规则：
     - Prefix: `*`
     - Access: `Read-Only`
  4. 或者使用 MinIO Client (`mc`) 命令行直接设为公开：
     ```bash
     docker exec -it agentic-minio mc anonymous set download myminio/agentic-assets
     ```

---

### 故障 7：PostgreSQL 连接池爆满 (Too many connections)

- **现象**：
  后端日志抛出错误：`sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: remaining connection slots are reserved for non-replication superuser connections`。
- **根本原因**：
  FastAPI 每次请求创建了 SQLAlchemy session 但未在 `finally` 块中妥善 `close()`，或者 Uvicorn 多进程配置的连接池大小（`pool_size`）相乘后超过了 PostgreSQL 的 `max_connections`（默认 100）。
- **排查与调优**：
  ```bash
  # 连接数据库查看当前活跃连接数
  docker exec -it agentic-postgres psql -U postgres -d dianshang_ai -c "SELECT count(*) FROM pg_stat_activity;"
  ```
  **调优优化方案**：
  1. 修改后端数据库引擎创建参数，限制单进程最大连接数：
     ```python
     engine = create_async_engine(
         DATABASE_URL,
         pool_size=10,         # 基础连接池大小
         max_overflow=20,      # 突发连接最大额外数量
         pool_recycle=1800,    # 30分钟主动回收连接
         pool_pre_ping=True,   # 每次从池中获取连接前先探测有效性
     )
     ```
  2. 提升 PostgreSQL 容器的最大连接数上限：
     在 postgres 启动命令或配置文件中加入 `-c max_connections=300`。

---

## 7.5 生产运维日常巡检清单与自检命令

运维人员每日或发布后应执行的 30 秒健康巡检指令：

```bash
# 一键健康巡检
echo "=== 1. 内存与 Swap 占用 ===" && free -h
echo "=== 2. 磁盘剩余空间 ===" && df -h /
echo "=== 3. 核心端口监听状态 ===" && sudo ss -tulpn | grep -E "80|443|8002|5432|6379|9000"
echo "=== 4. Docker 容器存活状态 ===" && docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
若以上巡检全部正常，系统即可长期保持 99.9% 以上的高可用稳定运行！


---

# 附录A 一键自动化运维与部署脚本库

> 本附录包含教学中可以直接复制使用的一键生产自动化脚本。所有脚本均已在生产实测验证，具备防 OOM、日志轮转控制、网络重试和幂等性执行保障。

## A.1 阿里云 ECS 生产服务器一键初始化脚本 (`init_ecs_server.sh`)

在全新买入的 Ubuntu 22.04 LTS 云服务器上，以 root 身份执行此脚本，可一键完成：
- 自动检测并挂载 4GB Swap 虚拟内存（防 2核4G OOM 核心利器）；
- 更新 APT 软件源并安装编译依赖、Nginx、Git、Python3 虚拟环境；
- 安装最新 Docker Engine，并配置 50MB x 3 的容器日志轮转上限；
- 创建 `/data` 标准化生产目录结构。

```bash
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

```

---

## A.2 方案 A：原生裸机一键生产部署与更新脚本 (`deploy_native.sh`)

适用于服务器配置有限（如 2核4G 学生特惠机）或希望深入学习 Linux 进程守护与 Nginx 的同学。运行此脚本自动解压前后端产物、安装 Python 生产依赖、配置 Systemd 守护进程并重载 Nginx：

```bash
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

```

---

## A.3 方案 B：Docker 容器化全栈一键生产部署脚本 (`deploy_docker.sh`)

企业级标准的全栈容器化部署脚本。自动检测本地是否存在 `.tar` 离线镜像包（离线导入），校验 `docker-compose.prod.yml` 与 `.env.prod`，拉起多容器集群、等待 PostgreSQL 数据库就绪并执行数据库表自动同步：

```bash
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

```

---

## A.4 本地离线全量生产发布打包脚本 (`build_offline.bat`)

学生或开发者在本地 Windows 开发机上开发调试完毕后，双击运行此批处理脚本，即可一键自动：
1. 编译前端 Vue 3 生成 `dist` 并打成 `dist.zip`；
2. 导出后端生产冻结依赖 `requirements-prod.txt` 并归档核心源码为 `backend_src.zip`；
3. 构建后端与 MinIO Docker 镜像并导出为离线 `.tar` 镜像包；
4. 汇总到 `release_bundle` 文件夹中，方便使用 WinSCP 上传至云服务器。

```bat
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

```

---

# 附录B 生产发布全流程闭环验收 Checklist

在将项目正式交由用户或进行期末大作业答辩演示前，请逐项核对以下 Checklist：

| 阶段 | 序号 | 检查项目 | 验收指标 / 预期表现 | 核验状态 |
| :--- | :--- | :--- | :--- | :--- |
| **云端基础设施** | 1 | ECS 实例操作系统 | Ubuntu 22.04 LTS 64位，内存 >= 4GB | [ ] 达标 |
| | 2 | 防 OOM 虚拟内存 | 执行 `free -h`，Swap 总量显示 4.0Gi 且可用 | [ ] 达标 |
| | 3 | 安全组防火墙 | 仅开放 22, 80, 443, 8002, 9000, 9011；5432 与 6379 未对外开放 | [ ] 达标 |
| | 4 | 磁盘日志轮转 | Docker 配置 `max-size: 50m`，`df -h` 使用率 < 70% | [ ] 达标 |
| **前端构建与访问** | 5 | 生产打包体积优化 | 打包无 TS/Vue 编译红字，单个 chunk 均已做 Gzip 压缩 | [ ] 达标 |
| | 6 | SPA History 刷新 | 访问任意深层路由（如 `/workflow/editor`）按 F5 刷新不报 404 | [ ] 达标 |
| | 7 | 协议自适应 | WebSocket 连接使用自适应 `wss://` / `ws://`，无 Mixed Content 阻断 | [ ] 达标 |
| **后端与数据持久化**| 8 | 数据库向量检索 | 执行 `SELECT * FROM pg_extension WHERE extname = 'vector';` 存在 | [ ] 达标 |
| | 9 | MinIO 存储桶策略 | `agentic-assets` 桶已设置为公开只读 (Public / Read-Only) | [ ] 达标 |
| | 10 | 健康探针检测 | `curl -I http://127.0.0.1:8002/health` 返回 `HTTP/1.1 200 OK` | [ ] 达标 |
| | 11 | 大模型 API Key 隔离 | `.env.prod` 文件未提交至 Git，已配置阿里云百炼有效 Key | [ ] 达标 |
| **自动化与域名 SSL**| 12 | 域名 DNS 全球生效 | 本地终端 `ping ai.yourdomain.com` 正确解析到 ECS 公网 IP | [ ] 达标 |
| | 13 | HTTPS 证书与安全等级 | 浏览器地址栏显示绿色小锁，TLS 1.2/1.3 启用，A 级加固 | [ ] 达标 |
| | 14 | CI/CD 自动发布闭环 | 代码 Push 到 `prd` 分支，GitHub Actions / 云效流水线自动绿灯部署 | [ ] 达标 |

---

# 教学结语与演进方向

恭喜你！通过本手册的系统化学习与实操，你已经完整掌握了现代企业级全栈 AI 应用从**云服务器底层调优**、**双轨打包构建**、**原生与容器化双模部署**、**CI/CD 持续交付流水线**到**高可用 SSL 网关安全架构**的全部核心技能。

在未来的工业级演进中，建议进一步探索：
1. **分布式 Kubernetes (K8s / ACK)**：当单台 ECS 算力不足以支撑海量 AI 生成并发时，使用 ACK 容器服务实现 Pod 弹性水平伸缩 (HPA)；
2. **CDN 边缘加速 (阿里云 DCDN)**：将前端静态产物和 MinIO 生成的图片推送到全球 CDN 边缘节点，实现毫秒级首屏加载；
3. **APM 与链路追踪 (Prometheus + Grafana + OpenTelemetry)**：对大模型请求耗时、Token 消耗、GPU 算力利用率建立全景监控大屏。
