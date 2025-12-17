# AI Multi-Agent System - Complete Documentation

**Version:** 1.0  
**Last Updated:** December 7, 2025  
**Author:** Production-Ready Multi-Agent Architecture

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Component Responsibilities](#component-responsibilities)
7. [Conversation History & Memory](#conversation-history--memory)
8. [Data Flow & Query Processing](#data-flow--query-processing)
9. [Setup & Installation](#setup--installation)
10. [Running the Application](#running-the-application)
11. [API Documentation](#api-documentation)
12. [Configuration](#configuration)
13. [Docker & Kubernetes Guide](#docker--kubernetes-guide)
14. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Want to run the entire system in one command? Even after reboot?**

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-multi-agent-project

# Run everything with one command
./start-all.sh
```

That's it! The script will:
- ✅ Start Minikube
- ✅ Deploy all services to Kubernetes
- ✅ Start Ollama with required models
- ✅ Setup port forwarding
- ✅ Start the frontend
- ✅ Ingest documents

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs

**To stop:**
```bash
./stop-all.sh
```

For detailed setup and configuration, continue reading below.

---

## Project Overview

### What is This System?

An **intelligent conversational AI assistant** that combines multiple specialized agents to answer questions from various data sources:

- **Database Queries** - SQL queries on PostgreSQL
- **Document Search** - RAG (Retrieval-Augmented Generation) using Qdrant vector database
- **Web Search** - Real-time web scraping and search
- **General Conversation** - Direct LLM responses for casual chat, math, and general knowledge
- **Multi-Source Fusion** - Combines multiple sources when queries span different domains

### Key Features

✅ **Multi-Agent Architecture** - Specialized agents for different tasks  
✅ **Intelligent Routing** - Automatically routes queries to appropriate agents  
✅ **Conversation Memory** - PostgreSQL-backed persistent conversation history  
✅ **Full MCP Integration** - Model Context Protocol for tool orchestration  
✅ **LangChain/LangGraph** - Structured agent workflows and LLM abstractions  
✅ **Vector Search** - Semantic document retrieval with Qdrant  
✅ **Multi-Provider LLM Support** - OpenAI, Groq, OpenRouter, Ollama (local)  
✅ **Production Ready** - Kubernetes deployment, health checks, logging

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│                  React Frontend (Port 5173)                      │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API Service                           │
│                   FastAPI (Port 8000)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph Workflow                           │  │
│  │                                                            │  │
│  │  ┌──────────┐                                             │  │
│  │  │  Router  │──> LangChain → Ollama (llama3)             │  │
│  │  │  Agent   │──> Route Decision (general/rag/db/web/multi)│  │
│  │  └────┬─────┘                                             │  │
│  │       │                                                   │  │
│  │       ├─> General Agent ──> LangChain → Ollama (llama3)  │  │
│  │       │                                                   │  │
│  │       ├─> RAG Agent ────┬──> LangChain → Ollama (llama3) │  │
│  │       │                 └──> MCP Service ─> Qdrant DB    │  │
│  │       │                                                   │  │
│  │       ├─> DB Agent ─────┬──> LangChain → Ollama (llama3) │  │
│  │       │                 └──> MCP Service ─> PostgreSQL   │  │
│  │       │                                                   │  │
│  │       ├─> Web Agent ────┬──> LangChain → Ollama (llama3) │  │
│  │       │                 └──> MCP Service ─> DuckDuckGo   │  │
│  │       │                                                   │  │
│  │       └─> Multi ────────> All Three Agents (parallel)    │  │
│  │                                  │                        │  │
│  │                                  ▼                        │  │
│  │                   ┌────────────────────────────┐         │  │
│  │                   │ Fusion Agent               │         │  │
│  │                   │ LangChain → Ollama (llama3)│         │  │
│  │                   └──────────┬─────────────────┘         │  │
│  │                              │                            │  │
│  │                              ▼                            │  │
│  │                   ┌────────────────────────────┐         │  │
│  │                   │ Final Answer Agent         │         │  │
│  │                   │ (Uses conversation history)│         │  │
│  │                   │ LangChain → Ollama (llama3)│         │  │
│  │                   └────────────────────────────┘         │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────┬─────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│              Memory Service (Conversation History)             │
│                      PostgreSQL Storage                        │
│                                                                │
│  • Load last 5 exchanges on each query (context window)       │
│  • Save user message + assistant response                     │
│  • Per-user isolation (user_id)                               │
│  • Auto-cleanup after 30 days                                 │
│  • Indexed for fast retrieval                                 │
└───────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    MCP Service (Port 8001)                       │
│              Model Context Protocol Tools                        │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │   RAG Tool     │  │    DB Tool     │  │   Web Tool      │  │
│  │   (Qdrant)     │  │  (PostgreSQL)  │  │ (DuckDuckGo)    │  │
│  │                │  │                │  │                 │  │
│  │ Embeddings:    │  │ SQL Generation:│  │ No LLM         │  │
│  │ Ollama         │  │ LangChain      │  │ (Web scraping) │  │
│  │ nomic-embed    │  │ → Ollama       │  │                │  │
│  └───────┬────────┘  └───────┬────────┘  └────────┬────────┘  │
└──────────┼───────────────────┼──────────────────────┼──────────┘
           │                   │                      │
           ▼                   ▼                      ▼
    ┌──────────────┐   ┌─────────────┐      ┌───────────────┐
    │   Qdrant     │   │ PostgreSQL  │      │  Web Search   │
    │Vector Database│   │   Database  │      │  (Internet)   │
    │  Port 6333   │   │  Port 5432  │      │               │
    └──────────────┘   └─────────────┘      └───────────────┘
    - 21 documents     - Users table         - DuckDuckGo API
    - nomic-embed-text - Orders table        - BeautifulSoup
    - Semantic search  - Conv. history       - Live web data
                       - Context-aware

┌─────────────────────────────────────────────────────────────────┐
│                    Ollama Service                                │
│                 http://localhost:11434                          │
│                                                                  │
│  Models:                                                        │
│  • llama3 (Chat) - Used by all agents for text generation      │
│  • nomic-embed-text (Embeddings) - Used for vector search      │
└─────────────────────────────────────────────────────────────────┘
```

### Infrastructure Deployment Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         HOST MACHINE (macOS)                            │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    LOCAL SERVICES                               │   │
│  │                                                                  │   │
│  │  ┌──────────────────────┐      ┌───────────────────────────┐  │   │
│  │  │   Ollama Service     │      │   Frontend (Vite)         │  │   │
│  │  │   localhost:11434    │      │   localhost:5173          │  │   │
│  │  │                      │      │                           │  │   │
│  │  │  • llama3 (chat)     │      │  • React UI               │  │   │
│  │  │  • nomic-embed-text  │      │  • Axios API client       │  │   │
│  │  │    (embeddings)      │      │  • Vite proxy to :8000    │  │   │
│  │  └──────────────────────┘      └─────────────┬─────────────┘  │   │
│  │                                               │                 │   │
│  └───────────────────────────────────────────────┼─────────────────┘   │
│                                                   │                     │
│                                                   │ HTTP                │
│                                                   │                     │
│  ┌────────────────────────────────────────────────┼─────────────────┐  │
│  │              PORT FORWARDING LAYER             │                 │  │
│  │                                                │                 │  │
│  │  localhost:8000 ←──┐                          │                 │  │
│  │  localhost:8001 ←──┼──────────────────────────┘                 │  │
│  │  localhost:5432 ←──┤  kubectl port-forward                      │  │
│  │  localhost:6333 ←──┘  (exposes K8s services)                    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                          │                                              │
└──────────────────────────┼──────────────────────────────────────────────┘
                           │ TCP/IP
                           ▼
┌────────────────────────────────────────────────────────────────────────┐
│              KUBERNETES CLUSTER (Minikube)                              │
│              Namespace: multiagent-assistant                            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    APPLICATION LAYER                              │ │
│  │                                                                    │ │
│  │  ┌─────────────────────────┐    ┌──────────────────────────────┐│ │
│  │  │  Backend Service        │    │  MCP Service                 ││ │
│  │  │  ClusterIP: backend     │    │  ClusterIP: mcp-service      ││ │
│  │  │  Port: 8000             │    │  Port: 8001                  ││ │
│  │  └────────┬────────────────┘    └──────────┬───────────────────┘│ │
│  │           │                                 │                    │ │
│  │           ▼                                 ▼                    │ │
│  │  ┌─────────────────────────┐    ┌──────────────────────────────┐│ │
│  │  │  Backend Deployment     │    │  MCP Deployment              ││ │
│  │  │  Replicas: 1            │    │  Replicas: 1                 ││ │
│  │  │                         │    │                              ││ │
│  │  │  Pod: backend-xxx       │    │  Pod: mcp-service-xxx        ││ │
│  │  │  Image:                 │    │  Image:                      ││ │
│  │  │   multiagent-backend    │    │   multiagent-mcp:latest      ││ │
│  │  │   :latest               │    │                              ││ │
│  │  │                         │    │  Tools:                      ││ │
│  │  │  Agents:                │    │  • RAG Tool (Qdrant)         ││ │
│  │  │  • Router Agent         │    │  • DB Tool (PostgreSQL)      ││ │
│  │  │  • General Agent        │    │  • Web Tool (DuckDuckGo)     ││ │
│  │  │  • RAG Agent            │    │                              ││ │
│  │  │  • DB Agent             │    │  Connects to:                ││ │
│  │  │  • Web Agent            │    │  • Qdrant: qdrant:6333       ││ │
│  │  │  • Fusion Agent         │    │  • PostgreSQL: postgres:5432 ││ │
│  │  │  • Final Answer Agent   │    │  • Ollama: host.minikube     ││ │
│  │  │                         │    │    .internal:11434           ││ │
│  │  │  Connects to:           │    │                              ││ │
│  │  │  • MCP: mcp-service:8001│    └──────────────────────────────┘│ │
│  │  │  • PostgreSQL:          │                                    │ │
│  │  │    postgres:5432        │                                    │ │
│  │  │  • Qdrant: qdrant:6333  │                                    │ │
│  │  │  • Ollama: host.minikube│                                    │ │
│  │  │    .internal:11434      │                                    │ │
│  │  └─────────────────────────┘                                    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    DATA LAYER                                     │ │
│  │                                                                    │ │
│  │  ┌────────────────────────┐       ┌─────────────────────────────┐│ │
│  │  │  PostgreSQL Service    │       │  Qdrant Service             ││ │
│  │  │  ClusterIP: postgres   │       │  ClusterIP: qdrant          ││ │
│  │  │  Port: 5432            │       │  Port: 6333                 ││ │
│  │  └────────┬───────────────┘       └──────────┬──────────────────┘│ │
│  │           │                                   │                   │ │
│  │           ▼                                   ▼                   │ │
│  │  ┌────────────────────────┐       ┌─────────────────────────────┐│ │
│  │  │  PostgreSQL Deployment │       │  Qdrant Deployment          ││ │
│  │  │  Replicas: 1           │       │  Replicas: 1                ││ │
│  │  │                        │       │                             ││ │
│  │  │  Pod: postgres-xxx     │       │  Pod: qdrant-xxx            ││ │
│  │  │  Image: postgres:14    │       │  Image: qdrant/qdrant       ││ │
│  │  │                        │       │                             ││ │
│  │  │  Data:                 │       │  Data:                      ││ │
│  │  │  • Database: appdb     │       │  • Collection: documents    ││ │
│  │  │  • Users: appuser      │       │  • Vectors: 21 chunks       ││ │
│  │  │  • Password: apppass   │       │  • Dimensions: 768          ││ │
│  │  │                        │       │  • Distance: Cosine         ││ │
│  │  │  Tables:               │       │                             ││ │
│  │  │  • users               │       │  Storage:                   ││ │
│  │  │  • orders              │       │  • PersistentVolume         ││ │
│  │  │  • conversation_history│       │  • /qdrant/storage          ││ │
│  │  │  • user_sessions       │       │                             ││ │
│  │  │  • user_actions        │       │                             ││ │
│  │  │                        │       │                             ││ │
│  │  │  Storage:              │       │                             ││ │
│  │  │  • PersistentVolume    │       │                             ││ │
│  │  │  • /var/lib/postgresql │       │                             ││ │
│  │  └────────────────────────┘       └─────────────────────────────┘│ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                   CONFIGURATION LAYER                             │ │
│  │                                                                    │ │
│  │  ConfigMaps:                      Secrets:                       │ │
│  │  • backend-config                 • backend-secret               │ │
│  │    - POSTGRES_DSN                   - POSTGRES_PASSWORD          │ │
│  │    - QDRANT_URL                   • mcp-secret                   │ │
│  │    - MCP_SERVICE_URL                - POSTGRES_PASSWORD          │ │
│  │    - OLLAMA_BASE_URL                                             │ │
│  │  • mcp-config                                                    │ │
│  │    - POSTGRES_HOST                                               │ │
│  │    - QDRANT_URL                                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└────────────────────────────────────────────────────────────────────────┘

NETWORK FLOW:
═════════════

1. USER → Frontend (localhost:5173)
   ↓
2. Frontend → Backend API (localhost:8000 via port-forward)
   ↓
3. Backend → LangGraph Workflow
   ↓
4. Router Agent → LangChain → Ollama (host.minikube.internal:11434)
   ↓
5. Based on route:
   
   a) RAG Path:
      Backend → MCP Service (mcp-service:8001)
      → RAG Tool → Qdrant (qdrant:6333)
      → Embeddings → Ollama (host.minikube.internal:11434)
      
   b) DB Path:
      Backend → MCP Service (mcp-service:8001)
      → DB Tool → PostgreSQL (postgres:5432)
      
   c) Web Path:
      Backend → MCP Service (mcp-service:8001)
      → Web Tool → Internet (DuckDuckGo)
   
6. Results → Fusion Agent → LangChain → Ollama
   ↓
7. Final Answer Agent → LangChain → Ollama
   ↓
8. Response → Backend → Frontend → User

STORAGE:
════════
• PostgreSQL PersistentVolume: Conversation history, users, orders
• Qdrant PersistentVolume: Document embeddings (21 chunks)
• Both survive pod restarts and cluster reboots
```

### Deployment Architecture (Legacy - Docker Compose)

For reference, the previous Docker Compose architecture:

```
┌─────────────────────────────────────────────────────────────┐
│              Docker Compose Network                          │
│                                                              │
│  ┌─────────────────┐         ┌──────────────────┐          │
│  │   PostgreSQL    │         │     Qdrant       │          │
│  │   Container     │         │   Container      │          │
│  │   Port: 5432    │         │   Port: 6333     │          │
│  └────────┬────────┘         └────────┬─────────┘          │
│           │                            │                     │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
            └────────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Local Services     │
              │  - Backend (8000)    │
              │  - MCP (8001)        │
              │  - Frontend (5173)   │
              └──────────────────────┘
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Backend Framework** | FastAPI | 0.104+ | High-performance async REST API |
| **Frontend Framework** | React + Vite | 18.3+ | Modern UI with fast dev experience |
| **LLM Framework** | LangChain | 0.3.27 | LLM abstraction and prompt management |
| **Agent Orchestration** | LangGraph | Latest | State-based agent workflow graphs |
| **Tool Protocol** | MCP (Model Context Protocol) | Custom | Standardized tool calling interface |
| **Vector Database** | Qdrant | Latest | Semantic document search |
| **SQL Database** | PostgreSQL | 14+ | Structured data and conversation history |
| **LLM Provider** | Ollama (llama3) | Latest | Local LLM inference |
| **Embeddings** | nomic-embed-text | Latest | Text vectorization |
| **Container Orchestration** | Kubernetes (Minikube) | 1.28+ | Service deployment |

### Python Dependencies

**Backend (`backend/requirements.txt`):**
```
fastapi                 # REST API framework
uvicorn                # ASGI server
pydantic               # Data validation
sqlalchemy             # Database ORM
httpx                  # Async HTTP client
qdrant-client          # Qdrant vector DB client
langgraph              # Agent workflow graphs
langchain              # LLM framework
langchain-core         # Core abstractions
langchain-community    # Community integrations
langchain-openai       # OpenAI-compatible interface
pydantic-settings      # Settings management
openai                 # OpenAI SDK
psycopg2-binary        # PostgreSQL driver
tenacity               # Retry logic
```

**MCP Service (`mcp_service/requirements.txt`):**
```
fastapi                # REST API
uvicorn                # Server
pydantic               # Validation
httpx                  # HTTP client
beautifulsoup4         # Web scraping
psycopg2-binary        # PostgreSQL
qdrant-client          # Qdrant
```

**Frontend (`frontend/package.json`):**
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }
}
```

---

## Project Structure

```
ai-multi-agent-project/
├── backend/                          # Main backend service
│   ├── agents/                       # Specialized agents
│   │   ├── router_agent.py           # Query routing logic
│   │   ├── general_agent.py          # General conversation handler
│   │   ├── rag_agent.py              # Document retrieval agent
│   │   ├── db_agent.py               # Database query agent
│   │   ├── web_agent.py              # Web search agent
│   │   ├── fusion_agent.py           # Multi-source result combiner
│   │   └── final_answer_agent.py     # Response formatter
│   │
│   ├── api/                          # REST API layer
│   │   ├── routes.py                 # API endpoints
│   │   └── schemas.py                # Request/response models
│   │
│   ├── config/                       # Configuration
│   │   ├── settings.py               # Environment settings
│   │   ├── langchain_config.py       # LangChain LLM factory
│   │   └── llm_config.py             # Legacy LLM config
│   │
│   ├── graphs/                       # LangGraph workflows
│   │   ├── multi_agent_graph.py      # Main agent workflow
│   │   └── state_schema.py           # State type definitions
│   │
│   ├── models/                       # Database models
│   │   └── user_model.py             # User data models
│   │
│   ├── prompts/                      # LLM prompts
│   │   ├── router.txt                # Routing classification
│   │   ├── rag.txt                   # RAG generation
│   │   ├── db.txt                    # SQL generation
│   │   └── web.txt                   # Web search planning
│   │
│   ├── services/                     # Service layer
│   │   ├── memory_service.py         # Conversation history (PostgreSQL)
│   │   ├── postgres_service.py       # Database operations
│   │   ├── qdrant_service.py         # Vector search
│   │   └── embeddings_service.py     # Text embeddings
│   │
│   ├── utils/                        # Utilities
│   │   ├── helpers.py                # Helper functions
│   │   └── logger.py                 # Logging setup
│   │
│   ├── main.py                       # FastAPI application
│   ├── requirements.txt              # Python dependencies
│   └── .env                          # Environment variables
│
├── mcp_service/                      # MCP Tool Service
│   ├── api/
│   │   ├── routes.py                 # MCP endpoints (/rag, /db, /plan)
│   │   └── schemas.py                # Request/response schemas
│   │
│   ├── tools/                        # MCP tools
│   │   ├── rag_tool.py               # Qdrant vector search
│   │   ├── db_tool.py                # SQL generation & execution
│   │   └── web_tool.py               # Web scraping & search
│   │
│   ├── planner/
│   │   └── mcp_planner.py            # Tool execution planner
│   │
│   ├── utils/
│   │   └── logger.py                 # Logging
│   │
│   ├── main.py                       # FastAPI application
│   └── requirements.txt              # Dependencies
│
├── frontend/                         # React UI
│   ├── src/
│   │   ├── App.jsx                   # Main application
│   │   ├── main.jsx                  # Entry point
│   │   └── api/
│   │       └── client.js             # API client
│   │
│   ├── index.html                    # HTML template
│   ├── package.json                  # NPM dependencies
│   └── vite.config.js                # Vite configuration
│
├── embeddings/                       # Document ingestion
│   ├── document_loader.py            # Load documents
│   ├── ingestion_pipeline.py         # Process & embed documents
│   └── cleanup.py                    # Cleanup utilities
│
├── data/docs/                        # Source documents
│   ├── technical_documentation.txt
│   ├── user_guide.txt
│   └── confluence_troubleshooting.txt
│
├── minikube/                         # Kubernetes manifests
│   └── postgres/
│       ├── postgres-deployment.yaml
│       └── postgres-service.yaml
│
├── logs/                             # Application logs
│   ├── backend.log
│   ├── mcp.log
│   └── frontend.log
│
├── startup.sh                        # Start all services
├── shutdown.sh                       # Stop all services
├── docker-compose.yml                # Docker orchestration
└── requirements.txt                  # Root dependencies
```

---

## Component Responsibilities

### 1. LangChain

**Role:** LLM Abstraction Layer

**Responsibilities:**
- **Provider Abstraction** - Uniform interface for OpenAI, Groq, OpenRouter, Ollama
- **Prompt Management** - Structured prompt templates with variables
- **Message Formatting** - Convert between different chat formats
- **Output Parsing** - Parse structured LLM outputs (JSON, Pydantic models)
- **Retry Logic** - Handle transient API failures
- **Token Management** - Track and limit token usage

**Key Files:**
- `backend/config/langchain_config.py` - LLM factory (`get_langchain_llm()`)
- All agents use LangChain's `ChatOpenAI` for LLM calls
- Prompt templates using `ChatPromptTemplate`

**Example Usage:**
```python
from langchain.prompts import ChatPromptTemplate
from config.langchain_config import get_langchain_llm

llm = get_langchain_llm(temperature=0.7)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("human", "{query}")
])
response = llm.invoke(prompt.format_messages(query="Hello"))
```

### 2. LangGraph

**Role:** Agent Workflow Orchestration

**Responsibilities:**
- **State Management** - Maintain conversation state across agents
- **Graph-Based Routing** - Define agent execution flow as a directed graph
- **Conditional Edges** - Route based on runtime conditions (e.g., route decision)
- **Parallel Execution** - Run multiple agents concurrently when needed
- **Error Handling** - Graceful degradation when agents fail

**Architecture:**
```python
# backend/graphs/multi_agent_graph.py

StateGraph Workflow:
  Router → [General | RAG | DB | Web | Multi]
           ↓         ↓      ↓     ↓      ↓
        Final     Fusion  Fusion Fusion  RAG→DB→Web→Fusion
           ↓         ↓                           ↓
          END     Final                       Final
                     ↓                           ↓
                    END                         END
```

**State Schema:**
```python
class GraphState(TypedDict):
    user_id: str
    query: str
    conversation_history: List[dict]
    route: Optional[Route]  # general/rag/db/web/multi
    rag_results: List[dict]
    db_results: List[dict]
    web_results: List[dict]
    general_response: str
    fused_context: str
    answer: str
    debug: dict
```

**Flow Control:**
- `router_agent` → Determines route
- Conditional edges route to appropriate agent(s)
- `fusion_agent` → Combines multi-source results
- `final_answer_agent` → Formats user-facing response

### 3. MCP (Model Context Protocol)

**Role:** Standardized Tool Execution Service

**Responsibilities:**
- **Tool Abstraction** - Separate tool logic from main backend
- **Reusability** - Tools can be called by multiple agents
- **Safety** - Centralized validation and error handling
- **Scalability** - Independent service can scale separately
- **API Gateway** - Single interface for multiple data sources

**Endpoints:**

| Endpoint | Method | Purpose | Input | Output |
|----------|--------|---------|-------|--------|
| `/health` | GET | Health check | - | `{"status":"healthy"}` |
| `/rag` | POST | Vector search | `{query, top_k}` | `{documents: [...]}` |
| `/db` | POST | SQL execution | `{query}` | `{results: [...], sql}` |
| `/plan` | POST | Web search | `{plan}` | `{results: [...]}` |

**RAG Tool Workflow:**
```
1. Receive query from backend
2. Generate embeddings using Ollama (nomic-embed-text)
3. Query Qdrant vector database
4. Retrieve top K similar documents
5. Return documents with scores and metadata
```

**DB Tool Workflow:**
```
1. Receive natural language query
2. Generate SQL using LLM
3. Validate SQL (prevent DROP, DELETE, etc.)
4. Execute on PostgreSQL
5. Return results with row count
```

**Web Tool Workflow:**
```
1. Receive search plan from backend
2. Parse search queries from plan
3. Execute DuckDuckGo searches
4. Scrape result pages
5. Extract and clean content
6. Return formatted results
```

### 4. Qdrant Vector Database

**Role:** Semantic Document Search

**Responsibilities:**
- **Vector Storage** - Store document embeddings
- **Similarity Search** - Find semantically similar documents
- **Metadata Filtering** - Filter by document attributes
- **Scalability** - Handle millions of vectors efficiently
- **Persistence** - Durable storage of embeddings

**Configuration:**
```python
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION_NAME = "documents"
EMBEDDING_MODEL = "nomic-embed-text"  # 768 dimensions
```

**Collection Schema:**
```python
{
    "vectors": {
        "size": 768,  # nomic-embed-text dimensions
        "distance": "Cosine"
    },
    "payload": {
        "text": str,        # Original text chunk
        "source": str,      # Source file name
        "chunk_id": int,    # Chunk number
        "metadata": dict    # Additional metadata
    }
}
```

**Current Data:**
- **21 document chunks** from 3 source files
- Technical documentation
- User guides
- Troubleshooting content

**Query Process:**
```python
# 1. Generate query embedding
query_vector = ollama.embeddings(
    model="nomic-embed-text",
    prompt=query
)

# 2. Search Qdrant
results = qdrant_client.query_points(
    collection_name="documents",
    query=query_vector,
    limit=3
)

# 3. Return top matches with scores
```

### 5. PostgreSQL Database

**Role:** Structured Data & Conversation History

**Responsibilities:**
- **Relational Data** - Store users, orders, sessions
- **Conversation Memory** - Persistent chat history
- **ACID Transactions** - Data consistency guarantees
- **Complex Queries** - JOIN operations, aggregations
- **Indexing** - Fast lookups on user_id, timestamps

**Database Schema:**

**Users Table:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Orders Table:**
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_name VARCHAR(255),
    amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Conversation History Table:**
```sql
CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_conversation_user_created 
ON conversation_history(user_id, created_at DESC);
```

**Connection Details:**
```
Host: localhost (via kubectl port-forward)
Port: 5432
Database: appdb
User: appuser
Password: apppass
```

---

## Conversation History & Memory

### Overview

The system implements **persistent conversation history** using PostgreSQL, enabling context-aware conversations that remember previous interactions across sessions.

### Key Features

✅ **Persistent Storage** - Conversations survive service restarts and system reboots
✅ **Per-User Isolation** - Each user has their own conversation history (identified by `user_id`)
✅ **Context Window** - Last 5 exchanges (10 messages) included in every query
✅ **Automatic Cleanup** - Conversations older than 30 days are auto-deleted
✅ **Fast Retrieval** - Indexed on `user_id` and `created_at` for <10ms query time
✅ **Thread Safety** - SQLAlchemy session management ensures concurrent access

### How It Works

**1. On Every Chat Request:**
```python
# Load conversation history (last 5 exchanges)
history = memory_service.get_history(user_id, limit=5)

# Add user message to history
memory_service.add_message(user_id, "user", message)

# Pass history to agents (router, general, final_answer)
state["conversation_history"] = history

# After generating response, save assistant message
memory_service.add_message(user_id, "assistant", answer)
```

**2. General Agent Uses History:**
```python
# Maintains context for casual conversations
for msg in history[-10:]:  # Last 10 messages
    messages.append({"role": msg["role"], "content": msg["content"]})
```

**3. Final Answer Agent Uses History:**
```python
# Includes history in context for specialized queries
if history:
    history_text = "\n\nPrevious conversation:\n"
    for msg in history[-6:]:  # Last 3 exchanges
        role_label = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role_label}: {msg['content']}\n"
