"""
数据库初始化脚本: 创建全部数据表并校验 pgvector 插件
"""

import asyncio
from app.clients.postgres import engine
from app.models.base import Base

async def init_db():
    print("正在连接数据库并创建数据表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("全部数据表初始化创建完成！")

if __name__ == "__main__":
    asyncio.run(init_db())
