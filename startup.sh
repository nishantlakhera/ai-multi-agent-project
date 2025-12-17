#!/bin/bash

################################################################################
# AI Multi-Agent System - Automated Startup Script
# 
# This script automates the complete startup process for the multi-agent system
# including port forwarding, service verification, and application startup.
#
# Usage: ./startup.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Export environment variables for MCP service
export POSTGRES_DSN="${POSTGRES_DSN:-postgresql://appuser:apppass@localhost:5432/appdb}"
export QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
export QDRANT_COLLECTION_NAME="${QDRANT_COLLECTION_NAME:-documents}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3}"
export LLM_PROVIDER="${LLM_PROVIDER:-ollama}"
export MCP_SERVICE_URL="${MCP_SERVICE_URL:-http://localhost:8001}"

# Log file
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/startup_${TIMESTAMP}.log"

################################################################################
# Helper Functions
################################################################################

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if a port is in use
port_in_use() {
    lsof -i :"$1" >/dev/null 2>&1
}

# Kill process on port
kill_port() {
    local port=$1
    if port_in_use "$port"; then
        log_warning "Port $port is in use. Killing process..."
        lsof -ti:"$port" | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=15  # Reduced from 30
    local attempt=0
    
    log_info "Waiting for $name to be ready at $url..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -m 2 "$url" >/dev/null 2>&1; then  # Added 2 second timeout
            log "✓ $name is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log_error "$name failed to start after $max_attempts attempts"
    return 1
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    log "Starting pre-flight checks..."
    
    # Check required commands
    local required_commands=("kubectl" "python3" "node" "npm" "curl" "lsof")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
    log "✓ All required commands found"
    
    # Check Python version
    python_version=$(python3 --version | awk '{print $2}')
    log_info "Python version: $python_version"
    
    # Check Node version
    node_version=$(node --version)
    log_info "Node version: $node_version"
    
    # Check kubectl connection
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "Cannot connect to Kubernetes cluster. Is minikube running?"
        exit 1
    fi
    log "✓ Kubernetes cluster is accessible"
    
    # Check if namespace exists
    if ! kubectl get namespace multiagent-assistant >/dev/null 2>&1; then
        log_error "Namespace 'multiagent-assistant' not found"
        exit 1
    fi
    log "✓ Namespace 'multiagent-assistant' exists"
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        log_error "Ollama is not running. Please start Ollama first: ollama serve"
        exit 1
    fi
    log "✓ Ollama is running"
    
    # Check if required models are installed
    if ! curl -s http://localhost:11434/api/tags | grep -q "llama3"; then
        log_error "llama3 model not found. Please install: ollama pull llama3"
        exit 1
    fi
    if ! curl -s http://localhost:11434/api/tags | grep -q "nomic-embed-text"; then
        log_error "nomic-embed-text model not found. Please install: ollama pull nomic-embed-text"
        exit 1
    fi
    log "✓ Required Ollama models are installed"
    
    log "✓ All pre-flight checks passed!"
    echo ""
}

################################################################################
# Port Forwarding Setup
################################################################################

setup_port_forwarding() {
    log "Setting up Kubernetes port forwarding..."
    
    # Kill existing port forwards
    pkill -f "kubectl port-forward.*postgres" 2>/dev/null || true
    pkill -f "kubectl port-forward.*qdrant" 2>/dev/null || true
    sleep 2
    
    # PostgreSQL port forward
    log_info "Starting PostgreSQL port forward (5432)..."
    kubectl port-forward -n multiagent-assistant svc/postgres 5432:5432 \
        > "$LOG_DIR/postgres-port-forward.log" 2>&1 &
    POSTGRES_PF_PID=$!
    sleep 3
    
    if ! port_in_use 5432; then
        log_error "PostgreSQL port forward failed"
        exit 1
    fi
    log "✓ PostgreSQL port forward active (PID: $POSTGRES_PF_PID)"
    
    # Qdrant port forward
    log_info "Starting Qdrant port forward (6333)..."
    kubectl port-forward -n multiagent-assistant svc/qdrant 6333:6333 \
        > "$LOG_DIR/qdrant-port-forward.log" 2>&1 &
    QDRANT_PF_PID=$!
    sleep 3
    
    if ! port_in_use 6333; then
        log_error "Qdrant port forward failed"
        exit 1
    fi
    log "✓ Qdrant port forward active (PID: $QDRANT_PF_PID)"
    
    # Save PIDs for cleanup
    echo "$POSTGRES_PF_PID" > "$LOG_DIR/postgres.pid"
    echo "$QDRANT_PF_PID" > "$LOG_DIR/qdrant.pid"
    
    echo ""
}

