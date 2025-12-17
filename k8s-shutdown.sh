#!/bin/bash

# Kubernetes Shutdown Script
# This script stops all port-forwards and the frontend

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

# Kill any process on port 5173
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
echo "  kubectl delete deployment backend mcp-service -n multiagent-assistant"
echo ""
echo "To start services again, run: ./k8s-startup.sh"
