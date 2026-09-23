"""
ImageGenerator Agent (图片生成智能体)
并发调用图像大模型 API (通义万相 Wan 2.1 等) 并落盘 MinIO
"""

from app.agent.state import AgentState

async def image_generator_node(state: AgentState) -> dict:
    """批量渲染主图与场景卖点图"""
    return {
        "current_step": "image_generator",
        "completed_steps": ["image_generator"],
        "generated_images": []
    }
