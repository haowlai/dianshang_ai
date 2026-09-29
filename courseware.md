# 智能跨境电商融合平台 (AgenticCommerce) 核心实战课件
（作者：尚硅谷研究院）
版本：V3.0 深度商业落地版（含核心技术栈扫盲与实操）

## 第一章 项目概述与技术栈全景图

### 1.1 项目背景
AgenticCommerce 是一个基于 **多智能体（Multi-Agent）架构** 的跨境电商智能内容生成平台。传统的跨境电商运营面临多语种翻译难、商品拍摄成本高、视频剪辑周期长等痛点。本项目旨在通过 AI 自动化接管从“受众分析 -> 文案生成 -> 图像生成 -> 视频生成 -> 合规审核”的完整工作流。用户只需输入商品基础信息，即可一键生成全套高转化营销物料。

### 1.2 核心技术栈与官方资源指南
为了让同学们在完成项目的同时，掌握行业最前沿、最具竞争力的技术储备，本项目严格采用当前一线大厂的主流技术选型。

| 技术分类 | 技术名称 | 官网与参考文档链接 | 核心应用场景说明 |
| :--- | :--- | :--- | :--- |
| **基础语言** | Python 3.12 | [python.org](https://www.python.org/) | 采用最新的 Python 3.12，支持高级异步特性与类型提示。 |
| **依赖管理** | uv | [astral.sh/uv](https://github.com/astral-sh/uv) | 替代传统 pip 的超高速 Rust 编写的 Python 包管理器。 |
| **Web 框架** | FastAPI | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) | 构建极速、高并发的全异步 RESTful API 后端服务。 |
| **ORM 框架** | SQLAlchemy 2.0 | [sqlalchemy.org](https://www.sqlalchemy.org/) | 业界标准的数据库对象关系映射工具，结合 `asyncpg` 实现异步读写。 |
| **关系型数据库** | PostgreSQL 16 | [postgresql.org](https://www.postgresql.org/) | 世界最先进的开源关系型数据库，本项目用于存储商品与任务元数据。 |
| **内存缓存** | Redis 7 | [redis.io](https://redis.io/) | 高性能 KV 内存数据库，用于高频任务状态轮询与热点数据缓存。 |
| **对象存储** | MinIO | [min.io](https://min.io/) | AWS S3 兼容的私有化对象存储，专用于存放 AI 生成的超大图片和视频资产。 |
| **智能体框架** | LangGraph | [langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/) | 构建复杂、支持循环与状态记忆的多智能体（Multi-Agent）图计算工作流。 |
| **云端 AI 模型** | 阿里云百炼 (DashScope) | [help.aliyun.com/zh/model-studio](https://help.aliyun.com/zh/model-studio) | 接入通义千问大模型、通义万相 3.0 图像与视频大模型原生 API。 |

---

## 第二章 核心架构设计与工作流解析

### 2.1 整体技术架构 (Architecture Diagram)
本项目采用严格的**前后端分离**与**三层架构**设计，后端通过 HTTP API 驱动大模型生成，通过对象存储管理多模态文件。

```mermaid
architecture-beta
    group frontend(Frontend)
    service vue(Vue 3 + Vite) in frontend

    group backend(Backend FastAPI)
    service api(API Routers - 薄控制器) in backend
    service svc(Services - 核心业务) in backend
    service agent(LangGraph Core - 图引擎) in backend
    
    group data(Infrastructure)
    service db(PostgreSQL) in data
    service cache(Redis) in data
    service oss(MinIO) in data

    group cloud(Cloud AI APIs)
    service llm(Qwen LLM) in cloud
    service img(Qwen Image 3.0) in cloud
    service vid(Wan 3.0 Video) in cloud

    vue:R --> L:api
    api:B --> T:svc
    svc:B --> T:agent
    svc:R --> L:db
    svc:L --> R:cache
    svc:B --> T:oss
    agent:R --> L:llm
    agent:R --> L:img
    agent:R --> L:vid
```

### 2.2 多智能体核心业务图 (LangGraph State Machine)
有别于传统线性的代码调用，LangGraph 将业务转化为有状态流转的节点图（Node Graph）。当某个节点失败时，可以自动流转回上一个节点进行自我纠错（Self-Correction）。

```mermaid
graph TD
    A[用户触发创建商品生成任务] --> B(进入 LangGraph 初始化状态)
    
    subgraph 多智能体协作链路 (7-Agent Workflow)
        B -->|步骤 1| C(需求分析师 Agent)
        C -->|提取受众与卖点| D(创意策划师 Agent)
        D -->|撰写出海爆款文案| E(分镜设计师 Agent)
        E -->|拆解视频镜头| F(图像生成 Agent - 万相3.0)
        E -->|生成视频 Prompt| G(视频生成 Agent - 万相3.0)
        F --> H(合规与质检审查 Agent)
        G --> H
        H -->|发现违禁词| C
    end
    
    H -->|审核通过, 满分!| I[最终多模态资产落库保存]
```

### 2.3 数据库实体关系 (ER Diagram)
基于 PostgreSQL 构建的核心电商表结构如下：

```mermaid
erDiagram
    SKU ||--o{ TASK : triggers
    SKU ||--o{ ASSET : owns
    TASK ||--o{ ASSET : outputs_multimodal_files
    TASK ||--o{ COPY : outputs_text_copy

    SKU {
        string id PK "商品唯一ID"
        string code "商品编码"
        string name "商品名称"
        jsonb specs "商品规格与属性字典"
    }
    TASK {
        string id PK "任务调度ID"
        string sku_id FK "关联的SKU"
        string status "运行状态(running/completed/failed)"
        string current_node "当前所在Agent节点"
    }
    ASSET {
        string id PK "资产唯一ID"
        string task_id FK "来源任务"
        string type "类型(image/video)"
        string url "MinIO存储桶直链"
    }
    COPY {
        string id PK "文案ID"
        string task_id FK "来源任务"
        string language "文案语言(en/ja/es)"
        text description "生成的产品详情"
    }
```

---

## 第三章 基础设施与开发环境搭建

### 3.1 极速环境配置：uv 工具链使用
传统 Python 开发者使用 `pip` 与 `virtualenv`，速度慢且容易发生依赖冲突。本项目引入当今最火的 `uv` 包管理器。

**安装 uv：**
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**使用 uv 创建项目并安装依赖：**
```bash
# 瞬间创建虚拟环境
uv venv
# 激活环境
.venv\Scripts\activate
# 秒级安装全家桶
uv pip install "fastapi[standard]" sqlalchemy asyncpg httpx langgraph pydantic-settings
```

### 3.2 容器化部署：Docker Compose 实战
为了在本地开发环境中避免安装复杂的数据库软件，我们使用 Docker 进行一键容器化部署。
> **官网与说明**：[docker.com](https://www.docker.com/)。Docker 允许我们将系统连同软件打包成一个隔离的“集装箱”（容器），保证在任何电脑上都能运行。

**创建 `docker-compose.yaml`**：
```yaml
version: '3.8'

services:
  # 1. PostgreSQL 关系型数据库
  postgres:
    image: postgres:16-alpine
    container_name: agentic_postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: agentic_commerce
    ports:
      - "5434:5432" # 映射到物理机的 5434，防止与本地原有 DB 冲突
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

  # 2. Redis 内存缓存
  redis:
    image: redis:7-alpine
    container_name: agentic_redis
    ports:
      - "6381:6379"
    restart: always

  # 3. MinIO 对象存储系统
  minio:
    image: minio/minio:latest
    container_name: agentic_minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9011"
    ports:
      - "9010:9000" # S3 API 通信端口
      - "9011:9011" # 网页控制台端口
    volumes:
      - miniodata:/data
    restart: always

volumes:
  pgdata:
  miniodata:
```
**一键启动命令：** `docker compose up -d`

---

## 第四章 从 0 到 1 核心代码实战

本章将带你手把手实现后端的完整闭环。标准的项目结构如下：
```text
AgenticCommerce/
├── app/  
│   ├── api/v1/            # Router 层：HTTP 接口入站口
│   ├── services/          # Service 层：业务逻辑处理
│   ├── models/            # Model 层：数据库表映射
│   ├── clients/           # 第三方客户端（如大模型调用工厂）
│   ├── agent/             # LangGraph 核心工作流引擎
│   └── conf/              # 全局配置解析 (读取 .env)
├── .env                   # 核心密钥配置
└── main.py                # FastAPI 启动入口
```

### 4.1 全局配置管理 (Pydantic Settings)
传统的 `os.environ.get()` 容易拼写错误且没有类型检查。我们使用 `pydantic-settings` 自动读取 `.env` 文件。

**1. 配置文件 `.env`**
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5434
# 阿里云百炼 API KEY（须注册获取）
DASHSCOPE_API_KEY=sk-your-real-key-here
```

**2. 配置类 `app/conf/config.py`**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    POSTGRES_PORT: int = 5434
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DASHSCOPE_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@127.0.0.1:{self.POSTGRES_PORT}/agentic_commerce"

settings = Settings()
```

### 4.2 接入阿里云万相原生 API (ProviderFactory)
我们采用“工厂设计模式”（Factory Pattern）来封装对不同 AI 模型的调用，使得外部代码不需要关心底层是用 HTTP 还是 SDK。

**`app/clients/provider_factory.py`**
```python
import httpx
from typing import Dict, Any
from app.conf.config import settings

class WanxImageClient:
    """封装通义万相 Qwen-Image-3.0-Pro 接口"""
    # 官方生图 Endpoint
    SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    async def generate_images(self, prompt: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        # 严格按照阿里云官方要求的 Payload 结构
        payload = {
            "model": "qwen-image-3.0-pro",
            "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
            "parameters": {"prompt_extend": True}
        }
        # 异步发起 HTTP 请求，绝不阻塞主线程
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.SUBMIT_URL, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                img_url = data["output"]["choices"][0]["message"]["content"][0]["image"]
                return {"urls": [img_url], "status": "success"}
            return {"status": "failed", "error": resp.text}

class ProviderFactory:
    @staticmethod
    def get_image_client() -> WanxImageClient:
        return WanxImageClient()
```

### 4.3 数据库 ORM (SQLAlchemy 2.0)
使用 SQLAlchemy 将面向对象的类自动映射为数据库的表结构。

**`app/models/sku.py`**
```python
import uuid
from sqlalchemy import String, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Sku(Base):
    __tablename__ = "ac_sku"
    # 定义表字段
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    specs: Mapped[dict] = mapped_column(JSON, default=dict)
```

### 4.4 核心业务分层：Service 层与 Router 层
**三层架构规范**要求：Router 层仅仅作为接待员，负责参数校验；Service 层作为后厨，负责真正的查数据库与计算业务。

**1. Service 层：`app/services/task_service.py`**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task

class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, sku_id: str) -> str:
        # 生成新任务记录写入数据库
        new_task = Task(sku_id=sku_id, status="running")
        self.session.add(new_task)
        await self.session.commit()
        return new_task.id
```

**2. Router 层：`app/api/v1/tasks.py`**
```python
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.services.task_service import TaskService
from app.agent.graph import app_workflow

router = APIRouter(prefix="/tasks", tags=["任务管理"])

# 定义一个后台运行的协程任务
async def run_workflow_bg(task_id: str, sku_name: str):
    state = {"task_id": task_id, "sku_name": sku_name}
    # 触发 LangGraph 智能体网络启动
    await app_workflow.ainvoke(state)

@router.post("/create")
async def create_new_task(sku_id: str, bg_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # 1. 实例化 Service，执行数据库操作
    svc = TaskService(db)
    task_id = await svc.create_task(sku_id)
    
    # 2. 将耗时的 AI 生成任务丢入 BackgroundTasks 后台队列
    bg_tasks.add_task(run_workflow_bg, task_id, "豪华高背露营椅")
    
    # 3. 立即响应前端，不让用户界面卡死转圈
    return {"code": 200, "data": {"task_id": task_id}, "msg": "任务创建成功并已后台启动"}
```

### 4.5 项目主入口 (main.py)
最后，将所有组件挂载到 FastAPI 引擎上，提供 Web 服务能力。
```python
import uvicorn
from fastapi import FastAPI
from app.api.v1 import tasks

app = FastAPI(title="AgenticCommerce 核心 API")

# 注册子路由
app.include_router(tasks.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "智能跨境电商系统已就绪！"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
```

## 第五章 总结与项目验收
通过以上章节，我们完整落地了一个企业级的 AI 应用系统。不仅打通了底层数据流（Postgres + MinIO），实现了严格规范的工程化架构（MVC 三层结构），更是深度集成了最新的前沿 AI 技术（LangGraph + 通义万相多模态生成）。掌握了这套技术体系，就等于掌握了开发任何复杂 AI SaaS 系统的“武林秘籍”！
