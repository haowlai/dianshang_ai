import os

courseware_path = r'D:\wl-temp\资料\电商项目\AgenticCommerce课件.md'
instructor_path = r'D:\wl-temp\资料\电商项目\AgenticCommerce教师保姆级讲义.md'

os.makedirs(os.path.dirname(courseware_path), exist_ok=True)

courseware_content = """# 智能跨境电商融合平台 (AgenticCommerce) 核心实战课件
（作者：尚硅谷研究院）
版本：V4.0 商业级开源完整版

## 第一章 项目概述与商业价值
### 1.1 项目背景
AgenticCommerce 是一款面向跨境电商出海场景的 **多智能体 (Multi-Agent) 协同生成平台**。在亚马逊、TikTok 等电商平台上，卖家面临商品翻译难、请外籍模特拍摄贵、带货短视频剪辑周期长等痛点。本项目旨在通过大语言模型（LLM）与多模态模型（图像、视频大模型），全自动接管从“受众分析 -> 创意策划 -> 视觉设计 -> 合规审核”的完整工作流。

### 1.2 为什么是 LangGraph？
传统的单体大模型调用（如 LangChain 的普通 Chain）是单向的流水线，一旦某个环节（如生图失败）出现问题，整个链路就会崩溃。我们采用了当今业内最顶尖的图计算框架 **LangGraph**，它允许系统构建状态机（State Machine），让 Agent 在错误时自动回退、自我纠错重试，极大地提高了生成质量和系统的鲁棒性。

---

## 第二章 核心技术栈与官方资源索引

为确保同学们接触的是一线大厂目前正在使用的技术，本项目涉及的技术栈全家桶如下：

| 技术层 | 技术名称 | 核心作用与场景 | 官方网站/参考文档 |
| :--- | :--- | :--- | :--- |
| **基础语言** | Python 3.12 | 采用最新版，支持高级异步特性、类型提示。 | [python.org](https://www.python.org/) |
| **包管理器** | uv | 极速 Rust 编写的 Python 依赖管理器，秒级解析。 | [astral.sh/uv](https://docs.astral.sh/uv/) |
| **后端框架** | FastAPI | 高性能异步 Web 框架，处理 HTTP 请求的入口。 | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) |
| **ORM框架** | SQLAlchemy 2.0 | 对象关系映射，操作数据库的利器。 | [sqlalchemy.org](https://www.sqlalchemy.org/) |
| **异步驱动** | asyncpg | 配合 SQLAlchemy 实现对 Postgres 的全异步读写。 | [magicstack.github.io/asyncpg](https://magicstack.github.io/asyncpg/) |
| **核心数据库** | PostgreSQL 16 | 世界最先进的开源关系型数据库，存储商品、任务数据。 | [postgresql.org](https://www.postgresql.org/) |
| **内存缓存** | Redis 7.x | 内存级 KV 数据库，用于加速高频状态读取与限流。 | [redis.io](https://redis.io/) |
| **对象存储** | MinIO | 兼容 S3 的私有化网盘，存储海量生成的图像、视频文件。 | [min.io](https://min.io/) |
| **智能体框架** | LangGraph | 编排多 Agent 的状态图结构流转与自我纠错引擎。 | [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/) |
| **云端AI能力** | 阿里云 DashScope | 接入通义千问 LLM、通义万相（图像/视频）生成大模型。 | [help.aliyun.com/zh/model-studio](https://help.aliyun.com/zh/model-studio/) |

---

## 第三章 系统核心架构与工作流程图

### 3.1 整体技术架构拓扑 (Mermaid)
本系统采用标准的前后端分离，配合后台异步 Agent 调度队列：

```mermaid
architecture-beta
    group frontend(前端应用层)
    service vue(Vue3 Dashboard) in frontend

    group backend(后端服务层 - FastAPI)
    service api(Router接口层) in backend
    service svc(Service业务层) in backend
    service agent(LangGraph引擎) in backend
    
    group data(本地基础设施层)
    service db(PostgreSQL) in data
    service cache(Redis) in data
    service oss(MinIO) in data

    group cloud(云端模型层)
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

### 3.2 7-Agent 多智能体协同状态流转图
用户只管在前端提交商品信息，后端队列接管后，会在 LangGraph 图中自动走完以下链路，若合规审查发现违禁词，将自动返回策划阶段重做：

```mermaid
stateDiagram-v2
    [*] --> 需求分析师: 接收SKU
    需求分析师 --> 创意策划师: 目标人群画像
    创意策划师 --> 分镜设计师: 爆款文案提纲
    分镜设计师 --> 图像生成Agent: 视觉提示词
    分镜设计师 --> 视频生成Agent: 动态镜头指令
    图像生成Agent --> 合规质检审查
    视频生成Agent --> 合规质检审查
    合规质检审查 --> 创意策划师: [打回] 发现亚马逊违禁词
    合规质检审查 --> [*]: [通过] 多模态资产落库保存
```

### 3.3 数据库实体与 ER 模型
核心表围绕“商品(SKU)”、“生成任务(TASK)”及“生成资产(ASSET)”建立：

```mermaid
erDiagram
    TENANT ||--o{ SKU : owns
    SKU ||--o{ TASK : triggers
    TASK ||--o{ ASSET : outputs
    TASK ||--o{ COPY : outputs

    SKU {
        string id PK "商品ID"
        string code "商品编码"
        string name "商品名称"
        jsonb specs "商品规格字典"
    }
    TASK {
        string id PK "任务ID"
        string sku_id FK "关联的商品"
        string status "状态(running/done/failed)"
    }
    ASSET {
        string id PK "资产ID"
        string task_id FK "来源任务"
        string type "类型(image/video)"
        string url "MinIO存储链"
    }
    COPY {
        string id PK "文案ID"
        string task_id FK "来源任务"
        string language "文案语言(en/ja)"
        text description "正文详情"
    }
```

---

## 第四章 极速环境搭建与 Docker 基础设施部署

### 4.1 项目初始化与 uv 极速包管理
我们摒弃了传统的 `pip`，改用当今最先进的 `uv` 工具进行依赖管理。

1. **创建项目与虚拟环境：**
```bash
# 初始化项目
mkdir AgenticCommerce && cd AgenticCommerce
uv init
# 此时会生成 pyproject.toml 文件
```

2. **添加核心依赖（注意：此处使用 uv add 语法将其写入 toml）：**
```bash
uv add "fastapi[standard]" sqlalchemy asyncpg httpx "langchain>=0.2.0" langgraph pydantic-settings python-multipart
```

### 4.2 容器化基石：Docker Compose 一键起飞
为解决开发环境软件安装带来的各种报错（端口占用、系统不兼容），必须使用 Docker 技术。
在项目根目录下新建 `docker/docker-compose.yaml`：

```yaml
version: '3.8'

services:
  # 1. PostgreSQL - 关系型主数据库
  postgres:
    image: postgres:16-alpine
    container_name: agentic_postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: agentic_commerce
    ports:
      - "5434:5432" # 避开默认 5432，防止端口冲突
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: always

  # 2. Redis - 高性能内存缓存
  redis:
    image: redis:7-alpine
    container_name: agentic_redis
    ports:
      - "6381:6379"
    restart: always

  # 3. MinIO - 私有化对象存储集群
  minio:
    image: minio/minio:latest
    container_name: agentic_minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9011"
    ports:
      - "9010:9000" # API 端口
      - "9011:9011" # 控制台端口
    volumes:
      - miniodata:/data
    restart: always

volumes:
  pgdata:
  miniodata:
```

**启动命令：**
```bash
cd docker
docker compose up -d
```
启动后，你可以通过 `http://localhost:9011` (账号密码 minioadmin) 登录查看你的对象存储！

---

## 第五章 核心业务逻辑实现 (代码级详解)

项目遵循标准的 `Router -> Service -> Model` 三层架构。

### 5.1 配置管理 (pydantic-settings)
新建 `app/conf/config.py`，用现代化的 Pydantic 解析 `.env`：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_PORT: int = 8002
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5434
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "agentic_commerce"
    DASHSCOPE_API_KEY: str = "" # 阿里云百炼申请

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
```

### 5.2 ORM 数据模型 (SQLAlchemy 2.0)
使用 SQLAlchemy 将面向对象的类映射为数据表。
新建 `app/models/sku.py`：

```python
import uuid
from sqlalchemy import String, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Sku(Base):
    \"\"\"商品数据表映射实体\"\"\"
    __tablename__ = "ac_sku"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    specs: Mapped[dict] = mapped_column(JSON, default=dict)
```

### 5.3 阿里云大模型接入工厂 (ProviderFactory)
我们使用 Factory 模式，保证未来可灵活替换其他模型厂商。
新建 `app/clients/provider_factory.py`：

```python
import httpx
from typing import Dict, Any
from app.conf.config import settings

class WanxImageClient:
    \"\"\"通义万相 Qwen-Image-3.0-Pro 异步生图客户端\"\"\"
    SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    async def generate_images(self, prompt: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        # 组装官网要求的 Payload
        payload = {
            "model": "qwen-image-3.0-pro",
            "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
            "parameters": {"prompt_extend": True}
        }
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

### 5.4 业务服务层 (Service)
Service 层专门负责复杂的数据库操作与计算。
新建 `app/services/task_service.py`：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task

class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, sku_id: str) -> str:
        \"\"\"核心业务：创建任务并落库\"\"\"
        new_task = Task(sku_id=sku_id, status="running")
        self.session.add(new_task)
        await self.session.commit()
        return new_task.id
```

### 5.5 控制器与入口层 (Router & main.py)
Router 负责 HTTP 参数校验并路由给 Service。
新建 `app/api/v1/tasks.py`：

```python
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.services.task_service import TaskService
# 假设 app_workflow 已经在 app/agent/graph.py 中定义好
from app.agent.graph import app_workflow

router = APIRouter(prefix="/tasks", tags=["任务调度"])

async def run_workflow_bg(task_id: str):
    \"\"\"后台任务，不阻塞前端 HTTP 响应\"\"\"
    state = {"task_id": task_id, "sku_data": {"name": "保温杯"}}
    await app_workflow.ainvoke(state)

@router.post("/create")
async def create_new_task(sku_id: str, bg_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # 1. 实例化 Service 并调用
    svc = TaskService(db)
    task_id = await svc.create_task(sku_id)
    
    # 2. 丢入后台执行 LangGraph 大模型生成
    bg_tasks.add_task(run_workflow_bg, task_id)
    
    # 3. 立即返回
    return {"code": 200, "data": {"task_id": task_id}, "msg": "任务创建成功"}
```

最后组装整个系统，新建 `main.py`：
```python
import uvicorn
from fastapi import FastAPI
from app.api.v1 import tasks

app = FastAPI(title="AgenticCommerce 核心服务")

app.include_router(tasks.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
```

## 第六章 总结与答疑
这套系统代码规范极其严苛，完全参照了一线大型互联网企业（阿里、字节）的规范：
1. **彻底解耦**：数据库操作放在 `Service`，接口请求放在 `Router`，调用第三方服务抽象到 `Factory`。
2. **完全异步**：从 `FastAPI` 到 `asyncpg` 再到 `httpx` 发送请求，全链路非阻塞。
3. **图计算引擎**：运用 `LangGraph` 让 AI 具备状态流转与自我修复能力。
掌握此项目，同学们足以在求职面试中脱颖而出！
"""