```

### Database Schema

```sql
CREATE TABLE conversation_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,           -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_conversation_user_created 
ON conversation_history(user_id, created_at DESC);
```

### API Endpoints

**Get History:**
```bash
GET /api/history/{user_id}?limit=10
```

**Clear History:**
```bash
DELETE /api/history/{user_id}
```

**Admin Cleanup (delete old conversations):**
```bash
POST /api/admin/cleanup-history?days=30
```

### Example: Multi-Turn Conversation

```bash
# Turn 1
curl -X POST http://localhost:8000/api/chat \
  -d '{"user_id":"alice","message":"My name is Alice"}'
# Response: "Nice to meet you, Alice!"

# Turn 2 (remembers context)
curl -X POST http://localhost:8000/api/chat \
  -d '{"user_id":"alice","message":"What is my name?"}'
# Response: "Your name is Alice!"

# Turn 3 (different user, separate history)
curl -X POST http://localhost:8000/api/chat \
  -d '{"user_id":"bob","message":"What is my name?"}'
# Response: "I don't have information about your name yet."
```

### Configuration

**Change context window size** (in `backend/api/routes.py`):
```python
history = memory_service.get_history(req.user_id, limit=5)  # Change 5 to 10 for more context
```

**Change retention period** (in `backend/api/routes.py`):
```python
def cleanup_old_history(days: int = 30):  # Change 30 to 60 days
```

### Performance & Monitoring

**Check storage size:**
```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('conversation_history')) as total_size,
    COUNT(*) as total_messages,
    COUNT(DISTINCT user_id) as unique_users
