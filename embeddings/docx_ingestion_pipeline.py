from pathlib import Path
import sys
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load backend .env file
backend_env = ROOT_DIR / "backend" / ".env"
load_dotenv(backend_env)

from embeddings.docx_loader import load_docx_files
from embeddings.doc_loader import load_doc_files
from backend.services.embeddings_service import embeddings_service
from backend.config.settings import settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

def _ensure_collection(client: QdrantClient, name: str, dim: int = 768):
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    if name not in names:
        client.recreate_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

def run_docx_ingestion(folder: str = "data/docs"):
    docs = load_docx_files(folder) + load_doc_files(folder)
    texts = [d["text"] for d in docs]
    if not texts:
        print(f"No .docx or .doc docs found in {folder}")
        return

    vectors = embeddings_service.embed_texts(texts)

    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        check_compatibility=False,
    )
    collection = settings.TESTCASE_QDRANT_COLLECTION_NAME
    _ensure_collection(client, collection)

    points = []
    for d, v in zip(docs, vectors):
        points.append(
            PointStruct(
                id=d["id"],
                vector=v,
                payload={
                    "text": d["text"],
                    **d["meta"],
                },
            )
        )

    client.upsert(collection_name=collection, points=points)
    print(f"Ingested {len(points)} .docx/.doc chunks into Qdrant collection '{collection}'.")

if __name__ == "__main__":
    run_docx_ingestion()
