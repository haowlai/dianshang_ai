"""
AI 模型厂商工厂 (支持 LLM / 生图 / 生视频 厂商插件化切换)
"""

class ProviderFactory:
    @staticmethod
    def get_llm_client(provider_type: str = "qwen"):
        # 默认通义千问，可切换 OpenAI / SenseNova
        pass

    @staticmethod
    def get_image_client(provider_type: str = "wanx"):
        # 默认通义万相，可切换商汤秒画
        pass

    @staticmethod
    def get_video_client(provider_type: str = "kling"):
        # 默认快手可灵 Kling
        pass