FROM conversation_history;
```

**Find active users:**
```sql
SELECT user_id, COUNT(*) as messages_today
FROM conversation_history
WHERE created_at > CURRENT_DATE
GROUP BY user_id
ORDER BY messages_today DESC;
```

**Performance:**
- Query Speed: <10ms for history retrieval
- Storage: ~1KB per message
- Scalability: Tested with 1M+ messages
- Index: Automatically created on (user_id, created_at)

---

## Data Flow & Query Processing

### Complete Query Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. USER SENDS QUERY                                              │
│    "How many users are in the database?"                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │ HTTP POST /api/chat
                     │ {user_id, message}
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. BACKEND API (FastAPI)                                         │
│    - Load conversation history from PostgreSQL (last 5 exchanges)│
│    - Save user message to conversation_history table             │
│    - Initialize GraphState with query + history                  │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Invoke LangGraph workflow
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. ROUTER AGENT (LangChain)                                      │
│    - Load prompt from prompts/router.txt                         │
│    - Call Ollama LLM: "Classify this query"                      │
│    - LLM returns: "db" (with 0.9 confidence)                     │
│    - Store in state: route = "db"                                │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Conditional edge based on route
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. DB AGENT (LangChain + MCP)                                    │
│    - Load prompt from prompts/db.txt                             │
│    - Call Ollama LLM: "Generate SQL for this query"              │
│    - LLM returns: "SELECT COUNT(*) FROM users;"                  │
│    - POST to MCP Service: http://localhost:8001/db               │
│      {query: "How many users..."}                                │
└────────────────────┬─────────────────────────────────────────────┘
                     │ HTTP call to MCP
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. MCP DB TOOL                                                   │
│    - Receive query from backend                                  │
│    - Generate SQL using LLM (with safety checks)                 │
│    - Validate SQL (block DROP, DELETE, ALTER)                    │
│    - Execute: SELECT COUNT(*) FROM users;                        │
│    - PostgreSQL returns: [(10,)]                                 │
│    - Format response: {results: [{count: 10}], sql: "..."}       │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Return results to backend
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. DB AGENT (continues)                                          │
│    - Receive MCP response                                        │
│    - Store in state: db_results = [{count: 10}]                  │
│    - Store debug info: db_sql, db_row_count                      │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Move to fusion agent
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 7. FUSION AGENT (LangChain)                                      │
│    - Check route: single source (db only)                        │
│    - Format context: "DB results: [{count: 10}]"                 │
│    - Store in state: fused_context = "..."                       │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Move to final answer
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 8. FINAL ANSWER AGENT (LangChain)                                │
│    - Load conversation history from state                        │
│    - Combine: history + fused_context                            │
│    - Call Ollama LLM: "Generate user-friendly answer"            │
│    - LLM returns: "Based on the database, there are 10 users."   │
│    - Store in state: answer = "..."                              │
└────────────────────┬─────────────────────────────────────────────┘
                     │ Return to API
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 9. BACKEND API (continues)                                       │
│    - Save assistant response to conversation_history table       │
│    - Build response: {answer, route, sources, debug}             │
│    - Return JSON to frontend                                     │
└────────────────────┬─────────────────────────────────────────────┘
                     │ HTTP 200 OK
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 10. FRONTEND (React)                                             │
│     - Display answer: "Based on the database, there are 10 users"│
│     - Show source indicator: 🗄️ [db]                             │
│     - Add to chat history UI                                     │
└──────────────────────────────────────────────────────────────────┘
```

### Multi-Source Query Flow (Example: "Count users AND search Tesla news")

```
Router → "multi" route
   ↓
RAG Agent → MCP /rag → Qdrant → [doc results]
   ↓
DB Agent → MCP /db → PostgreSQL → [count: 10]
   ↓
Web Agent → MCP /plan → DuckDuckGo → [Tesla articles]
   ↓
Fusion Agent → Combine all three sources
   ↓
Final Answer → "There are 10 users. Latest Tesla news: ..."
```

### Conversation Memory Flow

```
1. User sends message → Save to PostgreSQL conversation_history
2. Load last 5 exchanges (10 messages) from database
3. Pass history to General/Final Answer agents
4. Agents use history for context-aware responses
5. Save assistant response to database
6. History persists across service restarts
```

---

## Setup & Installation

### Prerequisites

**Required Software:**
```bash
# Core tools
✓ Python 3.9+
✓ Node.js 18+
✓ Docker Desktop
✓ Kubernetes (Minikube)
✓ kubectl
✓ Ollama

# Optional (for manual testing)
✓ curl or Postman
✓ PostgreSQL client (psql)
```

**Installation Commands:**

```bash
# macOS (using Homebrew)
brew install python@3.9 node kubernetes-cli minikube ollama

# Start Ollama
brew services start ollama

# Pull required models
ollama pull llama3
ollama pull nomic-embed-text

# Start Minikube
minikube start
```

### Step 1: Clone & Navigate

```bash
git clone <your-repo-url>
cd ai-multi-agent-project
```

### Step 2: Deploy Kubernetes Services

```bash
# Deploy PostgreSQL
kubectl apply -f minikube/postgres/

# Deploy Qdrant (if you have manifests, or use port-forward to existing)
# The project uses port-forwarding to existing Kubernetes services

# Verify deployments
kubectl get pods -n multiagent-assistant
```

Expected output:
```
NAME                          READY   STATUS    RESTARTS   AGE
postgres-xxx-yyy              1/1     Running   0          2m
qdrant-xxx-yyy                1/1     Running   0          2m
```

### Step 3: Configure Environment

```bash
# Backend environment
cd backend
cp .env.example .env  # If example exists, otherwise create new

# Edit .env file
vim .env
```

**Required `.env` configuration:**
```bash
# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Database
POSTGRES_DSN=postgresql://appuser:apppass@localhost:5432/appdb
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents

# Services
MCP_SERVICE_URL=http://localhost:8001
```

### Step 4: Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# MCP service dependencies
cd ../mcp_service
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install

# Return to root
cd ..
```

### Step 5: Load Initial Data

```bash
# Create database tables
python setup_database.py

# Ingest documents into Qdrant
PYTHONPATH=. python embeddings/ingestion_pipeline.py
```

Expected output:
```
✓ Connected to Qdrant
✓ Created collection 'documents'
✓ Loaded 3 documents
✓ Created 21 chunks
✓ Generated embeddings
✓ Uploaded to Qdrant
```

---

## Running the Application

### Complete Automated Startup (Recommended - Works After Reboot)

For a complete startup that handles everything from scratch, including after system reboot:

```bash
# Start everything (Minikube, Kubernetes, Ollama, Frontend)
./start-all.sh
```

This script will:
1. ✅ Check all prerequisites (minikube, kubectl, docker, ollama, npm, python3)
2. ✅ Start Minikube (if not running)
3. ✅ Create namespace (if not exists)
4. ✅ Build Docker images (if not exists)
5. ✅ Deploy all Kubernetes services (PostgreSQL, Qdrant, MCP, Backend)
6. ✅ Wait for all pods to be ready
7. ✅ Start/verify Ollama with required models
8. ✅ Setup port forwarding
9. ✅ Verify services health
10. ✅ Install frontend dependencies (if needed)
11. ✅ Start frontend
12. ✅ Ingest documents to Qdrant (if empty)

**To stop all services:**
```bash
./stop-all.sh
```

This preserves all data in PostgreSQL and Qdrant. Next time you run `./start-all.sh`, it will reuse existing data.

### Quick Startup (When Services Already Deployed)

If Kubernetes services are already deployed and you just need to start port forwarding and frontend:

```bash
# Start all services with one command
./k8s-startup.sh
```

This script:
1. ✓ Checks prerequisites (kubectl, ollama, etc.)
2. ✓ Sets up Kubernetes port forwarding (PostgreSQL, Qdrant)
3. ✓ Verifies database connections
4. ✓ Installs missing dependencies
5. ✓ Starts Backend (port 8000)
6. ✓ Starts MCP Service (port 8001)
7. ✓ Starts Frontend (port 5173)
8. ✓ Runs health checks
9. ✓ Displays service URLs

**Output:**
```
[2025-12-07 17:50:29] ===================================================================
[2025-12-07 17:50:29]      AI Multi-Agent System - Automated Startup
[2025-12-07 17:50:29] ===================================================================

[2025-12-07 17:50:29] Starting pre-flight checks...
✓ All required commands found
✓ Kubernetes cluster is accessible
✓ Ollama is running
✓ Required Ollama models are installed

[2025-12-07 17:50:34] ✓ PostgreSQL port forward active (PID: 24474)
[2025-12-07 17:50:37] ✓ Qdrant port forward active (PID: 24486)
[2025-12-07 17:50:44] ✓ Backend Service running (PID: 24613)
[2025-12-07 17:50:46] ✓ MCP Service running (PID: 24634)
[2025-12-07 17:50:48] ✓ Frontend running (PID: 24656)

╔════════════════════════════════════════════════════════════════╗
║           AI Multi-Agent System Started Successfully!          ║
╚════════════════════════════════════════════════════════════════╝

📊 Service Status:
   Frontend:     http://localhost:5173
   Backend API:  http://localhost:8000
   MCP Service:  http://localhost:8001
   PostgreSQL:   localhost:5432 (port-forwarded)
   Qdrant:       localhost:6333 (port-forwarded)
   Ollama:       localhost:11434
```

### Manual Startup

If you prefer to start services individually:

**Terminal 1 - Port Forwarding:**
```bash
# PostgreSQL
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432 &

# Qdrant
kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333 &
```

**Terminal 2 - Backend:**
```bash
cd backend
export PYTHONPATH=/path/to/project:/path/to/project/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 - MCP Service:**
```bash
cd mcp_service
export PYTHONPATH=/path/to/project/mcp_service
export POSTGRES_DSN=postgresql://appuser:apppass@localhost:5432/appdb
export QDRANT_URL=http://localhost:6333
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm run dev
```

### Verify Services

```bash
# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:5173

# Expected responses
{"status":"ok"}
{"status":"healthy","service":"mcp"}
<!DOCTYPE html>...
```

### Access the Application

Open your browser:
- **Frontend UI:** http://localhost:5173
- **Backend API Docs:** http://localhost:8000/docs
- **MCP Service Docs:** http://localhost:8001/docs

### Stopping Services

```bash
# Automated shutdown
./shutdown.sh
```

This will:
- Stop all running services (backend, MCP, frontend)
- Kill port-forward processes
- Clean up PIDs
- Preserve logs in `logs/` directory

**Manual shutdown:**
```bash
# Kill processes by port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:8001 | xargs kill -9  # MCP
lsof -ti:5173 | xargs kill -9  # Frontend

# Kill port forwards
pkill -f "kubectl port-forward.*postgres"
pkill -f "kubectl port-forward.*qdrant"
```

---

## API Documentation

### Backend API Endpoints

Base URL: `http://localhost:8000/api`

#### 1. Chat Endpoint

**POST** `/api/chat`

Send a query and get an intelligent response.

**Request:**
```json
{
  "user_id": "john_doe",
  "message": "How many users are in the database?"
}
```

**Response:**
```json
{
  "answer": "Based on the database, there are 10 users.",
  "route": "db",
  "sources": [
    {
      "type": "db",
      "meta": null
    }
  ],
  "debug": {
    "router_confidence": 0.9,
    "router_reasoning": "db",
    "db_sql": "SELECT COUNT(*) FROM users;",
    "db_row_count": 1,
    "answer_length": 45,
    "context_length": 42
  }
}
```

**Supported Query Types:**

| Route | Example Query | Response Source |
|-------|---------------|-----------------|
| `general` | "Hello, how are you?" | Direct LLM |
| `general` | "What is 25 * 47?" | Direct LLM |
| `rag` | "How do I troubleshoot Confluence?" | Qdrant documents |
| `db` | "Count users in database" | PostgreSQL |
| `web` | "Latest Tesla news" | Web search |
| `multi` | "Count users AND Tesla news" | All sources combined |

#### 2. Conversation History

**GET** `/api/history/{user_id}?limit=10`

Retrieve conversation history for a user.

**Response:**
```json
{
  "user_id": "john_doe",
  "history": [
    {
      "role": "user",
      "content": "My name is John",
      "timestamp": "2025-12-07T17:21:53.914384"
    },
    {
      "role": "assistant",
      "content": "Nice to meet you, John!",
      "timestamp": "2025-12-07T17:21:55.695520"
    }
  ],
  "count": 2
}
```

#### 3. Clear History

**DELETE** `/api/history/{user_id}`

Clear all conversation history for a user.

**Response:**
```json
{
  "status": "success",
  "message": "History cleared for user john_doe"
}
```

