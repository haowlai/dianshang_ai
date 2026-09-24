"""
知识库与 RAG 向量管理接口 (Knowledge Router)
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.models.knowledge import KnowledgeBaseDoc, KnowledgeChunk
from app.models.base import generate_uuid32
from app.clients.provider_factory import ProviderFactory

router = APIRouter(prefix="/knowledge", tags=["知识库RAG管理"])

class DocCreateRequest(BaseModel):
    category: str
    doc_type: str
    name: str
    content: str

class QueryTestRequest(BaseModel):
    query_text: str
    top_k: int = 3

@router.get("/docs")
async def list_docs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """分页获取知识库文档列表"""
    tenant_id = user_tenant["tenant_id"]
    query = select(KnowledgeBaseDoc).where(KnowledgeBaseDoc.tenant_id == tenant_id, KnowledgeBaseDoc.is_deleted == 0)

    if category:
        query = query.where(KnowledgeBaseDoc.category == category)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(KnowledgeBaseDoc.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    docs = result.scalars().all()

    items = [
        {
            "id": d.id,
            "category": d.category,
            "doc_type": d.doc_type,
            "name": d.name,
            "vector_status": d.vector_status,
            "create_time": d.create_time.isoformat() if d.create_time else None,
        }
        for d in docs
    ]

    return {
        "code": 200,
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
        "message": "获取成功"
    }

@router.post("/docs")
async def create_doc(
    req: DocCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """录入新知识库文档并执行向量切片"""
    tenant_id = user_tenant["tenant_id"]
    doc_id = f"doc_{generate_uuid32()[:12]}"
    
    doc = KnowledgeBaseDoc(
        id=doc_id,
        tenant_id=tenant_id,
        category=req.category,
        doc_type=req.doc_type,
        name=req.name,
        vector_status="indexed",
        created_by=user_tenant.get("user_id"),
    )
    db.add(doc)

    # 简易切片与 Embedding
    llm_client = ProviderFactory.get_llm_client()
    embedding = await llm_client.get_embedding(req.content)

    chunk = KnowledgeChunk(
        id=f"chunk_{generate_uuid32()[:12]}",
        tenant_id=tenant_id,
        doc_id=doc_id,
        doc_type=req.doc_type,
        chunk_index=1,
        content=req.content,
        embedding=embedding,
        metadata_json={"name": req.name, "category": req.category},
        created_by=user_tenant.get("user_id"),
    )
    db.add(chunk)
    await db.commit()

    return {"code": 200, "data": {"doc_id": doc_id}, "message": "知识库文档创建并向量化成功"}

@router.get("/docs/{doc_id}")
async def get_doc_detail(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """获取知识库文档详情与对应分块"""
    tenant_id = user_tenant["tenant_id"]
    res = await db.execute(
        select(KnowledgeBaseDoc).where(KnowledgeBaseDoc.id == doc_id, KnowledgeBaseDoc.tenant_id == tenant_id)
    )
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="文档不存在")

    chunks_res = await db.execute(select(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc_id))
    chunks = chunks_res.scalars().all()

    return {
        "code": 200,
        "data": {
            "id": d.id,
            "category": d.category,
            "doc_type": d.doc_type,
            "name": d.name,
            "vector_status": d.vector_status,
            "chunks": [
                {"id": c.id, "index": c.chunk_index, "content": c.content}
                for c in chunks
            ]
        },
        "message": "获取成功"
    }

@router.post("/query")
async def test_vector_search(
    req: QueryTestRequest,
    db: AsyncSession = Depends(get_db),
    user_tenant: dict = Depends(get_current_user_and_tenant),
):
    """测试向量相似度召回 (RAG 调试)"""
    tenant_id = user_tenant["tenant_id"]
    llm_client = ProviderFactory.get_llm_client()
    q_vec = await llm_client.get_embedding(req.query_text)

    # 检索分块
    query = (
        select(KnowledgeChunk)
        .where(KnowledgeChunk.tenant_id == tenant_id)
        .order_by(KnowledgeChunk.embedding.cosine_distance(q_vec))
        .limit(req.top_k)
    )
    result = await db.execute(query)
    chunks = result.scalars().all()

    return {
        "code": 200,
        "data": {
            "query": req.query_text,
            "results": [
                {"id": c.id, "content": c.content, "doc_type": c.doc_type}
                for c in chunks
            ]
        },
        "message": "检索完成"
    }
