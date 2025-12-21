#!/bin/bash
#############################################################################
# AI Multi-Agent System - Complete Startup Script
# This script starts everything from scratch, even after system reboot
#############################################################################

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AI Multi-Agent System - Complete Startup                    ║"
echo "║   Starting all services from scratch...                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

#############################################################################
# STEP 1: Prerequisites Check
#############################################################################
log_info "Step 1: Checking prerequisites..."

# Check required commands
REQUIRED_COMMANDS=("minikube" "kubectl" "docker" "ollama" "npm" "python3")
MISSING_COMMANDS=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v $cmd &> /dev/null; then
        MISSING_COMMANDS+=($cmd)
    fi
done

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    log_error "Missing required commands: ${MISSING_COMMANDS[*]}"
    log_error "Please install missing tools and try again"
    exit 1
fi

log_success "All required commands found"

#############################################################################
# STEP 2: Start Minikube (if not running)
#############################################################################
log_info "Step 2: Checking Minikube cluster..."

if ! minikube status &> /dev/null; then
    log_warning "Minikube is not running. Starting Minikube..."
    minikube start
    log_success "Minikube started"
else
    log_success "Minikube is already running"
fi

# Verify cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    log_error "Kubernetes cluster is not accessible"
    exit 1
fi

log_success "Kubernetes cluster is accessible"

#############################################################################
# STEP 3: Check/Create Namespace
#############################################################################
NAMESPACE="multiagent-assistant"

log_info "Step 3: Checking namespace..."

if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    log_warning "Namespace '$NAMESPACE' does not exist. Creating..."
    kubectl create namespace "$NAMESPACE"
    log_success "Namespace created"
else
    log_success "Namespace '$NAMESPACE' exists"
fi

#############################################################################
# STEP 4: Build Docker Images (if needed)
#############################################################################
log_info "Step 4: Checking Docker images..."

# Configure Docker to use Minikube's Docker daemon
eval "$(minikube docker-env)"

# Check if images exist
NEED_BUILD=false

if ! docker images | grep -q "multiagent-backend.*latest"; then
    log_warning "Backend image not found"
    NEED_BUILD=true
fi

if ! docker images | grep -q "multiagent-mcp.*latest"; then
    log_warning "MCP image not found"
    NEED_BUILD=true
fi

if [ "$NEED_BUILD" = true ]; then
    log_info "Building Docker images..."

    log_info "Building backend image..."
    docker build -f docker/backend.Dockerfile -t multiagent-backend:latest . || {
        log_error "Failed to build backend image"
        exit 1
    }
    log_success "Backend image built"

    log_info "Building MCP service image..."
    docker build -f docker/mcp.Dockerfile -t multiagent-mcp:latest . || {
        log_error "Failed to build MCP image"
        exit 1
    }
    log_success "MCP service image built"
else
    log_success "Docker images already exist"
fi

#############################################################################
# STEP 5: Deploy Kubernetes Services
#############################################################################
log_info "Step 5: Deploying Kubernetes services..."

# Check if services are already deployed and healthy; if anything is unhealthy, redeploy everything
if kubectl get deployment backend -n "$NAMESPACE" &> /dev/null; then
    log_warning "Services already deployed. Checking status..."

    NOT_RUNNING=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l || echo 0)

    if [ "$NOT_RUNNING" -gt 0 ]; then
        log_warning "Some pods are not running. Redeploying..."
        kubectl delete -n "$NAMESPACE" -f minikube/ --ignore-not-found=true
    fi
fi

log_info "Applying all services (idempotent)..."

# Deploy in order: data layer first, then application layer
kubectl apply -n "$NAMESPACE" -f minikube/postgres/ || { log_error "Failed to deploy PostgreSQL"; exit 1; }
kubectl apply -n "$NAMESPACE" -f minikube/qdrant/   || { log_error "Failed to deploy Qdrant"; exit 1; }
kubectl apply -n "$NAMESPACE" -f minikube/redis/    || { log_error "Failed to deploy Redis"; exit 1; }
kubectl apply -n "$NAMESPACE" -f minikube/mcp/      || { log_error "Failed to deploy MCP"; exit 1; }
kubectl apply -n "$NAMESPACE" -f minikube/backend/  || { log_error "Failed to deploy Backend"; exit 1; }
kubectl apply -n "$NAMESPACE" -f minikube/apisix/   || { log_error "Failed to deploy APISIX"; exit 1; }

log_success "Kubernetes manifests applied"

#############################################################################
# STEP 6: Wait for Pods to be Ready
#############################################################################
log_info "Step 6: Waiting for pods to be ready..."

log_info "Waiting for PostgreSQL..."
kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=120s || {
    log_error "PostgreSQL pod failed to start"
    kubectl logs -n "$NAMESPACE" -l app=postgres --tail=20 || true
    exit 1
}
log_success "PostgreSQL is ready"

