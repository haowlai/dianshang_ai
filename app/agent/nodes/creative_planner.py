"""
CreativePlanner Agent (创意策划智能体)
生成高转化多卖点文案（标题、五点、详情、关键词）及分镜脚本框架
"""

from app.agent.state import AgentState

async def creative_planner_node(state: AgentState) -> dict:
    """生成本土化电商文案及创意规划"""
    return {
        "current_step": "creative_planner",
        "completed_steps": ["creative_planner"],
        "creative_plan": {}
    }
