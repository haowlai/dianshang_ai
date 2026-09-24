---
name: agent-workflow-runner
description: >-
  7-Agent LangGraph 状态图工作流调试与执行规范。指导从命令行 CLI 或 Web API 触发
  Orchestrator、RequirementAnalyzer、CreativePlanner、VisualDesigner、Image/VideoGenerator、
  QualityReviewer 的 P-E-V 闭环执行，并验证指标追踪与重试路由。
---

# 智能体工作流执行与调试技能 (Agent Workflow Runner)

## 1. 核心流程拓扑 (P-E-V 闭环)

```mermaid
sequenceDiagram
    autonumber
    actor User as 运营/客户端
    participant O as Orchestrator
    participant R as RequirementAnalyzer
    participant C as CreativePlanner
    participant V as VisualDesigner
    participant Gen as Image/Video Generator
    participant Q as QualityReviewer
    participant DB as PostgreSQL/MinIO
    participant WS as WebSocket/Workbench

    User->>O: 提交生成任务 (SKU, 目标平台, 媒体类型)
    O->>WS: 推送 [node_start: orchestrator]
    O->>R: 初始化状态 AgentState
    
    R->>DB: pgvector 检索品牌与类目知识
    R->>WS: 推送需求报告完成
    R->>C: 移交创意文案策划
    
    C->>WS: 推送 [node_complete: creative_planner]
    C->>V: 移交视觉 Prompt 设计
    
    V->>Gen: 构造 Prompt 并路由分支
    Gen->>DB: 渲染并转存素材至 MinIO
    Gen->>Q: 移交质量审核
    
    Q->>DB: 检索广告法禁词库
    alt 审核通过 (Passed)
        Q->>DB: 写入 Copy & Asset 状态为 active
        Q->>WS: 推送 [task_completed]
    else 命中禁词且重试次数 < 2 (Retry)
        Q->>C: 回滚重做，附带 violations 与 suggestions
        C->>V: 针对性修复生成
    else 重试超限 (Failed)
        Q->>DB: 标记任务失败
        Q->>WS: 推送 [task_failed] (人工介入)
    end
```

---

## 2. CLI 调试指令与标准输出
开发者或测试人员可使用专用 CLI 脚本直接运行任意 SKU 的生成流程：

```bash
# 激活虚拟环境后运行
python run_workflow.py --sku-id <SKU_UUID> --media-type mixed --platform amazon
```

期望指标输出：
- `total_elapsed_ms`: 总耗时 (ms)
- `node_runs`: 各节点耗时、Token 消耗、输入输出快照
- `compliance_score`: 最终合规打分
- `violations`: 命中违禁词列表 (若有)
