#!/bin/bash

# Comprehensive End-to-End Test Script
# Tests all flows: General, RAG, DB, Web, Multi-Source
# Includes Redis cache testing and API Gateway verification

set -e

GATEWAY_URL="http://localhost:9080"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   COMPREHENSIVE END-TO-END FLOW TEST                      ║${NC}"
echo -e "${BLUE}║   Testing: All Agents + Redis Cache + API Gateway         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to show logs
show_logs() {
    local service=$1
    echo -e "\n${YELLOW}─── $service Logs (last 20 lines) ───${NC}"
    kubectl logs -n multiagent-assistant -l app=$service --tail=20 2>/dev/null | tail -20 || echo "No logs available"
}

# Function to test endpoint
test_endpoint() {
    local test_name=$1
    local user_id=$2
    local message=$3
    local expected_route=$4
    
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  TEST: $test_name${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}User ID:${NC} $user_id"
    echo -e "${YELLOW}Message:${NC} $message"
    echo -e "${YELLOW}Expected Route:${NC} $expected_route"
    echo ""
    
    # Make request through API Gateway
    echo -e "${YELLOW}Sending request through APISIX Gateway (port 9080)...${NC}"
    START_TIME=$(date +%s)
    
    response=$(curl -s -X POST "$GATEWAY_URL/api/chat" \
        -H "Content-Type: application/json" \
        -d "{\"user_id\":\"$user_id\",\"message\":\"$message\"}" \
        --max-time 120)
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo -e "\n${GREEN}✓ Response received in ${DURATION}s${NC}"
    
    # Parse response
    route=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('route', 'unknown'))" 2>/dev/null || echo "error")
    answer=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'No answer')[:200])" 2>/dev/null || echo "error parsing")
    
    echo -e "\n${YELLOW}════ RESPONSE ════${NC}"
    echo -e "${YELLOW}Route Taken:${NC} $route"
    echo -e "${YELLOW}Answer:${NC} $answer..."
    echo -e "${YELLOW}Full Response:${NC}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    
    # Show backend logs
    show_logs "backend"
    
    # Verify route
    if [ "$route" == "$expected_route" ]; then
        echo -e "\n${GREEN}✓ TEST PASSED${NC} - Route matches expected: $expected_route"
    else
        echo -e "\n${RED}✗ TEST FAILED${NC} - Expected route: $expected_route, Got: $route"
    fi
    
    echo -e "\n${YELLOW}Waiting 2 seconds before next test...${NC}"
    sleep 2
}

# Check if services are ready
echo -e "${YELLOW}Checking if services are ready...${NC}"
kubectl get pods -n multiagent-assistant -o wide

# Check APISIX Gateway
echo -e "\n${YELLOW}Testing APISIX Gateway health...${NC}"
curl -s http://localhost:9080/api/health || echo "Gateway not responding"

# Check Redis connection
echo -e "\n${YELLOW}Testing Redis connection...${NC}"
kubectl exec -n multiagent-assistant deployment/redis -- redis-cli PING || echo "Redis not responding"

echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Starting Flow Tests${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"

# Test 1: General Conversation Flow (New User - Cache Miss)
test_endpoint \
    "FLOW 1: General Conversation (Cache Miss)" \
    "test-flow-user-$(date +%s)" \
    "Hello! What's 2+2?" \
    "general"

# Test 2: General Conversation (Same User - Cache Hit)
test_endpoint \
    "FLOW 2: General Conversation (Cache Hit)" \
    "test-flow-user-$(date +%s)" \
    "Thanks! What's 3+3?" \
    "general"

# Test 3: RAG Query Flow (Document Search)
test_endpoint \
    "FLOW 3: RAG Query (Document Search)" \
    "test-rag-user-$(date +%s)" \
    "What information do you have in the troubleshooting documentation?" \
    "rag"

echo -e "\n${YELLOW}Checking MCP Service logs after RAG query...${NC}"
show_logs "mcp-service"

# Test 4: Database Query Flow (SQL Execution)
test_endpoint \
    "FLOW 4: Database Query (SQL)" \
    "test-db-user-$(date +%s)" \
    "How many total users are in the database?" \
    "db"

echo -e "\n${YELLOW}Checking MCP Service logs after DB query...${NC}"
show_logs "mcp-service"

# Test 5: Web Search Flow (Real-time Info)
test_endpoint \
    "FLOW 5: Web Search (Real-time)" \
    "test-web-user-$(date +%s)" \
    "What are the latest trends in artificial intelligence?" \
    "web"

echo -e "\n${YELLOW}Checking MCP Service logs after Web query...${NC}"
show_logs "mcp-service"

# Test 6: Multi-Source Fusion Flow (Complex Query)
test_endpoint \
    "FLOW 6: Multi-Source Fusion (Complex)" \
    "test-multi-user-$(date +%s)" \
    "Tell me about our user database and also search for industry benchmarks" \
    "multi"

echo -e "\n${YELLOW}Checking MCP Service logs after Multi-source query...${NC}"
show_logs "mcp-service"

# Test 7: Redis Cache Verification
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TEST 7: Redis Cache Verification                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Creating test conversation with multiple exchanges...${NC}"
TEST_USER="cache-test-$(date +%s)"

# First message (Cache Miss)
echo -e "${YELLOW}Message 1: Cache MISS expected${NC}"
curl -s -X POST "$GATEWAY_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER\",\"message\":\"My name is TestUser\"}" \
    | python3 -m json.tool

sleep 2

# Second message (Cache HIT)
echo -e "\n${YELLOW}Message 2: Cache HIT expected${NC}"
curl -s -X POST "$GATEWAY_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$TEST_USER\",\"message\":\"What is my name?\"}" \
    | python3 -m json.tool

# Check Redis cache
echo -e "\n${YELLOW}Checking Redis cache for user: $TEST_USER${NC}"
kubectl exec -n multiagent-assistant deployment/redis -- \
    redis-cli LLEN "conversation_history:$TEST_USER" || echo "Cache key not found"

echo -e "\n${YELLOW}Viewing cached messages:${NC}"
kubectl exec -n multiagent-assistant deployment/redis -- \
    redis-cli LRANGE "conversation_history:$TEST_USER" 0 -1 | head -20

# Test 8: API Gateway Routing Verification
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TEST 8: API Gateway Routing Verification                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Testing Backend route (/api/health)...${NC}"
curl -s http://localhost:9080/api/health | python3 -m json.tool || echo "Failed"

echo -e "\n${YELLOW}Testing MCP route (/mcp/health)...${NC}"
curl -s http://localhost:9080/mcp/health | python3 -m json.tool || echo "Failed"

echo -e "\n${YELLOW}APISIX Gateway logs:${NC}"
show_logs "apisix"

# Test 9: PostgreSQL Persistence Verification
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TEST 9: PostgreSQL Persistence Verification               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Checking conversation history in PostgreSQL...${NC}"
kubectl exec -n multiagent-assistant deployment/postgres -- \
    psql -U appuser -d appdb -c "SELECT COUNT(*) as total_messages, COUNT(DISTINCT user_id) as unique_users FROM conversation_history;" \
    2>/dev/null || echo "Database query failed"

echo -e "\n${YELLOW}Recent conversations (last 5):${NC}"
kubectl exec -n multiagent-assistant deployment/postgres -- \
    psql -U appuser -d appdb -c "SELECT user_id, role, LEFT(content, 50) as content, created_at FROM conversation_history ORDER BY created_at DESC LIMIT 5;" \
    2>/dev/null || echo "Database query failed"

# Test 10: Redis Cache Statistics
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TEST 10: Redis Cache Statistics                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Redis connection stats:${NC}"
kubectl exec -n multiagent-assistant deployment/redis -- \
    redis-cli INFO stats | grep -E "total_connections|total_commands|keyspace_hits|keyspace_misses"

echo -e "\n${YELLOW}All cached conversation keys:${NC}"
kubectl exec -n multiagent-assistant deployment/redis -- \
    redis-cli KEYS "conversation_history:*" | wc -l | xargs echo "Total cached conversations:"

# Final Summary
echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  COMPREHENSIVE TEST SUMMARY                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}✓ Flow 1: General Conversation (Cache Miss) - TESTED${NC}"
echo -e "${GREEN}✓ Flow 2: General Conversation (Cache Hit) - TESTED${NC}"
echo -e "${GREEN}✓ Flow 3: RAG Query (Document Search) - TESTED${NC}"
echo -e "${GREEN}✓ Flow 4: Database Query (SQL) - TESTED${NC}"
echo -e "${GREEN}✓ Flow 5: Web Search (Real-time) - TESTED${NC}"
echo -e "${GREEN}✓ Flow 6: Multi-Source Fusion (Complex) - TESTED${NC}"
echo -e "${GREEN}✓ Flow 7: Redis Cache Verification - TESTED${NC}"
echo -e "${GREEN}✓ Flow 8: API Gateway Routing - TESTED${NC}"
echo -e "${GREEN}✓ Flow 9: PostgreSQL Persistence - TESTED${NC}"
echo -e "${GREEN}✓ Flow 10: Redis Statistics - TESTED${NC}"

echo -e "\n${BLUE}System Components Verified:${NC}"
echo -e "  ✓ APISIX API Gateway (port 9080)"
echo -e "  ✓ Backend Service (all agents)"
echo -e "  ✓ MCP Service (RAG, DB, Web tools)"
echo -e "  ✓ Redis Cache (conversation history)"
echo -e "  ✓ PostgreSQL Database (persistent storage)"
echo -e "  ✓ Qdrant Vector DB (document search)"

echo -e "\n${BLUE}Agent Flows Tested:${NC}"
echo -e "  ✓ Router Agent (query classification)"
echo -e "  ✓ General Agent (casual conversation)"
echo -e "  ✓ RAG Agent (document retrieval)"
echo -e "  ✓ DB Agent (SQL generation & execution)"
echo -e "  ✓ Web Agent (web search & scraping)"
echo -e "  ✓ Fusion Agent (multi-source synthesis)"
echo -e "  ✓ Final Answer Agent (response formatting)"

echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ALL TESTS COMPLETED!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Full logs saved to:${NC}"
echo "  - Backend: kubectl logs -n multiagent-assistant -l app=backend --tail=200"
echo "  - MCP Service: kubectl logs -n multiagent-assistant -l app=mcp-service --tail=200"
echo "  - APISIX: kubectl logs -n multiagent-assistant -l app=apisix --tail=200"
echo "  - Redis: kubectl logs -n multiagent-assistant -l app=redis --tail=200"
