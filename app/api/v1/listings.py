from fastapi import APIRouter

router = APIRouter(prefix="/listings", tags=["Listings"])

@router.get("")
async def list_listings():
    # 二期工程功能预留
    return {"code": 200, "data": {"items": [], "total": 0}, "message": "成功"}