#### 4. Admin - Cleanup Old Conversations

**POST** `/api/admin/cleanup-history?days=30`

Delete conversations older than specified days.

**Response:**
```json
{
  "status": "success",
  "deleted_count": 156,
  "message": "Deleted conversations older than 30 days"
}
```

### MCP Service Endpoints

Base URL: `http://localhost:8001`

#### 1. RAG (Retrieval-Augmented Generation)

**POST** `/rag`

Search vector database for relevant documents.

**Request:**
```json
{
  "query": "How to troubleshoot Confluence?",
  "top_k": 3
}
```

**Response:**
```json
{
  "documents": [
    {
      "text": "To troubleshoot Confluence issues...",
      "score": 0.85,
      "metadata": {
        "source": "confluence_troubleshooting.txt",
        "chunk_id": 5
      }
    }
  ]
}
```

#### 2. Database Query

**POST** `/db`

Execute natural language query on PostgreSQL.

**Request:**
```json
{
  "query": "How many active users do we have?"
}
```

**Response:**
```json
{
  "results": [
    {
      "count": 8
    }
  ],
  "sql": "SELECT COUNT(*) FROM users WHERE is_active = true;",
  "row_count": 1
}
```

#### 3. Web Search

**POST** `/plan`

Execute web search plan.

**Request:**
```json
{
  "plan": "Search for latest Tesla news and summarize"
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "Tesla Announces New Model",
      "snippet": "Tesla Inc. announced today...",
      "url": "https://example.com/tesla-news"
    }
  ]
}
```

---

## Configuration

### Environment Variables

**Backend (`.env`):**
```bash
# LLM Provider (openai/groq/openrouter/ollama)
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3
EMBEDDING_MODEL=nomic-embed-text

# OpenAI (if using)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Groq (if using)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-70b-versatile

# Databases
POSTGRES_DSN=postgresql://appuser:apppass@localhost:5432/appdb
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents

# Services
MCP_SERVICE_URL=http://localhost:8001
```

### Changing LLM Provider

**To use OpenAI:**
```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

**To use Groq:**
```bash
# .env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk-your-key-here
GROQ_MODEL=llama-3.1-70b-versatile
```

**To use Ollama (default):**
```bash
# .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### Conversation History Retention

Default: 30 days. To change:

Edit `backend/api/routes.py`:
```python
@router.post("/admin/cleanup-history")
def cleanup_old_history(days: int = 30):  # Change default here
```

Set up daily cleanup cron:
```bash
# Add to crontab
0 2 * * * curl -X POST http://localhost:8000/api/admin/cleanup-history?days=30
```

---

## Docker & Kubernetes Guide

### Understanding the Deployment Architecture

This project uses **Minikube** for Kubernetes deployment. Here's what you need to know:

#### Docker Desktop vs Minikube Docker

**Why don't I see my containers in Docker Desktop?**

Minikube uses its **own isolated Docker environment** inside the Minikube VM, completely separate from your host Docker.

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR HOST MACHINE (macOS)                 │
│                                                              │
│  Docker Desktop (GUI)                                        │
│  ├── Your personal containers (if any)                       │
│  └── Minikube VM container (gcr.io/k8s-minikube/kicbase)    │
│      ↑                                                       │
│      └── This is the ONLY container you see                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │       MINIKUBE VM (Runs Inside Docker Desktop)         │ │
│  │                                                        │ │
│  │  Minikube's Docker Daemon (ISOLATED & SEPARATE)       │ │
│  │  ├── multiagent-backend:latest       ✅               │ │
│  │  ├── multiagent-mcp:latest           ✅               │ │
│  │  ├── postgres:14                     ✅               │ │
│  │  ├── qdrant/qdrant:v1.11.0           ✅               │ │
│  │  └── Kubernetes system images        ✅               │ │
│  │                                                        │ │
│  │  Kubernetes Cluster                                   │ │
│  │  └── Pods run using above images                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Viewing Your Containers

#### Option 1: Kubernetes Dashboard (Recommended)
```bash
# Open Minikube dashboard
minikube dashboard

# Then navigate to:
# Namespace: multiagent-assistant → Workloads → Pods
```

**You'll see:**
- backend-xxx (Running)
- mcp-service-xxx (Running)
- postgres-xxx (Running)
- qdrant-xxx (Running)

#### Option 2: kubectl Commands
```bash
# View all resources
kubectl get all -n multiagent-assistant

# View pods with details
kubectl get pods -n multiagent-assistant -o wide

# View deployments
kubectl get deployments -n multiagent-assistant

# View services
kubectl get svc -n multiagent-assistant

# View persistent volumes
kubectl get pvc -n multiagent-assistant
```

#### Option 3: Minikube Docker CLI
```bash
# Switch to Minikube's Docker environment
eval $(minikube docker-env)

# Now you can see containers inside Minikube
docker ps | grep multiagent
docker images | grep multiagent

# Switch back to host Docker
eval $(minikube docker-env -u)
```

### Docker Commands Cheat Sheet

#### Host Docker (What you see in Docker Desktop)
```bash
# Regular docker commands on host
docker ps                    # Only shows Minikube VM
docker images                # Only shows host images
docker-compose up            # Uses host Docker (not recommended for this project)
```

#### Minikube Docker (Where your app actually runs)
```bash
# Switch to Minikube Docker environment
eval $(minikube docker-env)

# Now docker commands target Minikube's Docker
docker ps                    # Shows ALL your app containers
docker images                # Shows multiagent-backend, multiagent-mcp, etc.
docker logs <container_id>   # View logs

# Build images in Minikube (already done by start-all.sh)
docker build -t multiagent-backend:latest -f docker/backend.Dockerfile .
docker build -t multiagent-mcp:latest -f docker/mcp.Dockerfile .

# Switch back to host Docker when done
eval $(minikube docker-env -u)
```

### Kubernetes Commands Cheat Sheet

#### Cluster Management
```bash
# Check cluster status
minikube status

# Start cluster
minikube start

# Stop cluster (keeps data)
minikube stop

# Delete cluster (removes everything)
minikube delete

# View cluster info
kubectl cluster-info

# Access Kubernetes dashboard
minikube dashboard
```

#### Pod Management
```bash
# List all pods
kubectl get pods -n multiagent-assistant

# Describe a pod (detailed info)
kubectl describe pod <pod-name> -n multiagent-assistant

# View pod logs
kubectl logs <pod-name> -n multiagent-assistant

# Follow logs (real-time)
kubectl logs -f <pod-name> -n multiagent-assistant

# Execute command in pod
kubectl exec -it <pod-name> -n multiagent-assistant -- /bin/bash

# Delete and recreate pod (deployment will auto-recreate)
kubectl delete pod <pod-name> -n multiagent-assistant
```

#### Deployment Management
```bash
# List deployments
kubectl get deployments -n multiagent-assistant

# Scale deployment
kubectl scale deployment backend --replicas=3 -n multiagent-assistant

# Restart deployment (rolling restart)
kubectl rollout restart deployment backend -n multiagent-assistant

# Check rollout status
kubectl rollout status deployment backend -n multiagent-assistant

# View deployment history
kubectl rollout history deployment backend -n multiagent-assistant
```

#### Service & Networking
```bash
# List services
kubectl get svc -n multiagent-assistant

# Port forward to access service locally
kubectl port-forward -n multiagent-assistant svc/backend 8000:8000
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432

# View service endpoints
kubectl get endpoints -n multiagent-assistant

# Test service connectivity from inside cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n multiagent-assistant -- sh
# Then: curl http://backend:8000/health
```

#### ConfigMap & Secrets
```bash
# View ConfigMaps
kubectl get configmap -n multiagent-assistant

# View ConfigMap content
kubectl describe configmap backend-config -n multiagent-assistant

# View Secrets (base64 encoded)
kubectl get secrets -n multiagent-assistant

# Decode secret
kubectl get secret backend-secret -n multiagent-assistant -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

#### Storage
```bash
# View PersistentVolumeClaims
kubectl get pvc -n multiagent-assistant

# View PersistentVolumes
kubectl get pv

# Describe PVC
kubectl describe pvc postgres-pvc -n multiagent-assistant
```

#### Troubleshooting
```bash
# View all events (useful for debugging)
kubectl get events -n multiagent-assistant --sort-by='.lastTimestamp'

# Check resource usage
kubectl top nodes
kubectl top pods -n multiagent-assistant

# Get pod YAML definition
kubectl get pod <pod-name> -n multiagent-assistant -o yaml

# Get pod status and restart count
kubectl get pods -n multiagent-assistant -o wide
```

### Why This Architecture?

**Benefits of Minikube + Isolated Docker:**

✅ **Clean Separation** - Project images don't clutter your host Docker  
✅ **No Registry Needed** - `imagePullPolicy: Never` means no push to Docker Hub  
✅ **Fast Builds** - Images built directly in Kubernetes environment  
✅ **Easy Cleanup** - `minikube delete` removes everything cleanly  
✅ **Production-like** - Mimics real Kubernetes behavior locally  
✅ **Persistent Data** - PersistentVolumes survive pod restarts  

### Image Build Process

When you run `./start-all.sh`, here's what happens:

```bash
# 1. Switch to Minikube's Docker environment
eval $(minikube docker-env)

# 2. Build images (they go into Minikube's Docker, not host)
docker build -t multiagent-backend:latest -f docker/backend.Dockerfile .
docker build -t multiagent-mcp:latest -f docker/mcp.Dockerfile .

# 3. Deploy to Kubernetes (uses images from Minikube's Docker)
kubectl apply -f minikube/backend/backend-deployment.yaml
# Deployment uses: image: multiagent-backend:latest
# With: imagePullPolicy: Never (don't pull from registry)

# 4. Kubernetes pulls image from Minikube's local Docker
```

### Common Misconceptions

❌ **"I don't see containers in Docker Desktop - something is wrong!"**  
✅ **Correct:** Your containers are in Minikube's Docker, view them in Minikube Dashboard

❌ **"docker ps shows nothing - the app isn't running!"**  
✅ **Correct:** Use `kubectl get pods` or `eval $(minikube docker-env) && docker ps`

❌ **"I need to push images to Docker Hub"**  
✅ **Correct:** `imagePullPolicy: Never` uses local Minikube images

❌ **"Where is my data stored?"**  
✅ **Correct:** In Kubernetes PersistentVolumes inside Minikube VM at:  
   `/var/lib/docker/volumes/` (inside Minikube VM)

### Data Persistence

**Q: What happens if I restart my computer?**

```bash
# Minikube cluster stops but data persists
minikube status  # Will show "Stopped"

# Start cluster again
minikube start

# Pods will restart automatically
kubectl get pods -n multiagent-assistant

# Data in PostgreSQL and Qdrant persists (PersistentVolumes)
```

**Q: How do I completely remove everything?**

```bash
# Delete Minikube cluster
minikube delete

# This removes:
# - All pods, deployments, services
# - All PersistentVolumes (YOUR DATA)
# - All Docker images inside Minikube
# - The Minikube VM itself

# Start fresh
./start-all.sh
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

#### 2. Ollama Not Running

**Error:** `Connection refused to localhost:11434`

**Solution:**
```bash
# Start Ollama
brew services start ollama

# Or run manually
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

#### 3. Port Forward Failed

**Error:** `Unable to connect to PostgreSQL/Qdrant`

**Solution:**
```bash
# Check Kubernetes pods
kubectl get pods -n multiagent-assistant

# Restart port forward
pkill -f "kubectl port-forward"
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432 &
kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333 &
```

#### 4. LLM 404 Errors

**Error:** `404 page not found` from Ollama

**Issue:** Incorrect base URL configuration

**Solution:**
```bash
# .env should have
OLLAMA_BASE_URL=http://localhost:11434
# NOT http://localhost:11434/v1

# The /v1 is added automatically by LangChain
```

#### 5. Conversation History Not Persisting

**Check table exists:**
```bash
# Via API
curl http://localhost:8000/api/history/test_user

# If error, restart backend (table auto-creates)
./shutdown.sh && ./startup.sh
```

#### 6. Frontend Not Loading

**Check Vite server:**
```bash
cd frontend
npm run dev

# If error, reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Logs

**View logs:**
```bash
# Backend
tail -f logs/backend.log

# MCP Service
tail -f logs/mcp.log

# Frontend
tail -f logs/frontend.log

# Startup logs
tail -f logs/startup_*.log
```

**Check specific errors:**
```bash
# Search for errors
grep ERROR logs/backend.log

# Check recent activity
tail -100 logs/backend.log
```

### Health Checks

```bash
# All services
curl http://localhost:8000/health && \
curl http://localhost:8001/health && \
curl http://localhost:5173/ | head -5

# Expected
{"status":"ok"}
{"status":"healthy","service":"mcp"}
<!DOCTYPE html>
```

### Reset Everything

```bash
# Stop all services
./shutdown.sh

# Kill all related processes
pkill -f "uvicorn"
pkill -f "node"
pkill -f "kubectl port-forward"

# Clean logs
rm -rf logs/*

# Restart
./startup.sh
```

---

## Testing

### Quick Test Suite

```bash
# Test all routes
echo "=== Testing General Agent ===" && \
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Hello!"}' | jq '.route, .answer' && \

echo -e "\n=== Testing DB Agent ===" && \
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Count users"}' | jq '.route, .answer' && \

echo -e "\n=== Testing RAG Agent ===" && \
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Troubleshoot Confluence"}' | jq '.route, .answer' && \

echo -e "\n=== Testing Web Agent ===" && \
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Latest AI news"}' | jq '.route, .answer' && \

echo -e "\n=== Testing Multi-Agent ===" && \
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"Count users AND Tesla news"}' | jq '.route, .sources'
```

### Expected Results

```json
// General
"general"
"Hi! How can I help you today?"

// DB
"db"
"Based on the database, there are 10 users."

// RAG
"rag"
"To troubleshoot Confluence, check server logs..."

// Web
"web"
"Latest AI news: TechCrunch reports..."

// Multi
"multi"
[{"type":"rag"},{"type":"db"},{"type":"web"}]
```

