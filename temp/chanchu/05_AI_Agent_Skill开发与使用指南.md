# AI Agent Skill 技能开发与实战使用全指南

> **适用场景**：面向使用 Claude Code、Google Antigravity、Cursor、Cline 等下一代 AI 编程智能体的开发者与架构师。  
> **核心痛点解决**：彻底告别「每次开新会话都要把项目背景、规范要求重新复制粘贴一遍」的低效操作，学会如何沉淀领域知识库，将规范固化为可复用、按需自动加载的 **Agent Skill（智能体技能包）**。

---

## 目录
- [一、什么是 Skill？为什么它是 AI 时代的核心工程实践？](#一什么是-skill为什么它是-ai-时代的核心工程实践)
  - [1.1 Skill、System Prompt 与 Global Rules 的区别](#11-skill系统提示词与全局规则的区别)
  - [1.2 Skill 的底层触发与加载机制（按需召回）](#12-skill-的底层触发与加载机制按需召回)
- [二、Skill 标准目录结构与规范规范详解](#二skill-标准目录结构与规范规范详解)
  - [2.1 目录组织全景图](#21-目录组织全景图)
  - [2.2 SKILL.md 核心结构与 YAML Frontmatter 规范](#22-skillmd-核心结构与-yaml-frontmatter-规范)
- [三、如何编写提示词让 Claude Code 自动生成一个高质量 Skill？](#三如何编写提示词让-claude-code-自动生成一个高质量-skill)
  - [3.1 Skill 生成的「元提示词」（Meta-Prompt 黄金模板）](#31-skill-生成的元提示词meta-prompt-黄金模板)
  - [3.2 实际交互演练：输入指令到文件落盘全过程](#32-实际交互演练输入指令到文件落盘全过程)
- [四、AgenticCommerce 项目定制的 3 大生产级 Skill 实战剖析](#四agenticcommerce-项目定制的-3-大生产级-skill-实战剖析)
  - [4.1 实战案例 1：电商广告法合规质检技能 (ad-compliance-checker)](#41-实战案例-1电商广告法合规质检技能-ad-compliance-checker)
  - [4.2 实战案例 2：LangGraph P-E-V 状态图调试技能 (agent-workflow-runner)](#42-实战案例-2langgraph-p-e-v-状态图调试技能-agent-workflow-runner)
  - [4.3 实战案例 3：第三方大模型统一集成规范 (model-provider-integrator)](#43-实战案例-3第三方大模型统一集成规范-model-provider-integrator)
- [五、Skill 的日常使用、调试与团队共享协作](#五skill-的日常使用调试与团队共享协作)

---

## 一、什么是 Skill？为什么它是 AI 时代的核心工程实践？

### 1.1 Skill、系统提示词与全局规则的区别

在开发复杂工程（如 7-Agent 多智能体系统）时，AI 经常会「遗忘」你的架构规范，比如偷偷用物理外键、不用三层架构、或者忘记写异步 `async/await`。传统的解法是写在全局规则（Rules）中，但随着规则变长，会严重挤占上下文窗口（Context Window），导致成本飙升和模型推理注意力分散。

| 机制类型 | 生效时机 | 上下文 Token 占用 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **System Prompt / Rules** | 会话中的**每一轮对话**都会强制全量注入 | **持续占用**，规则越多越容易超出窗口上限 | 全局编码风格、禁止直接写死密钥、代码缩进等普适性硬约束 |
| **Agent Skill** | **按需加载（On-demand）**：仅在用户的任务意图命中 Skill 描述时才动态激活 | **平时只占几行元数据**，使用时才加载正文 | 针对具体业务流程（如数据库迁移规范、模型对接调试、端到端页面验收）的专门知识库 |

### 1.2 Skill 的底层触发与加载机制（按需召回）

Claude Code / Antigravity 等智能体在启动时，会首先扫描工作区目录下的所有 Skill，仅提取其 **YAML Frontmatter** 中的 `name` 和 `description`，作为工具箱清单常驻内存。

当用户输入：“*帮我给系统新接一个百炼通义万相 2.1 模型*” 时：
1. **意图路由判定**：智能体在后台比对 Skill 描述，命中 `model-provider-integrator`；
2. **动态读取正文**：智能体主动调用 `view_file` 工具读取该技能的 `SKILL.md` 正文；
3. **精准规范执行**：智能体按照技能中的契约（Contract）、重试策略、单测要求完成编码。

---

## 二、Skill 标准目录结构与规范规范详解

### 2.1 目录组织全景图

在项目根目录下，Skill 统一存放在 `.agents/skills/`（或 `.claude/skills/`）目录下：

```text
d:\code\dianshang\
├── .agents/
│   └── skills/
│       ├── ad-compliance-checker/           <-- 技能包根目录
│       │   ├── SKILL.md                     <-- [必需] 核心指令与规范入口文件
│       │   ├── scripts/                     <-- [可选] 辅助自动化检查脚本
│       │   │   └── check_blacklist.py
│       │   ├── examples/                    <-- [可选] 优质示范与反面教材
│       │   │   └── good_prompt_output.json
│       │   └── references/                  <-- [可选] 官方文档或 API 契约文档
│       │       └── advertising_law_2026.md
```

### 2.2 SKILL.md 核心结构与 YAML Frontmatter 规范

每一个 `SKILL.md` 文件**必须且只能以三道横线包裹的 YAML Frontmatter 开头**：

```markdown
---
name: ad-compliance-checker
description: >-
  电商出海合规与广告法违禁词检测技能。当用户涉及商品文案生成、合规审核节点(quality_reviewer)修改、
  添加新的敏感词黑名单或处理平台申诉规则时触发此技能。
---

# 电商出海合规质检技能规范

## 1. 目标与定位
说明这个 Skill 解决什么问题、输出什么产物...

## 2. 检查清单与执行步骤
一步步指导智能体如何排查、调用什么脚本...

## 3. 常见陷阱与避坑准则
明确告知智能体哪些做法是严厉禁止的...
```

> **核心技巧**：`description` 是这个 Skill 能否被准确触发的关键！必须明确写出**在什么场景下、遇到什么关键词时需要激活**！

---

## 三、如何编写提示词让 Claude Code 自动生成一个高质量 Skill？

不用手动去辛苦写一个 Skill 的全部文档，我们完全可以使用 **Claude Code「元提示词」（Prompt for Prompts）** 让 AI 为我们生成！

### 3.1 Skill 生成的「元提示词」（Meta-Prompt 黄金模板）

直接复制以下提示词发送给 Claude Code：

````text
你现在是顶级 AI Agent 架构师与 Customization 专家。
请为我的项目【AgenticCommerce 跨境电商智能生成平台】定制生成一个全新的 Agent Skill。

【技能基本信息】
1. 技能名称: ad-compliance-checker
2. 解决的核心问题: 解决跨境电商文案生成中的虚假宣传、广告法极限词（如国家级、最先进）以及平台封店风险，指导质量审核智能体 (quality_reviewer) 进行双重质检。
3. 涉及的核心代码路径: app/agent/nodes/quality_reviewer.py, app/models/compliance.py

【Skill 产出规范要求】
1. 请在工作区的 `.agents/skills/ad-compliance-checker/` 目录下生成完整的 `SKILL.md`。
2. 必须包含严格合规的 YAML frontmatter (name 与 description)。description 必须清晰定义触发条件。
3. 文档正文必须包含：
   - 技能定位与核心目标
   - 广告法三级风险矩阵（禁止级、限制级、预警级）
   - 代码执行规范（必须同时包含硬规则正则匹配与 LLM 语义复审两道防线）
   - 数据库落盘规范（必须将批注写入 ac_compliance 表）
   - 单元测试与验收核验命令
4. 语言使用严谨、专业的简体中文，提供可直接运行的代码示例。
````

---

### 3.2 实际交互演练：输入指令到文件落盘全过程

当你把上述元提示词发给 Claude Code 时，Claude Code 会在后台自动完成：
1. 识别并提取 Skill 的命名规范；
2. 自动创建目录 `.agents/skills/ad-compliance-checker/`；
3. 输出结构严密的 `SKILL.md`；
4. 提示你该技能已生效，并已加入智能体技能池！

---

## 四、AgenticCommerce 项目定制的 3 大生产级 Skill 实战剖析

在本项目中，已经预先为各位打造了 3 个生产级实战 Skill，可随时点击查看与借鉴：

### 4.1 实战案例 1：电商广告法合规质检技能
文件路径：`.agents/skills/ad-compliance-checker/SKILL.md`

**核心内容**：
- 定义了四大电商平台（Amazon、TikTok Shop、Shopee、Temu）的高压红线词库；
- 明确了如果发现违禁词，必须打回至 `creative_planner` 节点，并且附带违规位置与修改建议。

---

### 4.2 实战案例 2：LangGraph P-E-V 状态图调试技能
文件路径：[agent-workflow-runner SKILL.md](file:///d:/code/dianshang/.agents/skills/agent-workflow-runner/SKILL.md)

**核心内容**：
- 指导如何通过命令行独立运行单节点、验证 P-E-V 闭环；
- 监控 `task_node_run` 表中的耗时与状态流转；
- 验证当模拟审核不通过时，工作流是否能正确重试回退 2 次后终止。

---

### 4.3 实战案例 3：第三方大模型统一集成规范
文件路径：[model-provider-integrator SKILL.md](file:///d:/code/dianshang/.agents/skills/model-provider-integrator/SKILL.md)

**核心内容**：
- 规范新增大模型（如接入 MiniMax、DeepSeek、Kling 等）的统一步骤；
- 必须实现 `BaseLLMClient` 统一接口；
- 必须在 `app/clients/provider_factory.py` 中注册；
- 必须提供 Mock 离线降级开关，保障在无网络或额度欠费时单测仍然能 100% 跑通。

---

## 五、Skill 的日常使用、调试与团队共享协作

### 5.1 显式触发 vs 自动隐式触发
1. **自动隐式触发**：你直接提问：*“帮我看看现在的广告法质检为什么没拦住‘顶级’这个词？”*，智能体自动激活该 Skill 并按照既定规范修复代码。
2. **显式触发**：你可以直接指定：*“请使用 ad-compliance-checker 技能，帮我重新审查 app/agent/nodes/quality_reviewer.py 的逻辑。”*

### 5.2 团队 Git 共享
将 `.agents/skills/` 目录纳入 Git 版本控制：
```bash
git add .agents/skills/
git commit -m "feat(skills): 沉淀电商合规审核与LangGraph调试核心Skill"
git push
```
这样，团队中的任何成员（无论使用 Claude Code、Cursor 还是 Antigravity）在 `git pull` 后，都能立刻共享该技能包，实现整个团队研发水平与 AI 对齐能力的无缝升级！
