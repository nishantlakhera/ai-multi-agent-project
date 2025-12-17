#!/bin/bash

# AI Multi-Agent Project Setup Script
# This script sets up the complete development environment

set -e  # Exit on error

echo "🚀 AI Multi-Agent Project Setup"
echo "================================"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Not running in a virtual environment${NC}"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created and activated${NC}"
else
    echo -e "${GREEN}✓ Virtual environment detected${NC}"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install frontend dependencies
echo ""
echo "📦 Installing frontend dependencies..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend directory not found, skipping...${NC}"
fi

# Check for required services
echo ""
echo "🔍 Checking required services..."

# Check PostgreSQL
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL CLI found${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL CLI not found. Please install PostgreSQL.${NC}"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker found${NC}"
else
    echo -e "${YELLOW}⚠️  Docker not found. Install Docker to run services.${NC}"
fi

# Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p data/docs
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"

# Check environment file
echo ""
echo "🔧 Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
else
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cat > .env << EOF
# LLM Provider Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3
EMBEDDING_MODEL=nomic-embed-text

# OpenAI Configuration (optional)
# OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Ollama Configuration (for local development)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Database Configuration
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/ai_app

# Vector Database Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=documents

# MCP Service Configuration
MCP_SERVICE_URL=http://localhost:8001

# Environment
ENV=dev
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start required services (PostgreSQL, Qdrant)"
echo "   - Option A: docker-compose up -d"
echo "   - Option B: Use local Ollama + start services manually"
echo ""
echo "2. Initialize database:"
echo "   psql -h localhost -U postgres -d ai_app -f backend/db_setup.sql"
echo ""
echo "3. Ingest documents:"
echo "   python -m embeddings.ingestion_pipeline"
echo ""
echo "4. Start backend:"
echo "   uvicorn backend.main:app --reload --port 8000"
echo ""
echo "5. Start MCP service:"
echo "   uvicorn mcp_service.main:app --reload --port 8001"
echo ""
echo "6. Start frontend:"
echo "   cd frontend && npm run dev"
echo ""

