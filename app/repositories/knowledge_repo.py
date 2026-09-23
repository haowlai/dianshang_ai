from .base import BaseRepository
from app.models.knowledge import KnowledgeChunk

class KnowledgeRepository(BaseRepository[KnowledgeChunk]):
    def __init__(self, session):
        super().__init__(KnowledgeChunk, session)

    async def search_vectors(self, tenant_id: str, query_vector: list, limit: int = 5, threshold: float = 0.5):
        # 待接入 pgvector <=> 余弦距离计算查询
        return []
