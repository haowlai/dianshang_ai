from .base import BaseService

class KnowledgeService(BaseService):
    async def process_and_vectorize_doc(self, tenant_id: str, doc_id: str):
        # 待接入文档分块与 text-embedding-v4 嵌入计算
        return True
