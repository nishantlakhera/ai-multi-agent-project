#!/bin/bash
#############################################################################
# Start Frontend Only (with Backend in Kubernetes)
# This script sets up port-forwarding and starts the frontend locally
#############################################################################

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Frontend-Only Local Development Setup                       ║"
echo "║   Backend/MCP/Redis/PostgreSQL running in Kubernetes          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${YELLOW}kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${YELLOW}Kubernetes cluster not accessible. Please start minikube first.${NC}"
    exit 1
fi

NAMESPACE="multiagent-assistant"

echo -e "${BLUE}[1/3]${NC} Checking Kubernetes services..."

# Check if backend service exists
if ! kubectl get service backend -n "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}Backend service not found in namespace '$NAMESPACE'${NC}"
    echo "Please ensure your Kubernetes services are running."
    exit 1
fi

echo -e "${GREEN}✓${NC} Backend service found"

# Kill any existing port-forward processes
echo -e "${BLUE}[2/3]${NC} Setting up port-forwarding..."

# Kill existing port-forwards for backend
pkill -f "port-forward.*backend" 2>/dev/null || true

# Start port-forward in background
kubectl port-forward -n "$NAMESPACE" svc/backend 8333:8000 &> /tmp/backend-port-forward.log &
BACKEND_PF_PID=$!

# Wait a moment for port-forward to establish
sleep 2

# Verify port-forward is working
if ! ps -p $BACKEND_PF_PID > /dev/null; then
    echo -e "${YELLOW}Failed to establish port-forward. Check /tmp/backend-port-forward.log${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Backend port-forwarded: localhost:8333 -> k8s backend:8000"
echo -e "  ${BLUE}PID:${NC} $BACKEND_PF_PID"

# Start frontend
echo -e "${BLUE}[3/3]${NC} Starting frontend..."
cd "$PROJECT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Frontend:${NC} http://localhost:5173"
echo -e "${BLUE}Backend (via port-forward):${NC} http://localhost:8333"
echo ""
echo -e "${YELLOW}Note:${NC} Backend is running in Kubernetes with Redis/PostgreSQL"
echo -e "${YELLOW}      All conversation history will be saved to the cluster${NC}"
echo ""
echo -e "Press Ctrl+C to stop the frontend (port-forward will continue)"
echo -e "To stop port-forward: kill $BACKEND_PF_PID"
echo ""

# Start frontend dev server
npm run dev