---

## Performance

### Benchmarks

| Operation | Avg Time | Notes |
|-----------|----------|-------|
| Simple query (general) | 1-2s | Direct LLM response |
| Database query | 2-3s | SQL generation + execution |
| RAG query | 2-4s | Embedding + vector search + LLM |
| Web search | 5-10s | Search + scraping + LLM |
| Multi-source | 8-15s | Sequential execution of all agents |

### Optimization Tips

1. **Use Ollama for speed** - Local LLM is faster than API calls
2. **Limit conversation history** - Default 5 exchanges is optimal
3. **Qdrant top_k=3** - Balance between quality and speed
4. **Enable caching** - LangChain cache for repeated queries
5. **Parallel execution** - Multi-agent queries run sequentially, consider parallelization

---

## Kubernetes Deployment Guide

### Overview

This section covers deploying the backend and MCP service to Kubernetes (Minikube) while running the frontend locally. The architecture uses:

- **Kubernetes Pods:** Backend, MCP Service, PostgreSQL, Qdrant
- **Port Forwarding:** Access Kubernetes services from localhost
- **Local Frontend:** Vite dev server connecting to Kubernetes backend

### Architecture

```
┌──────────────────────────────────────────────────────┐
│         Kubernetes Cluster (Minikube)                │
│         Namespace: multiagent-assistant              │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐   │
│  │  Backend    │  │ MCP Service │  │PostgreSQL│   │
│  │  Pod        │  │    Pod      │  │   Pod    │   │
│  │  Port 8000  │  │  Port 8001  │  │Port 5432 │   │
│  └─────────────┘  └─────────────┘  └──────────┘   │
│                                                      │
│  ┌──────────┐                                       │
│  │  Qdrant  │                                       │
│  │   Pod    │                                       │
│  │Port 6333 │                                       │
│  └──────────┘                                       │
└──────────────────────────────────────────────────────┘
         │                │              │        │
         │ kubectl        │              │        │
         │ port-forward   │              │        │
         ▼                ▼              ▼        ▼
    localhost:8000  localhost:8001  localhost:5432  localhost:6333
         │                │              │        │
         └────────────────┴──────────────┴────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   Local Frontend       │
              │   Vite Dev Server      │
              │   Port 5173            │
              │                        │
              │   Connects to:         │
              │   - Backend (8000)     │
              │   - PostgreSQL (5432)  │
              │   - Qdrant (6333)      │
              └────────────────────────┘
```

### Prerequisites

```bash
# Verify installations
minikube version          # Minikube installed
kubectl version --client  # kubectl installed
docker --version         # Docker Desktop running
ollama list              # Ollama running with llama3

# Start Minikube (if not running)
minikube start

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### Step 1: Build Docker Images

Docker images must be built in Minikube's Docker environment so they're available to Kubernetes.

#### Set Docker Environment

```bash
# Configure shell to use Minikube's Docker daemon
eval $(minikube docker-env)

# Verify (should show Minikube's Docker)
docker ps
```

⚠️ **Important:** Run all docker build commands in the same terminal session after running `eval $(minikube docker-env)`.

#### Build Backend Image

```bash
cd /path/to/ai-multi-agent-project

# Build backend Docker image
docker build -f docker/backend.Dockerfile -t multiagent-backend:latest .
```

**Expected Output:**
```
[+] Building 85.3s (13/13) FINISHED
 => [internal] load build definition
 => [internal] load metadata
 => [1/8] FROM docker.io/library/python:3.11-slim
 => [4/8] RUN pip install --no-cache-dir -r requirements.txt
 => [5/8] COPY backend ./backend
 => [8/8] WORKDIR /app/backend
 => exporting to image
 => => naming to docker.io/library/multiagent-backend:latest
```

**Verify:**
```bash
docker images | grep multiagent-backend
# multiagent-backend   latest   a9db71023150   2 minutes ago   525MB
```

#### Build MCP Service Image

```bash
# Build MCP service Docker image
docker build -f docker/mcp.Dockerfile -t multiagent-mcp:latest .
```

**Expected Output:**
```
[+] Building 10.2s (13/13) FINISHED
 => exporting to image
 => => naming to docker.io/library/multiagent-mcp:latest
```

**Verify:**
```bash
docker images | grep multiagent-mcp
# multiagent-mcp   latest   7c85ff63565c   1 minute ago   286MB
```

#### Dockerfile Contents

**Backend Dockerfile (`docker/backend.Dockerfile`):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend ./backend
COPY embeddings ./embeddings
COPY data ./data

# Set Python path and working directory
ENV PYTHONPATH=/app:/app/backend
WORKDIR /app/backend

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**MCP Dockerfile (`docker/mcp.Dockerfile`):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY mcp_service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_service ./mcp_service

# Set Python path and working directory
ENV PYTHONPATH=/app:/app/mcp_service
WORKDIR /app/mcp_service

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Step 2: Deploy to Kubernetes

#### Kubernetes Manifests Structure

```
minikube/
├── backend/
│   ├── backend-configmap.yaml    # Environment variables
│   ├── backend-secret.yaml       # Sensitive data (passwords)
│   ├── backend-deployment.yaml   # Backend deployment spec
│   └── backend-service.yaml      # Backend service (ClusterIP)
│
├── mcp/
│   ├── mcp-configmap.yaml        # Environment variables
│   ├── mcp-secret.yaml           # Sensitive data
│   ├── mcp-deployment.yaml       # MCP deployment spec
│   └── mcp-service.yaml          # MCP service (ClusterIP)
│
├── postgres/
│   ├── postgres-pvc.yaml         # PersistentVolumeClaim (5Gi storage)
│   ├── postgres-secret.yaml      # Credentials (user, password, database)
│   ├── postgres-deployment.yaml  # PostgreSQL deployment spec
│   └── postgres-service.yaml     # PostgreSQL service (ClusterIP)
│
└── qdrant/
    ├── qdrant-pvc.yaml           # PersistentVolumeClaim (5Gi storage)
    ├── qdrant-deployment.yaml    # Qdrant deployment spec
    └── qdrant-service.yaml       # Qdrant service (ClusterIP)
```

#### Backend ConfigMap

**File:** `minikube/backend/backend-configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: multiagent-assistant
data:
  # Database Configuration
  POSTGRES_HOST: "postgres"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "appdb"
  POSTGRES_USER: "appuser"
  POSTGRES_DSN: "postgresql://appuser:apppass@postgres:5432/appdb"
  
  # Qdrant Configuration
  QDRANT_HOST: "qdrant"
  QDRANT_PORT: "6333"
  QDRANT_COLLECTION: "documents"
  QDRANT_URL: "http://qdrant:6333"
  QDRANT_COLLECTION_NAME: "documents"
  
  # MCP Service Configuration
  MCP_SERVICE_URL: "http://mcp-service:8001"
  
  # LLM Configuration
  LLM_PROVIDER: "ollama"
  OLLAMA_BASE_URL: "http://host.minikube.internal:11434"
  OLLAMA_MODEL: "llama3"
  OLLAMA_EMBEDDING_MODEL: "nomic-embed-text"
  
  # Logging
  LOG_LEVEL: "INFO"
```

⚠️ **Note:** `host.minikube.internal` allows Kubernetes pods to access services on your host machine (Ollama).

#### Backend Secret

**File:** `minikube/backend/backend-secret.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secret
  namespace: multiagent-assistant
type: Opaque
stringData:
  POSTGRES_PASSWORD: "apppass"
```

#### Backend Deployment

**File:** `minikube/backend/backend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: multiagent-assistant
  labels:
    app: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: multiagent-backend:latest
        imagePullPolicy: Never  # Use local image, don't pull from registry
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: backend-config
        - secretRef:
            name: backend-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

#### Backend Service

**File:** `minikube/backend/backend-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: multiagent-assistant
  labels:
    app: backend
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: backend
```

#### MCP Service Manifests

Similar structure for MCP service - see `minikube/mcp/` directory.

**Key Configuration:**
```yaml
# minikube/mcp/mcp-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-config
  namespace: multiagent-assistant
data:
  POSTGRES_HOST: "postgres"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "appdb"
  POSTGRES_USER: "appuser"
  QDRANT_URL: "http://qdrant:6333"
  QDRANT_COLLECTION_NAME: "documents"
  OLLAMA_BASE_URL: "http://host.minikube.internal:11434"
  OLLAMA_EMBEDDING_MODEL: "nomic-embed-text"
```

#### PostgreSQL Manifests

**PersistentVolumeClaim:** `minikube/postgres/postgres-pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: multiagent-assistant
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard
```

**Secret:** `minikube/postgres/postgres-secret.yaml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: multiagent-assistant
type: Opaque
stringData:
  POSTGRES_USER: "appuser"
  POSTGRES_PASSWORD: "apppass"
  POSTGRES_DB: "appdb"
```

**Deployment:** `minikube/postgres/postgres-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: multiagent-assistant
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: "appdb"
        - name: POSTGRES_USER
          value: "appuser"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
          subPath: postgres
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

**Service:** `minikube/postgres/postgres-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: multiagent-assistant
spec:
  type: ClusterIP
  ports:
  - port: 5432
    targetPort: 5432
  selector:
    app: postgres
```

#### Qdrant Manifests

**PersistentVolumeClaim:** `minikube/qdrant/qdrant-pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qdrant-pvc
  namespace: multiagent-assistant
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: standard
```

**Deployment:** `minikube/qdrant/qdrant-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: multiagent-assistant
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.11.0
        ports:
        - containerPort: 6333
          name: http
        - containerPort: 6334
          name: grpc
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
        livenessProbe:
          httpGet:
            path: /
            port: 6333
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 6333
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
      volumes:
      - name: qdrant-storage
        persistentVolumeClaim:
          claimName: qdrant-pvc
```

**Service:** `minikube/qdrant/qdrant-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: qdrant
  namespace: multiagent-assistant
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 6333
    targetPort: 6333
  - name: grpc
    port: 6334
    targetPort: 6334
  selector:
    app: qdrant
```

#### Deploy All Services

**Deploy in order:**

```bash
# 1. Deploy PostgreSQL (data layer)
kubectl apply -f minikube/postgres/

# Expected output:
# persistentvolumeclaim/postgres-pvc created
# deployment.apps/postgres created
# service/postgres created

# 2. Deploy Qdrant (data layer)
kubectl apply -f minikube/qdrant/

# Expected output:
# persistentvolumeclaim/qdrant-pvc created
# deployment.apps/qdrant created
# service/qdrant created

# 3. Wait for data layer to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n multiagent-assistant --timeout=120s
kubectl wait --for=condition=ready pod -l app=qdrant -n multiagent-assistant --timeout=120s

# 4. Deploy MCP service (depends on PostgreSQL and Qdrant)
kubectl apply -f minikube/mcp/

# Expected output:
# configmap/mcp-config created
# deployment.apps/mcp-service created
# secret/mcp-secret created
# service/mcp-service created

# 5. Deploy backend (depends on MCP, PostgreSQL, Qdrant)
kubectl apply -f minikube/backend/

# Expected output:
# configmap/backend-config created
# deployment.apps/backend created
# secret/backend-secret created
# service/backend created
```

**Or deploy everything at once:**

```bash
# Deploy all manifests
kubectl apply -f minikube/

# This applies all YAML files recursively
```

#### Verify Deployment

```bash
# Check all pods
kubectl get pods -n multiagent-assistant

# Expected output:
# NAME                           READY   STATUS    RESTARTS   AGE
# backend-7d54965cc4-c6cpj       1/1     Running   0          2m
# mcp-service-57bff86dcb-j4s4z   1/1     Running   0          2m
# postgres-6ff98854d6-jxxhq      1/1     Running   0          5m
# qdrant-74745d4c5b-7q5z8        1/1     Running   0          5m

# Check all services
kubectl get svc -n multiagent-assistant

# Expected output:
# NAME          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)
# backend       ClusterIP   10.97.47.225     <none>        8000/TCP
# mcp-service   ClusterIP   10.96.154.147    <none>        8001/TCP
# postgres      ClusterIP   10.102.153.7     <none>        5432/TCP
# qdrant        ClusterIP   10.104.77.128    <none>        6333/TCP

# Check persistent volume claims
kubectl get pvc -n multiagent-assistant

# Expected output:
# NAME           STATUS   VOLUME                                     CAPACITY
# postgres-pvc   Bound    pvc-98fa8f13-5650-4368-8442-14401224e33f   5Gi
# qdrant-pvc     Bound    pvc-268c4148-12f8-46a0-8137-7a40721245bf   5Gi

# Check logs for each service
kubectl logs -n multiagent-assistant deployment/backend --tail=20
kubectl logs -n multiagent-assistant deployment/mcp-service --tail=20
kubectl logs -n multiagent-assistant deployment/postgres --tail=20
kubectl logs -n multiagent-assistant deployment/qdrant --tail=20
```

### Step 3: Understanding Kubernetes Networking

Before setting up services, it's crucial to understand how connectivity works in this hybrid setup.

#### Network Connectivity Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONNECTIVITY EXPLAINED                        │
└─────────────────────────────────────────────────────────────────┘

1. INSIDE KUBERNETES (Pod-to-Pod Communication)
   ============================================
   ✅ NO PORT-FORWARDING NEEDED
   
   Backend Pod → postgres:5432 → PostgreSQL Pod
   Backend Pod → qdrant:6333 → Qdrant Pod
   Backend Pod → mcp-service:8001 → MCP Pod
   
   How it works:
   • Kubernetes internal DNS resolves service names
   • ClusterIP services provide stable endpoints
   • All pods in same namespace can communicate directly
   • Fast, secure, internal-only networking


2. LOCALHOST TO KUBERNETES (Development Access)
   ============================================
   ✅ PORT-FORWARDING REQUIRED
   
   Frontend (localhost:5173) → localhost:8000
                                     ↓ (kubectl port-forward)
                                Backend Pod (8000)
   
   Your Browser/Curl → localhost:8000
                            ↓ (kubectl port-forward)
                       Backend Pod (8000)
   
   How it works:
   • kubectl port-forward creates TCP tunnel
   • Forwards localhost:8000 → backend pod:8000
   • Only for development/debugging
   • In production, use Ingress/LoadBalancer instead


3. KUBERNETES TO LOCALHOST (Ollama Connection)
   ============================================
   ✅ SPECIAL MINIKUBE FEATURE: host.minikube.internal
   
   Backend Pod → host.minikube.internal:11434
                            ↓
                    Your Mac (Ollama on localhost:11434)
   
   How it works:
   • Minikube provides special DNS: host.minikube.internal
   • Resolves to your host machine's IP (e.g., 192.168.65.2)
   • Ollama must listen on 0.0.0.0:11434 (all interfaces)
   • Backend ConfigMap: OLLAMA_BASE_URL=http://host.minikube.internal:11434
   
   Verify Ollama is accessible:
   # Check Ollama listens on all interfaces
   lsof -i :11434
   # Should show: TCP *:11434 (not 127.0.0.1:11434)
   
   # Test from inside backend pod
   kubectl exec -it -n multiagent-assistant deployment/backend -- bash
   curl http://host.minikube.internal:11434/api/tags
```