log_info "Waiting for Qdrant..."
kubectl wait --for=condition=ready pod -l app=qdrant -n "$NAMESPACE" --timeout=120s || {
    log_error "Qdrant pod failed to start"
    kubectl logs -n "$NAMESPACE" -l app=qdrant --tail=20 || true
    exit 1
}
log_success "Qdrant is ready"

log_info "Waiting for Redis..."
kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=120s || {
    log_error "Redis pod failed to start"
    kubectl logs -n "$NAMESPACE" -l app=redis --tail=20 || true
    exit 1
}
log_success "Redis is ready"

log_info "Waiting for MCP service..."
kubectl wait --for=condition=ready pod -l app=mcp-service -n "$NAMESPACE" --timeout=120s || {
    log_error "MCP service pod failed to start"
    kubectl logs -n "$NAMESPACE" -l app=mcp-service --tail=20 || true
    exit 1
}
log_success "MCP service is ready"

log_info "Waiting for Backend..."
kubectl wait --for=condition=ready pod -l app=backend -n "$NAMESPACE" --timeout=120s || {
    log_error "Backend pod failed to start"
    kubectl logs -n "$NAMESPACE" -l app=backend --tail=20 || true
    exit 1
}
log_success "Backend is ready"

log_info "Waiting for APISIX..."
kubectl wait --for=condition=ready pod -l app=apisix -n "$NAMESPACE" --timeout=120s || {
    log_error "APISIX pod failed to start"
    kubectl logs -n "$NAMESPACE" -l app=apisix --tail=20 || true
    exit 1
}
log_success "APISIX is ready"

log_info "All core services deployed successfully"

#############################################################################
# STEP 7: Start Ollama (if not running)
#############################################################################
log_info "Step 7: Checking Ollama service..."

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_warning "Ollama is not running. Starting Ollama..."

    # Try to start Ollama as a service
    if command -v brew &> /dev/null; then
        brew services start ollama
        sleep 5
    else
        log_error "Ollama is not running and cannot be started automatically"
        log_error "Please run: ollama serve"
        exit 1
    fi
fi

# Verify Ollama is accessible
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_success "Ollama is running"

    # Check required models
    MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || true)

    if ! echo "$MODELS" | grep -q "llama3"; then
        log_warning "llama3 model not found. Pulling..."
        ollama pull llama3 || true
    fi

    if ! echo "$MODELS" | grep -q "nomic-embed-text"; then
        log_warning "nomic-embed-text model not found. Pulling..."
        ollama pull nomic-embed-text || true
    fi

    log_success "Required Ollama models are available"
else
    log_error "Ollama failed to start"
    exit 1
fi

#############################################################################
# STEP 8: Setup Port Forwarding
#############################################################################
log_info "Step 8: Setting up port forwarding..."

# Kill existing port forwards
pkill -f "kubectl port-forward.*backend" 2>/dev/null || true
pkill -f "kubectl port-forward.*mcp" 2>/dev/null || true
pkill -f "kubectl port-forward.*postgres" 2>/dev/null || true
pkill -f "kubectl port-forward.*qdrant" 2>/dev/null || true
pkill -f "kubectl port-forward.*redis" 2>/dev/null || true
pkill -f "kubectl port-forward.*apisix" 2>/dev/null || true

sleep 2

# Create logs directory
mkdir -p logs

# Start port forwarding
log_info "Port forwarding PostgreSQL..."
kubectl port-forward -n "$NAMESPACE" svc/postgres 5432:5432 > logs/postgres-pf.log 2>&1 &
sleep 1

log_info "Port forwarding Qdrant..."
kubectl port-forward -n "$NAMESPACE" svc/qdrant 6333:6333 > logs/qdrant-pf.log 2>&1 &
sleep 1

log_info "Port forwarding Redis..."
kubectl port-forward -n "$NAMESPACE" svc/redis 6379:6379 > logs/redis-pf.log 2>&1 &
sleep 1

log_info "Port forwarding Backend..."
kubectl port-forward -n "$NAMESPACE" svc/backend 8000:8000 > logs/backend-pf.log 2>&1 &
sleep 1

log_info "Port forwarding MCP Service..."
kubectl port-forward -n "$NAMESPACE" svc/mcp-service 8001:8001 > logs/mcp-pf.log 2>&1 &
sleep 3

log_info "Port forwarding APISIX..."
kubectl port-forward -n "$NAMESPACE" svc/apisix 9080:9080 > logs/apisix-pf.log 2>&1 &
sleep 1

log_success "Port forwarding established"

#############################################################################
# STEP 9: Verify Services Health
#############################################################################
log_info "Step 9: Verifying services health..."

# Test Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_success "Backend is healthy (http://localhost:8000)"
else
    log_error "Backend health check failed"
    log_error "Check logs: kubectl logs -n $NAMESPACE -l app=backend"
fi

# Test MCP Service
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    log_success "MCP Service is healthy (http://localhost:8001)"
else
    log_error "MCP Service health check failed"
    log_error "Check logs: kubectl logs -n $NAMESPACE -l app=mcp-service"
