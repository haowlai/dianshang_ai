"""
VideoGenerator Agent (视频生成智能体)
调用视频大模型 API (快手可灵 Kling AI 等) 生成短视频
"""

from app.agent.state import AgentState

async def video_generator_node(state: AgentState) -> dict:
    """生成商品动态展示短视频"""
    return {
        "current_step": "video_generator",
        "completed_steps": ["video_generator"],
        "generated_video": None
    }