#### Why This Hybrid Setup?

**Services in Kubernetes:**
- ✅ Backend, MCP, PostgreSQL, Qdrant in K8s
- ✅ Production-like environment
- ✅ Easy to scale and monitor
- ✅ Isolated networking

**Frontend on Localhost:**
- ✅ Hot module reload during development
- ✅ Fast iteration without rebuilding containers
- ✅ Easy debugging with browser DevTools

**Ollama on Localhost:**
- ✅ Direct access to Mac's GPU/CPU
- ✅ Easy model management (`ollama pull`, `ollama list`)
- ✅ Faster model loading
- ✅ Can use Ollama for other projects
- ✅ No need to mount large model files into K8s

#### Connection Summary Table

| From | To | Method | URL | Notes |
|------|-----|--------|-----|-------|
| Frontend (localhost) | Backend (K8s) | Port-forward | `localhost:8000` | kubectl port-forward |
| Backend Pod | PostgreSQL Pod | Service DNS | `postgres:5432` | Internal K8s networking |
| Backend Pod | Qdrant Pod | Service DNS | `qdrant:6333` | Internal K8s networking |
| Backend Pod | MCP Pod | Service DNS | `mcp-service:8001` | Internal K8s networking |
| Backend Pod | Ollama (localhost) | Minikube magic | `host.minikube.internal:11434` | Minikube-specific feature |
| Your terminal | Backend (K8s) | Port-forward | `localhost:8000` | For testing with curl |

### Step 4: Setup Port Forwarding

Now that you understand the networking, let's set up port forwarding for development access.

#### Manual Port Forwarding

```bash
# PostgreSQL (optional - only if you want to connect from host)
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432 &

# Qdrant (optional - only if you want to connect from host)
kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333 &

# Backend (required - for frontend to connect)
kubectl port-forward -n multiagent-assistant svc/backend 8000:8000 &

# MCP Service (optional - for direct testing)
kubectl port-forward -n multiagent-assistant svc/mcp-service 8001:8001 &
```

**Note:** Port-forwarding for PostgreSQL and Qdrant is optional because:
- Backend pods connect directly via service DNS (no port-forward needed)
- Only forward these if you want to access them from your host machine (e.g., DBeaver, psql)

#### Automated Startup Script

**File:** `k8s-startup.sh`

```bash
#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Starting AI Multi-Agent System (Kubernetes Mode)"
echo "=================================================="

# Kill existing port-forwards and frontend
echo ""
echo "🧹 Cleaning up existing processes..."
pkill -f "kubectl port-forward.*backend" 2>/dev/null || true
pkill -f "kubectl port-forward.*mcp" 2>/dev/null || true
pkill -f "kubectl port-forward.*postgres" 2>/dev/null || true
pkill -f "kubectl port-forward.*qdrant" 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 2

# Check Kubernetes pods
echo ""
echo "📦 Checking Kubernetes pods..."
kubectl get pods -n multiagent-assistant

echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=backend -n multiagent-assistant --timeout=60s
kubectl wait --for=condition=ready pod -l app=mcp-service -n multiagent-assistant --timeout=60s
kubectl wait --for=condition=ready pod -l app=postgres -n multiagent-assistant --timeout=60s
kubectl wait --for=condition=ready pod -l app=qdrant -n multiagent-assistant --timeout=60s

# Start port-forwarding
echo ""
echo "🔌 Setting up port forwarding..."
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432 > logs/postgres-pf.log 2>&1 &
echo "   ✓ PostgreSQL: localhost:5432"
sleep 1

kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333 > logs/qdrant-pf.log 2>&1 &
echo "   ✓ Qdrant: localhost:6333"
sleep 1

kubectl port-forward -n multiagent-assistant svc/backend 8000:8000 > logs/backend-pf.log 2>&1 &
echo "   ✓ Backend: localhost:8000"
sleep 1

kubectl port-forward -n multiagent-assistant svc/mcp-service 8001:8001 > logs/mcp-pf.log 2>&1 &
echo "   ✓ MCP Service: localhost:8001"
sleep 3

# Test services
echo ""
echo "🧪 Testing services..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is healthy"
else
    echo "   ✗ Backend is not responding"
fi

if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✓ MCP Service is healthy"
else
    echo "   ✗ MCP Service is not responding"
fi

# Start frontend
echo ""
echo "🎨 Starting frontend..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

sleep 5

# Check if frontend is running
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "   ✓ Frontend started on http://localhost:5173"
else
    echo "   ✗ Frontend failed to start"
    echo "   Check logs/frontend.log for details"
fi

echo ""
echo "=================================================="
echo "✅ All services started!"
echo ""
echo "Service URLs:"
echo "  Frontend:    http://localhost:5173"
echo "  Backend:     http://localhost:8000"
echo "  MCP Service: http://localhost:8001"
echo "  PostgreSQL:  localhost:5432"
echo "  Qdrant:      http://localhost:6333"
echo ""
echo "Kubernetes Pods:"
kubectl get pods -n multiagent-assistant
echo ""
echo "To stop all services, run: ./k8s-shutdown.sh"
echo "To view logs: tail -f logs/frontend.log"
```

**Make executable:**
```bash
chmod +x k8s-startup.sh
```

**Run:**
```bash
./k8s-startup.sh
```

### Step 4: Configure Frontend

The frontend connects to the backend via Vite's proxy configuration.

**File:** `frontend/vite.config.js`

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",  // Backend via port-forward
        changeOrigin: true
      }
    }
  }
});
```

**Frontend API Client:** `frontend/src/api/client.js`

```javascript
import axios from "axios";

const api = axios.create({
  baseURL: "/api"  // Proxied to backend
});

export const chat = async (userId, message) => {
  const res = await api.post("/chat", { user_id: userId, message });
  return res.data;
};
```

### Step 5: Test End-to-End

```bash
# Test backend health
curl http://localhost:8000/health
# {"status":"ok"}

# Test MCP service
curl http://localhost:8001/health
# {"status":"healthy","service":"mcp"}

# Test chat API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"How many users are in the database?"}' | jq '.'

# Open frontend
open http://localhost:5173
```

### Updating Code and Redeploying

#### When You Make Code Changes

**Option 1: Automated Rebuild & Redeploy**

Create a script `rebuild-deploy.sh`:

```bash
#!/bin/bash
set -e

SERVICE=$1  # "backend" or "mcp"

if [ -z "$SERVICE" ]; then
    echo "Usage: ./rebuild-deploy.sh [backend|mcp|both]"
    exit 1
fi

# Set Minikube Docker environment
eval $(minikube docker-env)

rebuild_backend() {
    echo "🔨 Rebuilding backend image..."
    docker build -f docker/backend.Dockerfile -t multiagent-backend:latest .
    
    echo "🔄 Restarting backend deployment..."
    kubectl rollout restart deployment/backend -n multiagent-assistant
    
    echo "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/backend -n multiagent-assistant
    
    echo "✅ Backend redeployed!"
}

rebuild_mcp() {
    echo "🔨 Rebuilding MCP service image..."
    docker build -f docker/mcp.Dockerfile -t multiagent-mcp:latest .
    
    echo "🔄 Restarting MCP deployment..."
    kubectl rollout restart deployment/mcp-service -n multiagent-assistant
    
    echo "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/mcp-service -n multiagent-assistant
    
    echo "✅ MCP service redeployed!"
}

case $SERVICE in
    backend)
        rebuild_backend
        ;;
    mcp)
        rebuild_mcp
        ;;
    both)
        rebuild_backend
        rebuild_mcp
        ;;
    *)
        echo "Invalid service: $SERVICE"
        echo "Usage: ./rebuild-deploy.sh [backend|mcp|both]"
        exit 1
        ;;
esac

echo ""
echo "📊 Current pod status:"
kubectl get pods -n multiagent-assistant
```

**Make executable and use:**
```bash
chmod +x rebuild-deploy.sh

# After changing backend code
./rebuild-deploy.sh backend

# After changing MCP code
./rebuild-deploy.sh mcp

# After changing both
./rebuild-deploy.sh both
```

**Option 2: Manual Steps**

**Backend changes:**
```bash
# 1. Set Minikube Docker environment
eval $(minikube docker-env)

# 2. Rebuild image
docker build -f docker/backend.Dockerfile -t multiagent-backend:latest .

# 3. Restart deployment (pulls new image)
kubectl rollout restart deployment/backend -n multiagent-assistant

# 4. Watch rollout
kubectl rollout status deployment/backend -n multiagent-assistant

# 5. Check logs
kubectl logs -n multiagent-assistant deployment/backend --tail=50
```

**MCP service changes:**
```bash
# Same steps for MCP
eval $(minikube docker-env)
docker build -f docker/mcp.Dockerfile -t multiagent-mcp:latest .
kubectl rollout restart deployment/mcp-service -n multiagent-assistant
kubectl rollout status deployment/mcp-service -n multiagent-assistant
```

**Frontend changes:**
```bash
# Frontend runs locally, so just restart the dev server
# If already running via k8s-startup.sh, changes auto-reload

# Manual restart:
lsof -ti:5173 | xargs kill -9
cd frontend && npm run dev
```

#### Configuration Changes (ConfigMap/Secret)

**After updating ConfigMap or Secret files:**

```bash
# Apply changes
kubectl apply -f minikube/backend/backend-configmap.yaml
kubectl apply -f minikube/backend/backend-secret.yaml

# Restart deployment to pick up new config
kubectl rollout restart deployment/backend -n multiagent-assistant

# Same for MCP
kubectl apply -f minikube/mcp/mcp-configmap.yaml
kubectl rollout restart deployment/mcp-service -n multiagent-assistant
```

### Troubleshooting Kubernetes Deployment

#### Issue: Pods Not Starting

```bash
# Check pod status
kubectl get pods -n multiagent-assistant

# Describe pod for details
kubectl describe pod -n multiagent-assistant <pod-name>

# Common issues:
# - ImagePullBackOff: Image not found in Minikube's Docker
#   Solution: Rebuild with eval $(minikube docker-env)
# - CrashLoopBackOff: Application error
#   Solution: Check logs: kubectl logs -n multiagent-assistant <pod-name>
```

#### Issue: Import Errors in Pods

```bash
# Check logs
kubectl logs -n multiagent-assistant deployment/backend --tail=100

# Common cause: Wrong Python path or missing dependencies
# Solution: Rebuild image ensuring all dependencies are installed
```

#### Issue: Database Connection Errors

```bash
# Check if PostgreSQL pod is running
kubectl get pods -n multiagent-assistant | grep postgres

# Check service
kubectl get svc -n multiagent-assistant | grep postgres

# Verify DSN in ConfigMap
kubectl get configmap backend-config -n multiagent-assistant -o yaml | grep POSTGRES_DSN

# Should be: postgresql://appuser:apppass@postgres:5432/appdb
```

#### Issue: Backend Can't Connect to Ollama

**Symptoms:**
```
Connection refused to http://host.minikube.internal:11434
```

**Solution 1: Verify Ollama is listening on all interfaces**
```bash
# Check Ollama port binding
lsof -i :11434

# Should show:
# ollama  12345  user  TCP *:11434 (LISTEN)
#                           ↑
#                      Asterisk means all IPs (0.0.0.0)

# If it shows 127.0.0.1:11434, restart Ollama:
brew services restart ollama
# Or: ollama serve
```

**Solution 2: Test from inside backend pod**
```bash
# Get into backend pod shell
kubectl exec -it -n multiagent-assistant deployment/backend -- bash

# Test Ollama connection
curl http://host.minikube.internal:11434/api/tags

# If it fails, get host IP manually:
# Exit pod and run:
minikube ssh "route -n | grep ^0.0.0.0 | awk '{print \$2}'"
# Example output: 192.168.65.2

# Update ConfigMap with direct IP:
kubectl edit configmap backend-config -n multiagent-assistant
# Change: OLLAMA_BASE_URL: "http://192.168.65.2:11434"

# Restart backend to pick up change:
kubectl rollout restart deployment/backend -n multiagent-assistant
```

**Solution 3: Verify Ollama is running**
```bash
# Test Ollama from your Mac
curl http://localhost:11434/api/tags

# Expected response:
# {"models":[{"name":"llama3:latest",...}]}

# If not running:
brew services start ollama
# Or: ollama serve
```

#### Issue: Frontend Can't Connect to Backend

**Symptoms:**
```
Network Error: Failed to fetch
ERR_CONNECTION_REFUSED
```

**Solution 1: Check port-forward is running**
```bash
# Check if port-forward process exists
ps aux | grep "kubectl port-forward.*backend"

# Should show something like:
# kubectl port-forward -n multiagent-assistant svc/backend 8000:8000

# If not running, restart:
kubectl port-forward -n multiagent-assistant svc/backend 8000:8000 &
```

**Solution 2: Verify backend pod is healthy**
```bash
# Check pod status
kubectl get pods -n multiagent-assistant | grep backend

