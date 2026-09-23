"""
初始化演示种子数据（初始租户、初始管理员、默认模型厂商配置）
"""

import asyncio

async def seed_data():
    print("正在导入初始种子数据（租户、管理员、默认厂商配置）...")
    # 待导入种子数据
    print("种子数据初始化完毕！")

if __name__ == "__main__":
    asyncio.run(seed_data())
