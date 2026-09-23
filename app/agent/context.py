"""
工作流执行上下文
"""

from typing import Optional
from dataclasses import dataclass

@dataclass
class WorkflowContext:
    task_id: str
    tenant_id: str
    trace_id: str
    user_id: Optional[str] = None
