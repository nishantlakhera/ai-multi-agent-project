# 🚀 GET STARTED IN 5 MINUTES

## Prerequisites Check

```bash
# Check Python version (need 3.9+)
python3 --version

# Check if PostgreSQL is accessible
psql --version

# Check Docker (optional, for easy setup)
docker --version
```

## Method 1: Super Quick Start (Docker)

```bash
# 1. Start all services with Docker
docker-compose up -d

# 2. Wait 30 seconds for services to initialize
sleep 30

# 3. Initialize database
PGPASSWORD=postgres psql -h localhost -U postgres -d ai_app -f backend/db_setup.sql

# 4. Ingest documents
source .venv/bin/activate  # if using venv
python -m embeddings.ingestion_pipeline

# 5. Access the app
open http://localhost:5173
```

## Method 2: Quick Start (Local Services)

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Start PostgreSQL (if not running)
# brew services start postgresql  # macOS
# sudo service postgresql start   # Linux

# 3. Start Qdrant
docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant

# 4. Initialize database
psql -h localhost -U postgres -d ai_app -f backend/db_setup.sql

# 5. Ingest documents
python -m embeddings.ingestion_pipeline

# 6. Start backend (Terminal 1)
uvicorn backend.main:app --reload --port 8000

# 7. Start MCP service (Terminal 2)
uvicorn mcp_service.main:app --reload --port 8001

# 8. Start frontend (Terminal 3)
cd frontend && npm run dev
```

## Method 3: Automated Script

```bash
./quickstart.sh
```

## Verify It's Working

### Test Backend
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Test Chat API
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "How many users logged in today?"
  }'
```

### Expected Response
```json
{
  "answer": "According to the database, 7 users logged in today.",
  "route": "db",
  "sources": [{"type": "db"}],
  "debug": {...}
}
```

## 🎯 Try These Queries

Open http://localhost:5173 and try:

### Database Queries
- "How many users logged in today?"
- "Show me all users"
- "What are the recent orders?"
- "Total orders by status"

### Document Queries
- "How do I troubleshoot Confluence?"
- "What are the security best practices?"
- "Explain the backup strategy"
- "How does the caching work?"

### Web Queries
- "What are Tesla's new products?"
- "Latest AI news"
- "Apple upcoming releases"

## 🐛 Quick Troubleshooting

### Backend won't start
```bash
# Check if port is in use
lsof -i :8000
# Kill the process if needed
kill -9 <PID>
```

### Database connection error
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432
# If not, start it
docker-compose up -d postgres
```

### Qdrant not responding
```bash
# Check Qdrant health
curl http://localhost:6333/healthz
# If not running
docker-compose up -d qdrant
```

### No search results
```bash
# Re-run ingestion
python -m embeddings.ingestion_pipeline
```

## 📊 What's Included

✅ **Backend**: FastAPI with 6 agents (Router, RAG, DB, Web, Fusion, Final)
✅ **Database**: PostgreSQL with sample users and orders
✅ **Documents**: 3 sample docs with ~160 searchable chunks
✅ **Web Search**: Real DuckDuckGo integration
✅ **Frontend**: React chat interface
✅ **Docker**: Complete docker-compose setup

## 🎉 You're Ready!

Your AI Multi-Agent System is complete and ready to use!

For more details, see:
- **README.md** - Full documentation
- **COMPLETION_SUMMARY.md** - What was built
- **architecture.txt** - System architecture

Enjoy your AI assistant! 🤖

