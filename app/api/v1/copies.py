from fastapi import APIRouter

router = APIRouter(prefix="/copies", tags=["Copies"])

@router.get("/{id}")
async def get_copy(id: str):
    return {"code": 200, "data": {"id": id}, "message": "成功"}
