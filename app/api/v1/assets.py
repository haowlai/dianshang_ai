"""
素材资产库管理接口 (Asset Router)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.models.asset import Asset
from app.models.sku import Sku

router = APIRouter(prefix="/assets", tags=["素材资产管理"])

class AssetCreateRequest(BaseModel):
    sku_id: str
    task_id: Optional[str] = "manual_upload"
    type: str  # image / video
    sub_type: Optional[str] = "main"
    url: str
    meta: dict = {}

@router.get("")
async def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    type: Optional[str] = None,
    sub_type: Optional[str] = None,
    sku_id: Optional[str] = None,
    task_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """分页查询视觉与视频资产"""
    tenant_id = user_tenant["tenant_id"]
    query = select(Asset).where(Asset.tenant_id == tenant_id, Asset.is_deleted == 0)

    if type:
        query = query.where(Asset.type == type)
    if sub_type:
        query = query.where(Asset.sub_type == sub_type)
    if sku_id:
        query = query.where(Asset.sku_id == sku_id)
    if task_id:
        query = query.where(Asset.task_id == task_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Asset.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    assets = result.scalars().all()

    items = []
    for a in assets:
        sku_res = await db.execute(select(Sku.name, Sku.code).where(Sku.id == a.sku_id))
        sku_info = sku_res.first()
        items.append({
            "id": a.id,
            "task_id": a.task_id,
            "sku_id": a.sku_id,
            "sku_name": sku_info[0] if sku_info else "",
            "sku_code": sku_info[1] if sku_info else "",
            "type": a.type,
            "sub_type": a.sub_type,
            "url": a.url,
            "meta": a.meta,
            "status": a.status,
            "is_mock": a.is_mock,
            "create_time": a.create_time.isoformat() if a.create_time else None,
        })

    return {
        "code": 200,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
        "message": "获取成功"
    }

@router.post("")
async def create_asset(
    req: AssetCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """手动上传/登记素材"""
    tenant_id = user_tenant["tenant_id"]
    asset = Asset(
        tenant_id=tenant_id,
        sku_id=req.sku_id,
        task_id=req.task_id or "manual",
        type=req.type,
        sub_type=req.sub_type,
        url=req.url,
        meta=req.meta,
        status="completed",
        is_mock=0,
        created_by=user_tenant.get("user_id"),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return {"code": 200, "data": {"id": asset.id}, "message": "素材登记成功"}

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """删除素材"""
    tenant_id = user_tenant["tenant_id"]
    await db.execute(
        update(Asset).where(Asset.id == asset_id, Asset.tenant_id == tenant_id).values(is_deleted=1)
    )
    await db.commit()
    return {"code": 200, "data": {"id": asset_id}, "message": "删除成功"}
