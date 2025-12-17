#!/usr/bin/env python3
"""
Comprehensive test script to verify all components are working
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")

    try:
        import fastapi
        import uvicorn
        import openai
        import langchain
        import langgraph
        import httpx
        from qdrant_client import QdrantClient
        import psycopg2
        from sqlalchemy import create_engine
        from bs4 import BeautifulSoup
        import lxml
        from pydantic_settings import BaseSettings
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")

    try:
        from backend.config.settings import settings
        print(f"  - LLM Provider: {settings.LLM_PROVIDER}")
        print(f"  - Database: {settings.POSTGRES_DSN.split('@')[1] if '@' in settings.POSTGRES_DSN else 'configured'}")
        print(f"  - Qdrant: {settings.QDRANT_URL}")
        print(f"  - MCP: {settings.MCP_SERVICE_URL}")
        print("✅ Configuration loaded")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

def test_document_loader():
    """Test document loading functionality"""
    print("\n🔍 Testing document loader...")

    try:
        from embeddings.document_loader import load_text_files, chunk_text

        # Test chunking
        test_text = "This is a test. " * 100
        chunks = chunk_text(test_text, chunk_size=100, overlap=20)
        print(f"  - Chunking works: {len(chunks)} chunks created")

        # Test loading (won't fail if no files)
        docs = load_text_files("data/docs", chunk_documents=True)
        print(f"  - Document loading works: {len(docs)} documents loaded")

        print("✅ Document loader working")
        return True
    except Exception as e:
        print(f"❌ Document loader failed: {e}")
        return False

def test_agents():
    """Test that agent modules can be imported"""
    print("\n🔍 Testing agent modules...")

    try:
        from backend.agents.router_agent import router_agent
        from backend.agents.rag_agent import rag_agent
        from backend.agents.db_agent import db_agent
        from backend.agents.web_agent import web_agent
        from backend.agents.fusion_agent import fusion_agent
        from backend.agents.final_answer_agent import final_answer_agent
        print("✅ All agent modules loaded")
        return True
    except Exception as e:
        print(f"❌ Agent loading failed: {e}")
        return False

def test_graph():
    """Test LangGraph workflow"""
    print("\n🔍 Testing LangGraph workflow...")

    try:
        from backend.graphs.multi_agent_graph import graph_app
        print("✅ Graph compiled successfully")
        return True
    except Exception as e:
        print(f"❌ Graph compilation failed: {e}")
        return False

def test_web_tool():
    """Test web search tool"""
    print("\n🔍 Testing web search tool...")

    try:
        from mcp_service.tools.web_tool import execute_web_plan
        print("  - Web tool module loaded")

        # Test with a simple query (won't actually search in test)
        results = execute_web_plan("test query")
        print(f"  - Web search function works: {len(results)} results")

        print("✅ Web tool working")
        return True
    except Exception as e:
        print(f"❌ Web tool failed: {e}")
        return False

def test_api():
    """Test API routes"""
    print("\n🔍 Testing API routes...")

    try:
        from backend.api.routes import router
        from backend.api.schemas import ChatRequest, ChatResponse
        print("✅ API modules loaded")
        return True
    except Exception as e:
        print(f"❌ API loading failed: {e}")
        return False

def test_services_import():
    """Test service modules"""
    print("\n🔍 Testing service modules...")

    try:
        from backend.services.embeddings_service import embeddings_service
        from backend.services.memory_service import memory_service
        print("✅ Service modules loaded")
        return True
    except Exception as e:
        print(f"❌ Service loading failed: {e}")
        return False

def check_data_directory():
    """Check if data directory exists with documents"""
    print("\n🔍 Checking data directory...")

    data_dir = "data/docs"
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
        print(f"  - Data directory exists with {len(files)} .txt files")
        if files:
            print("✅ Sample documents ready for ingestion")
            return True
        else:
            print("⚠️  No .txt files found in data/docs")
            return True
    else:
        print("⚠️  Data directory not found (run: mkdir -p data/docs)")
        return True

def check_database_schema():
    """Check if database setup script exists"""
    print("\n🔍 Checking database setup...")

    sql_file = "backend/db_setup.sql"
    if os.path.exists(sql_file):
        print("✅ Database setup script ready")
        return True
    else:
        print("⚠️  Database setup script not found")
        return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 AI Multi-Agent System - Component Tests")
    print("=" * 60)

    tests = [
        test_imports,
        test_config,
        test_document_loader,
        test_agents,
        test_graph,
        test_web_tool,
        test_api,
        test_services_import,
        check_data_directory,
        check_database_schema,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✅ Your system is ready to run!")
        print("\nNext steps:")
        print("1. Start services: ./quickstart.sh")
        print("2. Or manually:")
        print("   - uvicorn backend.main:app --reload --port 8000")
        print("   - uvicorn mcp_service.main:app --reload --port 8001")
        print("   - cd frontend && npm run dev")
        return 0
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("\nPlease fix the failing tests before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

