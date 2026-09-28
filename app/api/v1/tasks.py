"""
生成任务与智能体工作流执行调度接口 (Task Router)
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.models.task import Task
from app.models.sku import Sku
from app.models.task_node_run import TaskNodeRun
from app.models.copy import Copy
from app.models.asset import Asset
from app.models.compliance import ComplianceReport
from app.models.base import generate_uuid32

logger = logging.getLogger("tasks_api")
router = APIRouter(prefix="/tasks", tags=["生成任务调度"])

class TaskCreateRequest(BaseModel):
    sku_id: str
    batch_id: Optional[str] = None
    config: Dict[str, Any] = {
        "language": "en",
        "platform": "amazon",
        "model_llm": "qwen",
        "model_image": "wanx",
        "model_video": "kling",
        "max_retries": 2
    }

async def run_agent_workflow_background(task_id: str, tenant_id: str, sku_id: str, config: dict):
    """后台异步触发 7-Agent 工作流"""
    try:
        from app.agent.graph import app_workflow
        # 1. 查询 SKU 详情
        from app.clients.postgres import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            sku_res = await session.execute(select(Sku).where(Sku.id == sku_id))
            sku = sku_res.scalar_one_or_none()
            if not sku:
                logger.error(f"后台工作流执行失败: 找不到 SKU {sku_id}")
                return
            sku_data = {
                "id": sku.id,
                "code": sku.code,
                "name": sku.name,
                "category": sku.category,
                "specs": sku.specs,
                "description": sku.description,
                "images": sku.images,
            }

        initial_state = {
            "task_id": task_id,
            "tenant_id": tenant_id,
            "sku_id": sku_id,
            "sku_data": sku_data,
            "config": config,
            "retry_count": 0,
            "max_retries": config.get("max_retries", 2),
            "completed_steps": [],
        }

        logger.info(f"后台异步启动任务: {task_id}")
        await app_workflow.ainvoke(initial_state)
        logger.info(f"后台任务 {task_id} 顺利执行完成")
    except Exception as e:
        logger.error(f"后台任务 {task_id} 执行遇到严重异常: {str(e)}")

@router.get("")
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    sku_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """分页查询生成任务列表"""
    tenant_id = user_tenant["tenant_id"]
    query = select(Task).where(Task.tenant_id == tenant_id, Task.is_deleted == 0)

    if status:
        query = query.where(Task.status == status)
    if sku_id:
        query = query.where(Task.sku_id == sku_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Task.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    items = []
    for t in tasks:
        # 获取关联 SKU 简要信息
        sku_res = await db.execute(select(Sku.name, Sku.code).where(Sku.id == t.sku_id))
        sku_info = sku_res.first()
        items.append({
            "id": t.id,
            "sku_id": t.sku_id,
            "sku_code": sku_info[1] if sku_info else "",
            "sku_name": sku_info[0] if sku_info else "",
            "batch_id": t.batch_id,
            "status": t.status,
            "current_node": t.current_node,
            "retry_count": t.retry_count,
            "config": t.config,
            "create_time": t.create_time.isoformat() if t.create_time else None,
        })

    return {
        "code": 200,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
        "message": "获取成功"
    }

@router.post("")
async def create_task(
    req: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """新建生成任务并自动调度 7-Agent 工作流"""
    tenant_id = user_tenant["tenant_id"]

    # 验证 SKU 是否存在
    sku_check = await db.execute(select(Sku).where(Sku.id == req.sku_id, Sku.tenant_id == tenant_id))
    if not sku_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="目标商品 SKU 不存在")

    task_id = f"task_{generate_uuid32()[:12]}"
    task = Task(
        id=task_id,
        tenant_id=tenant_id,
        sku_id=req.sku_id,
        batch_id=req.batch_id,
        status="running",
        current_node="orchestrator",
        retry_count=0,
        config=req.config,
        created_by=user_tenant.get("user_id"),
    )
    db.add(task)
    await db.commit()

    # 提交至后台执行
    background_tasks.add_task(
        run_agent_workflow_background,
        task_id=task_id,
        tenant_id=tenant_id,
        sku_id=req.sku_id,
        config=req.config
    )

    return {
        "code": 200,
        "data": {
            "task_id": task_id,
            "status": "running",
            "message": "工作流已成功调度执行"
        },
        "message": "任务创建成功"
    }

@router.get("/{task_id}")
async def get_task_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """获取单个任务详情（含文案产出、素材资产与质检报告）"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(select(Task).where(Task.id == task_id, Task.tenant_id == tenant_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 查询文案
    copy_res = await db.execute(select(Copy).where(Copy.task_id == task_id))
    copy_obj = copy_res.scalar_one_or_none()

    # 查询资产
    asset_res = await db.execute(select(Asset).where(Asset.task_id == task_id))
    assets = asset_res.scalars().all()

    # 查询审核报告
    report_res = await db.execute(select(ComplianceReport).where(ComplianceReport.task_id == task_id))
    report_obj = report_res.scalar_one_or_none()

    # 查询商品
    sku_res = await db.execute(select(Sku).where(Sku.id == task.sku_id))
    sku_obj = sku_res.scalar_one_or_none()

    return {
        "code": 200,
        "data": {
            "task": {
                "id": task.id,
                "sku_id": task.sku_id,
                "sku_name": sku_obj.name if sku_obj else "",
                "sku_code": sku_obj.code if sku_obj else "",
                "status": task.status,
                "current_node": task.current_node,
                "retry_count": task.retry_count,
                "config": task.config,
                "create_time": task.create_time.isoformat() if task.create_time else None,
            },
            "copy": {
                "title": copy_obj.title,
                "bullets": copy_obj.bullets,
                "description": copy_obj.description,
                "keywords": copy_obj.keywords,
            } if copy_obj else None,
            "assets": [
                {
                    "id": a.id,
                    "type": a.type,
                    "sub_type": a.sub_type,
                    "url": a.url,
                    "is_mock": a.is_mock,
                    "meta": a.meta,
                }
                for a in assets
            ],
            "compliance_report": {
                "score": report_obj.score,
                "passed": report_obj.passed,
                "dimensions": report_obj.dimensions,
                "violations": report_obj.violations,
                "suggestions": report_obj.suggestions,
            } if report_obj else None,
        },
        "message": "获取成功"
    }

