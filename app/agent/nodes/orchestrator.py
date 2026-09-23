"""
Orchestrator Agent (编排调度智能体)
"""

from app.agent.state import AgentState

async def orchestrator_node(state: AgentState) -> dict:
    """初始化任务全局参数与路由流向"""
    return {
        "current_step": "orchestrator",
        "completed_steps": ["orchestrator"]
    }