# Should show:
# backend-xxx   1/1   Running   0   5m

# Test backend health
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# If unhealthy, check logs:
kubectl logs -n multiagent-assistant deployment/backend --tail=50
```

**Solution 3: Check Vite proxy configuration**
```javascript
// frontend/vite.config.js should have:
export default defineConfig({
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  }
});
```

#### Issue: Port Forward Died

```bash
# Check if port forwards are running
ps aux | grep "kubectl port-forward"

# Restart all port forwards
./k8s-shutdown.sh
./k8s-startup.sh
```

#### Issue: "Host Not Found" Errors from Backend Pod

**Symptoms:**
```
Could not resolve host: postgres
Could not resolve host: qdrant
```

**Solution:**
```bash
# Verify services exist
kubectl get svc -n multiagent-assistant

# Should show:
# NAME          TYPE        CLUSTER-IP      PORT(S)
# backend       ClusterIP   10.96.xxx.xxx   8000/TCP
# mcp-service   ClusterIP   10.96.xxx.xxx   8001/TCP
# postgres      ClusterIP   10.96.xxx.xxx   5432/TCP
# qdrant        ClusterIP   10.96.xxx.xxx   6333/TCP

# If services missing, apply manifests:
kubectl apply -f minikube/postgres/
kubectl apply -f minikube/qdrant/ # if you have these

# Verify ConfigMap has correct service names:
kubectl get configmap backend-config -n multiagent-assistant -o yaml

# Should have:
# POSTGRES_HOST: "postgres"  # NOT "localhost"
# QDRANT_URL: "http://qdrant:6333"  # NOT "http://localhost:6333"
```

#### Issue: Kubernetes vs Localhost Confusion

**Understanding the difference:**

```bash
# ❌ WRONG: Using localhost in Kubernetes ConfigMaps
POSTGRES_DSN: "postgresql://appuser:apppass@localhost:5432/appdb"
# This fails because "localhost" inside pod refers to the pod itself

# ✅ CORRECT: Using service names in Kubernetes
POSTGRES_DSN: "postgresql://appuser:apppass@postgres:5432/appdb"
# "postgres" is the Kubernetes service name, DNS resolves it

# ❌ WRONG: Using service names from host machine
curl http://postgres:5432
# This fails because service names only work inside K8s cluster

# ✅ CORRECT: Using localhost from host machine via port-forward
curl http://localhost:5432
# Port-forward makes K8s service available on localhost
```

**Quick Reference:**

| Context | PostgreSQL | Qdrant | Backend | Ollama |
|---------|-----------|--------|---------|---------|
| Inside K8s Pod | `postgres:5432` | `qdrant:6333` | `backend:8000` | `host.minikube.internal:11434` |
| From Host (your Mac) | `localhost:5432` | `localhost:6333` | `localhost:8000` | `localhost:11434` |
| Needs port-forward? | Only for host access | Only for host access | Yes (for frontend) | No (runs on host) |

### Scaling Deployments

```bash
# Scale backend to 3 replicas
kubectl scale deployment backend --replicas=3 -n multiagent-assistant

# Check status
kubectl get pods -n multiagent-assistant | grep backend

# Scale back down
kubectl scale deployment backend --replicas=1 -n multiagent-assistant
```

### Viewing Logs

```bash
# Real-time logs from all backend pods
kubectl logs -n multiagent-assistant -l app=backend -f

# Logs from specific pod
kubectl logs -n multiagent-assistant <pod-name> --tail=100

# Previous pod logs (if pod crashed)
kubectl logs -n multiagent-assistant <pod-name> --previous
```

### Cleanup and Reset

**Shutdown script:** `k8s-shutdown.sh`

```bash
#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "🛑 Stopping AI Multi-Agent System (Kubernetes Mode)"
echo "=================================================="

# Stop frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    rm -f logs/frontend.pid
fi

lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Stop port-forwards
echo "Stopping port-forwards..."
pkill -f "kubectl port-forward.*backend" 2>/dev/null || true
pkill -f "kubectl port-forward.*mcp" 2>/dev/null || true
pkill -f "kubectl port-forward.*postgres" 2>/dev/null || true
pkill -f "kubectl port-forward.*qdrant" 2>/dev/null || true

sleep 2

echo ""
echo "✅ All services stopped!"
echo ""
echo "Kubernetes pods are still running. To stop them:"
echo "  kubectl delete -f minikube/"
echo ""
echo "To start services again, run: ./k8s-startup.sh"
```

**Partial teardown (keeps data):**
```bash
# Stop port forwards and frontend
./k8s-shutdown.sh

# Delete deployments (keeps PersistentVolumeClaims - data persists)
kubectl delete deployment backend mcp-service postgres qdrant -n multiagent-assistant

# To restart later:
kubectl apply -f minikube/
./k8s-startup.sh
```

**Full cleanup (deletes all data):**

```bash
# Stop port forwards and frontend
./k8s-shutdown.sh

# Delete all deployments and services
kubectl delete -f minikube/backend/
kubectl delete -f minikube/mcp/
kubectl delete -f minikube/postgres/
kubectl delete -f minikube/qdrant/

# Or delete everything at once
kubectl delete -f minikube/ --recursive

# Delete persistent volume claims (WARNING: deletes all data)
kubectl delete pvc postgres-pvc qdrant-pvc -n multiagent-assistant

# Verify everything is deleted
kubectl get all -n multiagent-assistant
# Should show: No resources found
```

**Fresh deployment:**

```bash
# Deploy everything
kubectl apply -f minikube/

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all -n multiagent-assistant --timeout=180s

# Start port forwarding and frontend
./k8s-startup.sh

# Re-ingest documents into Qdrant
PYTHONPATH=. python3 embeddings/ingestion_pipeline.py

# Setup database tables (if needed)
python3 setup_database.py
```

### Best Practices

1. **Always use Minikube's Docker:**
   ```bash
   eval $(minikube docker-env)
   ```

2. **Use `imagePullPolicy: Never`** in deployment specs to use local images

3. **Keep manifests in version control** (`minikube/` directory)

4. **Use ConfigMaps for configuration** - easy to update without rebuilding images

5. **Use Secrets for sensitive data** - never commit secrets to git

6. **Set resource limits** to prevent pods from consuming all cluster resources

7. **Use health checks** (liveness/readiness probes) for automatic recovery

8. **Check logs frequently** during development:
   ```bash
   kubectl logs -n multiagent-assistant deployment/backend -f
   ```

9. **Test locally first** before deploying to Kubernetes

10. **Keep startup scripts** for consistent deployment process

---

## Production Deployment (Cloud)

### Cloud Kubernetes Deployment

For production environments (AWS EKS, GCP GKE, Azure AKS):

**Changes needed:**

1. **Push images to container registry:**
   ```bash
   # Tag images
   docker tag multiagent-backend:latest your-registry/multiagent-backend:v1.0
   docker tag multiagent-mcp:latest your-registry/multiagent-mcp:v1.0
   
   # Push to registry
   docker push your-registry/multiagent-backend:v1.0
   docker push your-registry/multiagent-mcp:v1.0
   ```

2. **Update deployment manifests:**
   ```yaml
   # Change imagePullPolicy
   imagePullPolicy: Always  # Pull from registry
   
   # Use full image path
   image: your-registry/multiagent-backend:v1.0
   ```

3. **Use managed databases:**
   - Replace PostgreSQL with AWS RDS, Cloud SQL, or Azure Database
   - Replace Qdrant with Qdrant Cloud or self-hosted cluster
   - Update DSN in ConfigMaps

4. **Add ingress controller:**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: backend-ingress
   spec:
     rules:
     - host: api.yourdomain.com
       http:
         paths:
         - path: /
           backend:
             service:
               name: backend
               port:
                 number: 8000
   ```

5. **Enable TLS/HTTPS:**
   - Use cert-manager for automatic SSL certificates
   - Configure ingress with TLS

6. **Add authentication:**
   - Implement API key authentication
   - Use OAuth2/JWT tokens

7. **Setup monitoring:**
   - Prometheus for metrics
   - Grafana for dashboards
   - ELK stack for log aggregation

8. **Configure autoscaling:**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: backend-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: backend
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Environment-Specific Configs

**Development (Minikube):**
- Local Ollama
- Port-forwarding for access
- Single replica
- Debug logging enabled
- Hot reload enabled

**Staging:**
- Hosted LLM (Groq/OpenRouter)
- Internal Kubernetes services
- 2 replicas
- Info-level logging
- Automated testing

**Production:**
- OpenAI/Anthropic for reliability
- Managed PostgreSQL (AWS RDS)
- Managed Qdrant (Qdrant Cloud)
- 3+ replicas with autoscaling
- Error-level logging
- Rate limiting enabled
- Authentication required
- SSL/TLS enabled
- Monitoring and alerting

---

## RAG (Retrieval-Augmented Generation) System

### Overview

The RAG system enables semantic search over your document corpus using vector embeddings. When users ask questions about documentation, the system:

1. Converts the question to a vector embedding
2. Searches Qdrant for similar document chunks
3. Returns the most relevant passages
4. LLM generates an answer based on retrieved context

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Pipeline                              │
└─────────────────────────────────────────────────────────────┘

1. INGESTION (One-time or when adding new docs)
   ┌──────────────┐
   │ Source Docs  │ (*.txt files in data/docs/)
   │ - user_guide.txt
   │ - technical_documentation.txt
   │ - confluence_troubleshooting.txt
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Text Chunking│ (1000 chars, 200 overlap)
   │ Smart splitting at sentences/paragraphs
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Generate     │ Ollama: nomic-embed-text
   │ Embeddings   │ 768 dimensions per chunk
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Qdrant       │ Store vectors + metadata
   │ Vector DB    │ Collection: "documents"
   └──────────────┘

2. QUERY (Runtime when user asks a question)
   ┌──────────────┐
   │ User Query   │ "How to troubleshoot Confluence?"
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Embed Query  │ Ollama: nomic-embed-text
   │              │ Convert to 768-dim vector
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Vector Search│ Qdrant cosine similarity
   │ Top K=3      │ Find most similar chunks
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Retrieved    │ 3 most relevant passages
   │ Documents    │ with scores (0.0-1.0)
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ LLM          │ Llama3: Generate answer
   │ Generation   │ using retrieved context
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ Final Answer │ Context-aware response
   └──────────────┘
```

### Components

#### 1. Document Loader (`embeddings/document_loader.py`)

**Purpose:** Load and chunk text documents

**Key Functions:**

```python
def load_text_files(folder: str, chunk_documents: bool = True) -> List[Dict]:
    """
    Load .txt files from folder and split into chunks
    
    Args:
        folder: Path to docs (e.g., "data/docs")
        chunk_documents: Split large docs into chunks
    
    Returns:
        List of document chunks with metadata
    """
```

**Chunking Strategy:**
- **Chunk Size:** 1000 characters
- **Overlap:** 200 characters (maintains context across boundaries)
- **Smart Splitting:** Prefers paragraph breaks (`\n\n`), then sentence breaks (`. `)
- **Metadata:** Tracks source file, chunk index, total chunks

**Example Output:**
```python
[
    {
        "id": "uuid-1234",
        "text": "To troubleshoot Confluence...",
        "meta": {
            "path": "/path/to/confluence_troubleshooting.txt",
            "source": "local_file",
            "filename": "confluence_troubleshooting.txt",
            "chunk_index": 0,
            "total_chunks": 5
        }
    },
    # ... more chunks
]
```

#### 2. Embeddings Service (`backend/services/embeddings_service.py`)

**Purpose:** Convert text to vector embeddings

**Configuration:**
```python
MODEL: nomic-embed-text (via Ollama)
DIMENSIONS: 768
PROVIDER: Ollama (localhost:11434)
```

**Key Functions:**

```python
def embed_texts(texts: List[str]) -> List[List[float]]:
    """Batch embed multiple texts"""
    
def embed_query(text: str) -> List[float]:
    """Embed single query text"""
```

**Performance:**
- **Speed:** ~50ms per text (local Ollama)
- **Batch Size:** Up to 100 texts at once
- **Quality:** nomic-embed-text optimized for semantic search

#### 3. Qdrant Service (`backend/services/qdrant_service.py`)

**Purpose:** Vector database operations

**Collection Configuration:**
```python
{
    "name": "documents",
    "vectors": {
        "size": 768,           # nomic-embed-text dimensions
        "distance": "Cosine"   # Similarity metric
    }
}
```

**Key Functions:**

```python
def upsert_documents(docs: List[Dict]):
    """Insert/update documents in Qdrant"""
    
def search(query_vector: List[float], limit: int = 5):
    """Vector similarity search"""
```

**Search Process:**
1. Receive query vector (768 dimensions)
2. Calculate cosine similarity with all stored vectors
3. Return top K most similar documents
4. Include similarity scores (0.0-1.0, higher = more similar)

#### 4. Ingestion Pipeline (`embeddings/ingestion_pipeline.py`)

**Purpose:** Main ingestion script

**Workflow:**
```python
1. Load documents from data/docs/
2. Generate embeddings for all chunks
3. Upsert to Qdrant with metadata
4. Verify upload success
```

### Current Data

**Location:** `data/docs/`

**Files:**
1. `technical_documentation.txt` - Technical specifications and architecture
2. `user_guide.txt` - User manual and how-to guides
3. `confluence_troubleshooting.txt` - Troubleshooting procedures

**Statistics:**
- **Total Documents:** 3 files
- **Total Chunks:** 21 chunks (after splitting)
- **Average Chunk Size:** ~900 characters
- **Collection Size:** ~16KB in Qdrant

### Adding New Documents

#### Method 1: Add Text Files (Recommended)

**Step 1: Prepare Your Documents**

```bash
# Create new .txt files in data/docs/
cd ai-multi-agent-project/data/docs/

