#!/bin/bash

################################################################################
# AI Multi-Agent System - Shutdown Script
# 
# This script gracefully stops all services and cleans up processes.
#
# Usage: ./shutdown.sh
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

kill_process_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 2
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            log "✓ $service_name stopped"
        else
            log_warning "$service_name process (PID: $pid) not running"
        fi
        rm -f "$pid_file"
    else
        log_warning "$service_name PID file not found"
    fi
}

kill_port() {
    local port=$1
    local service_name=$2
    
    if lsof -i :"$port" >/dev/null 2>&1; then
        log "Stopping $service_name on port $port..."
        lsof -ti:"$port" | xargs kill -9 2>/dev/null || true
        sleep 1
        log "✓ $service_name stopped"
    fi
}

main() {
    log "==================================================================="
    log "     AI Multi-Agent System - Shutdown"
    log "==================================================================="
    echo ""
    
    # Stop services by PID files
    kill_process_by_pid_file "$LOG_DIR/frontend.pid" "Frontend"
    kill_process_by_pid_file "$LOG_DIR/backend.pid" "Backend Service"
    kill_process_by_pid_file "$LOG_DIR/mcp.pid" "MCP Service"
    
    # Stop port forwards
    kill_process_by_pid_file "$LOG_DIR/postgres.pid" "PostgreSQL Port Forward"
    kill_process_by_pid_file "$LOG_DIR/qdrant.pid" "Qdrant Port Forward"
    
    # Cleanup any remaining processes on ports
    log "Cleaning up any remaining processes..."
    kill_port 5173 "Frontend (fallback)"
    kill_port 8000 "Backend (fallback)"
    kill_port 8001 "MCP Service (fallback)"
    
    # Kill any remaining kubectl port-forward processes
    pkill -f "kubectl port-forward.*postgres" 2>/dev/null || true
    pkill -f "kubectl port-forward.*qdrant" 2>/dev/null || true
    
    echo ""
    log "✓ All services stopped successfully!"
    echo ""
    log "Logs are preserved in: $LOG_DIR"
    echo ""
}

main
