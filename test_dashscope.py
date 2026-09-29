import os
import asyncio
import httpx
import time

API_KEY = "sk-ws-H.PRMHDPL.8Vhp.MEUCIQDUCgPlmM8zhoXBgoo_Cvx3Fhe0EBP4CP4I6Ddf6Q1v5gIgeWwAgMvjhk5_AZrUuEsDZgIPWZZ7pMCy1ZbSP3p7W2g"

async def test_all():
    async with httpx.AsyncClient() as client:
        print("1. Testing Text Embedding...")
        resp = await client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "text-embedding-v4",
                "input": {"texts": ["衣服的质量杠杠的"]}
            }
        )
        print("Embedding Status:", resp.status_code)
        if resp.status_code != 200:
            print(resp.text)
        
        print("\n2. Testing Image Generation (qwen-image-3.0-pro)...")
        # Try user's endpoint first
        resp2 = await client.post(
            "https://llm-pqoya4ttmg66ljtm.cn-beijing.maas.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen-image-3.0-pro",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": "一只可爱的小猫"}]
                        }
                    ]
                },
                "parameters": {"prompt_extend": True}
            },
            timeout=60.0
        )
        print("Image (Custom URL) Status:", resp2.status_code)
        print(resp2.text[:200])

        print("\n3. Testing Video Generation (wan3.0-video)...")
        resp3 = await client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"
            },
            json={
                "model": "wan3.0-video",
                "input": {"prompt": "一只小猫在月光下的屋顶上奔跑，电影级画质。"},
                "parameters": {"resolution": "480P", "ratio": "adaptive", "duration": 5}
            }
        )
        print("Video Status:", resp3.status_code)
        print(resp3.text)

asyncio.run(test_all())
