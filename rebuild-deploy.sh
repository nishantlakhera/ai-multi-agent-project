#!/bin/bash
set -e

SERVICE=$1  # backend, mcp, apisix, redis, both, all

if [ -z "$SERVICE" ]; then
    echo "Usage: ./rebuild-deploy.sh [backend|mcp|apisix|redis|both|all]"
    exit 1
fi

NAMESPACE="multiagent-assistant"

# Set Minikube Docker environment
eval $(minikube docker-env)

rebuild_backend() {
    echo "🔨 Rebuilding backend image..."
    docker build -f docker/backend.Dockerfile -t multiagent-backend:latest .
    
    echo "🔄 Restarting backend deployment..."
    kubectl rollout restart deployment/backend -n "$NAMESPACE"
    
    echo "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/backend -n "$NAMESPACE"
    
    echo "✅ Backend redeployed!"
}

rebuild_mcp() {
    echo "🔨 Rebuilding MCP service image..."
    docker build -f docker/mcp.Dockerfile -t multiagent-mcp:latest .
    
    echo "🔄 Restarting MCP deployment..."
    kubectl rollout restart deployment/mcp-service -n "$NAMESPACE"
    
    echo "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/mcp-service -n "$NAMESPACE"
    
    echo "✅ MCP service redeployed!"
}

rebuild_redis() {
    echo "🔧 Applying Redis manifests..."
    kubectl apply -n "$NAMESPACE" -f minikube/redis/

    echo "🔄 Restarting Redis deployment..."
    kubectl rollout restart deployment/redis -n "$NAMESPACE"

    echo "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/redis -n "$NAMESPACE"

    echo "✅ Redis updated!"
}

rebuild_apisix() {
    echo "🔧 Applying APISIX manifests..."
    kubectl apply -n "$NAMESPACE" -f minikube/apisix/

    echo "🔄 Restarting APISIX deployment..."
    kubectl rollout restart deployment/apisix -n "$NAMESPACE"

    echo "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/apisix -n "$NAMESPACE"

    echo "✅ APISIX updated!"
}

case $SERVICE in
    backend)
        rebuild_backend
        ;;
    mcp)
        rebuild_mcp
        ;;
    redis)
        rebuild_redis
        ;;
    apisix)
        rebuild_apisix
        ;;
    both)
        rebuild_backend
        rebuild_mcp
        ;;
    all)
        rebuild_backend
        rebuild_mcp
        rebuild_redis
        rebuild_apisix
        ;;
    *)
        echo "Invalid service: $SERVICE"
        echo "Usage: ./rebuild-deploy.sh [backend|mcp|apisix|redis|both|all]"
        exit 1
        ;;
esac

echo ""
echo "📊 Current pod status:"
kubectl get pods -n "$NAMESPACE"
