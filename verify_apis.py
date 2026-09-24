"""
自动化 API 接口集成验证脚本
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import httpx
from main import app

async def run_tests():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health
        r = await client.get("/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        print("[PASS] 1. 健康检查接口 /health:", r.json())

        # 2. Login
        r = await client.post("/api/v1/auth/login", json={"email": "admin@agentic.com", "password": "admin123"})
        assert r.status_code == 200, f"Login failed: {r.text}"
        token = r.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[PASS] 2. 用户登录认证 /api/v1/auth/login, Token 签发正常")

        # 3. Current User
        r = await client.get("/api/v1/auth/me", headers=headers)
        assert r.status_code == 200
        print("[PASS] 3. 当前用户信息 /api/v1/auth/me:", r.json()["data"]["name"])

        # 4. SKUs List
        r = await client.get("/api/v1/skus", headers=headers)
        assert r.status_code == 200
        total_skus = r.json()["data"]["total"]
        print(f"[PASS] 4. 商品列表 /api/v1/skus: 共有 {total_skus} 款 SKU")

        # 5. Providers List & Test
        r = await client.get("/api/v1/providers", headers=headers)
        assert r.status_code == 200
        provs = r.json()["data"]["items"]
        print(f"[PASS] 5. 模型厂商 /api/v1/providers: 共有 {len(provs)} 家配置厂商")
        for p in provs:
            t_res = await client.post(f"/api/v1/providers/{p['id']}/test", headers=headers)
            assert t_res.status_code == 200
            print(f"       - 连通性测试 [{p['name']}]: {t_res.json()['message']}")

        # 6. Tasks List
        r = await client.get("/api/v1/tasks", headers=headers)
        assert r.status_code == 200
        total_tasks = r.json()["data"]["total"]
        print(f"[PASS] 6. 任务列表 /api/v1/tasks: 共有 {total_tasks} 条任务")

        # 7. Copies List
        r = await client.get("/api/v1/copies", headers=headers)
        assert r.status_code == 200
        print(f"[PASS] 7. 文案库 /api/v1/copies: 共有 {r.json()['data']['total']} 篇生成文案")

        # 8. Assets List
        r = await client.get("/api/v1/assets", headers=headers)
        assert r.status_code == 200
        print(f"[PASS] 8. 素材库 /api/v1/assets: 共有 {r.json()['data']['total']} 个图像/视频资产")

        # 9. Compliance Check
        r = await client.post(
            "/api/v1/compliance/check",
            json={"title": "超轻折叠椅", "content": "采用7075航天铝合金加厚牛津布"},
            headers=headers
        )
        assert r.status_code == 200
        print(f"[PASS] 9. 智能合规检测 /api/v1/compliance/check: 评分 {r.json()['data']['score']} 分")

        # 10. Knowledge Docs
        r = await client.get("/api/v1/knowledge/docs", headers=headers)
        assert r.status_code == 200
        print(f"[PASS] 10. 知识库管理 /api/v1/knowledge/docs: 共有 {r.json()['data']['total']} 份知识文档")

        # 11. Cost Analytics
        r = await client.get("/api/v1/audit/costs", headers=headers)
        assert r.status_code == 200
        c_data = r.json()["data"]
        print(f"[PASS] 11. 成本与 Token 大盘 /api/v1/audit/costs: 累计消耗 {c_data['total_tokens']} Tokens, 费用 ${c_data['total_cost_usd']}")

        # 12. Packages List
        r = await client.get("/api/v1/packages", headers=headers)
        assert r.status_code == 200
        print(f"[PASS] 12. 交付物打包列表 /api/v1/packages: 共有 {r.json()['data']['count']} 份待打包物料")

    print("\n" + "=" * 60)
    print("ALL 12 BACKEND CORE API INTEGRATION TESTS PASSED 100%!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
