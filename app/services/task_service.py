from .base import BaseService

class TaskService(BaseService):
    async def create_batch_and_tasks(self, tenant_id: str, user_id: str, data: dict):
        # 待接入批次与任务创建
        return {}