instructor_content = """# 智能跨境电商融合平台 (AgenticCommerce) 教师保姆级讲义

> **讲师必读：**
> 本讲义专为 **0 基础小白** 量身打造。针对之前课程中可能混淆的概念（如真正的 MVC 是什么，为什么用 uv add 等），本版本进行了**极其严谨的校对与数倍扩充**。讲课时请务必配合本讲义中的**“小白白话文比喻”**和**“大厂面试必杀技”**进行展开！

---

## 第一讲：打破认知壁垒与大模型图引擎原理

### 1.1 什么是跨境电商的多智能体 (Multi-Agent)？
**话术建议**：“同学们，传统写代码是教计算机做 1+1=2。今天，我们要给计算机分配‘大脑’和‘手脚’。你只要输入‘保温杯’，我们的系统会自动唤醒 7 个 AI（文案策划、美术设计、视频剪辑、法务审核等）拉一个微信群，相互交接工作。这就是 Multi-Agent 架构。”

### 1.2 为什么要用 LangGraph 而不是 LangChain？
**面试必杀技（敲黑板！）**：
*   **LangChain** 就像是流水线车间，工作是单向的（A传给B，B传给C）。如果 C 画出来的图里出现了违禁词，整个链路就会报错崩溃。
*   **LangGraph** 引入了“状态机”图计算的概念。它允许 AI 在一张图（Graph）里**反复打转**。如果 C 画错了，系统可以顺着边（Edge）退回给 A 重新出主意，这叫“AI 自我纠错（Self-Correction）”。这是目前最顶尖的大模型工程化落地标准。

---

## 第二讲：现代 Web 框架与 MVC / 三层架构揭秘

同学们可能听过 MVC，但对它在现代前后端分离项目里的实际演变非常模糊。请在这里给他们做最严谨的区分。

### 2.1 传统的 MVC 到底是什么？
MVC (Model-View-Controller) 是一种经典的架构模式。
*   **Model（模型层）**：负责管理应用程序的核心数据、业务逻辑和规则（相当于程序的“大脑”和“数据仓库”）。
*   **View（视图层）**：负责展示数据给用户看（前端 UI，各种漂亮的按钮）。
*   **Controller（控制层）**：充当 Model 和 View 之间的桥梁。它接收用户的点击，命令 Model 更新数据，然后再告诉 View 去刷新页面。

### 2.2 为什么我们现在流行三层架构 (Router-Service-Model)？
**大厂面试考点：**
“同学们注意，在过去，服务器要把网页（HTML）渲染好直接塞给用户，那时候 Controller 压力很大。但现在我们是**前后端彻底分离**的时代！”
*   **前端（View 的独立体）**：我们用 Vue 3（**官网：vuejs.org**）独立成了一个完整的项目，由浏览器自己去画页面。
*   **后端（FastAPI 三层架构）**：
    1.  **Router（路由层）**：相当于酒店的**迎宾前台**。它只管接客、校验你传来的 JSON 数据对不对，它**绝不亲自处理业务**。
    2.  **Service（服务核心层）**：相当于酒店的**厨师长**。真正的计算逻辑、判断打折、调用大模型都在这里发生！分离出这一层，代码极其好维护。
    3.  **Model（数据访问层）**：相当于**仓库管理员**。用 SQLAlchemy 把数据库里的表映射成 Python 能认出来的类。

---

## 第三讲：Python 零基础速成与极速包管理 (uv)

### 3.1 零基础听懂 Python 语法：
*   **函数 (Function)**：比如 `def get_sku(id):`，你可以理解为一个**“自动榨汁机”**。你给它扔苹果（传入参数），它嗡嗡一转，吐出果汁（`return` 返回值）。
*   **调用 (Call)**：榨汁机摆在那不会自己动，你得按开关去**使用**它，这在代码里就叫“调用”。
*   **方法 (Method)**：当这个榨汁机被焊死在一台特制房车（面向对象编程中的类 Class）上，作为这台车专属功能时，我们就叫它“方法”。

### 3.2 为什么课件里不用 pip install，而是用 uv add？
**工具科普与演示**：
*   **官网**: [docs.astral.sh/uv/](https://docs.astral.sh/uv/)
*   **原理解析**：以前我们用 `pip install fastapi`，它下包不仅慢，而且无法自动管理版本依赖。现在最新的业界标配是 `uv`。
*   **uv add 的好处**：当我们运行 `uv add fastapi` 时，它不仅会像闪电一样（用 Rust 底层语言编写，比 pip 快几十倍）把包下好，还会自动帮你把依赖信息写入现代化的 `pyproject.toml` 文件中。这就相当于自动帮你记账，你的同事接手项目时只要一句 `uv sync` 就齐活了！这是最优雅的工程化实践。

---

## 第四讲：海量数据护城河（Postgres、Redis、MinIO）与 Docker

### 4.1 Docker 降维打击
*   **痛点**：张三是 Windows，李四是 Mac。大家装同一个数据库能报一百种错。
*   **Docker 的本质**：它是一门**集装箱技术**。我们把 PostgreSQL、Redis、系统运行环境直接打包进一个封闭的集装箱（容器 Container）。只要你的电脑安装了 Docker，一键敲下 `docker compose up -d`，集装箱落地，所有的软件绝对乖乖跑起来，消灭一切“在我的电脑上明明没问题”的扯皮！

### 4.2 三大数据基石扫盲
1.  **PostgreSQL 16（主数据库）与 MVCC 原理**
    *   **官网**: [postgresql.org](https://postgresql.org/)
    *   **为什么不用 MySQL？** Postgres 号称世上最先进的开源数据库。在电商和 AI 领域，它对复杂的 JSONB 数据支持极好，还可以装 PGVector 插件做 AI 向量检索。
    *   **面试必杀：什么是 MVCC（多版本并发控制）？** 
        想象一下你和同桌同时在改同一份考卷。如果是老派数据库，为了防止冲突，只能把你俩锁起来排队（锁表）。而有了 MVCC，系统会偷偷给你们每个人“复印一份当前的快照”，你们各自在快照上改，最后系统智能合并。这就是淘宝双十一成千上万人同时买东西，数据库也不会卡死的秘密！
2.  **Redis 7（高速内存缓存）**
    *   **官网**: [redis.io](https://redis.io/)
    *   **比喻**：主数据库在仓库，跑过去拿盐太费时。Redis 就是你炒菜锅旁边的“极速调料盒”。它把热点数据全放在内存里，读取速度比普通数据库快百倍。
3.  **MinIO（私有化对象存储 OSS）**
    *   **官网**: [min.io](https://min.io/)
    *   **比喻**：数据库存个名字密码还行，但 AI 生成的几百兆的高清视频怎么存？这时候需要“自建版百度网盘”。MinIO 就是一套开源的对象存储系统，我们把视频丢给它，它生成一个 http 下载链接，我们只要把这个链接存进数据库就行了。

---

## 第五讲：工厂模式与云端 API 接入 (ProviderFactory)

### 5.1 什么是 API (应用程序接口)？
大模型好几百 T，我们不可能装进自己电脑。所以阿里云在云端开了个“插座”（API 接口）。我们用 Python 发起 HTTP 请求（这就叫“插头”），插上去，传过去一行字：“画一只小猫”，云端运算完，顺着网线传回来一张图。这就叫调用云端 API。

### 5.2 为什么要写 ProviderFactory（工厂模式）？
**高逼格代码设计考点：**
今天老板说用阿里云，如果我们在 100 个文件里全写死了阿里云的调用代码，明天老板说换百度文心一言，你就得加班改 100 个文件。
如果我们在系统里建一个“转换工厂（ProviderFactory）”，外部业务代码只喊：“给我个画图客户端！”，工厂在内部再决定实例化阿里云还是百度的客户端。未来不管换多少家模型，业务代码一行都不用改！这就是**面向对象设计原则**中的“向扩展开放，向修改封闭（OCP）”。

---
**讲课最终升华总结：**
“同学们，这套课程不仅带你跑通了最新的 AI Agent 架构，它更是为你建立了一套完全对标互联网一线大厂的技术视野。从底层的 Docker 容器化，到数据库的 MVCC 锁机制，再到 FastAPI 异步并发与工厂设计模式。带着这个项目的认知去面试，足以让面试官对你刮目相看！”
"""

with open(courseware_path, 'w', encoding='utf-8') as f:
    f.write(courseware_content)

with open(instructor_path, 'w', encoding='utf-8') as f:
    f.write(instructor_content)

print('Successfully generated the detailed markdown files.')
