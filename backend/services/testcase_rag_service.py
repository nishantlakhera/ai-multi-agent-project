from typing import List, Dict, Any, Optional
from services.embeddings_service import embeddings_service
from config.settings import settings
from qdrant_client import QdrantClient
from utils.logger import logger

def retrieve_testcase_chunks(query: str, limit: int = 6, filename: Optional[str] = None) -> List[Dict[str, Any]]:
    logger.info(f"[testcase_rag] Retrieving chunks for query={query!r}")
    vector = embeddings_service.embed_query(query)
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        check_compatibility=False,
    )
    collection = settings.TESTCASE_QDRANT_COLLECTION_NAME
    try:
        collections = client.get_collections().collections
        names = [c.name for c in collections]
        if collection not in names:
            logger.warning(f"[testcase_rag] Collection '{collection}' not found")
            return []
    except Exception as e:
        logger.error(f"[testcase_rag] Failed to list collections: {e}")
        return []

    res = client.query_points(
        collection_name=collection,
        query=vector,
        limit=limit,
        with_payload=True,
    )
    results = [
        {
            "id": r.id,
            "score": r.score,
            "payload": r.payload,
        } for r in res.points
    ]

    filtered: List[Dict[str, Any]] = []
    for r in results:
        payload = r.get("payload", {}) or {}
        if filename and payload.get("filename") != filename:
            continue
        text = payload.get("text") or payload.get("content") or ""
        filtered.append({
            "score": r.get("score", 0.0),
            "text": text,
            "metadata": {k: v for k, v in payload.items() if k not in {"text", "content"}},
        })

    return filtered

def format_context(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "NO_RELEVANT_DOCUMENTS"
    parts = []
    for idx, chunk in enumerate(chunks, 1):
        score = chunk.get("score", 0.0)
        meta = chunk.get("metadata", {})
        text = chunk.get("text", "")
        parts.append(f"[Chunk {idx}] (Score: {score:.3f}, Meta: {meta})\n{text}")
    return "\n\n".join(parts)
