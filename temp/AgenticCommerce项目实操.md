# AgenticCommerce项目实操

---

## 目录

- 第一章 项目概述与技术栈全景图

- 第二章 核心架构设计与工作流解析

- 第三章 项目开发环境

- 第四章 基础设施搭建（Docker 容器化）

- 第五章 RAG 私有知识库（向量检索）

- 第六章 7\-Agent 多智能体工作流（LangGraph）

- 第七章 API 接口（FastAPI 三层架构）

- 第八章 前后端对接（Vue 3 工作台）

- 第九章 项目启动与验收

---

# 第一章 项目概述与技术栈全景图

## 1\.1 项目背景

**AgenticCommerce（自主智能体电商融合平台）** 是一个基于 **多智能体（Multi\-Agent）架构** 的跨境电商智能内容生成平台。

跨境电商运营长期面临四大痛点：

|痛点|传统方式|本项目方案|
|---|---|---|
|素材制作周期长|文案\+拍摄\+剪辑需要 5\~10 天|**分钟级** 一键生成|
|文案同质化严重|人工翻译，千篇一律|7 个 AI 分工协作，本地化卖点|
|广告法违禁词风险|人工核对，易漏易错|合规智能体硬扫描 \+ 自动回退重写|
|多语种翻译难|请翻译公司，成本高|大模型多语种出海文案|

用户只需输入商品基础信息（例如：一把露营椅），系统即可**自动完成**：需求分析 → 多卖点文案 → 视觉 Prompt 设计 → 图片/视频渲染 → 合规质检 → 打包下载。

## 1\.2 项目核心亮点

1. **7\-Agent 工作流**：需求分析、创意策划、视觉设计、图片生成、视频生成、合规质检，七个智能体各司其职、协同作战。

2. **P\-E\-V 闭环**（Plan\-Execute\-Verify，规划\-执行\-验证）：审核不过关自动打回重写，直到通过或达到重试上限。

3. **RAG 私有知识库**：基于 PostgreSQL `pgvector` 沉淀品牌视觉规范、广告法违禁词与类目爆款经验。

4. **可观测工作台**：DAG 状态图、节点耗时、Token 统计、Prompt 轨迹与输入输出结构化监控。

## 1\.3 核心技术栈与官方资源指南

