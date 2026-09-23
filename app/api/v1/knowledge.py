from fastapi import APIRouter

router = APIRouter(prefix="/knowledge-docs", tags=["Knowledge"])

@router.get("")
async def list_knowledge_docs():
    return {"code": 200, "data": {"items": [], "total": 0}, "message": "成功"}
