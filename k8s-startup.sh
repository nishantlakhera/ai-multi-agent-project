#!/bin/bash

# Kubernetes Startup Script
# This script starts the backend and MCP services in Kubernetes and the frontend locally

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
