"""
LangChain configuration and utilities
Provides ChatOpenAI instances configured for different providers
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from config.settings import settings
from typing import Optional

def get_langchain_llm(temperature: float = 0.7, max_tokens: Optional[int] = None) -> ChatOpenAI:
    """
    Get LangChain ChatOpenAI instance configured based on provider
    
    Args:
        temperature: Controls randomness (0 = deterministic, 1 = creative)
        max_tokens: Maximum tokens in response
        
    Returns:
        Configured ChatOpenAI instance
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        # Ollama's OpenAI-compatible endpoint is at /v1
        base = (settings.LLM_BASE_URL or settings.OLLAMA_BASE_URL).rstrip('/')
        return ChatOpenAI(
            model=settings.LLM_MODEL or settings.OLLAMA_MODEL,
            openai_api_base=f"{base}/v1",
            api_key="ollama",  # Ollama doesn't need a real key
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=settings.LLM_MODEL or settings.OPENROUTER_MODEL,
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY or settings.LLM_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "groq":
        return ChatOpenAI(
            model=settings.LLM_MODEL or settings.GROQ_MODEL,
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY or settings.LLM_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:  # Default OpenAI
        return ChatOpenAI(
            model=settings.LLM_MODEL or settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY or settings.LLM_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def create_chat_prompt(system_template: str, human_template: str) -> ChatPromptTemplate:
    """
    Create a ChatPromptTemplate with system and human messages
    
    Args:
        system_template: Template for system message
        human_template: Template for human message
        
    Returns:
        ChatPromptTemplate instance
    """
    return ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template)
    ])
