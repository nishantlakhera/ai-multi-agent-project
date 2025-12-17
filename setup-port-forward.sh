#!/bin/bash

# Port Forward Script for Kubernetes Services
# Run this in a separate terminal to expose PostgreSQL and Qdrant

echo "🔌 Setting up port forwarding for Kubernetes services..."

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo "⚠️  Minikube is not running. Starting minikube..."
    minikube start
fi

# Get pod names
POSTGRES_POD=$(kubectl get pods -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
QDRANT_POD=$(kubectl get pods -l app=qdrant -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POSTGRES_POD" ]; then
    echo "❌ PostgreSQL pod not found. Please deploy it first:"
    echo "   kubectl apply -f minikube/postgres/"
    exit 1
fi

if [ -z "$QDRANT_POD" ]; then
    echo "❌ Qdrant pod not found. Please deploy it first:"
    echo "   kubectl apply -f minikube/qdrant/"
    exit 1
fi

echo "✅ Found PostgreSQL pod: $POSTGRES_POD"
echo "✅ Found Qdrant pod: $QDRANT_POD"

# Kill any existing port forwards
pkill -f "port-forward.*postgres" 2>/dev/null
pkill -f "port-forward.*qdrant" 2>/dev/null

echo ""
echo "Starting port forwards..."

# Forward PostgreSQL
kubectl port-forward $POSTGRES_POD 5432:5432 &
PG_PID=$!
echo "✅ PostgreSQL: localhost:5432 (PID: $PG_PID)"

# Forward Qdrant
kubectl port-forward $QDRANT_POD 6333:6333 6334:6334 &
QDRANT_PID=$!
echo "✅ Qdrant: localhost:6333 (PID: $QDRANT_PID)"

echo ""
echo "🎉 Port forwarding active!"
echo ""
echo "To stop port forwarding:"
echo "  kill $PG_PID $QDRANT_PID"
echo ""
echo "Or simply close this terminal."
echo ""
echo "Press Ctrl+C to stop..."

# Wait for interrupt
wait

