from fastapi import APIRouter

router = APIRouter(prefix="/compliance-reports", tags=["Compliance"])

@router.get("/{id}")
async def get_compliance_report(id: str):
    return {"code": 200, "data": {"id": id}, "message": "成功"}
