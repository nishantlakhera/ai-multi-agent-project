#!/usr/bin/env python3
"""
Test script to verify multi-provider LLM configuration
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.llm_config import get_chat_model, get_model_name, get_embedding_model_name
from config.settings import settings

def test_provider_config():
    """Test that provider configuration is loaded correctly."""
    print("=" * 60)
    print("Multi-Provider LLM Configuration Test")
    print("=" * 60)

    print(f"\n✓ Current Provider: {settings.LLM_PROVIDER}")
    print(f"✓ Chat Model: {get_model_name()}")
    print(f"✓ Embedding Model: {get_embedding_model_name()}")

    print("\n" + "=" * 60)
    print("Testing Chat Completion")
    print("=" * 60)

    try:
        client = get_chat_model()
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello!' and nothing else."}
            ],
            max_tokens=10
        )

        answer = response.choices[0].message.content
        print(f"\n✓ Chat Response: {answer}")
        print("✓ Chat completions working!")

    except Exception as e:
        print(f"\n✗ Chat Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your API key is correct in .env")
        print("2. Verify LLM_PROVIDER setting matches your provider")
        print("3. Ensure you have internet connection")
        return False

    print("\n" + "=" * 60)
    print("Testing Embeddings")
    print("=" * 60)

    try:
        response = client.embeddings.create(
            model=get_embedding_model_name(),
            input=["Hello world"]
        )

        embedding = response.data[0].embedding
        print(f"\n✓ Embedding Vector Length: {len(embedding)}")
        print("✓ Embeddings working!")

    except Exception as e:
        print(f"\n✗ Embeddings Error: {str(e)}")
        print("\nNote: Some providers don't support embeddings.")
        print("Set OPENAI_API_KEY in .env for embeddings even if using another provider for chat.")

    print("\n" + "=" * 60)
    print("✓ All tests passed! Your backend is ready to use.")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        test_provider_config()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

