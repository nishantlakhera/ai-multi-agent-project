#!/bin/bash

# Quick Start Script for AI Multi-Agent Project
# This script helps you get started quickly

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI Multi-Agent Project Quick Start   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to check if a service is running
check_service() {
    local url=$1
    local name=$2
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
        echo -e "${GREEN}✓ $name is running${NC}"
        return 0
    else
        echo -e "${RED}✗ $name is not running${NC}"
        return 1
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

# Check if in virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    if [ -d ".venv" ]; then
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        source .venv/bin/activate
    else
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv .venv
        source .venv/bin/activate
    fi
fi
echo -e "${GREEN}✓ Virtual environment active${NC}"

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

echo ""
echo "🚀 Starting services..."
echo ""

# Check if services are already running
POSTGRES_RUNNING=false
QDRANT_RUNNING=false
BACKEND_RUNNING=false
MCP_RUNNING=false

if check_service "http://localhost:5432" "PostgreSQL" 2>/dev/null; then
    POSTGRES_RUNNING=true
fi

if check_service "http://localhost:6333/healthz" "Qdrant" 2>/dev/null; then
    QDRANT_RUNNING=true
fi

if check_service "http://localhost:8000/health" "Backend" 2>/dev/null; then
    BACKEND_RUNNING=true
fi

if check_service "http://localhost:8001/health" "MCP Service" 2>/dev/null; then
    MCP_RUNNING=true
fi

echo ""

# Offer to start services with Docker
if ! $POSTGRES_RUNNING || ! $QDRANT_RUNNING; then
    echo -e "${YELLOW}Some services are not running.${NC}"
    echo ""
    echo "Options to start services:"
    echo "1. Docker Compose (recommended)"
    echo "2. Use existing local services"
    echo ""
    read -p "Choose option (1/2): " choice

    if [ "$choice" = "1" ]; then
        if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
            echo "Starting services with Docker Compose..."
            docker-compose up -d postgres qdrant
            echo "Waiting for services to be ready..."
            sleep 10
            echo -e "${GREEN}✓ Services started${NC}"
        else
            echo -e "${RED}Docker not found. Please install Docker or use local services.${NC}"
            exit 1
        fi
    fi
fi

# Initialize database if needed
echo ""
echo "🗄️  Setting up database..."
if [ -f "backend/db_setup.sql" ]; then
    read -p "Initialize database with sample data? (y/n): " init_db
    if [ "$init_db" = "y" ]; then
        PGPASSWORD=postgres psql -h localhost -U postgres -d ai_app -f backend/db_setup.sql 2>/dev/null || {
            echo -e "${YELLOW}Could not initialize database. Make sure PostgreSQL is running.${NC}"
        }
        echo -e "${GREEN}✓ Database initialized${NC}"
    fi
fi

# Ingest documents
echo ""
echo "📚 Ingesting documents..."
if [ -d "data/docs" ] && [ "$(ls -A data/docs/*.txt 2>/dev/null)" ]; then
    read -p "Ingest documents into Qdrant? (y/n): " ingest
    if [ "$ingest" = "y" ]; then
        python -m embeddings.ingestion_pipeline
        echo -e "${GREEN}✓ Documents ingested${NC}"
    fi
else
    echo -e "${YELLOW}No documents found in data/docs/${NC}"
fi

# Start backend if not running
echo ""
if ! $BACKEND_RUNNING; then
    echo "🔧 Starting Backend..."
    uvicorn backend.main:app --reload --port 8000 &
    BACKEND_PID=$!
    echo -e "${GREEN}✓ Backend starting (PID: $BACKEND_PID)${NC}"
    sleep 3
else
    echo -e "${GREEN}✓ Backend already running${NC}"
fi

# Start MCP service if not running
if ! $MCP_RUNNING; then
    echo "🔧 Starting MCP Service..."
    uvicorn mcp_service.main:app --reload --port 8001 &
    MCP_PID=$!
    echo -e "${GREEN}✓ MCP Service starting (PID: $MCP_PID)${NC}"
    sleep 2
else
    echo -e "${GREEN}✓ MCP Service already running${NC}"
fi

# Start frontend if it exists
if [ -d "frontend" ]; then
    echo ""
    read -p "Start frontend? (y/n): " start_frontend
    if [ "$start_frontend" = "y" ]; then
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        echo "🎨 Starting Frontend..."
        npm run dev &
        FRONTEND_PID=$!
        cd ..
        echo -e "${GREEN}✓ Frontend starting (PID: $FRONTEND_PID)${NC}"
    fi
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🎉 All Done!                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Your services are running at:"
echo -e "  ${GREEN}Backend:${NC}     http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC}    http://localhost:8000/docs"
echo -e "  ${GREEN}MCP:${NC}         http://localhost:8001"
echo -e "  ${GREEN}Frontend:${NC}    http://localhost:5173"
echo ""
echo "Test the API:"
echo '  curl -X POST http://localhost:8000/api/chat \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"user_id": "test", "message": "How many users logged in today?"}'"'"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Keep script running
wait