fi

# Test APISIX Gateway (any HTTP response is considered healthy)
APISIX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9080/ || echo "000")
if [ "$APISIX_STATUS" != "000" ]; then
    log_success "APISIX is reachable (http://localhost:9080)"
else
    log_error "APISIX is not reachable"
    log_error "Check logs: kubectl logs -n $NAMESPACE -l app=apisix"
fi



#############################################################################
# STEP 10: Install Frontend Dependencies (if needed)
#############################################################################
log_info "Step 10: Checking frontend dependencies..."

cd frontend || { log_error "Frontend directory not found"; exit 1; }

if [ ! -d "node_modules" ]; then
    log_warning "Frontend dependencies not found. Installing..."
    npm install || {
        log_error "Failed to install frontend dependencies"
        exit 1
    }
    log_success "Frontend dependencies installed"
else
    log_success "Frontend dependencies already installed"
fi

cd ..

#############################################################################
# STEP 11: Start Frontend
#############################################################################
log_info "Step 11: Starting frontend..."

# Kill existing frontend
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1

cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

sleep 5

# Verify frontend is running
if lsof -ti:5173 > /dev/null 2>&1; then
    log_success "Frontend started (http://localhost:5173)"
else
    log_error "Frontend failed to start"
    log_error "Check logs: tail -f logs/frontend.log"
fi

#############################################################################
# STEP 12: Ingest Documents (if Qdrant is empty)  -- robust check
#############################################################################
log_info "Step 12: Checking document ingestion..."

COLLECTION_URL="http://localhost:6333/collections/documents"

# request body + http code
HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" "$COLLECTION_URL" 2>/dev/null || echo -e "\n000")
HTTP_BODY=$(echo "$HTTP_RESPONSE" | sed '$d')      # all but last line
HTTP_CODE=$(echo "$HTTP_RESPONSE" | tail -n1)     # last line is HTTP status

# parse points_count using python3 (walks JSON to find points_count)
POINTS_COUNT=$(echo "$HTTP_BODY" | python3 - <<'PY'
import sys, json
s = sys.stdin.read()
try:
    obj = json.loads(s)
except Exception:
    print("-1")
    sys.exit(0)
def find_points(o):
    if isinstance(o, dict):
        if "points_count" in o and isinstance(o["points_count"], int):
            return o["points_count"]
        for v in o.values():
            r = find_points(v)
            if r is not None:
                return r
    elif isinstance(o, list):
        for v in o:
            r = find_points(v)
            if r is not None:
                return r
    return None
res = find_points(obj)
print(res if res is not None else -1)
PY
)

# Decide whether to ingest
if [ "$HTTP_CODE" != "200" ] || [ "$POINTS_COUNT" = "-1" ] || [ "$POINTS_COUNT" = "0" ]; then
    log_warning "Qdrant collection missing or empty (http=$HTTP_CODE points_count=$POINTS_COUNT). Ingesting documents..."
    export PYTHONPATH="$PROJECT_DIR:$PROJECT_DIR/backend"
    python3 embeddings/ingestion_pipeline.py || {
        log_warning "Document ingestion failed (not critical)"
    }
    log_success "Documents ingested"
else
    log_success "Documents already exist in Qdrant (points_count=$POINTS_COUNT)"
fi

#############################################################################
# Final Summary
#############################################################################
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            🚀 All Services Started Successfully! 🚀            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Service URLs:"
echo "   Frontend:          http://localhost:5173"
echo "   API Gateway:       http://localhost:9080"
echo "   Backend API:       http://localhost:8000"
echo "   Backend API Docs:  http://localhost:8000/docs"
echo "   MCP Service:       http://localhost:8001"
echo "   MCP Service Docs:  http://localhost:8001/docs"
echo "   PostgreSQL:        localhost:5432"
echo "   Qdrant:            http://localhost:6333"
echo "   Redis:             redis://localhost:6379"
echo "   Ollama:            http://localhost:11434"
echo ""
echo "🔍 Kubernetes Pods:"
kubectl get pods -n "$NAMESPACE"
echo ""
echo "📁 Logs:"
echo "   Frontend:          tail -f logs/frontend.log"
echo "   Backend:           kubectl logs -n $NAMESPACE -l app=backend -f"
echo "   MCP Service:       kubectl logs -n $NAMESPACE -l app=mcp-service -f"
echo "   APISIX:            kubectl logs -n $NAMESPACE -l app=apisix -f"
echo "   PostgreSQL:        kubectl logs -n $NAMESPACE -l app=postgres -f"
echo "   Qdrant:            kubectl logs -n $NAMESPACE -l app=qdrant -f"
echo ""
echo "🛑 To stop all services:"
echo "   ./stop-all.sh"
echo ""
echo "✅ System is ready! Open http://localhost:5173 in your browser"
echo ""
