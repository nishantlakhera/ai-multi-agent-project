from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config.settings import settings

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            check_compatibility=False
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self, dim: int = 768):  # Changed from 1536 to 768 for nomic-embed-text
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection_name not in names:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def upsert_documents(self, docs: List[Dict[str, Any]]):
        points = [
            PointStruct(id=d["id"], vector=d["vector"], payload=d["payload"])
            for d in docs
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        from qdrant_client.models import PointStruct, SearchRequest

        res = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            } for r in res.points
        ]

qdrant_service = QdrantService()
