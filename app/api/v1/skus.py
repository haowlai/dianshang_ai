"""
商品 SKU 管理接口 (SKU Router)
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.models.sku import Sku

router = APIRouter(prefix="/skus", tags=["商品SKU管理"])

class SkuCreateRequest(BaseModel):
    code: str
    name: str
    category: str
    specs: Dict[str, Any] = {}
    description: Optional[str] = None
    images: List[str] = []

class SkuUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    specs: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None

@router.get("")
async def list_skus(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """分页查询商品 SKU 列表"""
    tenant_id = user_tenant["tenant_id"]
    query = select(Sku).where(Sku.tenant_id == tenant_id, Sku.is_deleted == 0)

    if q:
        query = query.where((Sku.code.ilike(f"%{q}%")) | (Sku.name.ilike(f"%{q}%")))
    if category:
        query = query.where(Sku.category == category)

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页列表
    query = query.order_by(Sku.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    skus = result.scalars().all()

    items = [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "category": s.category,
            "specs": s.specs,
            "description": s.description,
            "images": s.images,
            "create_time": s.create_time.isoformat() if s.create_time else None,
        }
        for s in skus
    ]

    return {
        "code": 200,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        },
        "message": "获取成功"
    }

@router.post("")
async def create_sku(
    req: SkuCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """新建商品 SKU"""
    tenant_id = user_tenant["tenant_id"]
    # 检查 code 是否已存在
    check = await db.execute(
        select(Sku).where(Sku.tenant_id == tenant_id, Sku.code == req.code, Sku.is_deleted == 0)
    )
    if check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"商品编码 {req.code} 已存在")

    sku = Sku(
        tenant_id=tenant_id,
        code=req.code,
        name=req.name,
        category=req.category,
        specs=req.specs,
        description=req.description,
        images=req.images,
        created_by=user_tenant.get("user_id"),
    )
    db.add(sku)
    await db.commit()
    await db.refresh(sku)

    return {
        "code": 200,
        "data": {
            "id": sku.id,
            "code": sku.code,
            "name": sku.name,
        },
        "message": "商品创建成功"
    }

@router.get("/{sku_id}")
async def get_sku(
    sku_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """获取单个商品 SKU 详情"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(
        select(Sku).where(Sku.tenant_id == tenant_id, Sku.id == sku_id, Sku.is_deleted == 0)
    )
    sku = res.scalar_one_or_none()
    if not sku:
        raise HTTPException(status_code=404, detail="商品 SKU 不存在")

    return {
        "code": 200,
        "data": {
            "id": sku.id,
            "code": sku.code,
            "name": sku.name,
            "category": sku.category,
            "specs": sku.specs,
            "description": sku.description,
            "images": sku.images,
            "create_time": sku.create_time.isoformat() if sku.create_time else None,
        },
        "message": "获取成功"
    }

@router.put("/{sku_id}")
async def update_sku(
    sku_id: str,
    req: SkuUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """更新商品 SKU 信息"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(
        select(Sku).where(Sku.tenant_id == tenant_id, Sku.id == sku_id, Sku.is_deleted == 0)
    )
    sku = res.scalar_one_or_none()
    if not sku:
        raise HTTPException(status_code=404, detail="商品 SKU 不存在")

    update_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    if update_dict:
        await db.execute(
            update(Sku).where(Sku.id == sku_id).values(**update_dict)
        )
        await db.commit()

    return {"code": 200, "data": {"id": sku_id}, "message": "更新成功"}

@router.delete("/{sku_id}")
async def delete_sku(
    sku_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """逻辑删除商品 SKU"""
    tenant_id = user_tenant["tenant_id"]
    await db.execute(
        update(Sku).where(Sku.tenant_id == tenant_id, Sku.id == sku_id).values(is_deleted=1)
    )
    await db.commit()
    return {"code": 200, "data": {"id": sku_id}, "message": "删除成功"}
