import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend .env file
backend_env = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(backend_env)

from embeddings.document_loader import load_text_files
from backend.services.embeddings_service import embeddings_service
from backend.services.qdrant_service import qdrant_service

def run_ingestion():
    docs = load_text_files("data/docs")
    texts = [d["text"] for d in docs]
    if not texts:
        print("No docs found in data/docs")
        return
    vectors = embeddings_service.embed_texts(texts)

    qdrant_docs = []
    for d, v in zip(docs, vectors):
        qdrant_docs.append(
            {
                "id": d["id"],
                "vector": v,
                "payload": {
                    "text": d["text"],
                    **d["meta"],
                },
            }
        )

    qdrant_service.upsert_documents(qdrant_docs)
    print(f"Ingested {len(qdrant_docs)} docs into Qdrant.")

if __name__ == "__main__":
    run_ingestion()
