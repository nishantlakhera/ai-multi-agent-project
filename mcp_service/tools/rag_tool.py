"""
RAG Tool for MCP Service
Handles vector search and document retrieval from Qdrant
"""
import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from utils.logger import logger
import httpx

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME", "documents")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using Ollama's nomic-embed-text model
    """
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
    except Exception as e:
        logger.error(f"[rag_tool] Embedding generation failed: {e}")
        raise


def search_documents(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search for relevant documents in Qdrant vector database
    
    Args:
        query: User query text
        limit: Maximum number of results to return
        
    Returns:
        Dictionary containing search results and metadata
    """
    try:
        logger.info(f"[rag_tool] Searching for: {query}")
        
        # Initialize Qdrant client
        qdrant_client = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
        
        # Generate query embedding
        query_vector = get_embedding(query)
        
        if not query_vector:
            return {
                "success": False,
                "results": [],
                "error": "Failed to generate embedding for query"
            }
        
        # Search in Qdrant using query_points
        search_results = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            limit=limit,
            with_payload=True,
        ).points
        
        # Format results
        formatted_results = []
        for hit in search_results:
            payload = hit.payload or {}
            formatted_results.append({
                "id": hit.id,
                "score": hit.score,
                "text": payload.get("text") or payload.get("content", ""),
                "metadata": {k: v for k, v in payload.items() if k not in {"text", "content"}}
            })
        
        logger.info(f"[rag_tool] Found {len(formatted_results)} results")
        
        return {
            "success": True,
            "results": formatted_results,
            "query": query,
            "total_results": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"[rag_tool] Search failed: {e}", exc_info=True)
        return {
            "success": False,
            "results": [],
            "error": str(e)
        }


def rag_tool_execute(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Main execution function for RAG tool (called by MCP planner)
    """
    result = search_documents(query, limit)
    if result.get("success"):
        return result.get("results", [])
    else:
        logger.error(f"[rag_tool] Error: {result.get('error')}")
        return []

