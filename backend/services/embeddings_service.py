from typing import List
from config.llm_config import get_chat_model, get_embedding_model_name

client = get_chat_model()

class EmbeddingsService:
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        model_name = get_embedding_model_name()
        resp = client.embeddings.create(
            model=model_name,
            input=texts,
        )
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]

embeddings_service = EmbeddingsService()
