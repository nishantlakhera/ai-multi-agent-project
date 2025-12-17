# AI Multi-Agent Project Skeleton

This is a starter implementation for a multi-agent RAG + DB + Web system.

## Structure

- backend/ : FastAPI + LangGraph multi-agent backend
- mcp_service/ : MCP-like microservice for web tools
- embeddings/ : document ingestion into Qdrant
- frontend/ : React (Vite) chat UI
- docker/ : Dockerfiles
- minikube/ : example k8s manifests

## Quick Start (dev)

1. Create a virtualenv and install:

   ```bash
   pip install -r requirements.txt
   ```

2. Start backend:

   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

3. Start MCP service:

   ```bash
   uvicorn mcp_service.main:app --reload --port 8001
   ```

4. Start frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. Open browser at http://localhost:5173.