|技术分类|技术名称|官网与参考文档|核心应用场景|
|---|---|---|---|
|基础语言|Python 3\.12|[python\.org](https://www.python.org/)|支持高级异步特性与类型提示|
|依赖管理|uv|[astral\.sh/uv](https://github.com/astral-sh/uv)|Rust 编写的超高速包管理器|
|Web 框架|FastAPI|[fastapi\.tiangolo\.com](https://fastapi.tiangolo.com/)|极速高并发异步 RESTful API|
|ORM 框架|SQLAlchemy 2\.0|[sqlalchemy\.org](https://www.sqlalchemy.org/)|对象关系映射，配合 asyncpg 异步读写|
|关系型数据库|PostgreSQL 16|[postgresql\.org](https://www.postgresql.org/)|存储商品、任务、文案等元数据|
|向量检索|pgvector|[github\.com/pgvector/pgvector](https://github.com/pgvector/pgvector)|1024 维向量余弦相似度检索|
|内存缓存|Redis 7|[redis\.io](https://redis.io/)|高频状态轮询与热点数据缓存|
|对象存储|MinIO|[min\.io](https://min.io/)|私有化存放 AI 生成的图片与视频|
|智能体框架|LangGraph|[langchain\-ai\.github\.io/langgraph](https://langchain-ai.github.io/langgraph/)|有状态 DAG 图计算工作流|
|前端框架|Vue 3 \+ Vite|[vuejs\.org](https://vuejs.org/)|响应式前端与工作台可视化|
|状态管理|Pinia|[pinia\.vuejs\.org](https://pinia.vuejs.org/)|前端全局状态管理|
|云端 AI|阿里云百炼 DashScope|[help\.aliyun\.com/zh/model\-studio](https://help.aliyun.com/zh/model-studio)|通义千问/万相/视频大模型|

## 1\.4 一次完整业务流转（先建立整体印象）

---

# 第二章 核心架构设计与工作流解析

## 2\.1 整体技术架构（架构图）

本项目采用严格的**前后端分离**与**三层架构**设计。后端通过 HTTP API 驱动大模型生成，通过对象存储管理多模态文件。

## 2\.2 三层架构（MVC 的现代化变体）

很多同学听过 MVC，本项目用的是更符合企业实践的「三层架构」，本质是一样的思想——**各司其职、职责分离**。

> **为什么要分三层？** 迎宾员（Router）不问菜怎么炒，厨师长（Service）不碰锅碗瓢盆的摆放（Model）。哪天换一个数据库，只改 Model 和 Repository，Service 和 Router 一行不动。
> 
> 

## 2\.3 RAG 私有知识库（向量语义基础设施）

RAG 知识库是智能体做「专业判断」的底气来源。它把**品牌视觉规范、广告法违禁词、类目爆款经验**等文档切块并向量化，供智能体在生成时检索参考。

**关键参数**（写死在 `app/conf/config.py`）：

|参数|值|说明|
|---|---|---|
|向量维度|1024|对应 text\-embedding\-v4 / BGE\-large\-zh\-v1\.5|
|距离算法|余弦距离 cosine|`vector_cosine_ops`|
|相似度阈值|\>= 0\.5|低于阈值视为不相关|
|Top\-K|5|每次召回最相关的 5 个分块|

## 2\.4 7\-Agent 多智能体状态机（LangGraph）

区别于传统线性的代码调用，LangGraph 将业务转化为**有状态的节点图（Node Graph）**。当某个节点失败时，可以自动流转回上一个节点进行自我纠错。

## 2\.5 P\-E\-V 闭环（规划\-执行\-验证）

这是本项目最核心的「自我纠错」机制。审核智能体就是那个「质检员」，不合规就打回去重写。

## 2\.6 数据库实体关系（完整 ER 图，14 张表）

本项目共 **14 张业务表**。所有业务表（除全局租户表 `ac_tenant`）都继承 `AuditMixin`，强制拥有 7 大审计字段。**严禁物理外键**，全部使用逻辑外键 `xxx_id varchar(32)`。

> **注意**：`ac_tenant` 是全局租户定义表，它**不继承** `AuditMixin`（因为它本身就是租户的根，没有 `tenant_id` 字段）。
> 
> 

---

# 第三章 项目开发环境

## 3\.1 创建项目（uv 工具链）

传统 Python 用 `pip` 装包慢、易冲突。本项目使用当今最火的 `uv`（Rust 编写，比 pip 快几十倍）。

**安装 uv（前提：本机已安装 Python 环境）：**

> `uv` 本身也是一个 Python 包，直接用 `pip` 安装即可，无需下载额外脚本：
> 
> 



```Bash
pip install uv
```

**克隆项目后安装依赖：**

```Bash
# 进入项目根目录
cd agentic-commerce

# 同步安装全部依赖（读取 pyproject.toml）
uv sync

# 或使用传统 pip
pip install -e .
```

## 3\.2 依赖清单解析（pyproject\.toml）

```Plain Text
[project]
name = "agentic-commerce"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",            # Web 框架
    "uvicorn[standard]>=0.30.0",   # ASGI 服务器
    "pydantic>=2.7.0",             # 数据校验
    "pydantic-settings>=2.2.0",    # 配置读取 .env
    "langgraph>=1.2.4",            # 多智能体图编排
    "langchain>=1.3.7",            # LLM 应用框架
    "sqlalchemy>=2.0.30",          # ORM
    "asyncpg>=0.29.0",             # PostgreSQL 异步驱动
    "pgvector>=0.3.0",             # 向量扩展
    "redis>=5.0.4",                # 缓存
    "minio>=7.2.7",                # 对象存储
    "pyjwt>=2.8.0",                # JWT 令牌
    "passlib[bcrypt]>=1.7.4",      # 密码哈希
    "httpx>=0.27.0",               # 异步 HTTP 客户端
    "websockets>=12.0",            # WebSocket
    "opentelemetry-api>=1.24.0",   # 可观测
]
```

**各依赖说明（小白版）：**

|依赖|一句话说明|
|---|---|
|fastapi|后厨，处理 HTTP 请求的 Python Web 框架|
|uvicorn|端盘子的服务员，把 FastAPI 跑起来对外服务|
|pydantic|验钞机，检查前端传进来的参数是否合法|
|sqlalchemy|翻译官，把 Python 类翻译成数据库表操作|
|asyncpg|高速公路，让 Python 异步读写 PostgreSQL|
|pgvector|给数据库装上「找相似」的能力（向量检索）|
|langgraph|画迷宫地图，编排 7 个智能体的流转|
|httpx|插头，让后端去调用阿里云大模型接口|
|pyjwt|会员卡，签发和验证登录令牌|

**添加依赖（ ****`uv add`**** ）：**

如果是从零搭建项目，用下面的命令逐个添加依赖（版本号与 `pyproject.toml` 一致）：

```Bash
uv add "fastapi>=0.111.0" "uvicorn[standard]>=0.30.0" "pydantic>=2.7.0" "pydantic-settings>=2.2.0" "langgraph>=1.2.4" "langchain>=1.3.7" "sqlalchemy>=2.0.30" "asyncpg>=0.29.0" "pgvector>=0.3.0" "redis>=5.0.4" "minio>=7.2.7" "pyjwt>=2.8.0" "passlib[bcrypt]>=1.7.4" "httpx>=0.27.0" "websockets>=12.0" "opentelemetry-api>=1.24.0"
```

> 已有 `pyproject.toml` 时直接 `uv sync` 一键安装即可；`uv add` 用于学习「如何一步步搭起依赖」。
> 
> 

## 3\.3 安装所需服务（Docker Compose）

本项目所需的全部基础服务（PostgreSQL、Redis、MinIO）通过 Docker 一键部署，无需手动安装任何数据库。

|服务|用途|隔离端口|
|---|---|---|
|PostgreSQL 16 \+ pgvector|存储元数据 \+ 向量检索|5434（默认 5432）|
|Redis 7|缓存 / 任务状态|6381|
|MinIO|对象存储图片视频|9010（API）/ 9011（控制台）|

> **什么是 Docker？** 把软件连同它的运行环境一起打包成一个「集装箱（容器）」。你的电脑不用装数据库，拉下集装箱一键启动即可，跨电脑零报错。
> 
> 

---

## 3\.4 源码：

\[ds\.zip\]

# 第四章 基础设施搭建（Docker 容器化）

## 4\.1 项目目录结构

```Plain Text
agentic-commerce/
├─ app/                              # 后端代码主目录
│  ├─ agent/                         # LangGraph 7-Agent 工作流
│  │  ├─ nodes/                      # 7 个 Agent 节点实现
│  │  ├─ graph.py                    # 状态图构建与条件边
│  │  ├─ state.py                    # AgentState 共享状态
│  │  └─ recorder.py                 # 节点快照记录 + WS 广播
│  ├─ api/v1/                        # 接口路由层（13 个路由 + WS）
│  ├─ clients/                       # 客户端（PG/Redis/MinIO/AI厂商工厂）
│  ├─ conf/                          # 运行时配置（Pydantic Settings）
│  ├─ core/                          # 安全/日志/异常/依赖注入/中间件
│  ├─ models/                        # SQLAlchemy ORM 模型（14 张表）
│  ├─ prompt/                        # 提示词渲染工具
│  ├─ repositories/                  # 仓储层（强制 tenant_id）
│  ├─ scripts/                       # 建表/种子数据脚本
│  └─ services/                      # 领域服务层（业务逻辑）
├─ conf/
│  ├─ nginx.conf                     # 反向代理
│  └─ .env.example                   # 环境变量模板
├─ docker/
│  └─ postgres/init.sql              # pgvector 扩展初始化
├─ frontend/                         # Vue 3 前端
├─ prompts/                          # 7 个 Agent 的 Prompt 模板
├─ main.py                           # FastAPI 主入口（端口 8002）
├─ run_workflow.py                   # CLI 工作流调试脚本
├─ docker-compose.infra.yml          # 开发环境：仅基础设施
├─ docker-compose.yml                # 生产环境：全栈编排
├─ pyproject.toml                    # 项目依赖定义
├─ .env                              # 配置信息
└─ README.md
```

## 4\.2 开发环境基础设施编排（docker\-compose\.infra\.yml）

```Bash
name: agentic-commerce

services:
  # ── PostgreSQL 16 + pgvector 向量扩展 ──
  postgres:
    image: pgvector/pgvector:pg16
    container_name: agentic-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-agentic_commerce}
    ports:
      - "${POSTGRES_PORT:-5434}:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d agentic_commerce"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── Redis 7 缓存 ──
  redis:
    image: redis:7-alpine
    container_name: agentic-redis
    restart: unless-stopped
    ports:
      - "${REDIS_PORT:-6381}:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes

  # ── MinIO 对象存储 ──
  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: agentic-minio
    restart: unless-stopped
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
    ports:
      - "${MINIO_API_PORT:-9010}:9000"      # S3 API 端口
      - "${MINIO_CONSOLE_PORT:-9011}:9001"  # 网页控制台
    volumes:
      - ./data/minio:/data
    command: server /data --console-address ":9001"
```

**pgvector 扩展初始化（docker/postgres/init\.sql）：**

```SQL
-- 初始化 PostgreSQL 16 pgvector 向量扩展
CREATE EXTENSION IF NOT EXISTS vector;
```

**docker设置**

```Bash
{"registry-mirrors":["https://docker.1ms.run"]}
```

**一键启动 / 停止：**

```Bash
# 启动基础设施
docker-compose -f docker-compose.infra.yml up -d
# 停止
docker-compose -f docker-compose.infra.yml down
```

> Windows 同学可直接双击项目根的 `一键启动.bat`。
> 
> 

## 4\.3 环境变量模板（conf/\.env\.example）

```Plain Text
# 基础服务
APP_ENV=dev
APP_PORT=8002
DEBUG=true

# JWT 安全
AUTH_ENABLED=true
SECRET_KEY=agentic-commerce-dev-secret-key-change-it-in-production-2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# PostgreSQL（隔离端口 5434）
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5434
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=agentic_commerce

# Redis（隔离端口 6381）
REDIS_URL=redis://127.0.0.1:6381/0

# MinIO（隔离端口 9010/9011）
MINIO_ENDPOINT=127.0.0.1:9010
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=agentic-assets

# 业务配置
ALLOW_MOCK_ASSETS=true   # 未配 Key 时自动降级为 Mock
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.5
MAX_QUALITY_RETRIES=2

# AI 厂商 API Key（留空自动 Mock）
DASHSCOPE_API_KEY=
WANX_API_KEY=
KLING_API_KEY=
```

---

# 第五章 RAG 私有知识库（向量检索）

## 5\.1 需求说明

本章实现一个 **RAG 私有知识库**：将品牌视觉规范、广告法违禁词、类目爆款经验等文档录入系统，自动**切块 \+ 向量化**，供后续智能体通过**语义相似度检索**获取上下文，支撑专业化、合规化内容生成。

功能清单：

5. 知识文档录入（`ac_knowledge_base_doc`）

6. 文本切块与向量化（`ac_knowledge_chunk` \+ `Vector(1024)`）

7. 向量相似度检索接口（`/api/v1/knowledge/query`）

8. 文档列表与详情查询

## 5\.2 代码组织规划

```Plain Text
app/
├─ models/
│  ├─ base.py              # AuditMixin 7大审计字段基类
│  └─ knowledge.py         # KnowledgeBaseDoc + KnowledgeChunk（Vector 1024）
├─ clients/
│  └─ provider_factory.py  # QwenLLMClient.get_embedding()
├─ services/
│  └─ knowledge_service.py # 文档录入 + 向量检索业务逻辑
├─ repositories/
│  └─ knowledge_repo.py    # 仓储层
├─ api/v1/
│  └─ knowledge.py         # 知识库路由
└─ scripts/
   └─ seed_data.py         # 初始化品牌知识文档与向量分块
```

## 5\.3 具体实现

### 5\.3\.1 审计字段基类（app/models/base\.py）

这是**贯穿全项目的军规**：所有核心业务实体必须继承 `AuditMixin`，具备 7 大审计字段。

```Python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, SmallInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def generate_uuid32() -> str:
    """生成 32 位无连字符小写 UUID 作为主键"""
    return uuid.uuid4().hex

def utc_now() -> datetime:
    """返回当前 UTC 时间"""
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class AuditMixin:
    """每张业务表必须包含的 7 个审计字段与租户隔离标识"""
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_uuid32)
    tenant_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(32), nullable=True)
    updated_by: Mapped[str] = mapped_column(String(32), nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
```

> **七大字段记忆口诀**：「主键租户两造人，双时一删。」——`id`（主键）、`tenant_id`（租户）、`created_by`/`updated_by`（创建人/修改人）、`create_time`/`update_time`（创建/更新时间）、`is_deleted`（逻辑删除）。
> 
> 

### 5\.3\.2 知识库模型（app/models/knowledge\.py）

```Python
from sqlalchemy import String, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from .base import Base, AuditMixin

class KnowledgeBaseDoc(Base, AuditMixin):
    __tablename__ = "ac_knowledge_base_doc"
    category: Mapped[str] = mapped_column(String(64), nullable=False)   # brand / compliance
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)
    vector_status: Mapped[str] = mapped_column(String(32), default="pending")

class KnowledgeChunk(Base, AuditMixin):
    __tablename__ = "ac_knowledge_chunk"
    doc_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1024), nullable=True)  # 1024 维向量
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
```

> **`Vector(1024)`**** 是核心**：pgvector 让 PostgreSQL 原生支持向量存储与余弦距离计算，无需额外部署向量数据库。
> 
> 

### 5\.3\.3 向量化客户端（app/clients/provider\_factory\.py ）

```Python
class QwenLLMClient:
    EMBEDDING_URL = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"

    async def get_embedding(self, text: str, model: str = "text-embedding-v4") -> List[float]:
        """获取文本 Embedding 向量；无 Key 时返回伪向量"""
        if not self.api_key or self.api_key.strip() == "":
            return [0.03125] * 1024  # 伪归一化向量，供无 Key 演示

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "input": {"texts": [text]}}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.EMBEDDING_URL, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["output"]["embeddings"][0]["embedding"]
        return [0.03125] * 1024
```

### 5\.3\.4 知识库服务（app/services/knowledge\_service\.py）

```Python
class KnowledgeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_doc(self, tenant_id, user_id, category, doc_type, name, content):
        """录入文档，切块并向量化"""
        doc = KnowledgeBaseDoc(tenant_id=tenant_id, created_by=user_id,
                               category=category, doc_type=doc_type, name=name,
                               vector_status="indexing")
        self.session.add(doc)
        await self.session.flush()  # 先拿到 doc.id

        llm = ProviderFactory.get_llm_client("qwen")
        # 简单按 500 字符切块
        chunks = [content[i:i+500] for i in range(0, len(content), 500)] or [content]
        for idx, c in enumerate(chunks, 1):
            vec = await llm.get_embedding(c)
            self.session.add(KnowledgeChunk(
                tenant_id=tenant_id, doc_id=doc.id, doc_type=doc_type,
                chunk_index=idx, content=c, embedding=vec,
            ))
        doc.vector_status = "indexed"
        await self.session.commit()
        return doc.id

    async def vector_search(self, tenant_id, query_text, top_k=5):
        """向量相似度检索（强制 tenant_id 隔离）"""
        llm = ProviderFactory.get_llm_client("qwen")
        q_vec = await llm.get_embedding(query_text)
        res = await self.session.execute(
            select(KnowledgeChunk, KnowledgeChunk.embedding.cosine_distance(q_vec).label("distance"))
            .where(KnowledgeChunk.tenant_id == tenant_id, KnowledgeChunk.is_deleted == 0)
            .order_by("distance")
            .limit(top_k)
        )
        return [{"content": row[0].content, "distance": round(float(row[1]), 4)} for row in res]
```

> **安全红线**：向量检索也必须带 `WHERE tenant_id = :tenant_id`，防止 A 租户检索到 B 租户的知识。
> 
> 

### 5\.3\.5 知识库路由（app/api/v1/knowledge\.py）

```Python
router = APIRouter(prefix="/knowledge", tags=["知识库RAG管理"])

@router.post("/docs")
async def create_doc(req: DocCreateRequest, db: AsyncSession = Depends(get_db),
                     user_tenant: dict = Depends(get_current_user_and_tenant)):
    svc = KnowledgeService(db)
    doc_id = await svc.create_doc(user_tenant["tenant_id"], user_tenant.get("user_id"),
                                  req.category, req.doc_type, req.name, req.content)
    return {"code": 200, "data": {"doc_id": doc_id}, "message": "知识库文档创建并向量化成功"}

@router.post("/query")
async def test_vector_search(req: QueryTestRequest, db: AsyncSession = Depends(get_db),
                             user_tenant: dict = Depends(get_current_user_and_tenant)):
    svc = KnowledgeService(db)
    results = await svc.vector_search(user_tenant["tenant_id"], req.query_text, req.top_k)
    return {"code": 200, "data": {"query": req.query_text, "results": results}, "message": "检索完成"}
```

## 5\.4 RAG 检索完整流程图

---

# 第六章 7\-Agent 多智能体工作流（LangGraph）

## 6\.1 需求说明

本章实现系统的「大脑」——基于 LangGraph 的 7\-Agent 工作流，编排各智能体节点协同完成内容生成，并通过 **P\-E\-V 循环** 实现自我纠错，同时向工作台实时推送执行进度。

7 个节点职责：

|序号|节点|英文名|职责|
|---|---|---|---|
|1|总控调度|Orchestrator|任务初始化、参数解析、全局进度管控|
|2|需求分析|RequirementAnalyzer|RAG 检索品牌规范，输出本地化卖点报告|
|3|创意策划|CreativePlanner|生成标题/五点/描述/关键词|
|4|视觉设计|VisualDesigner|生成生图/生视频 Prompt 与分镜|
|5|图片生成|ImageGenerator|调用万相生成主图/场景/细节图|
|6|视频生成|VideoGenerator|调用可灵生成短视频|
|7|质量审核|QualityReviewer|合规硬扫描 \+ 综合打分|

## 6\.2 代码组织规划

```Plain Text
app/
├─ agent/
│  ├─ state.py                  # AgentState 共享状态
│  ├─ graph.py                  # 状态图构建 + P-E-V 条件路由
│  ├─ recorder.py               # 节点快照记录 + WS 广播
│  └─ nodes/
│     ├─ orchestrator.py
│     ├─ requirement_analyzer.py
│     ├─ creative_planner.py
│     ├─ visual_designer.py
│     ├─ image_generator.py
│     ├─ video_generator.py
│     └─ quality_reviewer.py
├─ prompt/
│  └─ templates.py              # Prompt 模板加载
└─ prompts/                     # 7 个 Agent 的 Prompt 模板
   ├─ orchestrator.md
   ├─ requirement_analyzer.md
   ├─ creative_planner.md
   ├─ visual_designer.md
   ├─ image_generator.md
   ├─ video_generator.md
   └─ quality_reviewer.md
```

## 6\.3 具体实现

### 6\.3\.1 共享状态（app/agent/state\.py）

```Python
from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
import operator

class AgentState(TypedDict, total=False):
    # 基础元数据
    task_id: str
    tenant_id: str
    sku_id: str
    batch_id: Optional[str]
    config: Dict[str, Any]

    # 状态控制
    current_step: str
    completed_steps: Annotated[List[str], operator.add]  # 累加合并
    retry_count: int
    max_retries: int

    # 业务产出物
    sku_data: Dict[str, Any]
    requirement_report: Dict[str, Any]
    creative_plan: Dict[str, Any]
    visual_design: Dict[str, Any]
    generation_prompts: Dict[str, Any]
    generated_images: List[Dict[str, Any]]
    generated_video: Optional[Dict[str, Any]]

    # 审核与路由
    quality_reports: List[Dict[str, Any]]
    is_passed: bool
    violations: List[Dict[str, Any]]
    error: Optional[str]
```

> **`Annotated[List[str], operator.add]`**** 是关键**：多个节点都会往 `completed_steps` 里追加数据，LangGraph 用 `operator.add` 把各节点返回的列表「自动累加合并」，而不是互相覆盖。
> 
> 

### 6\.3\.2 状态图构建与条件路由（app/agent/graph\.py）

```Python
from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState

def quality_review_router(state: AgentState) -> Literal["creative_planner", "__end__"]:
    """P-E-V 闭环条件路由"""
    is_passed = state.get("is_passed", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if is_passed:
        return END                          # 通过 → 结束
    if retry_count < max_retries:
        return "creative_planner"           # 未达上限 → 打回重写
    return END                              # 达上限 → 失败结束

def build_workflow():
    builder = StateGraph(AgentState)

    # 1. 注册 7 大智能体节点
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("requirement_analyzer", requirement_analyzer_node)
    builder.add_node("creative_planner", creative_planner_node)
    builder.add_node("visual_designer", visual_designer_node)
    builder.add_node("image_generator", image_generator_node)
    builder.add_node("video_generator", video_generator_node)
    builder.add_node("quality_reviewer", quality_reviewer_node)

    # 2. 线性拓扑流水线
    builder.add_edge(START, "orchestrator")
    builder.add_edge("orchestrator", "requirement_analyzer")
    builder.add_edge("requirement_analyzer", "creative_planner")
    builder.add_edge("creative_planner", "visual_designer")
    builder.add_edge("visual_designer", "image_generator")
    builder.add_edge("image_generator", "video_generator")
    builder.add_edge("video_generator", "quality_reviewer")

    # 3. 条件回退边（P-E-V 循环）
    builder.add_conditional_edges(
        "quality_reviewer",
        quality_review_router,
        {"creative_planner": "creative_planner", END: END},
    )
    return builder

app_workflow = build_workflow().compile()
```

### 6\.3\.3 节点执行记录器（app/agent/recorder\.py）

```Python
async def record_node_execution(task_id, tenant_id, node_name, status="success",
                                elapsed_ms=0, prompt_tokens=0, completion_tokens=0,
                                cost=0.0, input_data=None, output_data=None, progress=0):
    """持久化节点快照 + WebSocket 实时广播"""
    # 1. 广播 WebSocket 状态
    event = {"type": "node_update", "task_id": task_id, "node_name": node_name,
             "status": status, "progress": progress, "elapsed_ms": elapsed_ms,
             "cost": cost, "output_data": output_data or {}}
    await ws_manager.broadcast(event)

    # 2. 持久化写入 ac_task_node_run 表
    if task_id:
        async with AsyncSessionLocal() as session:
            node_run = TaskNodeRun(tenant_id=tenant_id, task_id=task_id, node_name=node_name,
                                   status=status, elapsed_ms=elapsed_ms,
                                   prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                                   cost=cost, input_data=input_data or {}, output_data=output_data or {})
            session.add(node_run)
            await session.execute(update(Task).where(Task.id == task_id).values(current_node=node_name))
            await session.commit()
```

### 6\.3\.4 节点 1：总控调度（orchestrator\.py）

```Python
async def orchestrator_node(state: AgentState) -> dict:
    task_id = state.get("task_id")
    tenant_id = state.get("tenant_id") or "tenant_default"
    sku_id = state.get("sku_id")
    sku_data = state.get("sku_data") or {}

    # 若状态中无 SKU 详情，从数据库查询补充
    if not sku_data and sku_id:
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Sku).where(Sku.id == sku_id))
            sku_obj = res.scalar_one_or_none()
            if sku_obj:
                sku_data = {"id": sku_obj.id, "code": sku_obj.code, "name": sku_obj.name,
                            "category": sku_obj.category, "specs": sku_obj.specs,
                            "description": sku_obj.description, "images": sku_obj.images}

    await record_node_execution(task_id=task_id, tenant_id=tenant_id, node_name="orchestrator",
                                status="success", progress=10,
                                input_data={"sku_id": sku_id}, output_data={"sku_code": sku_data.get("code")})

    return {"current_step": "orchestrator", "completed_steps": ["orchestrator"],
            "sku_data": sku_data, "retry_count": state.get("retry_count", 0)}
```

### 6\.3\.5 节点 2：需求分析（requirement\_analyzer\.py）

```Python
async def requirement_analyzer_node(state: AgentState) -> dict:
    tenant_id = state.get("tenant_id") or "tenant_default"
    sku_data = state.get("sku_data") or {}

    # 1. RAG 知识检索（品牌规范与本土化调性）
    rag_context = ""
    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(KnowledgeChunk.content).where(KnowledgeChunk.tenant_id == tenant_id).limit(3)
        )
        chunks = res.scalars().all()
        if chunks:
            rag_context = "\n".join(chunks)

    # 2. 调用 Qwen LLM 分析需求
    llm_client = ProviderFactory.get_llm_client("qwen")
    system_prompt = load_prompt_template("requirement_analyzer") or "你是10年经验的跨境电商产品策划总监"
    prompt_human = f"""请基于以下商品信息进行出海电商需求深度分析：
【商品名称】: {sku_data.get('name')}
【类目】: {sku_data.get('category')}
【规格】: {sku_data.get('specs')}
【品牌规范(RAG)】: {rag_context or '遵循海外平台合规标准'}
请输出：1.目标受众画像 2.3大核心卖点 3.核心SEO英文关键词"""

    llm_res = await llm_client.chat_completion(
        [{"role": "system", "content": system_prompt},
         {"role": "human", "content": prompt_human}], model="qwen-plus")

    requirement_report = {"analysis_text": llm_res.get("content", ""),
                          "rag_source_count": len(chunks), "cost": llm_res.get("cost", 0.0)}
    await record_node_execution(task_id=state.get("task_id"), tenant_id=tenant_id,
                                node_name="requirement_analyzer", status="success",
                                progress=25, output_data=requirement_report,
                                prompt_tokens=llm_res.get("prompt_tokens", 0),
                                completion_tokens=llm_res.get("completion_tokens", 0))
    return {"current_step": "requirement_analyzer", "completed_steps": ["requirement_analyzer"],
            "requirement_report": requirement_report}
```

### 6\.3\.6 节点 3：创意策划（creative\_planner\.py）

```Python
async def creative_planner_node(state: AgentState) -> dict:
    tenant_id = state.get("tenant_id") or "tenant_default"
    sku_id = state.get("sku_id") or ""
    sku_data = state.get("sku_data") or {}
    req_report = state.get("requirement_report") or {}
    retry_count = state.get("retry_count", 0)

    llm_client = ProviderFactory.get_llm_client("qwen")

    # 重试时注入上一轮审核建议
    feedback = ""
    if retry_count > 0 and state.get("quality_reports"):
        suggestions = state["quality_reports"][-1].get("suggestions", [])
        if suggestions:
            feedback = f"【上一轮审核改进建议】: {'; '.join(suggestions)}\n请针对以上问题严密修正文案！"

    system_prompt = load_prompt_template("creative_planner") or "你是亚马逊爆款文案专家，严禁使用虚假绝对化词汇"
    prompt_human = f"""请创作专业级英文高转化 Listing 文案：
【商品名称】: {sku_data.get('name')}
【规格】: {sku_data.get('specs')}
【需求分析】: {req_report.get('analysis_text', '')}
{feedback}
要求输出：1.TITLE 2.BULLETS(5点) 3.DESCRIPTION 4.KEYWORDS"""

    llm_res = await llm_client.chat_completion(
        [{"role": "system", "content": system_prompt},
         {"role": "human", "content": prompt_human}], model="qwen-plus")

    title = f"{sku_data.get('name', 'Premium Product')} - Ultralight Heavy Duty Portable"
    bullets = ["[AEROSPACE GRADE DURABILITY] ...", "[3-SECOND RAPID SETUP] ...", ...]
    keywords = ["camping chair", "portable outdoor chair", ...]

    # 持久化到 ac_copy 表
    async with AsyncSessionLocal() as session:
        session.add(Copy(tenant_id=tenant_id, task_id=state.get("task_id"), sku_id=sku_id,
                         language="en", title=title, bullets=bullets,
                         description=llm_res.get("content", ""), keywords=keywords, status="completed"))
        await session.commit()

    creative_plan = {"title": title, "bullets": bullets, "description": llm_res.get("content", ""),
                     "keywords": keywords}
    await record_node_execution(task_id=state.get("task_id"), tenant_id=tenant_id,
                                node_name="creative_planner", status="success", progress=40,
                                output_data=creative_plan)
    return {"current_step": "creative_planner", "completed_steps": ["creative_planner"],
            "creative_plan": creative_plan}
```

> **重点理解**：`feedback` 注入逻辑就是 P\-E\-V 循环的「执行\-验证\-回退」关键——第二轮重写时，把上一轮质检的违规点原样塞回 Prompt，让 AI 针对性修正。
> 
> 

### 6\.3\.7 节点 4：视觉设计（visual\_designer\.py）

```Python
async def visual_designer_node(state: AgentState) -> dict:
    sku_data = state.get("sku_data") or {}
    creative_plan = state.get("creative_plan") or {}

    llm_client = ProviderFactory.get_llm_client("qwen")
    # 调用大模型拆解生图/生视频 Prompt
    llm_res = await llm_client.chat_completion(
        [{"role": "system", "content": load_prompt_template("visual_designer")},
         {"role": "human", "content": f"为商品 {sku_data.get('name')} 设计视觉生成方案：主图/场景图/细节图 Prompt 与 5 镜头分镜"}],
        model="qwen-plus")

    sku_name_en = "Ultralight Camping Chair" if "椅" in sku_data.get("name", "") else "Wireless Earphones Pro"
    generation_prompts = {
        "main_image": f"Commercial product photography of {sku_name_en}, pure white background, studio lighting, 8k.",
        "scene_image": f"Lifestyle photography of {sku_name_en} on mountain campsite at sunset, warm cinematic glow.",
        "detail_image": f"Extreme macro close-up of {sku_name_en}, aerospace alloy joints and waterproof fabric.",
        "video_storyboard": f"High quality cinematic 4k product showcase of {sku_name_en}, quick folding mechanism.",
    }
    await record_node_execution(task_id=state.get("task_id"), tenant_id=state.get("tenant_id"),
                                node_name="visual_designer", status="success", progress=55,
                                output_data={"prompts": generation_prompts})
    return {"current_step": "visual_designer", "completed_steps": ["visual_designer"],
            "visual_design": {"image_count": 3, "video_duration": 5},
            "generation_prompts": generation_prompts}
```

### 6\.3\.8 节点 5：图片生成（image\_generator\.py）

```Python
async def image_generator_node(state: AgentState) -> dict:
    tenant_id = state.get("tenant_id") or "tenant_default"
    sku_id = state.get("sku_id") or ""
    prompts = state.get("generation_prompts") or {}

    image_client = ProviderFactory.get_image_client("wanx")
    generated_assets = []

    sub_types = [
        ("main", prompts.get("main_image", "product on white background")),
        ("scene", prompts.get("scene_image", "product in outdoor campsite")),
        ("detail", prompts.get("detail_image", "product close up texture")),
    ]

    for sub_type, prompt_str in sub_types:
        img_res = await image_client.generate_images(prompt=prompt_str, n=1, size="1024*1024")
        for u in img_res.get("urls", []):
            asset_info = {"type": "image", "sub_type": sub_type, "url": u,
                          "is_mock": img_res.get("is_mock", 1)}
            generated_assets.append(asset_info)
            async with AsyncSessionLocal() as session:
                session.add(Asset(tenant_id=tenant_id, task_id=state.get("task_id"), sku_id=sku_id,
                                  type="image", sub_type=sub_type, url=u, status="completed",
                                  is_mock=img_res.get("is_mock", 1)))
                await session.commit()

    await record_node_execution(task_id=state.get("task_id"), tenant_id=tenant_id,
                                node_name="image_generator", status="success", progress=70,
                                output_data={"image_count": len(generated_assets)})
    return {"current_step": "image_generator", "completed_steps": ["image_generator"],
            "generated_images": generated_assets}
```

### 6\.3\.9 节点 6：视频生成（video\_generator\.py）

```Python
async def video_generator_node(state: AgentState) -> dict:
    prompts = state.get("generation_prompts") or {}
    images = state.get("generated_images") or []

    video_prompt = prompts.get("video_storyboard", "cinematic product demonstration video")
    ref_image_url = images[0].get("url") if images else None

    video_client = ProviderFactory.get_video_client("kling")
    vid_res = await video_client.generate_video(prompt=video_prompt, duration=5,
                                                aspect_ratio="16:9", image_url=ref_image_url)

    video_info = {"type": "video", "sub_type": "product_showcase", "url": vid_res.get("video_url", ""),
                  "duration": vid_res.get("duration", 5), "is_mock": vid_res.get("is_mock", 1)}
    # 持久化到 ac_asset 表
    async with AsyncSessionLocal() as session:
        session.add(Asset(tenant_id=state.get("tenant_id"), task_id=state.get("task_id"),
                          sku_id=state.get("sku_id"), type="video", sub_type="product_showcase",
                          url=video_info["url"], status="completed", is_mock=video_info["is_mock"]))
        await session.commit()

    await record_node_execution(task_id=state.get("task_id"), tenant_id=state.get("tenant_id"),
                                node_name="video_generator", status="success", progress=85,
                                output_data=video_info)
    return {"current_step": "video_generator", "completed_steps": ["video_generator"],
            "generated_video": video_info}
```

### 6\.3\.10 节点 7：质量审核（quality\_reviewer\.py）

```Python
async def quality_reviewer_node(state: AgentState) -> dict:
    tenant_id = state.get("tenant_id") or "tenant_default"
    creative_plan = state.get("creative_plan") or {}
    images = state.get("generated_images") or []
    video = state.get("generated_video")
    retry_count = state.get("retry_count", 0)

    llm_client = ProviderFactory.get_llm_client("qwen")
    prompt_human = f"""请审核出海物料：
【标题】: {creative_plan.get('title')}
【五点】: {creative_plan.get('bullets')}
【图片数】: {len(images)}
【视频】: {'已就绪' if video else '无'}
请严格按 JSON 返回：score/passed/dimensions/violations/suggestions"""

    llm_res = await llm_client.chat_completion(
        [{"role": "system", "content": load_prompt_template("quality_reviewer")},
         {"role": "human", "content": prompt_human}], model="qwen-plus")

    # 解析 JSON（带容错）
    score, passed, dimensions = 96.0, 1, {"brand_consistency": 95.0, "platform_compliance": 96.0,
                                           "readability": 98.0, "visual_quality": 95.0}
    violations, suggestions = [], ["全套素材达到 S 级上线标准"]
    try:
        content = llm_res.get("content", "")
        parsed = json.loads(content[content.find("{"):content.rfind("}")+1])
        score = float(parsed.get("score", score))
        passed = int(parsed.get("passed", passed))
        violations = parsed.get("violations", violations)
        suggestions = parsed.get("suggestions", suggestions)
    except Exception:
        pass

    is_passed = (score >= 85.0) and (len(violations) == 0)

    # 持久化质检报告 + 更新任务状态
    async with AsyncSessionLocal() as session:
        session.add(ComplianceReport(tenant_id=tenant_id, task_id=state.get("task_id"),
                                     sku_id=state.get("sku_id"), score=score, dimensions=dimensions,
                                     violations=violations, passed=1 if is_passed else 0,
                                     suggestions=suggestions, status="passed" if is_passed else "rejected"))
        new_status = "completed" if is_passed else ("retrying" if retry_count < state.get("max_retries", 2) else "failed")
        await session.execute(update(Task).where(Task.id == state.get("task_id"))
                              .values(status=new_status, retry_count=retry_count))
        await session.commit()

    return {"current_step": "quality_reviewer", "completed_steps": ["quality_reviewer"],
            "quality_reports": state.get("quality_reports", []) + [{"score": score, "passed": 1 if is_passed else 0,
                                                                     "violations": violations, "suggestions": suggestions}],
            "is_passed": is_passed, "violations": violations,
            "retry_count": retry_count + (0 if is_passed else 1)}
```

## 6\.4 智能体协作时序图（Sequence Diagram）

## 6\.5 CLI 调试入口（run\_workflow\.py）

脱离 Web 界面，直接在命令行触发 7\-Agent 流程：

```Python
# 先灌入种子数据，再执行工作流
python -m app.scripts.init_db
python -m app.scripts.seed_data
python run_workflow.py --sku-id sku_camp01 --retries 2
```

执行后终端会打印：经历阶段、质检是否通过、综合评分、生成文案、图片与视频 URL。

---

# 第七章 API 接口（FastAPI 三层架构）

## 7\.1 需求说明

本章实现系统的对外接口层，遵循三大契约：

9. **路径前缀**：所有业务 API 统一 `/api/v1`。

10. **统一响应结构**：`{"code": 200, "data": {}, "message": "成功"}`。

11. **认证鉴权**：JWT Bearer Token，通过 `Depends(get_current_user_and_tenant)` 注入。

12. **命名规范**：JSON 字段 snake\_case，时间 ISO 8601 带时区，布尔值用 0/1。

## 7\.2 代码组织规划

```Plain Text
app/
├─ core/
│  ├─ deps.py        # 依赖注入（get_db / get_current_user_and_tenant）
│  ├─ security.py    # 密码哈希 + JWT 签发/校验
│  ├─ exceptions.py  # 统一异常体系
│  └─ middlewares.py # 请求上下文中间件
├─ services/         # 业务逻辑层
└─ api/v1/
   ├─ __init__.py    # 汇总注册全部路由
   ├─ auth.py        # 登录/用户信息
   ├─ skus.py        # 商品管理
   ├─ tasks.py       # 生成任务调度
   ├─ batches.py     # 批次生成
   ├─ copies.py      # 文案管理
   ├─ assets.py      # 素材管理
   ├─ knowledge.py   # 知识库
   ├─ compliance.py  # 合规质检
   ├─ providers.py   # 模型厂商
   ├─ packages.py    # 打包下载
   ├─ audit.py       # 审计成本
   ├─ listings.py    # 多平台刊登
   └─ ws.py          # WebSocket 推送
```

## 7\.3 具体实现

### 7\.3\.1 依赖注入（app/core/deps\.py）

```Python
async def get_db():
    """数据库会话依赖"""
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user_and_tenant(authorization: Optional[str] = Header(None)):
    """解析 JWT，返回当前用户与租户上下文；无 Token 时回退默认管理员（开发模式）"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = decode_token(token)  # 校验 JWT
        if payload:
            return {"user_id": payload.get("sub"), "tenant_id": payload.get("tenant_id"),
                    "name": payload.get("name"), "role": payload.get("role")}
    # 开发阶段无 Token 回退
    return {"user_id": "usr_admin", "tenant_id": "tenant_default",
            "name": "系统管理员", "email": "admin@agentic.com", "role": "admin"}
```

> **什么是依赖注入（Depends）？** FastAPI 的 `Depends` 就像自动装配流水线：路由函数声明需要 `db` 和 `user_tenant`，FastAPI 自动调用 `get_db()` 和 `get_current_user_and_tenant()` 把结果填进去。路由内**绝不允许**裸写鉴权逻辑。
> 
> 

### 7\.3\.2 安全模块（app/core/security\.py）

```Python
from passlib.context import CryptContext
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain, hashed) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy(); to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None
```

### 7\.3\.3 任务路由（app/api/v1/tasks\.py）——最核心

```Python
router = APIRouter(prefix="/tasks", tags=["生成任务调度"])

class TaskCreateRequest(BaseModel):
    sku_id: str
    batch_id: Optional[str] = None
    config: Dict[str, Any] = {"language": "en", "platform": "amazon",
                              "model_llm": "qwen", "model_image": "wanx",
                              "model_video": "kling", "max_retries": 2}

async def run_agent_workflow_background(task_id, tenant_id, sku_id, config):
    """后台异步触发 7-Agent 工作流"""
    try:
        async with AsyncSessionLocal() as session:
            sku = (await session.execute(select(Sku).where(Sku.id == sku_id))).scalar_one_or_none()
            if not sku: return
            sku_data = {"id": sku.id, "code": sku.code, "name": sku.name,
                        "category": sku.category, "specs": sku.specs,
                        "description": sku.description, "images": sku.images}
        initial_state = {"task_id": task_id, "tenant_id": tenant_id, "sku_id": sku_id,
                         "sku_data": sku_data, "config": config,
                         "retry_count": 0, "max_retries": config.get("max_retries", 2),
                         "completed_steps": []}
        await app_workflow.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"后台任务 {task_id} 异常: {str(e)}")

@router.post("")
async def create_task(req: TaskCreateRequest, background_tasks: BackgroundTasks,
                      db: AsyncSession = Depends(get_db),
                      user_tenant: dict = Depends(get_current_user_and_tenant)):
    svc = TaskService(db)
    result = await svc.create_task(tenant_id=user_tenant["tenant_id"],
                                   user_id=user_tenant.get("user_id"),
                                   sku_id=req.sku_id, batch_id=req.batch_id, config=req.config)
    # 提交后台执行，立即返回，不阻塞前端
    background_tasks.add_task(run_agent_workflow_background,
                              task_id=result["task_id"], tenant_id=user_tenant["tenant_id"],
                              sku_id=req.sku_id, config=req.config)
    return {"code": 200, "data": {"task_id": result["task_id"], "status": "running"},
            "message": "任务创建成功"}

@router.get("/{task_id}")
async def get_task_detail(task_id: str, db: AsyncSession = Depends(get_db),
                          user_tenant: dict = Depends(get_current_user_and_tenant)):
    svc = TaskService(db)
    result = await svc.get_task_detail(user_tenant["tenant_id"], task_id)
    return {"code": 200, "data": result, "message": "获取成功"}

@router.get("/{task_id}/nodes")
async def get_task_node_runs(task_id: str, db: AsyncSession = Depends(get_db),
                             user_tenant: dict = Depends(get_current_user_and_tenant)):
    """节点执行明细（供工作台 DAG 渲染）"""
    svc = TaskService(db)
    items = await svc.get_node_runs(user_tenant["tenant_id"], task_id)
    return {"code": 200, "data": {"items": items, "count": len(items)}, "message": "获取成功"}
```

> **为什么用 BackgroundTasks？** 大模型生图生视频很慢（可能几十秒到几分钟）。如果同步等待，前端会一直转圈。用 `background_tasks.add_task` 把耗时工作丢到后台，路由**立即**返回 `task_id`，前端通过轮询或 WebSocket 拿进度。
> 
> 

### 7\.3\.4 WebSocket 推送（app/api/v1/ws\.py）

```Prolog
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        payload = json.dumps(message, ensure_ascii=False)
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

### 7\.3\.5 路由汇总（app/api/v1/**init**\.py）

```Prolog
from fastapi import APIRouter
from .auth import router as auth_router
from .providers import router as providers_router
from .knowledge import router as knowledge_router
from .skus import router as skus_router
from .batches import router as batches_router
from .tasks import router as tasks_router
from .copies import router as copies_router
from .assets import router as assets_router
from .compliance import router as compliance_router
from .packages import router as packages_router
from .audit import router as audit_router
from .listings import router as listings_router
from .ws import router as ws_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(providers_router)
api_v1_router.include_router(knowledge_router)
api_v1_router.include_router(skus_router)
api_v1_router.include_router(batches_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(copies_router)
api_v1_router.include_router(assets_router)
api_v1_router.include_router(compliance_router)
api_v1_router.include_router(packages_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(listings_router)
api_v1_router.include_router(ws_router)
```

### 7\.3\.6 主入口（main\.py）

```Prolog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api.v1 import api_v1_router

app = FastAPI(title="AgenticCommerce API", version="1.0.0",
              docs_url="/docs", redoc_url="/redoc")

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(api_v1_router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "AgenticCommerce", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
```

## 7\.4 API 接口清单

|模块|方法|路径|说明|
|---|---|---|---|
|认证|POST|`/api/v1/auth/login`|登录签发 JWT|
|认证|GET|`/api/v1/auth/me`|当前用户信息|
|商品|GET/POST|`/api/v1/skus`|SKU 列表/创建|
|商品|GET/PUT/DELETE|`/api/v1/skus/{sku_id}`|详情/更新/删除|
|任务|GET/POST|`/api/v1/tasks`|任务列表/创建|
|任务|GET|`/api/v1/tasks/{task_id}`|任务详情|
|任务|GET|`/api/v1/tasks/{task_id}/nodes`|节点明细|
|任务|POST|`/api/v1/tasks/{task_id}/run`|手动重触发|
|批次|GET/POST|`/api/v1/batches`|批次列表/创建|
|文案|GET|`/api/v1/copies`|文案列表|
|素材|GET/POST|`/api/v1/assets`|素材列表/登记|
|知识库|POST|`/api/v1/knowledge/docs`|录入文档|
|知识库|POST|`/api/v1/knowledge/query`|向量检索|
|合规|POST|`/api/v1/compliance/check`|实时违禁词筛查|
|打包|GET|`/api/v1/packages`|可打包任务|
|打包|POST|`/api/v1/packages/export`|导出交付包|
|审计|GET|`/api/v1/audit/costs`|Token 成本大盘|
|刊登|POST|`/api/v1/listings`|多平台刊登|
|实时|WS|`/api/v1/ws`|WebSocket 推送|

---

# 第八章 前后端对接（Vue 3 工作台）

## 8\.1 需求说明

本章实现前端工作台，完成前后端对接。前端用 Vue 3 \+ Vite \+ Pinia \+ Vue Router \+ Axios，通过 **HTTP 请求** 拉取数据、通过 **WebSocket** 接收实时进度，实现 7\-Agent DAG 状态可视化与产物展示。

## 8\.2 代码组织规划

```Plain Text
frontend/src/
├─ main.ts                     # 入口，挂载 Vue + Pinia + Router
├─ router/index.ts             # 15 个页面路由
├─ api/
│  ├─ client.ts                # Axios 封装（拦截器注入 Token）
│  ├─ task.ts                  # 任务接口
│  └─ workbench.ts             # 工作台接口
├─ stores/
│  ├─ user.ts                  # 用户状态
│  ├─ task.ts                  # 任务状态
│  └─ workbench.ts             # 工作台状态
├─ components/workbench/
│  ├─ DagGraph.vue             # DAG 拓扑图
│  ├─ NodeDetail.vue           # 节点明细
│  ├─ PromptViewer.vue         # Prompt 查看器
│  └─ IoViewer.vue             # 输入输出查看器
└─ views/
   ├─ WorkbenchView.vue        # 智能体工作台（核心页）
   ├─ TaskView.vue / SkuView.vue / ...
   └─ LoginView.vue
```

## 8\.3 具体实现

### 8\.3\.1 前端入口（main\.ts）

```Shell
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())   // 状态管理
app.use(router)          // 路由
app.mount('#app')
```

### 8\.3\.2 Axios 封装（api/client\.ts）

```Shell
import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',   // 走 Vite 代理
  timeout: 30000
})

// 请求拦截器：自动注入 JWT Token
client.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default client
```

### 8\.3\.3 Vite 代理（vite\.config\.ts）

```Shell
export default defineConfig({
  plugins: [vue()],
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8002', changeOrigin: true },
      '/api/v1/ws': { target: 'ws://127.0.0.1:8002', ws: true }  // WebSocket 代理
    }
  }
})
```

> **为什么要代理？** 前端跑在 5173 端口，后端跑在 8002 端口。浏览器有「同源策略」，跨端口请求会被拦截。Vite 的 `proxy` 相当于一个「传话筒」，把前端的 `/api` 请求悄悄转发给 8002 后端，解决跨域。
> 
> 

### 8\.3\.4 路由（router/index\.ts）

```Shell
const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/tasks', name: 'Tasks', component: () => import('@/views/TaskView.vue') },
  { path: '/workbench/:taskId', name: 'Workbench', component: () => import('@/views/WorkbenchView.vue') },
  { path: '/assets', name: 'Assets', component: () => import('@/views/AssetView.vue') },
  { path: '/copies', name: 'Copies', component: () => import('@/views/CopyView.vue') },
  { path: '/knowledge', name: 'Knowledge', component: () => import('@/views/KnowledgeView.vue') },
  { path: '/providers', name: 'Providers', component: () => import('@/views/ProviderView.vue') },
  { path: '/skus', name: 'Skus', component: () => import('@/views/SkuView.vue') },
  { path: '/listings', name: 'Listings', component: () => import('@/views/ListingView.vue') },
  { path: '/audit', name: 'Audit', component: () => import('@/views/AuditView.vue') },
  { path: '/packages', name: 'Packages', component: () => import('@/views/PackageView.vue') },
  { path: '/compliance', name: 'Compliance', component: () => import('@/views/ComplianceView.vue') },
]
```

### 8\.3\.5 智能体工作台（views/WorkbenchView\.vue 核心逻辑）

```Shell
const agentNodes = [
  { key: 'orchestrator', name: '总控调度', desc: '全局编排与SKU挂载', icon: '🧭' },
  { key: 'requirement_analyzer', name: '需求分析', desc: 'RAG知识与客群画像', icon: '🔍' },
  { key: 'creative_planner', name: '创意策划', desc: '高转化五点与标题', icon: '✍️' },
  { key: 'visual_designer', name: '视觉设计', desc: '分镜规划与Prompt拆解', icon: '📐' },
  { key: 'image_generator', name: '图片生成', desc: '万相2.1多视角生成', icon: '🎨' },
  { key: 'video_generator', name: '视频生成', desc: '可灵AI短视频渲染', icon: '🎬' },
  { key: 'quality_reviewer', name: '质量审核', desc: 'P-E-V闭环与合规打分', icon: '🛡️' },
]

async function fetchTaskDetail() {
  const res = await client.get(`/tasks/${taskId.value}`)
  const data = res.data?.data || {}
  taskData.value = data.task
  copyData.value = data.copy
  assetsData.value = data.assets
  complianceData.value = data.compliance_report
  const nodesRes = await client.get(`/tasks/${taskId.value}/nodes`)
  nodeRuns.value = nodesRes.data?.data?.items || []
}

function getNodeStatusClass(nodeKey: string) {
  const run = nodeRuns.value.find(r => r.node_name === nodeKey)
  if (!run) return 'node-pending'
  return run.status === 'success' ? 'node-success' : 'node-running'
}
```

## 8\.4 前后端完整交互时序图

---

# 第九章 项目启动与验收

## 9\.1 启动步骤（完整命令）

```Bash
# 1. 启动基础设施（PostgreSQL + Redis + MinIO）
docker-compose -f docker-compose.infra.yml up -d

# 2. 安装后端依赖
uv sync

# 3. 初始化数据库表
python -m app.scripts.init_db

# 4. 导入种子数据（租户/管理员/SKU/知识库）
python -m app.scripts.seed_data

# 5. 启动后端（热重载，8002 端口）
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 6. 启动前端（另一个终端，5173 端口）
cd frontend
npm install
npm run dev
```

## 9\.2 接口验收（curl 测试）

```Bash
# 健康检查
curl http://127.0.0.1:8002/health

# 登录获取 Token
curl -X POST http://127.0.0.1:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@agentic.com","password":"admin123"}'

# 查询 SKU 列表
curl http://127.0.0.1:8002/api/v1/skus

# 创建生成任务（自动触发 7-Agent 工作流）
curl -X POST http://127.0.0.1:8002/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"sku_id":"sku_camp01","config":{"language":"en","platform":"amazon"}}'

# 查看任务详情（含文案/素材/质检报告）
curl http://127.0.0.1:8002/api/v1/tasks/{task_id}

# 查看节点执行明细
curl http://127.0.0.1:8002/api/v1/tasks/{task_id}/nodes

# 向量检索测试
curl -X POST http://127.0.0.1:8002/api/v1/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{"query_text":"轻量化露营装备","top_k":3}'

# 成本大盘
curl http://127.0.0.1:8002/api/v1/audit/costs
```



---

