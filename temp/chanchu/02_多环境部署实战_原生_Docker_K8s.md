# AgenticCommerce 多环境部署实战：从裸机、Docker 到 Kubernetes

> **适用场景**：指导开发者从本地研发环境、团队测试机、生产单机服务器，一直平滑演进到企业级云原生高可用 K8s 集群。  
> **涵盖方案**：  
> 1. **方案一：原生裸机部署（Bare Metal）** —— 深度理解各组件底层依赖与服务进程守护  
> 2. **方案二：Docker & Docker Compose 容器编排** —— 团队标准化快速拉起与生产标准容器交付  
> 3. **方案三：Kubernetes (K8s) 高可用云原生集群部署** —— 包含企业级清单、弹性伸缩（HPA）、持久化存储（PVC）与 Ingress 网关路由

---

## 目录
- [一、环境依赖与端口矩阵规划](#一环境依赖与端口矩阵规划)
- [二、方案一：原生裸机部署（Linux / Windows）](#二方案一原生裸机部署linux--windows)
  - [2.1 基础运行环境准备 (Python 3.12 + Node.js 20)](#21-基础运行环境准备-python-312--nodejs-20)
  - [2.2 PostgreSQL 16 与 pgvector 扩展安装](#22-postgresql-16-与-pgvector-扩展安装)
  - [2.3 Redis 7 缓存安装与配置](#23-redis-7-缓存安装与配置)
  - [2.4 MinIO 对象存储单机安装](#24-minio-对象存储单机安装)
  - [2.5 后端服务初始化与 Systemd 守护进程](#25-后端服务初始化与-systemd-守护进程)
  - [2.6 前端打包编译与 Nginx 静态托管](#26-前端打包编译与-nginx-静态托管)
- [三、方案二：Docker & Docker Compose 容器化编排](#三方案二docker--docker-compose-容器化编排)
  - [3.1 容器编排架构全景](#31-容器编排架构全景)
  - [3.2 后端多阶段 Dockerfile 解析](#32-后端多阶段-dockerfile-解析)
  - [3.3 前端 Nginx Dockerfile 解析](#33-前端-nginx-dockerfile-解析)
  - [3.4 docker-compose.yml 生产全量编排文件](#34-docker-composeyml-生产全量编排文件)
  - [3.5 一键启动、健康检查与常用运维命令](#35-一键启动健康检查与常用运维命令)
- [四、方案三：Kubernetes (K8s) 企业级云原生部署](#四方案三kubernetes-k8s-企业级云原生部署)
  - [4.1 K8s 部署架构拓扑](#41-k8s-部署架构拓扑)
  - [4.2 命名空间与敏感凭据 (Namespace, Secret, ConfigMap)](#42-命名空间与敏感凭据-namespace-secret-configmap)
  - [4.3 持久化存储定义 (PVC & StorageClass)](#43-持久化存储定义-pvc--storageclass)
  - [4.4 数据库有状态集 (PostgreSQL StatefulSet)](#44-数据库有状态集-postgresql-statefulset)
  - [4.5 后端无状态应用 (Deployment + Service + HPA)](#45-后端无状态应用-deployment--service--hpa)
  - [4.6 前端应用与统一 Ingress 网关配置](#46-前端应用与统一-ingress-网关配置)
  - [4.7 集群部署流水线与故障排查速查](#47-集群部署流水线与故障排查速查)

---

## 一、环境依赖与端口矩阵规划

在开始部署前，必须规划好服务器网络端口，避免端口冲突：

| 服务名称 | 进程名/镜像 | 默认端口 | 协议 | 是否暴露公网 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nginx 网关** | nginx:alpine | 80, 443 | HTTP/HTTPS | **必须暴露** | 统一入口、SSL 终止与前端静态资源托管 |
| **Vue 3 前端** | Vite / Nginx | 5173 / 80 | HTTP | 内部访问 | 前端工作台 |
| **FastAPI 后端** | uvicorn main:app | 8002 | HTTP/WS | 可选暴露 | RESTful API 与实时 WebSocket 广播 |
| **PostgreSQL 16**| pgvector:pg16 | 5432 | TCP | **严禁暴露** | 关系型主库 + 向量索引检索 |
| **Redis 7** | redis:7-alpine | 6379 | TCP | **严禁暴露** | 会话缓存与生成状态队列 |
| **MinIO API** | minio server | 9000 | S3/HTTP | **必须暴露** | 图片/视频等素材二进制上传与拉取 |
| **MinIO Console**| minio console | 9001 | Web | 可选暴露 | MinIO 可视化管理控制台后台 |

---

## 二、方案一：原生裸机部署（Linux / Windows）

原生部署适合个人开发者本地深度调试、没有 Docker 权限的传统服务器环境。以 **Ubuntu 22.04 LTS** 为例。

### 2.1 基础运行环境准备 (Python 3.12 + Node.js 20)

```bash
# 1. 更新 apt 软件源并安装基础构建依赖
sudo apt update && sudo apt install -y curl wget git build-essential software-properties-common

# 2. 安装 Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 3. 安装 Rust 编写的高性能 Python 包管理器 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
uv --version

# 4. 安装 Node.js 20 (通过 NodeSource 官方脚本)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v # 应输出 v20.x.x
npm -v
```

---

### 2.2 PostgreSQL 16 与 pgvector 扩展安装

`pgvector` 是本项目做 RAG 向量检索的核心扩展。原生环境必须将其安装并加载。

```bash
# 1. 添加 PostgreSQL 官方 APT 源
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# 2. 安装 PostgreSQL 16 服务端及开发库
sudo apt install -y postgresql-16 postgresql-server-dev-16

# 3. 安装 pgvector (推荐通过源码一键编译安装)
git clone --branch v0.7.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
cd ..

# 4. 启动 PostgreSQL 并设置开机自启
sudo systemctl enable --now postgresql

# 5. 创建数据库用户与数据库
sudo -u postgres psql << EOF
CREATE USER postgres WITH PASSWORD 'postgres';
CREATE DATABASE agentic_commerce OWNER postgres;
\c agentic_commerce
CREATE EXTENSION IF NOT EXISTS vector;
\q
EOF
```

---

### 2.3 Redis 7 缓存安装与配置

```bash
# 安装 Redis
sudo apt install -y redis-server

# 开启 AOF 持久化保证任务状态不丢失
sudo sed -i 's/appendonly no/appendonly yes/g' /etc/redis/redis.conf

# 启动并设置开机自启
sudo systemctl enable --now redis-server
redis-cli ping # 正常应返回 PONG
```

---

### 2.4 MinIO 对象存储单机安装

```bash
# 1. 下载 MinIO 二进制执行文件
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# 2. 创建数据目录与运行用户
sudo useradd -r minio-user -s /sbin/nologin
sudo mkdir -p /data/minio
sudo chown -R minio-user:minio-user /data/minio

# 3. 编写 Systemd 配置文件
sudo tee /etc/systemd/system/minio.service << EOF
[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
User=minio-user
Group=minio-user
Environment="MINIO_ROOT_USER=minioadmin"
Environment="MINIO_ROOT_PASSWORD=minioadmin"
ExecStart=/usr/local/bin/minio server /data/minio --address ":9000" --console-address ":9001"
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# 4. 启动 MinIO
sudo systemctl daemon-reload
sudo systemctl enable --now minio
```

---

### 2.5 后端服务初始化与 Systemd 守护进程

```bash
# 1. 切换至代码目录
cd /data/code/dianshang

# 2. 使用 uv 创建独立虚拟环境并安装依赖
uv venv .venv --python 3.12
source .venv/bin/activate
uv pip install -r <(uv pip compile pyproject.toml)

# 3. 执行数据库结构初始化与种子数据注入
python -m app.scripts.init_db
python -m app.scripts.seed_data

# 4. 编写后端服务的 systemd 守护进程 (避免关闭终端后服务中断)
sudo tee /etc/systemd/system/agentic-backend.service << EOF
[Unit]
Description=AgenticCommerce FastAPI Backend Service
After=network.target postgresql.service redis-server.service minio.service

[Service]
Type=simple
User=root
WorkingDirectory=/data/code/dianshang
ExecStart=/data/code/dianshang/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4
Restart=always
RestartSec=5
EnvironmentFile=/data/code/dianshang/.env

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now agentic-backend
sudo systemctl status agentic-backend
```

---

### 2.6 前端打包编译与 Nginx 静态托管

```bash
# 1. 进入前端工程并编译生产包
cd /data/code/dianshang/frontend
npm install -g pnpm
pnpm install
pnpm build
# 产物生成在 /data/code/dianshang/frontend/dist

# 2. 配置 Nginx 反向代理与静态托管
sudo tee /etc/nginx/sites-available/agentic.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # 前端页面单页应用托管
    location / {
        root /data/code/dianshang/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html; # 支持 Vue Router History 模式
    }

    # 后端 RESTful API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8002/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s; # Agent 生成耗时较长，增加超时阈值
    }

    # WebSocket 长连接反向代理 (推送 DAG 状态)
    location /api/v1/ws/ {
        proxy_pass http://127.0.0.1:8002/api/v1/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }

    # MinIO 对象存储反向代理 (图片/视频外链)
    location /agentic-assets/ {
        proxy_pass http://127.0.0.1:9000/agentic-assets/;
        proxy_set_header Host $host;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/agentic.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

---

## 三、方案二：Docker & Docker Compose 容器化编排

容器化是现代企业级交付的标准方式。它抹平了开发机（Windows/Mac）与线上服务器（Linux）的环境差异。

### 3.1 容器编排架构全景

```
                     [ 外部访问 HTTP :80 / HTTPS :443 ]
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │    agentic-nginx (网关代理)    │
                     └───────┬───────────────┬───────┘
                             │               │
            ┌────────────────▼┐             ┌▼────────────────────────┐
            │ agentic-frontend│             │     agentic-backend     │
            │  (Vue3 Dist)    │             │   (FastAPI Python 3.12) │
            └─────────────────┘             └───────┬─────┬─────┬─────┘
                                                    │     │     │
                      ┌─────────────────────────────┼─────┼─────┘
                      │                             │     │
                      ▼                             ▼     ▼
             ┌─────────────────┐           ┌──────────┐ ┌──────────────┐
             │ agentic-postgres│           │agentic-  │ │agentic-minio │
             │  (+ pgvector)   │           │  redis   │ │ (对象存储)    │
             └─────────────────┘           └──────────┘ └──────────────┘
```

### 3.2 后端多阶段 Dockerfile 解析
代码路径：[Dockerfile](file:///d:/code/dianshang/Dockerfile)

```dockerfile
# ==============================================================================
# 后端 Dockerfile：采用精简的 Python 3.12-slim 镜像
# ==============================================================================
FROM python:3.12-slim AS runner

# 设置时区与防 Python 输出缓冲
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 安装必要的系统底层运行库 (libpq 用于 postgres, curl 用于健康检查)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从官方复制 uv 工具链
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 先复制依赖描述文件，充分利用 Docker 层缓存
COPY pyproject.toml ./
RUN uv pip install --system -r <(uv pip compile pyproject.toml)

# 复制整个项目源码
COPY . .

# 暴露 FastAPI 服务端口
EXPOSE 8002

# 容器启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "2"]
```

### 3.3 前端 Nginx Dockerfile 解析
代码路径：`frontend/Dockerfile`

```dockerfile
# ── Stage 1: 前端静态资源构建 ──
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# ── Stage 2: 生产 Nginx 镜像托管 ──
FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
# 替换默认 Nginx 配置，添加 try_files 支持路由
RUN echo 'server { listen 80; location / { root /usr/share/nginx/html; try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3.4 docker-compose.yml 生产全量编排文件
已在根目录准备完成：[docker-compose.yml](file:///d:/code/dianshang/docker-compose.yml)

核心亮点：
1. **自带初始化 SQL**：挂载 `./docker/postgres/init.sql` 到 `/docker-entrypoint-initdb.d/init.sql`，容器启动时自动激活 `CREATE EXTENSION IF NOT EXISTS vector;`！
2. **严格的健康检查依赖链**：
   - 后端 `backend` 依赖 `postgres`, `redis`, `minio`，且状态必须是 `service_healthy`，保证不会出现数据库还未初始化完毕后端就报错崩溃的情况！

### 3.5 一键启动、健康检查与常用运维命令

```bash
# 1. 复制环境变量模板
cp conf/.env.example .env
# 编辑 .env 文件填入 DASHSCOPE_API_KEY

# 2. 一键构建并启动所有 6 个容器
docker compose up -d --build

# 3. 检查所有容器健康状态 (STATUS 必须显示 healthy 或 running)
docker compose ps

# 输出示例：
# NAME               IMAGE                     STATUS                    PORTS
# agentic-postgres   pgvector/pgvector:pg16    Up 2 minutes (healthy)    5432/tcp
# agentic-redis      redis:7-alpine            Up 2 minutes (healthy)    6379/tcp
# agentic-minio      minio/minio:latest        Up 2 minutes (healthy)    9000/tcp, 9001/tcp
# agentic-backend    dianshang-backend         Up 1 minute               0.0.0.0:8002->8002/tcp
# agentic-frontend   dianshang-frontend        Up 1 minute               0.0.0.0:5173->80/tcp
# agentic-nginx      nginx:alpine              Up 1 minute               0.0.0.0:80->80/tcp

# 4. 执行一次数据库初始化脚本（在后端容器内执行）
docker compose exec backend python -m app.scripts.init_db
docker compose exec backend python -m app.scripts.seed_data

# 5. 查看实时滚动日志
docker compose logs -f backend

# 6. 停止与销毁容器
docker compose down
```

---

## 四、方案三：Kubernetes (K8s) 企业级云原生部署

针对企业生产环境的高并发、高可用诉求，我们提供整套经过生产检验的 K8s 清单（Manifests）。

### 4.1 K8s 部署架构拓扑

```
               [ 外部用户 / 浏览器 ]
                         │
                         ▼
             [ Ingress Controller (Nginx) ]
             (SSL 卸载 / /api 路由分流 / WS 支持)
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
  [ Service: frontend ]           [ Service: backend ]
         │                               │
  [ Pods: Vue 3 x2 ]              [ Pods: FastAPI x3 (HPA 自动伸缩) ]
                                         │
                   ┌─────────────────────┼─────────────────────┐
                   ▼                     ▼                     ▼
            [ Service: pg ]       [ Service: redis ]    [ Service: minio ]
                   │                     │                     │
           [ Pod: Postgres ]      [ Pod: Redis ]        [ Pod: MinIO ]
           [ PVC: 50Gi NVMe]      [ PVC: 20Gi ]         [ PVC: 200Gi SSD ]
```

---

### 4.2 命名空间与敏感凭据 (Namespace, Secret, ConfigMap)

创建文件 `k8s/01-namespace-config.yaml`：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agentic-commerce
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: agentic-config
  namespace: agentic-commerce
data:
  APP_ENV: "production"
  POSTGRES_HOST: "postgres-service"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "agentic_commerce"
  REDIS_URL: "redis://redis-service:6379/0"
  MINIO_ENDPOINT: "minio-service:9000"
  MINIO_BUCKET: "agentic-assets"
  DEFAULT_LLM_MODEL: "qwen-max"
---
apiVersion: v1
kind: Secret
metadata:
  name: agentic-secret
  namespace: agentic-commerce
type: Opaque
stringData:
  POSTGRES_USER: "postgres"
  POSTGRES_PASSWORD: "SuperSecurePassword123!"
  MINIO_ACCESS_KEY: "minioadmin"
  MINIO_SECRET_KEY: "minioadmin123!"
  DASHSCOPE_API_KEY: "sk-your-dashscope-key-here"
```

---

### 4.3 持久化存储定义 (PVC & StorageClass)

创建文件 `k8s/02-pvc.yaml`：

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pgdata-pvc
  namespace: agentic-commerce
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: miniodata-pvc
  namespace: agentic-commerce
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 200Gi
```

---

### 4.4 数据库有状态集 (PostgreSQL StatefulSet)

创建文件 `k8s/03-postgres.yaml`：

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: agentic-commerce
spec:
  serviceName: "postgres-service"
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: pgvector/pgvector:pg16
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: agentic-secret
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: agentic-secret
                  key: POSTGRES_PASSWORD
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: agentic-config
                  key: POSTGRES_DB
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: pgdata
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
      volumes:
        - name: pgdata
          persistentVolumeClaim:
            claimName: pgdata-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: agentic-commerce
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

---

### 4.5 后端无状态应用 (Deployment + Service + HPA)

创建文件 `k8s/04-backend.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: agentic-commerce
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: registry.cn-hangzhou.aliyuncs.com/your-org/agentic-backend:v1.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8002
          envFrom:
            - configMapRef:
                name: agentic-config
            - secretRef:
                name: agentic-secret
          resources:
            requests:
              cpu: "1000m"
              memory: "2Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
          # 存活探针：异常自动重启 Pod
          livenessProbe:
            httpGet:
              path: /health
              port: 8002
            initialDelaySeconds: 15
            periodSeconds: 10
          # 就绪探针：就绪后才接入流量
          readinessProbe:
            httpGet:
              path: /health
              port: 8002
            initialDelaySeconds: 10
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: agentic-commerce
spec:
  selector:
    app: backend
  ports:
    - port: 8002
      targetPort: 8002
---
# 自动弹性伸缩 HPA：CPU 占用超过 70% 时自动扩容至最多 10 个 Pod
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: agentic-commerce
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

### 4.6 前端应用与统一 Ingress 网关配置

创建文件 `k8s/05-ingress.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: agentic-commerce
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: registry.cn-hangzhou.aliyuncs.com/your-org/agentic-frontend:v1.0.0
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: agentic-commerce
spec:
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
---
# Ingress 统一路由分发规则
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: agentic-ingress
  namespace: agentic-commerce
  annotations:
    kubernetes.io/ingress.class: "nginx"
    # 增加超时以容纳 AI Agent 长时间流式生成
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    # 开启 WebSocket 支持
    nginx.ingress.kubernetes.io/websocket-services: "backend-service"
spec:
  rules:
    - host: ai.yourdomain.com
      http:
        paths:
          # 1. 静态前端页面
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
          # 2. 后端 RESTful API 与 WebSocket
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend-service
                port:
                  number: 8002
```

---

### 4.7 集群部署流水线与故障排查速查

```bash
# 1. 顺序应用所有清单
kubectl apply -f k8s/01-namespace-config.yaml
kubectl apply -f k8s/02-pvc.yaml
kubectl apply -f k8s/03-postgres.yaml
kubectl apply -f k8s/04-backend.yaml
kubectl apply -f k8s/05-ingress.yaml

# 2. 查看 Pod 启动与部署状态
kubectl get pods -n agentic-commerce -w

# 3. 登录后端 Pod 执行数据库迁移与初始化
POD_NAME=$(kubectl get pods -n agentic-commerce -l app=backend -o jsonpath="{.items[0].metadata.name}")
kubectl exec -it -n agentic-commerce $POD_NAME -- python -m app.scripts.init_db
kubectl exec -it -n agentic-commerce $POD_NAME -- python -m app.scripts.seed_data

# 4. 查看后端日志排错
kubectl logs -n agentic-commerce -l app=backend -f --tail=100
```
