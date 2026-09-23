from fastapi import APIRouter

router = APIRouter(prefix="/providers", tags=["Providers"])

@router.get("")
async def list_providers():
    return {"code": 200, "data": [], "message": "成功"}
