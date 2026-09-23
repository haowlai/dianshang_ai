"""
统一大模型实例延迟初始化与厂商适配
"""

from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel

def get_chat_model(provider: str = "qwen", model_name: Optional[str] = None, temperature: float = 0.7) -> BaseChatModel:
    # 待具体厂商客户端接入
    pass
