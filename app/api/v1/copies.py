"""
文案库管理接口 (Copy Router)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.models.copy import Copy
from app.models.sku import Sku

router = APIRouter(prefix="/copies", tags=["文案管理"])

class CopyUpdateRequest(BaseModel):
    title: Optional[str] = None
    bullets: Optional[List[str]] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: Optional[str] = None

@router.get("")
async def list_copies(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sku_id: Optional[str] = None,
    task_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """分页查询文案列表"""
    tenant_id = user_tenant["tenant_id"]
    query = select(Copy).where(Copy.tenant_id == tenant_id, Copy.is_deleted == 0)

    if sku_id:
        query = query.where(Copy.sku_id == sku_id)
    if task_id:
        query = query.where(Copy.task_id == task_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Copy.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    copies = result.scalars().all()

    items = []
    for c in copies:
        sku_res = await db.execute(select(Sku.name, Sku.code).where(Sku.id == c.sku_id))
        sku_info = sku_res.first()
        items.append({
            "id": c.id,
            "task_id": c.task_id,
            "sku_id": c.sku_id,
            "sku_name": sku_info[0] if sku_info else "",
            "sku_code": sku_info[1] if sku_info else "",
            "language": c.language,
            "title": c.title,
            "bullets": c.bullets,
            "description": c.description,
            "keywords": c.keywords,
            "status": c.status,
            "create_time": c.create_time.isoformat() if c.create_time else None,
        })

    return {
        "code": 200,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
        "message": "获取成功"
    }

@router.get("/{copy_id}")
async def get_copy(
    copy_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """获取单个文案详情"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(select(Copy).where(Copy.id == copy_id, Copy.tenant_id == tenant_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="文案不存在")

    return {
        "code": 200,
        "data": {
            "id": c.id,
            "task_id": c.task_id,
            "sku_id": c.sku_id,
            "language": c.language,
            "title": c.title,
            "bullets": c.bullets,
            "description": c.description,
            "keywords": c.keywords,
            "status": c.status,
            "create_time": c.create_time.isoformat() if c.create_time else None,
        },
        "message": "获取成功"
    }

@router.put("/{copy_id}")
async def update_copy(
    copy_id: str,
    req: CopyUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """人工修改并调整文案"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(select(Copy).where(Copy.id == copy_id, Copy.tenant_id == tenant_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="文案不存在")

    update_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    if update_dict:
        await db.execute(update(Copy).where(Copy.id == copy_id).values(**update_dict))
        await db.commit()

    return {"code": 200, "data": {"id": copy_id}, "message": "文案保存成功"}
