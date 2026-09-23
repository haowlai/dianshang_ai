from fastapi import APIRouter

router = APIRouter(prefix="/batches", tags=["Batches"])

@router.get("")
async def list_batches():
    return {"code": 200, "data": {"items": [], "total": 0}, "message": "成功"}
