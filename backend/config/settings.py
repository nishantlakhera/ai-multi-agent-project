from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Provider Configuration
    LLM_PROVIDER: str = "ollama"  # openai, openrouter, groq, gemini, ollama
    LLM_BASE_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None

    # OpenAI (fallback/default)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"

    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # Google Gemini
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"

    # Ollama (Local)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    POSTGRES_DSN: str = "postgresql://postgres:postgres@localhost:5432/ai_app"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "documents"

    MCP_SERVICE_URL: str = "http://localhost:8001"

    # Redis (optional cache)
    REDIS_URL: Optional[str] = None
    REDIS_HISTORY_TTL_SECONDS: int = 3600
    REDIS_HISTORY_MAX_ITEMS: int = 50

    ENV: str = "dev"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
