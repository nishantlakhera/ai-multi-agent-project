# Local Development Setup Guide

This guide covers different scenarios for running the AI Multi-Agent project locally.

## Scenario 1: Frontend-Only Local (Recommended for Frontend Development)

**When to use:** You're developing the frontend and want to use the backend services running in Kubernetes.

### Setup:

1. **Ensure Kubernetes is running:**
   ```bash
   minikube status
   # If not running: minikube start
   ```

2. **Run the setup script:**
   ```bash
   ./start-frontend-only.sh
   ```

   This will:
   - Port-forward backend from Kubernetes to `localhost:8333`
   - Start the frontend dev server on `http://localhost:5173`

### Manual Setup:

If you prefer manual setup:

```bash
# Terminal 1: Port-forward backend
kubectl port-forward -n multiagent-assistant svc/backend 8333:8000

# Terminal 2: Start frontend
cd frontend
npm install  # First time only
npm run dev
```

### Configuration:

- **Frontend:** Uses [vite.config.js](frontend/vite.config.js) proxy (already configured)
- **Backend:** Running in Kubernetes with all services (Redis, PostgreSQL, Qdrant)
- **No `.env` files needed**

---

## Scenario 2: Backend + MCP Local (All Services Local)

**When to use:** You're developing backend/MCP services and need full control, but still use Kubernetes for infrastructure (Redis, PostgreSQL, Qdrant).

### Prerequisites:

Port-forward infrastructure services from Kubernetes:

```bash
# Terminal 1: Redis
kubectl port-forward -n multiagent-assistant svc/redis 6379:6379

# Terminal 2: PostgreSQL
kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432

# Terminal 3: Qdrant
kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333
```

### Required `.env` Files:

#### `backend/.env`:
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HISTORY_TTL_SECONDS=3600
REDIS_HISTORY_MAX_ITEMS=50

# Database Configuration
POSTGRES_DSN=postgresql://appuser:apppass@localhost:5432/appdb

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents

# MCP Service Configuration
MCP_SERVICE_URL=http://localhost:8444

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Environment
ENV=dev
```

#### `mcp_service/.env`:
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Database Configuration
POSTGRES_DSN=postgresql://appuser:apppass@localhost:5432/appdb

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Environment
ENV=dev
```

### Start Services:

```bash
# Terminal 4: Backend
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8333 --reload

# Terminal 5: MCP
cd mcp_service
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8444 --reload

# Terminal 6: Frontend
cd frontend
npm run dev
```

### Frontend Configuration:

Update [frontend/vite.config.js](frontend/vite.config.js) to point to local backend (already configured for port 8333).

---

## Scenario 3: Everything in Kubernetes

**When to use:** Testing production-like deployment.

### Setup:

```bash
./start-all.sh
```

Access services:
- Frontend: `minikube service frontend -n multiagent-assistant --url`
- Backend: `minikube service backend -n multiagent-assistant --url`

---

## Verification Commands

### Check Redis Connection:
```bash
# If Redis is port-forwarded to localhost:6379
redis-cli -h localhost -p 6379 ping

# View conversation history keys
redis-cli -h localhost -p 6379 KEYS "conversation_history:*"

# View specific user's history
redis-cli -h localhost -p 6379 LRANGE "conversation_history:demo-user" 0 -1
```

### Check PostgreSQL:
```bash
# Connect to PostgreSQL
psql postgresql://appuser:apppass@localhost:5432/appdb

# Query conversation history
SELECT user_id, role, content, created_at 
FROM conversation_history 
ORDER BY created_at DESC 
LIMIT 10;
```

### Check Backend Logs:
```bash
# Local backend: Check terminal output

# Kubernetes backend:
kubectl logs -n multiagent-assistant -l app=backend --tail=50 -f
```

---

## Troubleshooting

### Redis Not Caching Locally

**Problem:** Running backend locally but conversation history not saved to Redis.

**Solution:** Ensure:
1. Redis is port-forwarded: `kubectl port-forward -n multiagent-assistant svc/redis 6379:6379`
2. `REDIS_URL=redis://localhost:6379/0` is set in `backend/.env`
3. Backend was restarted after creating `.env` file
4. Check backend logs for: `[MemoryService] Redis cache enabled`

### Port Already in Use

**Problem:** `Address already in use` error.

**Solution:**
```bash
# Find process using port
lsof -i :8333  # or :8444, :5173

# Kill process
kill -9 <PID>
```

### Port-Forward Disconnects

**Problem:** Port-forward randomly disconnects.

**Solution:** Port-forwards can disconnect. Restart them:
```bash
# Find and kill old port-forward
pkill -f "port-forward.*redis"

# Restart
kubectl port-forward -n multiagent-assistant svc/redis 6379:6379
```

---

## Summary

| Scenario | Frontend | Backend | MCP | Infrastructure | `.env` Files Needed |
|----------|----------|---------|-----|----------------|---------------------|
| **Frontend-Only** | Local | K8s | K8s | K8s | None |
| **Full Local Dev** | Local | Local | Local | K8s (port-forwarded) | `backend/.env`, `mcp_service/.env` |
| **Full K8s** | K8s | K8s | K8s | K8s | None (uses ConfigMaps) |

**Recommendation:** Use **Frontend-Only** setup for UI development, **Full Local Dev** for backend development.
