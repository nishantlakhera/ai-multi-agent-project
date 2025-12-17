# AI Multi-Agent System - Comprehensive Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Component Details](#component-details)
5. [RAG Pipeline & Data Ingestion](#rag-pipeline--data-ingestion)
6. [Local Development Setup](#local-development-setup)
7. [Running the Services](#running-the-services)
8. [Testing the System](#testing-the-system)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

This is a **multi-agent AI system** built with LangGraph that intelligently routes user queries to specialized agents based on the query type. The system combines:
- **RAG (Retrieval Augmented Generation)** for document-based questions
- **Database queries** for structured data retrieval
- **Web search** for real-time internet information
- **Multi-source fusion** for complex queries requiring multiple data sources

### Key Features
- Intelligent query routing with few-shot learning
- Vector similarity search using Qdrant
- PostgreSQL database integration
- Web search via DuckDuckGo
- MCP (Model Context Protocol) service architecture
- React-based frontend interface
- Local LLM support via Ollama

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                      http://localhost:5173                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP/REST API
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    Backend Service (FastAPI)                     │
│                      http://localhost:8000                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph Multi-Agent System                 │  │
│  │                                                            │  │
│  │  ┌─────────┐    ┌──────┐   ┌──────┐   ┌──────┐          │  │
│  │  │ Router  │───▶│ RAG  │   │  DB  │   │ Web  │          │  │
│  │  │  Agent  │    │Agent │   │Agent │   │Agent │          │  │
│  │  └────┬────┘    └───┬──┘   └───┬──┘   └───┬──┘          │  │
│  │       │             │          │          │              │  │
│  │       │LLM          │LLM       │LLM       │LLM           │  │
│  │       ▼             ▼          ▼          ▼              │  │
│  │       └─────────────┴──────────┴──────────┘              │  │
│  │                     │                                     │  │
│  │              ┌──────▼──────┐                              │  │
│  │              │   Fusion    │                              │  │
│  │              │    Agent    │◀───────LLM                   │  │
│  │              └──────┬──────┘                              │  │
│  │                     │                                     │  │
│  │              ┌──────▼──────┐                              │  │
│  │              │Final Answer │                              │  │
│  │              │    Agent    │◀───────LLM                   │  │
│  │              └─────────────┘                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────┬───────────────────┬───────────────────┬─────────┘
               │                   │                   │
               │                   │                   │
    ┌──────────▼─────────┐ ┌──────▼────────┐ ┌───────▼─────────┐
    │   Qdrant Vector    │ │  PostgreSQL   │ │  MCP Service    │
    │   Database         │ │   Database    │ │  (Port 8001)    │
    │   (Port 6333)      │ │  (Port 5432)  │ │                 │
    │                    │ │               │ │  ┌───────────┐  │
    │ Kubernetes Pod     │ │Kubernetes Pod │ │  │Web Search │  │
    │ (Port-Forwarded)   │ │(Port-Forward) │ │  │   Tool    │  │
    └────────────────────┘ └───────────────┘ └──┴───────────┴──┘
               │                                       │
               │Embeddings                             │LLM (web planning)
               │                                       │
               └───────────────┬───────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │   Ollama (LLM)       │
                    │   Port 11434         │
                    │                      │
                    │   Models:            │
                    │   - llama3 (chat)    │◀──── Used by ALL agents
                    │   - nomic-embed-text │◀──── Used for embeddings
                    └──────────────────────┘
```

---

## Technology Stack

### Backend Technologies
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | Latest | REST API server |
| Runtime | Python | 3.9+ | Backend language |
| Orchestration | LangGraph | Latest | Multi-agent workflow |
| LLM Provider | Ollama | Latest | Local LLM inference for ALL agents |
| Vector DB | Qdrant | Latest | Semantic search |
| SQL DB | PostgreSQL | 14+ | Structured data |
| Embeddings | nomic-embed-text | Latest | Text vectorization (RAG) |
| Chat Model | llama3 | Latest | Used by Router, RAG, DB, Web, Fusion, Final agents |

### Frontend Technologies
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | React 18 | UI library |
| Build Tool | Vite | Fast dev server |
| Language | JavaScript | Frontend logic |

### Infrastructure
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Container Orchestration | Kubernetes (Minikube) | DB hosting |
| Port Forwarding | kubectl | Local access to K8s services |
| Package Manager | pip, npm | Dependency management |

---

## Component Details

### 1. Router Agent
**File:** `backend/agents/router_agent.py`

**Purpose:** Analyzes incoming queries and routes them to the appropriate specialized agent(s).

**Routing Logic:**
- `rag`: Questions about documentation, confluence, troubleshooting guides
- `db`: Database queries about users, orders, sessions, counts
- `web`: Real-time information, websites, news, external data
- `multi`: Complex queries requiring multiple data sources

**Implementation:**
- **Uses Ollama llama3 model** to analyze query intent
- Uses few-shot learning with 10+ training examples
- Temperature set to 0.1 for deterministic routing
- Fallback regex patterns for edge cases
- Validates output against allowed routes

**Example Routes:**
```
"How to troubleshoot Confluence?" → rag
"How many users logged in today?" → db
"What's the latest about Tesla.com?" → web
"Count orders AND search Microsoft.com" → multi
```

### 2. RAG Agent
**File:** `backend/agents/rag_agent.py`

**Purpose:** Retrieves relevant documents from Qdrant vector database and generates context-aware answers.

**Process Flow:**
1. Convert user query to embedding vector (Ollama nomic-embed-text)
2. Query Qdrant for top-5 similar documents (cosine similarity)
3. Pass retrieved documents + query to **Ollama llama3 LLM**
4. Generate answer based on retrieved context

**Key Features:**
- Vector similarity search
- Relevance scoring
- Context-aware generation using llama3
- Source attribution

### 3. Database Agent
**File:** `backend/agents/db_agent.py`

**Purpose:** Generates and executes SQL queries against PostgreSQL database.

**Database Schema:**
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- User sessions table
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total_amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
);
```

**Safety Features:**
- **Query relevance check using llama3** (skips if not DB-related)
- **SQL generation via Ollama llama3** with schema context
- SQL extraction from LLM output (handles markdown, prefixes)
- URL validation (rejects queries with .com, .net, etc.)
- Error handling with empty result fallback
- SQL injection prevention via parameterized queries

### 4. Web Agent
**File:** `backend/agents/web_agent.py`

**Purpose:** Performs web searches via MCP service to gather real-time information.

**Process:**
1. **Use Ollama llama3 to generate** search plan with multiple query variations
2. Send search request to MCP service
3. MCP service executes DuckDuckGo searches (also uses llama3 for planning)
4. Extract and summarize search results
5. Return formatted web data

**Features:**
- LLM-powered search query generation
- JSON extraction from markdown responses
- Result aggregation
- Error handling for failed searches

### 5. Fusion Agent
**File:** `backend/agents/fusion_agent.py`

**Purpose:** Combines results from multiple agents into a coherent answer.

**Input Sources:**
- RAG results (documents)
- Database results (SQL query results)
- Web results (search snippets)

**Process:**
- **Uses Ollama llama3** to intelligently combine and synthesize information
- Prioritizes and weighs different data sources
- Resolves conflicts between sources

**Output:** Unified, synthesized answer that incorporates all relevant data.

### 6. Final Answer Agent
**File:** `backend/agents/final_answer_agent.py`

**Purpose:** Formats the final response for user consumption.

**Process:**
- **Uses Ollama llama3** to format and polish the final answer
- Ensures clarity and completeness
- Maintains conversational tone

---

## RAG Pipeline & Data Ingestion

### Vector Database Architecture

**Qdrant Collection:** `documents`

**Configuration:**
- **Vector Size:** 768 dimensions (nomic-embed-text output)
- **Distance Metric:** Cosine similarity
- **Storage:** In Kubernetes pod, accessed via port-forward

### Data Ingestion Process

#### Step-by-Step Ingestion Flow

```
┌──────────────────┐
│  Source Files    │
│  (data/docs/)    │
└────────┬─────────┘
         │
         │ 1. Read files
         ▼
┌──────────────────────┐
│  Document Loader     │
│  Split into chunks   │
│  (500 chars overlap) │
└────────┬─────────────┘
         │
         │ 2. Chunk text
         ▼
┌──────────────────────┐
│  Embeddings Service  │
│  (Ollama nomic)      │
│  Generate vectors    │
└────────┬─────────────┘
         │
         │ 3. Vectorize
         ▼
┌──────────────────────┐
│  Qdrant Service      │
│  Upsert documents    │
│  with metadata       │
└──────────────────────┘
```

#### Current Ingested Data

**Location:** `data/docs/`

**Files:**
1. `confluence_troubleshooting.txt` - Confluence setup and troubleshooting
2. `technical_documentation.txt` - Technical system documentation
3. `user_guide.txt` - User guide and instructions

**Total Chunks:** 21 document chunks

**Metadata Stored:**
- Document ID (UUID)
- Source filename
- Chunk text content
- Embedding vector (768 dimensions)

### How to Ingest New Data

#### Option 1: Add Files to Existing Directory

1. **Place your documents** in `data/docs/` directory:
   ```bash
   cp your_document.txt data/docs/
   ```

2. **Run the ingestion pipeline:**
   ```bash
   cd /Users/nishant.lakhera/projects/learning/ai-multi-agent-project
   PYTHONPATH=$PWD:$PWD/backend python3 embeddings/ingestion_pipeline.py
   ```

3. **Verify ingestion** - check logs for:
   ```
   Loaded X documents from data/docs/
   Split into Y chunks
   Starting ingestion into Qdrant...
   Successfully ingested Y chunks
   ```

#### Option 2: Programmatic Ingestion

Create a custom script:

```python
import os
from dotenv import load_dotenv
from embeddings.document_loader import load_documents_from_directory
from services.embeddings_service import embeddings_service
from services.qdrant_service import qdrant_service

# Load backend environment variables
load_dotenv('/path/to/backend/.env')

# Load your documents
docs = load_documents_from_directory('/path/to/your/docs')
print(f"Loaded {len(docs)} documents")

# Generate embeddings
for doc in docs:
    vector = embeddings_service.embed_query(doc.page_content)
    
    # Upsert to Qdrant
    qdrant_service.add_documents([{
        'id': doc.metadata.get('id'),
        'vector': vector,
        'payload': {
            'text': doc.page_content,
            'source': doc.metadata.get('source', 'unknown')
        }
    }])

print("Ingestion complete!")
```

#### Option 3: API-Based Ingestion (Future Enhancement)

You can add an endpoint to the backend API:

```python
@router.post("/ingest")
async def ingest_document(text: str, source: str):
    """Ingest a new document into the RAG system"""
    vector = embeddings_service.embed_query(text)
    qdrant_service.add_documents([{
        'id': str(uuid.uuid4()),
        'vector': vector,
        'payload': {'text': text, 'source': source}
    }])
    return {"status": "success", "message": "Document ingested"}
```

### Document Chunking Strategy

**File:** `embeddings/document_loader.py`

**Strategy:**
- **Chunk Size:** Variable (context-dependent)
- **Overlap:** 500 characters between chunks
- **Splitter:** RecursiveCharacterTextSplitter
- **Preserves:** Semantic boundaries (paragraphs, sentences)

**Why This Matters:**
- Maintains context across chunk boundaries
- Prevents information loss at splits
- Improves retrieval accuracy

### Cleaning/Resetting Vector Database

To start fresh:

```bash
# Option 1: Delete collection via API
curl -X DELETE http://localhost:6333/collections/documents

# Option 2: Recreate collection
curl -X PUT http://localhost:6333/collections/documents \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    }
  }'

# Then re-run ingestion
PYTHONPATH=$PWD:$PWD/backend python3 embeddings/ingestion_pipeline.py
```

---

## Local Development Setup

### Prerequisites

1. **Minikube/Kubernetes** - Running with PostgreSQL and Qdrant pods
2. **Ollama** - Installed with llama3 and nomic-embed-text models
3. **Python 3.9+** - Backend runtime
4. **Node.js 16+** - Frontend development
5. **kubectl** - Kubernetes CLI tool

### Environment Configuration

#### Backend Environment Variables

**File:** `backend/.env`

```bash
# LLM Provider Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Database Configuration
POSTGRES_DSN=postgresql://appuser:apppass@localhost:5432/appdb

# Vector Database Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# MCP Service Configuration
MCP_SERVICE_URL=http://localhost:8001

# API Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### Kubernetes Services

Your setup has PostgreSQL and Qdrant running in Kubernetes:

**Namespace:** `multiagent-assistant`

**Services:**
1. **PostgreSQL**
   - Service: `postgres`
   - Port: 5432
   - Credentials: `appuser` / `apppass`
   - Database: `appdb`

2. **Qdrant**
   - Service: `qdrant`
   - Port: 6333
   - Collection: `documents`

### Port Forwarding Setup

Port forwarding allows your local services to access Kubernetes-hosted databases:

```bash
# PostgreSQL port forwarding
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432

# Qdrant port forwarding
kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333
```

**Keep these running in separate terminal windows throughout development.**

---

## Running the Services

### Manual Startup Process

#### 1. Start Port Forwarding

```bash
# Terminal 1: PostgreSQL
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432

# Terminal 2: Qdrant
kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333
```

#### 2. Verify Ollama

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should show llama3 and nomic-embed-text models
# If not running, start Ollama:
ollama serve
```

#### 3. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt --user

# Frontend dependencies
cd ../frontend
npm install
```

#### 4. Start Backend Service

```bash
# Terminal 3: Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

#### 5. Start MCP Service

```bash
# Terminal 4: MCP Service
cd mcp_service
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

#### 6. Start Frontend

```bash
# Terminal 5: Frontend
cd frontend
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Service Health Checks

Verify all services are running:

```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# MCP service health
curl http://localhost:8001/health
# Expected: {"status": "ok"}

# Qdrant health
curl http://localhost:6333/collections
# Expected: JSON with collections list

# PostgreSQL health
psql postgresql://appuser:apppass@localhost:5432/appdb -c "SELECT 1"
# Expected: 1 row returned

# Ollama health
curl http://localhost:11434/api/tags
# Expected: JSON with model list

# Frontend
open http://localhost:5173
# Expected: Web interface loads
```

---

## Testing the System

### Test Queries by Category

#### RAG Queries (Document-based)
```
"How do I troubleshoot Confluence connection issues?"
"What are the steps in the technical documentation for system setup?"
"Explain the user guide section about authentication"
```

#### Database Queries
```
"How many users are registered?"
"How many users logged in today?"
"Show me all orders with status pending"
"Count total orders in the system"
```

#### Web Queries
```
"What are the latest developments in artificial intelligence?"
"Tell me about Tesla.com"
"Search for information about NASA Mars mission"
```

#### Multi-Source Queries
```
"How many orders are in the database AND what's the latest news about Tesla.com?"
"Show me user statistics AND search for current ecommerce trends"
"Tell me about Confluence troubleshooting from docs AND find information about Atlassian.com"
```

### Expected Behavior

**For Single-Source Queries:**
1. Router identifies correct agent (rag/db/web)
2. Single agent executes
3. Fusion agent passes through result
4. Final answer returned

**For Multi-Source Queries:**
1. Router identifies as "multi"
2. RAG agent retrieves documents
3. DB agent checks relevance and runs SQL (or skips)
4. Web agent performs searches
5. Fusion agent combines all results
6. Final comprehensive answer returned

### Backend Log Monitoring

Watch backend logs to understand routing decisions:

```bash
# In the terminal running backend
# Look for these log patterns:

# Routing decision
INFO:backend:[router_agent] route=multi for query='...'

# RAG execution
INFO:backend:[rag_agent] retrieved 5 docs

# DB execution
INFO:backend:[db_agent] generated SQL: SELECT COUNT(*) FROM users
INFO:backend:[db_agent] skipping - query not relevant to database

# Web execution
INFO:backend:[web_agent] LLM plan: {...}
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "Connection refused" to PostgreSQL

**Symptom:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection refused
```

**Solution:**
```bash
# Check if port-forward is running
lsof -i :5432

# If not, restart port-forward
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432

# Verify connection
psql postgresql://appuser:apppass@localhost:5432/appdb -c "SELECT 1"
```

#### 2. "Connection refused" to Qdrant

**Symptom:**
```
httpx.ConnectError: [Errno 61] Connection refused
```

**Solution:**
```bash
# Check if port-forward is running
lsof -i :6333

# If not, restart port-forward
kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333

# Verify connection
curl http://localhost:6333/collections
```

#### 3. Ollama Authentication Error

**Symptom:**
```
openai.AuthenticationError: Error code: 401
```

**Solution:**
```bash
# Check LLM_PROVIDER in backend/.env
cat backend/.env | grep LLM_PROVIDER
# Should be: LLM_PROVIDER=ollama

# Restart backend to reload environment
# Kill backend process and restart:
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Frontend Shows Blank Page

**Symptom:** Browser shows empty page

**Solution:**
```bash
# Check if index.html exists
ls -la frontend/index.html

# Check frontend console for errors
# Open browser DevTools (F12) and look at Console tab

# Restart frontend dev server
cd frontend
npm run dev
```

#### 5. Invalid SQL Generated by DB Agent

**Symptom:**
```
ERROR:backend:[db_agent] SQL execution failed: syntax error
```

**Solution:**
- DB agent has improved SQL extraction logic
- Check if query contains web URLs (will be rejected)
- Review `backend/prompts/db.txt` for prompt quality
- Check backend logs for raw LLM output
- Consider using a more capable model (GPT-4 instead of llama3)

#### 6. Router Misroutes Queries

**Symptom:** Query goes to wrong agent

**Solution:**
- Review `backend/prompts/router.txt` few-shot examples
- Add more training examples for edge cases
- Check temperature setting in `router_agent.py` (should be 0.1)
- Monitor backend logs for routing decisions
- Consider fine-tuning or using a larger model

#### 7. MCP Service Connection Failed

**Symptom:**
```
httpx.ConnectError: Connection refused to localhost:8001
```

**Solution:**
```bash
# Check if MCP service is running
lsof -i :8001

# If not, start it
cd mcp_service
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Update backend/.env if needed
# MCP_SERVICE_URL=http://localhost:8001
```

#### 8. No Documents Retrieved by RAG

**Symptom:** RAG agent returns empty results

**Solution:**
```bash
# Check if documents are ingested
curl http://localhost:6333/collections/documents

# Re-run ingestion if needed
cd /Users/nishant.lakhera/projects/learning/ai-multi-agent-project
PYTHONPATH=$PWD:$PWD/backend python3 embeddings/ingestion_pipeline.py

# Verify ingestion
curl http://localhost:6333/collections/documents/points/scroll \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"limit": 1}'
```

### Port Conflicts

If ports are already in use:

```bash
# Find and kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Find and kill process on port 8001 (MCP)
lsof -ti:8001 | xargs kill -9

# Find and kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### Kubernetes Pod Issues

```bash
# Check pod status
kubectl get pods -n multiagent-assistant

# View pod logs
kubectl logs -n multiagent-assistant <pod-name>

# Restart a pod
kubectl delete pod -n multiagent-assistant <pod-name>
# Kubernetes will automatically recreate it
```

---

## Performance Optimization

### RAG Retrieval Tuning

**File:** `backend/agents/rag_agent.py`

```python
# Adjust number of retrieved documents
results = qdrant_service.query(
    collection_name="documents",
    query_vector=vector,
    limit=5  # Increase for more context, decrease for speed
)
```

### Database Query Optimization

- Add indexes to frequently queried columns
- Use EXPLAIN ANALYZE to profile slow queries
- Consider connection pooling for high load

### LLM Response Speed

- Use smaller models for faster responses (current: llama3)
- Reduce max_tokens in agent completions
- Consider GPU acceleration for Ollama
- Implement response streaming for better UX

---

## Next Steps & Enhancements

### Recommended Improvements

1. **Better LLM Model**
   - Replace llama3 with GPT-4 or Claude for better reasoning
   - Reduce SQL generation errors
   - Improve routing accuracy

2. **Streaming Responses**
   - Implement SSE (Server-Sent Events) for real-time streaming
   - Show progress as agents execute
   - Better user experience

3. **Authentication & Authorization**
   - Add user authentication
   - Track query history per user
   - Rate limiting

4. **Monitoring & Logging**
   - Add structured logging (JSON format)
   - Implement metrics (Prometheus)
   - Set up alerting for failures

5. **Testing Suite**
   - Unit tests for each agent
   - Integration tests for full workflows
   - Regression tests for routing accuracy

6. **API Documentation**
   - Auto-generated docs with FastAPI's Swagger UI
   - Available at http://localhost:8000/docs

7. **Production Deployment**
   - Containerize all services with Docker
   - Deploy to Kubernetes cluster
   - Add load balancing
   - Configure proper secrets management

---

## API Reference

### Backend Endpoints

**Base URL:** `http://localhost:8000`

#### POST /api/chat
Submit a query to the multi-agent system.

**Request:**
```json
{
  "query": "How many users are in the database?",
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "answer": "There are 150 users in the database.",
  "route": "db",
  "debug": {
    "db_sql": "SELECT COUNT(*) FROM users",
    "rag_docs": [],
    "web_results": []
  }
}
```

### MCP Service Endpoints

**Base URL:** `http://localhost:8001`

#### POST /plan
Execute a web search plan.

**Request:**
```json
{
  "plan": {
    "queries": ["Tesla.com", "Tesla news"],
    "goal": "Find information about Tesla"
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "query": "Tesla.com",
      "title": "Tesla Official Website",
      "snippet": "...",
      "url": "https://tesla.com"
    }
  ]
}
```

---

## Project Structure Reference

```
ai-multi-agent-project/
├── backend/
│   ├── agents/              # Agent implementations
│   │   ├── router_agent.py  # Query routing
│   │   ├── rag_agent.py     # Document retrieval
│   │   ├── db_agent.py      # SQL generation
│   │   ├── web_agent.py     # Web search
│   │   ├── fusion_agent.py  # Result combination
│   │   └── final_answer_agent.py
│   ├── api/                 # API routes and schemas
│   ├── config/              # Configuration files
│   ├── graphs/              # LangGraph definitions
│   ├── prompts/             # Agent prompts
│   ├── services/            # External service clients
│   ├── utils/               # Helper functions
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment variables
├── mcp_service/             # MCP microservice
│   ├── tools/               # MCP tool implementations
│   ├── main.py              # MCP FastAPI app
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   └── api/client.js    # API client
│   ├── index.html           # Entry point
│   ├── package.json         # NPM dependencies
│   └── vite.config.js       # Vite configuration
├── embeddings/              # Data ingestion
│   ├── ingestion_pipeline.py
│   ├── document_loader.py
│   └── cleanup.py
├── data/
│   └── docs/                # Source documents for RAG
├── minikube/                # Kubernetes manifests
│   └── postgres/
└── docker/                  # Dockerfiles

```

---

## Credits & License

**Project Type:** Educational/Research Multi-Agent AI System
**Architecture:** LangGraph-based Agent Orchestration
**Primary Use Case:** Intelligent query routing and multi-source information retrieval

---

**Document Version:** 1.0  
**Last Updated:** December 7, 2025  
**Maintained By:** Development Team