@router.get("/{task_id}/nodes")
async def get_task_node_runs(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """获取任务节点执行明细列表 (供工作台 DAG 实时渲染)"""
    tenant_id = user_tenant["tenant_id"]
    query = (
        select(TaskNodeRun)
        .where(TaskNodeRun.task_id == task_id, TaskNodeRun.tenant_id == tenant_id)
        .order_by(TaskNodeRun.create_time.asc())
    )
    result = await db.execute(query)
    node_runs = result.scalars().all()

    items = [
        {
            "id": r.id,
            "node_name": r.node_name,
            "status": r.status,
            "elapsed_ms": r.elapsed_ms,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "cost": r.cost,
            "input_data": r.input_data,
            "output_data": r.output_data,
            "create_time": r.create_time.isoformat() if r.create_time else None,
        }
        for r in node_runs
    ]

    return {
        "code": 200,
        "data": {"items": items, "count": len(items)},
        "message": "获取成功"
    }

@router.post("/{task_id}/run")
async def trigger_task_run(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """手动重新触发任务执行"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(select(Task).where(Task.id == task_id, Task.tenant_id == tenant_id))
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await db.execute(
        update(Task).where(Task.id == task_id).values(status="running", current_node="orchestrator")
    )
    await db.commit()

    background_tasks.add_task(
        run_agent_workflow_background,
        task_id=task_id,
        tenant_id=tenant_id,
        sku_id=task.sku_id,
        config=task.config or {}
    )

    return {"code": 200, "data": {"task_id": task_id, "status": "running"}, "message": "重新调度成功"}
