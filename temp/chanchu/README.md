# AgenticCommerce 教学与实操通关全景索引手册

> 欢迎查阅 **AgenticCommerce（自主智能体电商融合平台）** 超级完整教学与工程交付套件！  
> 本套套件专为**有一点编程基础但没做过 AI 项目的学生/学员**量身定制，涵盖 7-Agent 工作流精讲、4 种部署模式、自动化运维与数据迁移、AI Skill 体系构建、Vibe Coding 十步全流程提示词、以及硬件与模型显存选型。

---

## 📚 教学套件全景导航目录

| 序号 | 交付文档名称 | 核心知识点与教学价值 | 直接打开链接 |
| :---: | :--- | :--- | :---: |
| **01** | **全链路架构与核心代码逐行精讲** | • 7-Agent LangGraph 状态机与 P-E-V 闭环拓扑<br>• 端到端调用流转图谱（从点击到 WebSocket 推流）<br>• 12 个核心文件逐行带完整注释代码拆解<br>• 14 张实体表关系与 pgvector 向量检索原理 | [点击打开 01 文档](file:///d:/code/dianshang/temp/chanchu/01_%E5%85%A8%E9%93%BE%E8%B7%AF%E6%9E%B6%E6%9E%84%E4%B8%8E%E6%A0%B8%E5%BF%83%E4%BB%A3%E7%A0%81%E9%80%90%E8%A1%8C%E7%B2%BE%E8%AE%B2.md) |
| **02** | **多环境部署实战（原生 / Docker / K8s）** | • 方案一：Ubuntu 22.04 裸机安装、uv 环境、Systemd 守护进程<br>• 方案二：Docker Compose 6 容器统一编排与健康检查<br>• 方案三：K8s 生产全套清单（PVC、StatefulSet、HPA、Ingress） | [点击打开 02 文档](file:///d:/code/dianshang/temp/chanchu/02_%E5%A4%9A%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2%E5%AE%9E%E6%88%98_%E5%8E%9F%E7%94%9F_Docker_K8s.md) |
| **03** | **阿里云服务器宝塔面板零基础部署指南** | • 阿里云 ECS 实例规格选购与安全组端口放行避坑<br>• 宝塔面板一键安装与可视化管理<br>• pgvector 扩展编译、MinIO 容器化拉起<br>• Python 项目管理器守护、Vue3 托管、反向代理与免费 SSL | [点击打开 03 文档](file:///d:/code/dianshang/temp/chanchu/03_%E9%98%BF%E9%87%8C%E4%BA%91%E6%9C%8D%E5%8A%A1%E5%99%A8%E5%AE%9D%E5%A1%94%E9%9D%A2%E6%9D%BF%E9%9B%B6%E5%9F%BA%E7%A1%80%E9%83%A8%E7%BD%B2%E6%8C%87%E5%8D%97.md) |
| **04** | **运维管理与数据库迁移实战** | • `init_db.py` 与 `seed_data.py` 数据灌入原理<br>• 生产高频 ALTER TABLE 增量变更 SQL 汇总<br>• HNSW vs IVFFlat 向量索引调优<br>• pg_dump 自动定时备份+压缩+告警脚本与巡检脚本 | [点击打开 04 文档](file:///d:/code/dianshang/temp/chanchu/04_%E8%BF%90%E7%BB%B4%E7%AE%A1%E7%90%86%E4%B8%8E%E6%95%B0%E6%8D%AE%E5%BA%93%E8%BF%81%E7%A7%BB%E5%AE%9E%E6%88%98.md) |
| **05** | **AI Agent Skill 开发与使用指南** | • 什么是 Skill？它与 System Prompt / Rules 的本质区别<br>• SKILL.md 规范与 YAML Frontmatter 格式要求<br>• 让 Claude Code 自动生成 Skill 的元提示词模板<br>• 广告合规、LangGraph 调试等实战技能剖析 | [点击打开 05 文档](file:///d:/code/dianshang/temp/chanchu/05_AI_Agent_Skill%E5%BC%80%E5%8F%91%E4%B8%8E%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.md) |
| **06** | **Vibe Coding 全流程提示词手册** | • 真实从 0 到 1 十步实操 Prompt 清单<br>• 覆盖 uv init、数据库模型、三层架构、Agent 图、WebSocket、前端页面与端到端自愈测试<br>• 每一个步骤包含：目标说明 + 完整Prompt + 预期交付物 | [点击打开 06 文档](file:///d:/code/dianshang/temp/chanchu/06_Vibe_Coding%E5%85%A8%E6%B5%81%E7%A8%8B%E6%8F%90%E7%A4%BA%E8%AF%8D%E6%89%8B%E5%86%8C.md) |
| **07** | **硬件配置与模型显存算力选型指南** | • 个人开发电脑硬件推荐（CPU、内存 16G/32G 瓶颈分析）<br>• 阿里云 ECS 服务器生产选型与流量计费避坑<br>• 本地跑 Qwen2.5 / SDXL / Flux 显存严密计算公式<br>• 云端商业 API 调用成本模型与自建算力决策矩阵 | [点击打开 07 文档](file:///d:/code/dianshang/temp/chanchu/07_%E7%A1%AC%E4%BB%B6%E9%85%8D%E7%BD%AE%E4%B8%8E%E6%A8%A1%E5%9E%8B%E6%98%BE%E5%AD%98%E7%AE%97%E5%8A%9B%E9%80%89%E5%9E%8B%E6%8C%87%E5%8D%97.md) |

---

## 🎯 建议教学讲授与学习路径

1. **第一天（建立全局认知与动手跑通）**：
   - 学习 `01_全链路架构与核心代码逐行精讲.md`，搞懂 7 个 Agent 是怎么开会分工的、什么是 P-E-V 闭环；
   - 按照 `02_多环境部署实战_原生_Docker_K8s.md` 的方案二，用 Docker Compose 在本地 5 分钟跑通。
2. **第二天（掌握现代 AI 编程利器）**：
   - 学习 `06_Vibe_Coding全流程提示词手册.md`，打开 Claude Code 体验从零搭建一个功能模块；
   - 学习 `05_AI_Agent_Skill开发与使用指南.md`，为自己团队定制第一个 Agent Skill。
3. **第三天（云端上线交付与生产运维）**：
   - 学习 `03_阿里云服务器宝塔面板零基础部署指南.md`，跟着截图级指令将项目上线到阿里云公网，配置域名与 SSL；
   - 学习 `04_运维管理与数据库迁移实战.md`，运行备份脚本与 ALTER 变更语句；
   - 参考 `07_硬件配置与模型显存算力选型指南.md`，评估商用化算力预算。
