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