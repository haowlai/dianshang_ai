from fastapi import APIRouter

router = APIRouter(prefix="/packages", tags=["Packages"])

@router.post("")
async def create_package():
    return {"code": 200, "data": {"package_id": "mock_package_id", "status": "processing"}, "message": "打包任务已创建"}