# Add your documents
echo "Your content here..." > new_document.txt
echo "More content..." > another_document.txt
```

**Supported Content:**
- Product documentation
- User guides
- FAQs
- Technical specifications
- Troubleshooting guides
- Knowledge base articles
- Meeting notes
- Standard operating procedures

**Best Practices:**
- ✅ Use descriptive filenames: `api_authentication.txt`
- ✅ Plain text format (.txt)
- ✅ UTF-8 encoding
- ✅ Clear structure with headings
- ✅ One topic per file for better retrieval
- ❌ Avoid very short files (<100 chars)
- ❌ Avoid binary formats (PDF, DOCX) - convert first

**Step 2: Run Ingestion**

```bash
# From project root
cd /path/to/ai-multi-agent-project

# Set environment
export PYTHONPATH=$PWD:$PWD/backend

# Run ingestion pipeline
python3 embeddings/ingestion_pipeline.py
```

**Expected Output:**
```
Loaded 25 document chunks from 5 files
Generating embeddings...
Uploading to Qdrant...
✓ Ingested 25 docs into Qdrant.
```

**Step 3: Verify Upload**

```bash
# Test RAG query
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","message":"What is in the new documentation?"}' | jq '.answer'
```

#### Method 2: Programmatic Ingestion

**For Custom Data Sources:**

```python
# custom_ingestion.py
from backend.services.embeddings_service import embeddings_service
from backend.services.qdrant_service import qdrant_service
import uuid

# Your custom documents
documents = [
    {
        "text": "Custom content about API authentication...",
        "metadata": {
            "source": "api_docs",
            "category": "authentication",
            "date": "2025-12-07"
        }
    },
    # ... more docs
]

# Generate embeddings
texts = [doc["text"] for doc in documents]
vectors = embeddings_service.embed_texts(texts)

# Prepare for Qdrant
qdrant_docs = []
for doc, vector in zip(documents, vectors):
    qdrant_docs.append({
        "id": str(uuid.uuid4()),
        "vector": vector,
        "payload": {
            "text": doc["text"],
            **doc["metadata"]
        }
    })

# Upload
qdrant_service.upsert_documents(qdrant_docs)
print(f"✓ Ingested {len(qdrant_docs)} documents")
```

#### Method 3: Bulk Import from Other Sources

**From PDF files:**

```bash
# Install PDF library
pip install pypdf2

# Convert PDFs to text
python3 << EOF
import PyPDF2
from pathlib import Path

pdf_dir = Path("data/pdfs")
txt_dir = Path("data/docs")

for pdf_file in pdf_dir.glob("*.pdf"):
    with open(pdf_file, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    # Save as .txt
    txt_file = txt_dir / f"{pdf_file.stem}.txt"
    txt_file.write_text(text, encoding="utf-8")
    print(f"✓ Converted {pdf_file.name}")
EOF

# Now run normal ingestion
python3 embeddings/ingestion_pipeline.py
```

**From Confluence/Notion:**

```python
# confluence_import.py
import requests

# Fetch from Confluence API
confluence_url = "https://your-domain.atlassian.net"
auth = ("email", "api_token")

response = requests.get(
    f"{confluence_url}/wiki/rest/api/content",
    auth=auth,
    params={"type": "page", "expand": "body.storage"}
)

# Extract and save
for page in response.json()["results"]:
    title = page["title"]
    content = page["body"]["storage"]["value"]
    
    # Clean HTML if needed
    from bs4 import BeautifulSoup
    text = BeautifulSoup(content, "html.parser").get_text()
    
    # Save
    Path(f"data/docs/{title}.txt").write_text(text)

# Run ingestion
os.system("python3 embeddings/ingestion_pipeline.py")
```

**From Database:**

```python
# db_to_rag.py
import psycopg2

# Connect to your database
conn = psycopg2.connect("postgresql://user:pass@localhost/db")
cursor = conn.execute("SELECT title, content FROM articles")

# Export to text files
for row in cursor.fetchall():
    title, content = row
    filename = f"data/docs/{title.replace(' ', '_')}.txt"
    Path(filename).write_text(f"# {title}\n\n{content}")

# Run ingestion
os.system("python3 embeddings/ingestion_pipeline.py")
```

### Updating Existing Documents

**Option 1: Replace and Re-ingest**

```bash
# 1. Update the source file
vim data/docs/user_guide.txt  # Make your changes

# 2. Clear old data (optional - upsert will update)
# To start fresh:
python3 embeddings/cleanup.py

# 3. Re-run ingestion
python3 embeddings/ingestion_pipeline.py
```

**Option 2: Incremental Update**

```python
# update_single_doc.py
from embeddings.document_loader import load_text_files
from backend.services.embeddings_service import embeddings_service
from backend.services.qdrant_service import qdrant_service

# Load only updated file
docs = load_text_files("data/docs", chunk_documents=True)
updated_docs = [d for d in docs if "user_guide.txt" in d["meta"]["filename"]]

# Generate embeddings
texts = [d["text"] for d in updated_docs]
vectors = embeddings_service.embed_texts(texts)

# Upsert (will update if ID exists)
qdrant_docs = []
for doc, vector in zip(updated_docs, vectors):
    qdrant_docs.append({
        "id": doc["id"],
        "vector": vector,
        "payload": {"text": doc["text"], **doc["meta"]}
    })

qdrant_service.upsert_documents(qdrant_docs)
print(f"✓ Updated {len(qdrant_docs)} chunks")
```

### Deleting Documents

**Clear entire collection:**

```bash
# Using cleanup script
python3 embeddings/cleanup.py
```

**Delete specific documents:**

```python
# delete_docs.py
from backend.services.qdrant_service import qdrant_service
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Delete by filename
qdrant_service.client.delete(
    collection_name="documents",
    points_selector={
        "filter": Filter(
            must=[
                FieldCondition(
                    key="filename",
                    match=MatchValue(value="old_document.txt")
                )
            ]
        )
    }
)
```

### RAG Query Configuration

**Adjusting Retrieval:**

**Number of documents returned (top_k):**
```python
# backend/agents/rag_agent.py
# Default: 3 documents
top_k = 3  # Increase for more context, decrease for faster responses
```

**Minimum similarity threshold:**
```python
# Filter results by score
MIN_SCORE = 0.5  # Only return docs with >50% similarity

results = qdrant_service.search(query_vector, limit=10)
filtered = [r for r in results if r["score"] > MIN_SCORE]
```

**Metadata filtering:**
```python
# Search only specific categories
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = qdrant_service.client.query_points(
    collection_name="documents",
    query=query_vector,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="category",
                match=MatchValue(value="troubleshooting")
            )
        ]
    ),
    limit=3
)
```

### RAG Performance Optimization

#### 1. Embedding Performance

**Current:** ~50ms per query (Ollama local)

**Optimization:**
```bash
# Use faster embedding model (if available)
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large  # Smaller, faster

# Or use OpenAI for speed
LLM_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # 10-20ms per query
```

#### 2. Chunk Size Tuning

**Current:** 1000 characters, 200 overlap

**Adjust for your use case:**

```python
# embeddings/document_loader.py

# Smaller chunks (better precision, more search time)
chunks = chunk_text(text, chunk_size=500, overlap=100)

# Larger chunks (more context, fewer results)
chunks = chunk_text(text, chunk_size=2000, overlap=400)
```

**Guidelines:**
- **Short FAQs:** 300-500 chars
- **Technical docs:** 800-1200 chars
- **Long articles:** 1500-2000 chars

#### 3. Qdrant Performance

**Indexing for speed:**
```python
# When creating collection, add HNSW index
from qdrant_client.models import HnswConfigDiff

qdrant_service.client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    hnsw_config=HnswConfigDiff(
        m=16,              # Links per node (higher = more accurate, slower)
        ef_construct=100,  # Build-time search depth
    )
)
```

**Query optimization:**
```python
# Use quantization for faster search (slight accuracy loss)
from qdrant_client.models import QuantizationConfig, ScalarQuantization

qdrant_service.client.update_collection(
    collection_name="documents",
    quantization_config=ScalarQuantization(
        type="int8",
        quantile=0.99
    )
)
```

### RAG Quality Improvement

#### 1. Improve Document Quality

**Before ingestion:**
- ✅ Remove boilerplate text (headers, footers)
- ✅ Fix formatting issues (extra spaces, line breaks)
- ✅ Add clear section headings
- ✅ Use consistent terminology

**Text cleaning script:**
```python
# clean_docs.py
import re
from pathlib import Path

docs_dir = Path("data/docs")

for file in docs_dir.glob("*.txt"):
    text = file.read_text()
    
    # Remove extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # Remove page numbers, headers
    text = re.sub(r'Page \d+', '', text)
    text = re.sub(r'Confidential.*\n', '', text)
    
    file.write_text(text)
```

#### 2. Add Metadata for Filtering

```python
# Enhanced metadata
docs.append({
    "id": str(uuid.uuid4()),
    "text": chunk,
    "meta": {
        "filename": path.name,
        "category": "troubleshooting",  # Add categories
        "product": "confluence",         # Add product tags
        "version": "8.0",                # Version info
        "date": "2025-12-07",            # Last updated
        "author": "tech_writer",         # Content owner
        "language": "en",                # Language
        "priority": "high"               # Importance
    }
})
```

#### 3. Hybrid Search (Keyword + Semantic)

```python
# Combine vector search with keyword matching
from qdrant_client.models import Filter, FieldCondition, MatchText

# Vector search
vector_results = qdrant_service.search(query_vector, limit=10)

# Keyword filter
keyword_results = qdrant_service.client.scroll(
    collection_name="documents",
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key="text",
                match=MatchText(text="confluence error")
            )
        ]
    )
)

# Combine and re-rank
combined = merge_and_rerank(vector_results, keyword_results)
```

### Monitoring RAG Performance

#### 1. Track Retrieval Quality

```python
# Add to rag_agent.py
def rag_agent(state: GraphState) -> GraphState:
    # ... existing code ...
    
    # Log retrieval metrics
    state.setdefault("debug", {})["rag_metrics"] = {
        "query": query,
        "num_results": len(documents),
        "avg_score": sum(d["score"] for d in documents) / len(documents),
        "top_score": documents[0]["score"] if documents else 0,
        "sources": [d["metadata"]["filename"] for d in documents]
    }
```

#### 2. Monitor Qdrant Health

```bash
# Check collection stats
curl http://localhost:6333/collections/documents

# Response includes:
# - vectors_count: Total documents
# - indexed_vectors_count: Indexed for search
# - points_count: Total data points
```

#### 3. Test Query Quality

```python
# test_rag_quality.py
test_queries = [
    ("How to troubleshoot Confluence?", ["confluence_troubleshooting.txt"]),
    ("API authentication guide", ["technical_documentation.txt"]),
    ("User login process", ["user_guide.txt"]),
]

for query, expected_sources in test_queries:
    response = test_query(query)
    actual_sources = [r["meta"]["filename"] for r in response["sources"]]
    
    match = any(exp in actual for exp in expected_sources for actual in actual_sources)
    print(f"{'✓' if match else '✗'} {query}")
```

### RAG Troubleshooting

#### Issue: No Results Returned

**Causes:**
1. Collection doesn't exist
2. No documents ingested
3. Query too specific

**Solutions:**
```bash
# Check collection
curl http://localhost:6333/collections/documents

# Re-run ingestion
python3 embeddings/ingestion_pipeline.py

# Test with broader query
curl -X POST http://localhost:8000/api/chat \
  -d '{"user_id":"test","message":"Tell me about the documentation"}'
```

#### Issue: Poor Quality Results

**Causes:**
1. Documents not well-structured
2. Chunk size too large/small
3. Wrong embedding model

**Solutions:**
```python
# 1. Improve document structure
# Add clear headings, remove noise

# 2. Adjust chunk size
chunk_text(text, chunk_size=800, overlap=150)  # Experiment

# 3. Try different embedding model
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
```

#### Issue: Slow Queries

**Causes:**
1. Large collection (>100k docs)
2. No indexing
3. Ollama inference slow

**Solutions:**
```python
# Enable HNSW indexing (see Performance section)
# Use quantization
# Switch to OpenAI embeddings for speed
```

### RAG Best Practices

1. **Document Preparation:**
   - Clean and structure documents before ingestion
   - Use consistent formatting
   - Add meaningful metadata

2. **Chunking Strategy:**
   - Balance chunk size (not too small, not too large)
   - Use overlap to maintain context
   - Prefer natural boundaries (paragraphs, sections)

3. **Embedding Quality:**
   - Use domain-specific embedding models if available
   - Test different models for your use case
   - Consider fine-tuning for specialized domains

4. **Retrieval Configuration:**
   - Start with top_k=3, adjust based on testing
   - Add similarity threshold filtering
   - Use metadata filters for targeted search

5. **Maintenance:**
   - Regular updates when documents change
   - Monitor retrieval quality metrics
   - Prune outdated documents
   - Schedule periodic re-indexing

6. **Testing:**
   - Create test query sets
   - Track retrieval accuracy over time
   - Compare against expected results
   - A/B test different configurations

---

## Additional Resources

### Documentation Files

- `CONVERSATION_HISTORY.md` - Conversation memory details
- `COMPREHENSIVE_GUIDE.md` - General usage guide
- `ENHANCED_SUMMARY.md` - Implementation summary
- `GETTING_STARTED.md` - Quick start guide
- `TEST_EXECUTION_REPORT.md` - Test results

### API Documentation

- Backend: http://localhost:8000/docs (Swagger UI)
- MCP Service: http://localhost:8001/docs (Swagger UI)

### Support

For issues and questions:
1. Check logs in `logs/` directory
2. Review troubleshooting section above
3. Test with curl commands
4. Check service health endpoints

---

## Conclusion

This AI Multi-Agent System demonstrates a production-ready architecture for building intelligent assistants that can:
- Route queries intelligently to specialized agents
- Search databases, documents, and the web
- Maintain conversation context across sessions
- Scale horizontally with Kubernetes
- Support multiple LLM providers
- Follow MCP standards for tool integration

The system is designed for extensibility - new agents, tools, and data sources can be added following the established patterns.

**Happy Building! 🚀**
