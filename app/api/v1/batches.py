"""
批次任务管理接口 (Batch Router)
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.models.batch import Batch
from app.models.task import Task
from app.models.base import generate_uuid32
from app.api.v1.tasks import run_agent_workflow_background

router = APIRouter(prefix="/batches", tags=["批次生成管理"])

class BatchCreateRequest(BaseModel):
    name: str
    sku_ids: List[str]
    config: Dict[str, Any] = {
        "language": "en",
        "platform": "amazon",
        "model_llm": "qwen",
        "model_image": "wanx",
        "model_video": "kling"
    }

@router.get("")
async def list_batches(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """分页获取批次列表"""
    tenant_id = user_tenant["tenant_id"]
    query = select(Batch).where(Batch.tenant_id == tenant_id, Batch.is_deleted == 0)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Batch.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    batches = result.scalars().all()

    items = [
        {
            "id": b.id,
            "name": b.name,
            "status": b.status,
            "total_count": b.total_count,
            "completed_count": b.completed_count,
            "failed_count": b.failed_count,
            "config": b.config,
            "create_time": b.create_time.isoformat() if b.create_time else None,
        }
        for b in batches
    ]

    return {
        "code": 200,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
        "message": "获取成功"
    }

@router.post("")
async def create_batch(
    req: BatchCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """创建批次并批量生成商品任务"""
    tenant_id = user_tenant["tenant_id"]
    if not req.sku_ids:
        raise HTTPException(status_code=400, detail="sku_ids 不能为空")

    batch_id = f"batch_{generate_uuid32()[:12]}"
    batch = Batch(
        id=batch_id,
        tenant_id=tenant_id,
        name=req.name,
        status="running",
        total_count=len(req.sku_ids),
        completed_count=0,
        failed_count=0,
        config=req.config,
        created_by=user_tenant.get("user_id"),
    )
    db.add(batch)

    # 循环创建任务并提交后台
    for sku_id in req.sku_ids:
        task_id = f"task_{generate_uuid32()[:12]}"
        task = Task(
            id=task_id,
            tenant_id=tenant_id,
            sku_id=sku_id,
            batch_id=batch_id,
            status="running",
            current_node="orchestrator",
            retry_count=0,
            config=req.config,
            created_by=user_tenant.get("user_id"),
        )
        db.add(task)
        background_tasks.add_task(
            run_agent_workflow_background,
            task_id=task_id,
            tenant_id=tenant_id,
            sku_id=sku_id,
            config=req.config
        )

    await db.commit()

    return {
        "code": 200,
        "data": {"batch_id": batch_id, "total_tasks": len(req.sku_ids)},
        "message": "批次任务创建成功并已启动"
    }

@router.get("/{batch_id}")
async def get_batch_detail(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """获取单个批次及下属任务状态"""
    tenant_id = user_tenant["tenant_id"]
    b_res = await db.execute(select(Batch).where(Batch.id == batch_id, Batch.tenant_id == tenant_id))
    batch = b_res.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    tasks_res = await db.execute(select(Task).where(Task.batch_id == batch_id))
    tasks = tasks_res.scalars().all()

    return {
        "code": 200,
        "data": {
            "batch": {
                "id": batch.id,
                "name": batch.name,
                "status": batch.status,
                "total_count": batch.total_count,
                "completed_count": batch.completed_count,
                "failed_count": batch.failed_count,
            },
            "tasks": [
                {"id": t.id, "sku_id": t.sku_id, "status": t.status, "current_node": t.current_node}
                for t in tasks
            ]
        },
        "message": "获取成功"
    }
