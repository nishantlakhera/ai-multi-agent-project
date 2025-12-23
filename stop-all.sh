#!/bin/bash
#############################################################################
# AI Multi-Agent System - Complete Shutdown Script
# This script stops all services cleanly
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

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   AI Multi-Agent System - Complete Shutdown                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

#############################################################################
# STEP 1: Stop Frontend
#############################################################################
log_info "Step 1: Stopping frontend..."

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null || true
        log_success "Frontend stopped (PID: $FRONTEND_PID)"
    fi
    rm -f logs/frontend.pid
fi

# Force kill any remaining frontend processes
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
log_success "Port 5173 freed"

#############################################################################
# STEP 2: Stop Port Forwards
#############################################################################
log_info "Step 2: Stopping port forwards..."

pkill -f "kubectl port-forward.*backend" 2>/dev/null || true
log_success "Backend port-forward stopped"

pkill -f "kubectl port-forward.*mcp" 2>/dev/null || true
log_success "MCP port-forward stopped"

pkill -f "kubectl port-forward.*postgres" 2>/dev/null || true
log_success "PostgreSQL port-forward stopped"

pkill -f "kubectl port-forward.*qdrant" 2>/dev/null || true
log_success "Qdrant port-forward stopped"

sleep 2

#############################################################################
# STEP 3: Display Kubernetes Status (pods remain running)
#############################################################################
log_info "Step 3: Checking Kubernetes pods status..."
echo ""

if kubectl get pods -n multiagent-assistant &> /dev/null; then
    kubectl get pods -n multiagent-assistant
    echo ""
    log_info "Kubernetes pods are still running (data is preserved)"
else
    log_info "No Kubernetes pods found"
fi

#############################################################################
# Final Summary
#############################################################################
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            ✅ All Local Services Stopped                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 What's Stopped:"
echo "   ✅ Frontend (port 5173)"
echo "   ✅ Port forwards (8000, 8001, 5432, 6333)"
echo ""
echo "📊 What's Still Running:"
echo "   🟢 Kubernetes pods (backend, mcp, postgres, qdrant)"
echo "   🟢 Minikube cluster"
echo "   🟢 Ollama service"
echo "   🟢 Data is preserved in PostgreSQL and Qdrant"
echo ""
echo "🔄 To restart services:"
echo "   ./start-all.sh"
echo ""
echo "🗑️  To delete everything (including data):"
echo "   kubectl delete namespace multiagent-assistant"
echo "   minikube stop"
echo ""
