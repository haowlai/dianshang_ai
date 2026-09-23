from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
async def login():
    return {"code": 200, "data": {}, "message": "成功"}

@router.post("/logout")
async def logout():
    return {"code": 200, "data": None, "message": "成功"}

@router.post("/refresh")
async def refresh_token():
    return {"code": 200, "data": {}, "message": "成功"}
