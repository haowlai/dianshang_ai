from fastapi import APIRouter

router = APIRouter(prefix="/skus", tags=["SKUs"])

@router.get("")
async def list_skus():
    return {"code": 200, "data": {"items": [], "total": 0}, "message": "成功"}