################################################################################
# Database Verification
################################################################################

verify_databases() {
    log "Verifying database connections..."
    
    # Wait for port forwards to stabilize
    sleep 3
    
    # Test PostgreSQL connection (try multiple times)
    log_info "Testing PostgreSQL connection..."
    pg_connected=false
    for i in {1..5}; do
        if command_exists psql; then
            if psql postgresql://appuser:apppass@localhost:5432/appdb -c "SELECT 1" >/dev/null 2>&1; then
                pg_connected=true
                break
            fi
        else
            # Fallback: use Python to test connection
            if python3 -c "import psycopg2; psycopg2.connect('postgresql://appuser:apppass@localhost:5432/appdb').close()" 2>/dev/null; then
                pg_connected=true
                break
            fi
        fi
        sleep 2
    done
    
    if [ "$pg_connected" = true ]; then
        log "✓ PostgreSQL connection successful"
    else
        log_error "Cannot connect to PostgreSQL after multiple attempts"
        exit 1
    fi
    
    # Test Qdrant connection
    if curl -s http://localhost:6333/collections >/dev/null 2>&1; then
        log "✓ Qdrant connection successful"
    else
        log_error "Cannot connect to Qdrant"
        exit 1
    fi
    
    # Check if documents collection exists
    if curl -s http://localhost:6333/collections/documents >/dev/null 2>&1; then
        doc_count=$(curl -s http://localhost:6333/collections/documents | grep -o '"points_count":[0-9]*' | grep -o '[0-9]*' || echo "0")
        log "✓ Qdrant 'documents' collection exists ($doc_count documents)"
    else
        log_warning "Qdrant 'documents' collection not found. Run ingestion pipeline to create it."
    fi
    
    echo ""
}

################################################################################
# Install Dependencies
################################################################################

install_dependencies() {
    log "Checking and installing dependencies..."
    
    # Backend dependencies
    if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
        log_error "backend/.env not found. Please create it from backend/.env.example"
        exit 1
    fi
    
    cd "$PROJECT_ROOT/backend"
    log_info "Installing backend Python dependencies..."
    pip3 install -r requirements.txt --user >> "$LOG_FILE" 2>&1 || {
        log_error "Failed to install backend dependencies"
        exit 1
    }
    log "✓ Backend dependencies installed"
    
    # MCP service dependencies
    cd "$PROJECT_ROOT/mcp_service"
    if [ -f "requirements.txt" ]; then
        log_info "Installing MCP service dependencies..."
        pip3 install -r requirements.txt --user >> "$LOG_FILE" 2>&1 || {
            log_warning "Failed to install MCP dependencies (non-critical)"
        }
    fi
    
    # Frontend dependencies
    cd "$PROJECT_ROOT/frontend"
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install >> "$LOG_FILE" 2>&1 || {
            log_error "Failed to install frontend dependencies"
            exit 1
        }
        log "✓ Frontend dependencies installed"
    else
        log "✓ Frontend dependencies already installed"
    fi
    
    cd "$PROJECT_ROOT"
    echo ""
}

################################################################################
# Start Services
################################################################################

start_backend() {
    log "Starting Backend Service..."
    
    kill_port 8000
    
    cd "$PROJECT_ROOT/backend"
    python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 \
        > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
    
    wait_for_service "http://localhost:8000/health" "Backend Service" || exit 1
    
    log "✓ Backend Service running (PID: $BACKEND_PID)"
    echo ""
}

start_mcp_service() {
    log "Starting MCP Service..."
    
    kill_port 8001
    
    cd "$PROJECT_ROOT/mcp_service"
    python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001 \
        > "$LOG_DIR/mcp.log" 2>&1 &
    MCP_PID=$!
    echo "$MCP_PID" > "$LOG_DIR/mcp.pid"
    
    if wait_for_service "http://localhost:8001/health" "MCP Service"; then
        log "✓ MCP Service running (PID: $MCP_PID)"
    else
        log_warning "MCP Service failed to start (web search will not work)"
        log_warning "Check logs/mcp.log for details"
        # Kill the failed process
        kill "$MCP_PID" 2>/dev/null || true
        rm -f "$LOG_DIR/mcp.pid"
    fi
    
    echo ""
}

start_frontend() {
    log "Starting Frontend..."
    
    kill_port 5173
    
    cd "$PROJECT_ROOT/frontend"
    npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"
    
    wait_for_service "http://localhost:5173" "Frontend" || exit 1
    
    log "✓ Frontend running (PID: $FRONTEND_PID)"
    echo ""
}

################################################################################
# Post-Startup Verification
################################################################################

post_startup_verification() {
    log "Running post-startup verification..."
    
    # Test backend API
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        log "✓ Backend API is healthy"
    else
        log_warning "Backend API health check failed"
    fi
    
    # Test MCP service
    if curl -s http://localhost:8001/health | grep -q "ok"; then
        log "✓ MCP Service is healthy"
    else
        log_warning "MCP Service health check failed"
    fi
    
    echo ""
}

################################################################################
# Display Summary
################################################################################

display_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║           AI Multi-Agent System Started Successfully!          ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo -e "   Frontend:     ${GREEN}http://localhost:5173${NC}"
    echo -e "   Backend API:  ${GREEN}http://localhost:8000${NC}"
    echo -e "   MCP Service:  ${GREEN}http://localhost:8001${NC}"
    echo -e "   PostgreSQL:   ${GREEN}localhost:5432${NC} (port-forwarded)"
    echo -e "   Qdrant:       ${GREEN}localhost:6333${NC} (port-forwarded)"
    echo -e "   Ollama:       ${GREEN}localhost:11434${NC}"
    echo ""
    echo -e "${BLUE}📝 Useful Commands:${NC}"
    echo -e "   View logs:       ${YELLOW}tail -f $LOG_DIR/*.log${NC}"
    echo -e "   Stop services:   ${YELLOW}./shutdown.sh${NC}"
    echo -e "   Backend logs:    ${YELLOW}tail -f $LOG_DIR/backend.log${NC}"
    echo -e "   Frontend logs:   ${YELLOW}tail -f $LOG_DIR/frontend.log${NC}"
    echo ""
    echo -e "${BLUE}🧪 Test Queries:${NC}"
    echo -e "   RAG:      ${YELLOW}How do I troubleshoot Confluence?${NC}"
    echo -e "   Database: ${YELLOW}How many users are in the database?${NC}"
    echo -e "   Web:      ${YELLOW}Tell me about Tesla.com${NC}"
    echo -e "   Multi:    ${YELLOW}Count orders AND search for AI news${NC}"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC}"
    echo -e "   Comprehensive Guide: ${YELLOW}COMPREHENSIVE_GUIDE.md${NC}"
    echo -e "   API Docs:            ${YELLOW}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${GREEN}✨ Ready to use! Open ${YELLOW}http://localhost:5173${GREEN} in your browser${NC}"
    echo ""
}

################################################################################
# Cleanup Handler
################################################################################

cleanup() {
    log_info "Cleanup handler called"
}

trap cleanup EXIT

################################################################################
# Main Execution
################################################################################

main() {
    clear
    log "==================================================================="
    log "     AI Multi-Agent System - Automated Startup"
    log "==================================================================="
    echo ""
    
    preflight_checks
    setup_port_forwarding
    verify_databases
    install_dependencies
    start_backend
    start_mcp_service
    start_frontend
    post_startup_verification
    display_summary
    
    log "All services started successfully!"
    log "Logs are being written to: $LOG_DIR"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services and exit${NC}"
    echo ""
    
    # Keep script running
    wait
}

# Run main function
main
