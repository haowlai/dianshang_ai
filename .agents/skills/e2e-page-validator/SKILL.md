---
name: e2e-page-validator
description: >-
  前端 15 个页面交互与后端 13 个业务路由的端到端集成测试与验收指南。
  包含路由连通性核验、Pinia 状态持久化、WebSocket 实时重连心跳与 UI 响应式规范。
---

# 前端全页面与接口验收技能 (E2E Page Validator)

## 1. 15 个核心页面验收清单

| 页面名称 | 路由路径 | 对应后端 API 模块 | 核心功能验收点 |
| :--- | :--- | :--- | :--- |
| **数据看板** | `/dashboard` | `/tasks`, `/assets` | 汇总数据统计、近期任务折线图、耗时分布 |
| **批次管理** | `/batches` | `/batches` | 提交批次表单、选择 SKU 列表、设置生成参数 |
| **任务中心** | `/tasks` | `/tasks` | 分页列表、状态过滤、跳转到可观测工作台 |
| **Agent 工作台** | `/workbench/:id` | `/tasks/{id}`, `/ws` | 7-Agent DAG 实时动态变色、Prompt/Token检查 |
| **素材审查** | `/assets` | `/assets` | 主图/场景图瀑布流预览、大图查看、重生成触发 |
| **文案编辑** | `/copies` | `/copies` | 标题/五点描述/关键词多语言在线编辑与保存 |
| **知识库** | `/knowledge` | `/knowledge-docs` | 上传品牌手册/合规文档、分块列表、向量化状态 |
| **厂商配置** | `/providers` | `/providers` | 千问/万相/可灵等厂商状态、API Key 更新、默认切换 |
| **SKU 管理** | `/skus` | `/skus` | SKU 编码、规格参数、参考原图录入与列表 |
| **打包下载** | `/packages` | `/packages` | 勾选多素材、创建 ZIP 打包、进度条与文件下载 |
| **合规审查** | `/compliance` | `/compliance-reports`| 违禁词高亮提示、修改建议对照、合规评分雷达图 |
| **操作审计** | `/audit` | `/audit-logs` | 用户操作轨迹、IP 地址、操作耗时记录列表 |
| **一键刊登** | `/listings` | `/listings` | 二期预留页面，平台授权提示与占位列表 |
| **系统设置** | `/settings` | `/auth` | 租户信息查看、配额限制、成员账号管理 |
| **登录中心** | `/login` | `/auth/login` | 邮箱密码认证、JWT 本地存储、角色重定向 |

---

## 2. 验收指令与流程
```bash
# 启动前端服务后访问
http://localhost:5173

# 检查各个页面组件是否渲染正常，控制台是否有 JS/CSS 报错
```
