"""
AgenticCommerce — CLI 智能体工作流执行入口
用于脱离 Web 界面直接在命令行触发与调试 7-Agent 生成流程
"""

import sys
import argparse
import asyncio
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import select
from app.clients.postgres import AsyncSessionLocal
from app.models.sku import Sku
from app.models.task import Task
from app.models.base import generate_uuid32
from app.agent.graph import app_workflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("workflow_runner")

async def run_workflow(sku_id: str = "sku_camp01", max_retries: int = 2):
    print("=" * 70)
    print("🚀 AgenticCommerce — 7-Agent 智能体工作流 CLI 调试执行器")
    print("=" * 70)

    # 1. 查找或准备目标 SKU
    async with AsyncSessionLocal() as session:
        sku_res = await session.execute(select(Sku).where((Sku.id == sku_id) | (Sku.code == sku_id)))
        sku_obj = sku_res.scalar_one_or_none()
        if not sku_obj:
            logger.error(f"未找到 SKU: {sku_id}，请先运行 python -m app.scripts.seed_data 注入种子数据！")
            return

        # 2. 创建本次生成任务记录
        task_id = f"task_{generate_uuid32()[:12]}"
        task = Task(
            id=task_id,
            tenant_id=sku_obj.tenant_id,
            sku_id=sku_obj.id,
            status="running",
            current_node="orchestrator",
            retry_count=0,
            config={"model_llm": "qwen", "model_image": "wanx", "model_video": "kling"},
        )
        session.add(task)
        await session.commit()

        target_sku_id = sku_obj.id
        tenant_id = sku_obj.tenant_id
        sku_data = {
            "id": sku_obj.id,
            "code": sku_obj.code,
            "name": sku_obj.name,
            "category": sku_obj.category,
            "specs": sku_obj.specs,
            "description": sku_obj.description,
            "images": sku_obj.images,
        }

    logger.info(f"成功创建执行任务: Task ID = {task_id}")
    logger.info(f"目标商品: [{sku_data['code']}] {sku_data['name']}")

    # 3. 构造 LangGraph 初始状态
    initial_state = {
        "task_id": task_id,
        "tenant_id": tenant_id,
        "sku_id": target_sku_id,
        "sku_data": sku_data,
        "config": {"language": "en", "target_platform": "amazon"},
        "retry_count": 0,
        "max_retries": max_retries,
        "completed_steps": [],
    }

    print("\n▶ 开始启动 LangGraph 状态图流转 (7-Agent P-E-V 循环)...")
    final_state = await app_workflow.ainvoke(initial_state)

    print("\n" + "=" * 70)
    print("✅ 智能体工作流执行完毕！最终结果汇总:")
    print("=" * 70)
    print(f"• 任务 ID: {final_state.get('task_id')}")
    print(f"• 经历阶段: {' -> '.join(final_state.get('completed_steps', []))}")
    print(f"• 质检是否通过: {'是 (PASSED)' if final_state.get('is_passed') else '否 (FAILED)'}")
    
    reports = final_state.get("quality_reports", [])
    if reports:
        last_rep = reports[-1]
        print(f"• 质检综合评分: {last_rep.get('score')} 分")
        print(f"• 各维度得分: {last_rep.get('dimensions')}")
        print(f"• 优化建议: {last_rep.get('suggestions')}")

    plan = final_state.get("creative_plan", {})
    if plan:
        print("\n【生成核心文案】:")
        print(f"• 标题: {plan.get('title')}")
        print("• 五点描述:")
        for b in plan.get("bullets", []):
            print(f"  - {b}")

    images = final_state.get("generated_images", [])
    print(f"\n【生成视觉素材】(共 {len(images)} 张图片):")
    for idx, img in enumerate(images, 1):
        print(f"  [{idx}] 视角: {img.get('sub_type')} | URL: {img.get('url')} (Mock: {img.get('is_mock')})")

    video = final_state.get("generated_video")
    if video:
        print(f"\n【生成带货短视频】: {video.get('url')} (时长: {video.get('duration')}s, Mock: {video.get('is_mock')})")

    print("\n" + "=" * 70)

def main():
    parser = argparse.ArgumentParser(description="AgenticCommerce CLI Workflow Runner")
    parser.add_argument("--sku-id", default="sku_camp01", help="目标商品 SKU ID 或 Code (默认: sku_camp01)")
    parser.add_argument("--retries", type=int, default=2, help="最大质检重试次数 (默认: 2)")
    args = parser.parse_args()

    asyncio.run(run_workflow(sku_id=args.sku_id, max_retries=args.retries))

if __name__ == "__main__":
    main()
