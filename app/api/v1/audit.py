from fastapi import APIRouter

router = APIRouter(prefix="/audit-logs", tags=["Audit"])

@router.get("")
async def list_audit_logs():
    return {"code": 200, "data": {"items": [], "total": 0}, "message": "成功"}
