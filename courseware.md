# 智能跨境电商融合平台 (AgenticCommerce) 课件
（作者：尚硅谷研究院）
版本：V1.0

## 第一章 项目概述
AgenticCommerce 是一个基于多智能体（Multi-Agent）架构的跨境电商智能生成平台。面向电商出海场景，旨在帮助跨境卖家通过 AI 自动化生成商品的高转化多语言文案、商品主图及带货短视频。用户无需学习复杂的提示词编写与大模型调试，只需录入商品 SKU 的基础信息，系统即可自动调度 7-Agent 工作流（包含需求分析、创意策划、分镜设计、视觉生成、合规审核等），大幅提升出海营销物料的产出效率，降低跨境电商运营门槛。

## 第二章 项目架构
### 2.1 架构概述
本项目采用经典的前后端分离架构结合大模型智能体工作流引擎。
*   **前端**：基于 Vue 3 + Vite 构建的高性能交互界面，提供工作台（Dashboard）实时渲染智能体执行状态。
*   **后端**：基于 FastAPI 搭建的高并发异步 Web 服务，采用标准三层架构（Router -> Service -> Model）解耦业务逻辑。
*   **数据存储**：使用 PostgreSQL 存储核心业务数据（SKU、任务、文案等），Redis 负责高速缓存与后台任务队列状态，MinIO 负责海量图像与视频资产的对象存储。
*   **智能体核心**：基于 LangGraph 构建多节点状态图（State Graph），并对接阿里云百炼（DashScope）提供的千问大模型（Qwen）、万相 3.0 图像（Qwen-Image-3.0-Pro）与万相 3.0 视频大模型（Wan3.0-Video），形成内容生成的闭环。

### 2.2 核心业务模块
1.  **商品 SKU 管理**：集中管理商品的属性、规格与原始素材。
2.  **批次与任务调度**：支持单商品或多商品批量创建生成任务，交由后台 BackgroundTasks 异步调度。
3.  **多模态资产库**：统一管理 AI 生成的图文与视频资产。
4.  **合规质检（Compliance）**：内置针对亚马逊等平台的绝对化词汇（如“世界第一”）屏蔽与合规引擎双重校验。

---

## 第三章 项目开发环境

### 3.1 依赖管理
本项目使用标准的 Python 虚拟环境与 `pip`（或 `uv`）进行依赖管理。

### 3.2 核心依赖库说明
执行命令安装核心依赖：
`pip install fastapi[standard] sqlalchemy asyncpg httpx langgraph dashscope pydantic-settings`

各依赖说明如下：
*   **fastapi[standard]**：高性能异步 Web 框架，作为整个服务的 API 入口。
*   **sqlalchemy**：Python 最主流 ORM，用统一模型管理数据库读写与事务。
*   **asyncpg**：PostgreSQL 的高性能 asyncio 驱动，配合 SQLAlchemy 实现全异步数据库访问。
*   **httpx**：高性能异步 HTTP 客户端，用于调用第三方大模型原生 API。
*   **langgraph**：用图结构构建可控 Agent 流程，管理状态流转。
*   **pydantic-settings**：强大的环境配置管理，自动加载 `.env` 变量。

---

## 第四章 基础设施搭建

### 4.1 核心服务
本项目所需的全部基础服务如下：
*   **PostgreSQL 16**：关系型数据库，存储电商元数据。
*   **Redis 7**：内存数据库。
*   **MinIO**：私有化部署的 S3 兼容对象存储，存放生成的图片与视频素材。

### 4.2 安装与启动
本项目所需的全部基础服务通过 Docker Compose 统一部署。
进入 `docker-compose.yaml` 所在目录，执行以下命令即可完成所有服务的安装与启动：
`docker compose up -d`

### 4.3 项目目录结构
项目目录结构分层如下：
```text
AgenticCommerce/
├── app/                  # 代码核心目录
│   ├── agent/            # LangGraph 智能体状态图逻辑
│   ├── api/v1/           # 对外接口层 (薄控制器 Router)
│   ├── clients/          # 外部大模型 API 客户端 (ProviderFactory)
│   ├── conf/             # 配置类 (Settings)
│   ├── core/             # 核心依赖 (如 get_db 依赖注入)
│   ├── models/           # 数据库实体类 (ORM Model)
│   └── services/         # 业务逻辑层 (Service)
├── conf/                 # 配置文件目录 (.env)
├── main.py               # FastAPI 服务入口
```

---

## 第五章 核心代码实现

### 5.1 全局配置管理
采用 Pydantic Settings 解析 `.env` 文件，在 `app/conf/config.py` 中定义：
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_PORT: int = 8002
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_PORT: int = 5434
    DASHSCOPE_API_KEY: str = ""

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@127.0.0.1:{self.POSTGRES_PORT}/agentic_commerce"

settings = Settings()
```

### 5.2 大模型客户端工厂 (ProviderFactory)
为了统一管理文生文、文生图、文生视频调用，在 `app/clients/provider_factory.py` 中实现了工厂模式封装阿里云百炼接口：
```python
import httpx
from app.conf.config import settings

class QwenLLMClient:
    # 封装千问对话与文本 Embedding 接口...
    pass

class WanxImageClient:
    # 封装 qwen-image-3.0-pro 接口...
    pass

class KlingVideoClient:
    # 封装 wan3.0-video 接口...
    pass

class ProviderFactory:
    @staticmethod
    def get_llm_client() -> QwenLLMClient:
        return QwenLLMClient()
```

### 5.3 Service 与 Router 三层架构设计
为避免代码臃肿，项目采用严格的三层架构：

**1. Service 层 (业务逻辑)** - `app/services/sku_service.py`
```python
from sqlalchemy import select
from app.models.sku import Sku
from app.services.base import BaseService

class SkuService(BaseService):
    async def get_sku(self, tenant_id: str, sku_id: str) -> dict:
        res = await self.session.execute(select(Sku).where(Sku.id == sku_id))
        sku = res.scalar_one_or_none()
        if not sku:
            raise ValueError("商品不存在")
        return {"id": sku.id, "name": sku.name}
```

**2. Router 层 (控制路由)** - `app/api/v1/skus.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sku_service import SkuService
from app.core.deps import get_db

router = APIRouter(prefix="/skus")

@router.get("/{sku_id}")
async def get_sku(sku_id: str, db: AsyncSession = Depends(get_db)):
    svc = SkuService(db)
    try:
        return {"code": 200, "data": await svc.get_sku("tenant_default", sku_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```
通过这种分层，接口只负责接客（参数校验、返回），服务层负责核心数据计算，保证了项目的高可维护性。
