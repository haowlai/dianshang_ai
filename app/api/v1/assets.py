from fastapi import APIRouter

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("")
async def list_assets():
    return {"code": 200, "data": {"items": [], "total": 0}, "message": "成功"}
