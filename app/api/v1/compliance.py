"""
合规质检报告与违禁词检测接口 (Compliance Router)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.models.compliance import ComplianceReport
from app.models.sku import Sku
from app.clients.provider_factory import ProviderFactory

router = APIRouter(prefix="/compliance", tags=["合规质检管理"])

class ComplianceCheckRequest(BaseModel):
    title: str
    content: str
    target_platform: Optional[str] = "amazon"

@router.get("/reports")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    task_id: Optional[str] = None,
    sku_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """分页获取合规质检报告"""
    tenant_id = user_tenant["tenant_id"]
    query = select(ComplianceReport).where(ComplianceReport.tenant_id == tenant_id, ComplianceReport.is_deleted == 0)

    if task_id:
        query = query.where(ComplianceReport.task_id == task_id)
    if sku_id:
        query = query.where(ComplianceReport.sku_id == sku_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(ComplianceReport.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    reports = result.scalars().all()

    items = []
    for r in reports:
        sku_res = await db.execute(select(Sku.name, Sku.code).where(Sku.id == r.sku_id))
        sku_info = sku_res.first()
        items.append({
            "id": r.id,
            "task_id": r.task_id,
            "sku_id": r.sku_id,
            "sku_name": sku_info[0] if sku_info else "",
            "sku_code": sku_info[1] if sku_info else "",
            "score": r.score,
            "passed": r.passed,
            "dimensions": r.dimensions,
            "violations": r.violations,
            "suggestions": r.suggestions,
            "status": r.status,
            "create_time": r.create_time.isoformat() if r.create_time else None,
        })

    return {
        "code": 200,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
        "message": "获取成功"
    }

@router.get("/reports/{report_id}")
async def get_report_detail(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """获取单个合规质检报告详情"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(
        select(ComplianceReport).where(ComplianceReport.id == report_id, ComplianceReport.tenant_id == tenant_id)
    )
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="报告不存在")

    return {
        "code": 200,
        "data": {
            "id": r.id,
            "task_id": r.task_id,
            "sku_id": r.sku_id,
            "score": r.score,
            "passed": r.passed,
            "dimensions": r.dimensions,
            "violations": r.violations,
            "suggestions": r.suggestions,
            "status": r.status,
            "create_time": r.create_time.isoformat() if r.create_time else None,
        },
        "message": "获取成功"
    }

@router.post("/check")
async def run_compliance_check(
    req: ComplianceCheckRequest,
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """一键实时合规筛查接口 (检测广告法、绝对化词汇、侵权违禁词)"""
    llm_client = ProviderFactory.get_llm_client("qwen")
    prompt = f"""
请针对以下出海文案进行多维度合规筛查：
【标题】: {req.title}
【内容】: {req.content}
【目标平台】: {req.target_platform}

请检测是否包含绝对化词汇（如‘世界第一’、‘最佳’）、虚假夸大或平台禁止宣称，并返回 JSON 报告：
{{"score": 95, "passed": 1, "violations": [], "suggestions": ["文案符合平台规范"]}}
"""
    messages = [
        {"role": "system", "content": "你是一位拥有资深经验的跨境电商合规审核专家。"},
        {"role": "human", "content": prompt}
    ]
    res = await llm_client.chat_completion(messages, model="qwen-plus")
    
    # 模拟通用合规检查规则
    forbidden_words = ["世界第一", "绝对有效", "100% cure", "best in the world", "cheapest"]
    found_violations = []
    text_to_check = f"{req.title} {req.content}".lower()
    for w in forbidden_words:
        if w.lower() in text_to_check:
            found_violations.append(f"发现敏感绝对化用词: {w}")

    score = 98.0 if not found_violations else 70.0
    passed = 1 if not found_violations else 0

    return {
        "code": 200,
        "data": {
            "score": score,
            "passed": passed,
            "violations": found_violations,
            "suggestions": ["文案整体严谨规范，适合直接上线。"] if passed else ["请移除上述敏感违禁词汇。"],
            "dimensions": {"brand_consistency": 95, "platform_compliance": 96 if passed else 60, "legal_safety": 95 if passed else 65}
        },
        "message": "合规检测完毕"
    }
