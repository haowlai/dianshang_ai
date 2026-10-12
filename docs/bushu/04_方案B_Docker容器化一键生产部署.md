# 04 方案 B：Docker 容器化一键生产部署（Docker Compose）

> **适用场景**：现代化云原生交付模式。通过 Docker 抹平开发机与生产服务器的全部底层差异，配合容器编排实现一键拉起、健康检查依赖链控制与零停机平滑滚动更新。

---

## 目录
- [一、生产容器化编排拓扑与目录规划](#一生产容器化编排拓扑与目录规划)
- [二、生产级编排定义 (docker-compose.prod.yml) 深度解析](#二生产级编排定义-docker-composeprodyml-深度解析)
- [三、生产数据卷持久化与脱敏安全规范](#三生产数据卷持久化与脱敏安全规范)
- [四、线上服务拉起、建表与健康自检 SOP](#四线上服务拉起建表与健康自检-sop)
- [五、生产滚动更新（Zero-Downtime Rolling Update）策略](#五生产滚动更新zero-downtime-rolling-update策略)
- [六、常用 Docker 容器化运维速查命令](#六常用-docker-容器化运维速查命令)

---

## 一、生产容器化编排拓扑与目录规划

在阿里云 ECS 宿主机上，我们创建专用目录 `/data/docker-deploy`：

```text
/data/docker-deploy/
├── docker-compose.prod.yml    # [核心] 生产环境 6 容器统一编排定义
├── .env.prod                  # [核心] 生产真实环境变量 (脱敏管理)
├── conf/
│   └── nginx.conf             # 生产 Nginx 网关反向代理配置文件
├── data/                      # [持久化宿主机映射目录，防止容器销毁数据丢失]
│   ├── pgdata/                # PostgreSQL 数据文件
│   ├── redisdata/             # Redis AOF 数据文件
│   └── miniodata/             # MinIO 素材对象存储文件
└── deploy_docker.sh           # 一键自动发布更新脚本
```

---

## 二、生产级编排定义 (docker-compose.prod.yml) 深度解析

创建 `/data/docker-deploy/docker-compose.prod.yml`：

```yaml
# ==============================================================================
# AgenticCommerce 生产全量编排文件
# 编排 6 大核心容器：PostgreSQL(向量), Redis, MinIO, Backend, Frontend, Nginx
# ==============================================================================
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
      - /etc/letsencrypt:/etc/letsencrypt:ro  # 挂载 SSL 证书
    depends_on:
      - backend
      - frontend
    networks:
      - agentic-prod-net

networks:
  agentic-prod-net:
    driver: bridge
```

---

## 三、生产数据卷持久化与脱敏安全规范

创建 `/data/docker-deploy/.env.prod`，严格设置生产安全强密码：

```ini
APP_ENV=prod
APP_VERSION=v1.0.0

# 数据库密码建议使用 16 位以上混合大小写强密码
POSTGRES_USER=postgres
POSTGRES_PASSWORD=PrdSec_DbP@ssword2026_xYz
POSTGRES_DB=agentic_commerce

# MinIO 凭证
MINIO_ACCESS_KEY=agentic_admin
MINIO_SECRET_KEY=PrdSec_MinioKey2026_AbCdEf
MINIO_BUCKET=agentic-assets

# 大模型 API 密钥
DASHSCOPE_API_KEY=sk-your-real-production-dashscope-key
DEFAULT_LLM_MODEL=qwen-max
```

> **安全底线**：`.env.prod` 文件**严禁提交至 Git 公共代码仓库**！应在服务器本地单独通过安全信道配置或由 CI/CD 变量注入。

---

## 四、线上服务拉起、建表与健康自检 SOP

在 ECS 服务器终端进入 `/data/docker-deploy`：

```bash
# 1. 如果采用离线镜像包方式，先导入镜像：
docker load -i agentic-images-v1.0.0.tar.gz

# 2. 一键启动所有容器并在后台守护
docker compose -f docker-compose.prod.yml up -d

# 3. 检查容器状态 (STATUS 必须全为 healthy 或 Up)
docker compose -f docker-compose.prod.yml ps

# 4. 在后端容器内部执行数据库建表与种子数据注入
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.init_db
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.seed_data

# 5. 校验后端健康探针
curl http://127.0.0.1/api/v1/health # 返回 {"status": "healthy"} 即代表通过 Nginx 反代全链路畅通！
```

---

## 五、生产滚动更新（Zero-Downtime Rolling Update）策略

当开发者合入新的代码并生成了 `v1.0.1` 新镜像时，**切忌执行 `docker compose down`（这会导致数秒的服务中断与数据库连接断开！）**。

**标准的生产平滑发布脚本逻辑**：
```bash
#!/bin/bash
# 1. 导入或拉取最新 v1.0.1 镜像
docker pull registry.cn-hangzhou.aliyuncs.com/your-org/agentic-backend:v1.0.1
docker pull registry.cn-hangzhou.aliyuncs.com/your-org/agentic-frontend:v1.0.1

# 2. 修改 .env.prod 中的版本号
sed -i 's/APP_VERSION=.*/APP_VERSION=v1.0.1/g' .env.prod

# 3. 执行轻量更新：只平滑重启业务容器，数据库与缓存保持不中断连接！
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend

# 4. 运行健康检查，确认新容器完全就绪后，清理无标签旧镜像
sleep 5
curl -f http://127.0.0.1/health || (echo "健康检查未通过！" && exit 1)
docker image prune -f
echo ">>> [发布成功] 业务已平滑升级至 v1.0.1！"
```

---

## 六、常用 Docker 容器化运维速查命令

| 操作需求 | 生产执行命令 |
| :--- | :--- |
| **实时查看后端业务日志** | `docker compose -f docker-compose.prod.yml logs -f --tail=100 backend` |
| **实时查看网关访问日志** | `docker compose -f docker-compose.prod.yml logs -f nginx` |
| **进入后端容器排查** | `docker compose -f docker-compose.prod.yml exec backend bash` |
| **进入 PostgreSQL 数据库** | `docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d agentic_commerce` |
| **查看各容器内存/CPU 消耗**| `docker stats` |
| **重启单项异常容器** | `docker compose -f docker-compose.prod.yml restart backend` |
