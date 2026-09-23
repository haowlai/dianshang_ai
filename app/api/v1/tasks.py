from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("")
async def list_tasks():
    return {"code": 200, "data": {"items": [], "total": 0}, "message": "成功"}

@router.get("/{task_id}")
async def get_task(task_id: str):
    return {"code": 200, "data": {"id": task_id}, "message": "成功"}
