#!/usr/bin/env python3
"""
Comprehensive Application Test Script
Tests all components of the AI Multi-Agent backend
"""
import sys
import requests
import json
from time import sleep

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_ollama():
    """Test Ollama service"""
    print_section("Testing Ollama Service")
    try:
        response = requests.get("http://localhost:11434/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✓ Ollama is running")
            print(f"✓ Available models: {len(models.get('data', []))}")
            for model in models.get('data', []):
                print(f"  - {model['id']}")
            return True
        else:
            print(f"✗ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        return False

def test_qdrant():
    """Test Qdrant service"""
    print_section("Testing Qdrant Service")
    try:
        response = requests.get("http://localhost:6333/collections", timeout=5)
        if response.status_code == 200:
            data = response.json()
            collections = data.get('result', {}).get('collections', [])
            print(f"✓ Qdrant is running")
            print(f"✓ Collections: {[c['name'] for c in collections]}")
            return True
        else:
            print(f"✗ Qdrant returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Qdrant connection failed: {e}")
        return False

def test_provider_config():
    """Test provider configuration"""
    print_section("Testing Provider Configuration")
    try:
        from config.llm_config import get_model_name, get_embedding_model_name
        from config.settings import settings

        print(f"✓ Provider: {settings.LLM_PROVIDER}")
        print(f"✓ Chat Model: {get_model_name()}")
        print(f"✓ Embedding Model: {get_embedding_model_name()}")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False

def test_embeddings():
    """Test embeddings generation"""
    print_section("Testing Embeddings Service")
    try:
        from services.embeddings_service import embeddings_service

        text = "Hello, this is a test."
        embedding = embeddings_service.embed_query(text)

        print(f"✓ Embeddings working")
        print(f"✓ Vector dimension: {len(embedding)}")
        print(f"✓ Sample values: {embedding[:5]}")
        return True
    except Exception as e:
        print(f"✗ Embeddings failed: {e}")
        return False

def test_qdrant_search():
    """Test Qdrant vector search"""
    print_section("Testing Qdrant Vector Search")
    try:
        from services.embeddings_service import embeddings_service
        from services.qdrant_service import qdrant_service

        # Generate a test query vector
        query = "artificial intelligence"
        query_vector = embeddings_service.embed_query(query)

        # Search Qdrant
        results = qdrant_service.search(query_vector, limit=3)

        print(f"✓ Qdrant search working")
        print(f"✓ Found {len(results)} results")

        if results:
            for i, result in enumerate(results[:3], 1):
                print(f"\n  Result {i}:")
                print(f"    Score: {result['score']:.4f}")
                payload = result.get('payload', {})
                if payload:
                    print(f"    Payload keys: {list(payload.keys())}")
        else:
            print("  ⚠ No documents in collection yet")

        return True
    except Exception as e:
        print(f"✗ Qdrant search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_completion():
    """Test chat completion with Ollama"""
    print_section("Testing Chat Completion")
    try:
        from config.llm_config import get_chat_model, get_model_name

        client = get_chat_model()
        response = client.chat.completions.create(
            model=get_model_name(),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello! I am working correctly.' and nothing else."}
            ],
            max_tokens=20
        )

        answer = response.choices[0].message.content
        print(f"✓ Chat completion working")
        print(f"✓ Response: {answer}")
        return True
    except Exception as e:
        print(f"✗ Chat completion failed: {e}")
        return False

def start_backend():
    """Start the backend server"""
    print_section("Starting Backend Server")
    import subprocess
    import os

    try:
        # Start server in background
        process = subprocess.Popen(
            ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        print("✓ Backend server starting...")
        print("  Waiting for server to be ready...")

        # Wait for server to start
        for i in range(30):
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    print(f"✓ Backend server is ready!")
                    return process
            except:
                pass
            sleep(1)

        print("✗ Server took too long to start")
        process.terminate()
        return None

    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        return None

def test_api_endpoint(server_process):
    """Test the chat API endpoint"""
    print_section("Testing Chat API Endpoint")

    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint working")
        else:
            print(f"✗ Health endpoint returned {response.status_code}")
            return False

        # Test chat endpoint
        payload = {
            "user_id": "test_user_123",
            "message": "What is 2+2?"
        }

        print("\n  Sending chat request...")
        print(f"  User: {payload['message']}")

        response = requests.post(
            "http://localhost:8000/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Chat API working!")
            print(f"✓ Route: {data.get('route', 'N/A')}")
            print(f"✓ Answer: {data.get('answer', 'N/A')[:200]}")

            if data.get('sources'):
                print(f"✓ Sources: {[s['type'] for s in data['sources']]}")

            return True
        else:
            print(f"✗ Chat API returned {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if server_process:
            print("\n  Stopping backend server...")
            server_process.terminate()
            server_process.wait()
            print("  ✓ Server stopped")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  AI Multi-Agent Backend - Comprehensive Test Suite")
    print("="*60)

    results = {
        "Ollama Service": test_ollama(),
        "Qdrant Service": test_qdrant(),
        "Provider Config": test_provider_config(),
        "Embeddings": test_embeddings(),
        "Qdrant Search": test_qdrant_search(),
        "Chat Completion": test_chat_completion(),
    }

    # Start server and test API
    server_process = start_backend()
    if server_process:
        results["API Endpoint"] = test_api_endpoint(server_process)
    else:
        results["API Endpoint"] = False

    # Print summary
    print_section("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} - {test}")

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")

    if passed == total:
        print("🎉 All tests passed! Your application is working correctly!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

