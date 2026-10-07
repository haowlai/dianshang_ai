# Vibe Coding 从 0 到 1 全流程实战提示词手册

> **核心原则**：**拒绝笼统、保姆级步骤、步步可执行、产物全透明**。  
> 无论是使用 Claude Code、Cursor、还是 Google Antigravity，本手册为你提供从 `uv init` 第一行空目录开始，到 7-Agent 多智能体、FastAPI 后端、Vue3 前端全栈落地的**每一步标准 Prompt 复制模板**。

---

## 目录
- [一、什么是 Vibe Coding？AI 时代的新型软件工程范式](#一什么是-vibe-codingai-时代的新型软件工程范式)
- [二、十步成诗：从 0 到 1 全流程提示词实操](#二十步成诗从-0-到-1-全流程提示词实操)
  - [Step 1：工程脚手架与 uv 依赖规划](#step-1工程脚手架与-uv-依赖规划)
  - [Step 2：基础设施与本地容器编排 (Docker Compose)](#step-2基础设施与本地容器编排-docker-compose)
  - [Step 3：配置中心与异步数据库引擎搭建](#step-3配置中心与异步数据库引擎搭建)
  - [Step 4：14 张业务数据表与 SQLAlchemy 2.0 模型](#step-414-张业务数据表与-sqlalchemy-20-模型)
  - [Step 5：三层架构之仓储层 (Repository) 与服务层 (Service)](#step-5三层架构之仓储层-repository-与服务层-service)
  - [Step 6：大模型统一网关与客户端工厂 (ProviderFactory)](#step-6大模型统一网关与客户端工厂-providerfactory)
  - [Step 7：7-Agent LangGraph 状态图与 P-E-V 闭环构建](#step-77-agent-langgraph-状态图与-p-e-v-闭环构建)
  - [Step 8：FastAPI 接口与 WebSocket 实时状态流广播](#step-8fastapi-接口与-websocket-实时状态流广播)
  - [Step 9：Vue 3 + Vite + Pinia 现代化前端工作台搭建](#step-9vue-3--vite--pinia-现代化前端工作台搭建)
  - [Step 10：端到端连通性测试与自动化自愈修复](#step-10端到端连通性测试与自动化自愈修复)
- [三、高阶 Vibe Coding 技巧：如何让 AI 越写越聪明？](#三高阶-vibe-coding-技巧如何让-ai-越写越聪明)

---

## 一、什么是 Vibe Coding？AI 时代的新型软件工程范式

**Vibe Coding（心流编程）** 是由 Andrej Karpathy 等人倡导的一种新型开发方式：**开发者不再逐行手动敲语法，而是充当「系统架构师与需求指挥官」，由 AI 编程智能体（如 Claude Code）完成具体的代码编写、测试运行与调试**。

但要想让 AI 写出企业级、无 Bug、高内聚低耦合的代码，**关键在于给出的 Prompt 不能是一句笼统的“帮我做个电商系统”，而必须是高度结构化、职责单一、边界清晰的“小步快跑”式指令！**

---

## 二、十步成诗：从 0 到 1 全流程提示词实操

---

### Step 1：工程脚手架与 uv 依赖规划
- **本步目标**：建立现代化 Python 3.12 工程，使用 Rust 编写的超高速包管理器 `uv` 初始化项目，规范目录结构。
- **发送给 Claude Code 的提示词**：

````text
你现在是资深 Python 架构师。请为项目【AgenticCommerce 跨境电商智能生成平台】初始化项目脚手架。

【环境与工具要求】
1. 使用 uv 初始化项目，Python 版本锁定为 3.12。
2. 创建 pyproject.toml，规划核心依赖：
   - Web框架: fastapi, uvicorn[standard], pydantic, pydantic-settings
   - 数据库与ORM: sqlalchemy>=2.0.0, asyncpg, pgvector
   - 缓存与存储: redis[asyncio], minio
   - AI与工作流: langgraph, langchain-core, dashscope, httpx
3. 建立标准分层项目目录：
   - app/api/v1/ (路由接入层)
   - app/services/ (业务逻辑层)
   - app/repositories/ (数据访问层)
   - app/models/ (SQLAlchemy 数据实体)
   - app/agent/ (LangGraph 7个智能体与状态机)
   - app/clients/ (第三方大模型与存储客户端)
   - app/conf/ (配置中心)
   - conf/ (部署与环境配置)
   - data/static/ (本地测试素材目录)
4. 输出完整的 pyproject.toml 文件内容，并执行 uv sync 完成虚拟环境依赖安装。
````

- **预期交付物**：`pyproject.toml`，干净清晰的 `app/` 骨架目录。

---

### Step 2：基础设施与本地容器编排 (Docker Compose)
- **本步目标**：准备系统所需的数据库、向量检索、缓存与对象存储环境，确保研发开箱即用。
- **发送给 Claude Code 的提示词**：

````text
请为 AgenticCommerce 项目编写基础设施本地快速启动的 docker-compose.infra.yml 文件。

【必须包含的容器服务】
1. postgres: 使用镜像 pgvector/pgvector:pg16，映射端口 5432，挂载初始化目录 ./docker/postgres/init.sql（自动执行 CREATE EXTENSION IF NOT EXISTS vector;）。
2. redis: 使用镜像 redis:7-alpine，映射端口 6379，开启 appendonly yes 持久化。
3. minio: 使用镜像 minio/minio:latest，映射端口 9000 (API) 与 9001 (Console 控制台)，设置凭据 minioadmin/minioadmin。
4. 所有容器加入统一网络 agentic-net，并配置健壮的 healthcheck 探针。
5. 编写一键启动批处理脚本或 Bash 脚本，启动后自动校验三者健康状态。
````

- **预期交付物**：`docker-compose.infra.yml`, `docker/postgres/init.sql`。

---

### Step 3：配置中心与异步数据库引擎搭建
- **本步目标**：统一管理环境变量，配置异步 SQLAlchemy 2.0 连接池。
- **发送给 Claude Code 的提示词**：

````text
请基于 pydantic-settings 和 SQLAlchemy 2.0，为项目实现配置中心与异步数据库会话管理。

【规范要求】
1. 在 app/conf/config.py 中定义 Settings 类，继承 BaseSettings：
   - 支持从 .env 文件自动加载环境变量
   - 包含 PostgreSQL, Redis, MinIO, DashScope API Key, App 环境等完整配置项
2. 在 app/core/database.py 中实现：
   - 使用 create_async_engine 创建异步引擎，驱动使用 postgresql+asyncpg://
   - 连接池配置: pool_size=20, max_overflow=10, pool_pre_ping=True
   - 使用 async_sessionmaker 创建 AsyncSessionLocal
   - 提供 FastAPI 专用的依赖注入生成器 get_db()
3. 在 conf/.env.example 中提供详尽的环境变量注释模板。
````

- **预期交付物**：`app/conf/config.py`, `app/core/database.py`, `conf/.env.example`。

---

### Step 4：14 张业务数据表与 SQLAlchemy 2.0 模型
- **本步目标**：沉淀电商商品、智能体任务、多模态资产、合规记录等 14 张核心实体表。
- **发送给 Claude Code 的提示词**：

````text
请基于 SQLAlchemy 2.0 Declarative 规范，在 app/models/ 下实现项目的全部 14 张实体表。

【核心建模原则】
1. 在 app/models/base.py 中定义 AuditMixin 审计基类：
   - 包含 id (varchar(32), 默认UUID), created_at, updated_at, created_by, updated_by, is_deleted (软删除), tenant_id (多租户ID)。
2. 严禁物理外键约束 (ForeignKey)，必须全部使用逻辑外键 (xxx_id varchar(32))。
3. 核心表清单：
   - ac_sku: 商品SKU表 (spu_code, title, category, price, specs JSONB)
   - ac_task: 任务主表 (sku_id, status PENDING/RUNNING/SUCCESS/FAILED, result_summary)
   - ac_task_node_run: 节点运行明细 (task_id, node_name, status, duration_ms, input_data, error_msg)
   - ac_copy: 生成营销文案表 (headline, bullet_points, body)
   - ac_asset: 多模态素材表 (asset_type IMAGE/VIDEO, storage_url, file_size)
   - ac_compliance: 质检审核记录 (is_passed, risk_level, details JSONB)
   - ac_knowledge: RAG知识库表，必须使用 pgvector 的 Vector(1024) 字段存储 embedding。
4. 编写 app/scripts/init_db.py 脚本，能够扫描所有模型一键建表。
````

- **预期交付物**：`app/models/*.py`, `app/scripts/init_db.py`。

---

### Step 5：三层架构之仓储层 (Repository) 与服务层 (Service)
- **本步目标**：隔离数据持久化与业务逻辑，确保代码高内聚低耦合。
- **发送给 Claude Code 的提示词**：

````text
请为项目实现现代化三层架构中的仓储层 (Repository) 与服务层 (Service)。

【要求】
1. 在 app/repositories/base.py 中实现泛型 BaseRepository[T]，封装基础异步 CRUD (get_by_id, list, create, update, soft_delete)。
2. 实现具体的 SkuRepository, TaskRepository, TaskNodeRunRepository, AssetRepository。
3. 在 app/services/task_service.py 中实现任务服务 TaskService：
   - 提供 create_and_run_task(sku_id, platform, language) 方法
   - 事务边界清晰：创建任务主记录 -> 启动后台异步任务 -> 返回任务ID
   - 配合 Redis 缓存最新任务状态，降低高频轮询对数据库的读取压力。
````

- **预期交付物**：`app/repositories/*.py`, `app/services/*.py`。

---

### Step 6：大模型统一网关与客户端工厂 (ProviderFactory)
- **本步目标**：封装阿里云百炼（通义千问、通义万相、视频生成）统一调用接口与 Mock 降级能力。
- **发送给 Claude Code 的提示词**：

````text
请为项目设计可插拔的第三方 AI 大模型接入层。

【技术规范】
1. 在 app/clients/base.py 中定义 BaseLLMClient 与 BaseImageClient 抽象基类。
2. 在 app/clients/qwen_client.py 中实现阿里百炼通义千问（Qwen-Max / Qwen-Plus）异步调用，支持 system 提示词与 JSON Mode 输出。
3. 在 app/clients/wanx_client.py 中实现通义万相 2.1 生图 API，包含异步提交任务与状态轮询机制。
4. 在 app/clients/provider_factory.py 中实现工厂类 ProviderFactory：
   - 单例模式复用连接
   - 支持环境变量 ALLOW_MOCK_ASSETS=true 时的离线 Mock 降级返回，确保无网络时本地开发不阻塞。
````

- **预期交付物**：`app/clients/*.py`。

---

### Step 7：7-Agent LangGraph 状态图与 P-E-V 闭环构建
- **本步目标**：核心关键步！使用 LangGraph 实现 7 个专业智能体的协作状态图与质检回退循环。
- **发送给 Claude Code 的提示词**：

````text
请基于 LangGraph 编排项目核心的 7-Agent 有状态工作流 DAG。

【工作流规范】
1. 在 app/agent/state.py 中定义 AgentState (TypedDict)，包含任务元数据、各阶段产出、以及 is_passed, review_feedback, retry_count 等控制字段。
2. 在 app/agent/nodes/ 目录下分别实现 7 个纯异步节点函数：
   - orchestrator.py: 总控调度与参数初始化
   - requirement_analyzer.py: 提取特征并检索 RAG 向量知识库
   - creative_planner.py: 策划多语种营销文案（接收审核反馈自我修复）
   - visual_designer.py: 产出结构化生图 Prompt
   - image_generator.py: 调用万相渲染并持久化转存 MinIO
   - video_generator.py: 生成动态演示短视频
   - quality_reviewer.py: 广告法硬扫描 + LLM 多模态盲审
3. 在 app/agent/recorder.py 中利用 asynccontextmanager 记录每个节点执行耗时至 task_node_run 表。
4. 在 app/agent/graph.py 中组装 StateGraph：
   - 编排线性流水线
   - 在 quality_reviewer 后挂载条件路由 quality_review_router：未通过且 retry_count < 2 时，自动打回至 creative_planner！通过后流向 END。
````

- **预期交付物**：`app/agent/state.py`, `app/agent/graph.py`, `app/agent/nodes/*.py`, `app/agent/recorder.py`。

---

### Step 8：FastAPI 接口与 WebSocket 实时状态流广播
- **本步目标**：对外暴露 RESTful API 并通过 WebSocket 实时推送智能体 DAG 状态。
- **发送给 Claude Code 的提示词**：

````text
请为项目实现对外 API 表现层。

【接口要求】
1. 在 app/api/v1/tasks.py 实现任务管理接口：
   - POST /api/v1/tasks/run: 触发单个生成任务
   - GET /api/v1/tasks/{id}: 查询任务详情与结果汇总
   - GET /api/v1/tasks/{id}/nodes: 查询 7 个节点的执行轨迹与耗时
2. 在 app/api/v1/ws.py 实现 WebSocket 实时通知：
   - /api/v1/ws/{task_id}: 前端连接后，实时推送 node_start, node_finish, task_completed 事件。
3. 在 main.py 中组装 FastAPI 实例，配置全局 CORS、静态资源挂载以及 lifespan 优雅启停钩子。
````

- **预期交付物**：`app/api/v1/*.py`, `main.py`。

---

### Step 9：Vue 3 + Vite + Pinia 现代化前端工作台搭建
- **本步目标**：打造高颜值、可视化、带 DAG 动态流转的现代化电商生成工作台。
- **发送给 Claude Code 的提示词**：

````text
请使用 Vue 3 + Vite + Pinia + Element Plus (或原生精美 CSS) 构建项目前端工作台。

【页面要求】
1. 页面 1：商品 SKU 列表与一键生成抽屉（支持选择出海平台与语言）。
2. 页面 2：任务生成工作台 (Workbench DAG 视图)：
   - 可视化展示 7 个节点的流转状态（灰色待执行、蓝色运行中旋转、绿色成功带耗时、红色失败）。
   - 右侧实时展示文案预览、图片瀑布流与短视频播放器。
   - 接入 WebSocket 自动接收后端广播并更新节点状态。
3. 页面 3：合规质检报告与一键导出刊登包 (Zip 打包下载)。
````

- **预期交付物**：`frontend/src/views/*.vue`, `frontend/src/stores/*.ts`。

---

### Step 10：端到端连通性测试与自动化自愈修复
- **本步目标**：打通前后端全链路，运行真实测试用例，让 AI 自动发现并修复 Bug。
- **发送给 Claude Code 的提示词**：

````text
请编写端到端自动化测试脚本 test_apis.py 与 run_workflow.py，并执行完整验收。

【验收要点】
1. 校验本地 8002 端口健康状态。
2. 模拟真实调用 POST /api/v1/tasks/run 创建任务。
3. 轮询监控任务从 RUNNING 演进到 SUCCESS，断言：
   - task_node_run 表中必须产生 7 条以上的节点记录。
   - copy 表中必须有生成的标题和 Bullet Points。
   - asset 表中必须有可访问的图片 URL。
4. 若执行过程中出现报错（如连接池断开、导入路径错误、JSON解析失败），请分析错误日志并自动进行代码自愈修复，直到整体验收 100% 通过！
````

---

## 三、高阶 Vibe Coding 技巧：如何让 AI 越写越聪明？

1. **上下文分段管理**：不要把所有代码一股脑扔给 AI，严格按「分层模型」推进。
2. **测试驱动自愈**：每次生成代码后，立即让 AI 运行一个轻量测试脚本（`python test_xxx.py`），借助报错反馈让 AI 自我修正。
3. **固化项目经验至 Skill**：当解决了一个棘手 Bug 后，立即触发 `/learn` 指令或使用第 5 章的元提示词，将该规则沉淀为一个永不失效的 Skill！
