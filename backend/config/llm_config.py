from openai import OpenAI
from config.settings import settings
from typing import Optional

def _get_provider_config():
    """Get provider-specific configuration based on LLM_PROVIDER setting."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openrouter":
        return {
            "api_key": settings.OPENROUTER_API_KEY or settings.LLM_API_KEY,
            "base_url": "https://openrouter.ai/api/v1",
            "model": settings.LLM_MODEL or settings.OPENROUTER_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL or settings.OPENAI_EMBEDDING_MODEL,
        }
    elif provider == "groq":
        return {
            "api_key": settings.GROQ_API_KEY or settings.LLM_API_KEY,
            "base_url": "https://api.groq.com/openai/v1",
            "model": settings.LLM_MODEL or settings.GROQ_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL or settings.OPENAI_EMBEDDING_MODEL,
        }
    elif provider == "gemini":
        # Gemini uses OpenAI-compatible API through LiteLLM or similar
        return {
            "api_key": settings.GOOGLE_API_KEY or settings.LLM_API_KEY,
            "base_url": settings.LLM_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": settings.LLM_MODEL or settings.GEMINI_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL or settings.OPENAI_EMBEDDING_MODEL,
        }
    elif provider == "ollama":
        # Ollama provides OpenAI-compatible API locally
        return {
            "api_key": "ollama",  # Ollama doesn't need an API key, but OpenAI SDK requires one
            "base_url": settings.LLM_BASE_URL or settings.OLLAMA_BASE_URL,
            "model": settings.LLM_MODEL or settings.OLLAMA_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL or settings.OLLAMA_EMBEDDING_MODEL,
        }
    else:  # Default to OpenAI
        return {
            "api_key": settings.OPENAI_API_KEY or settings.LLM_API_KEY,
            "base_url": settings.LLM_BASE_URL,
            "model": settings.LLM_MODEL or settings.OPENAI_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL or settings.OPENAI_EMBEDDING_MODEL,
        }

# Initialize client with provider-specific config
_config = _get_provider_config()
client = OpenAI(
    api_key=_config["api_key"],
    base_url=_config["base_url"]
)

def get_chat_model():
    """Get the configured chat model client."""
    return client

def get_model_name() -> str:
    """Get the configured model name."""
    return _config["model"]

def get_embedding_model_name() -> str:
    """Get the configured embedding model name."""
    return _config["embedding_model"]
