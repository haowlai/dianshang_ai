"""
FastAPI 依赖注入（租户上下文、当前用户、数据库会话）
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token

async def get_current_user_and_tenant(
    authorization: Optional[str] = Header(None)
) -> dict:
    """从 JWT Authorization 头解析租户 ID 与当前用户信息"""
    if not authorization or not authorization.startswith("Bearer "):
        # 演示/开发兼容模式
        return {"user_id": "00000000000000000000000000000001", "tenant_id": "00000000000000000000000000000001", "role": "tenant_admin"}
    
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或过期的访问令牌")
