"""
用户与认证接口 (Auth Router)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user_and_tenant
from app.core.security import verify_password, create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证管理"])

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    code: int = 200
    data: dict
    message: str = "登录成功"

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户邮箱密码登录，签发 JWT Access Token"""
    query = select(User).where(User.email == req.email, User.is_deleted == 0)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱或密码错误"
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用"
        )

    token_payload = {
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }
    access_token = create_access_token(token_payload)

    return {
        "code": 200,
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "tenant_id": user.tenant_id
            }
        },
        "message": "登录成功"
    }

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user_and_tenant)):
    """获取当前登录用户信息与租户上下文"""
    return {
        "code": 200,
        "data": user,
        "message": "获取成功"
    }

@router.post("/refresh")
async def refresh_token(user: dict = Depends(get_current_user_and_tenant)):
    """刷新访问令牌"""
    new_token = create_access_token(user)
    return {
        "code": 200,
        "data": {
            "access_token": new_token,
            "token_type": "bearer"
        },
        "message": "令牌刷新成功"
    }
