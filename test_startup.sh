#!/bin/bash

echo "🧪 Testing Startup/Shutdown Scripts"
echo "===================================="
echo ""

cd /Users/nishant.lakhera/projects/learning/ai-multi-agent-project

# Test 1: Shutdown
echo "✓ Test 1: Running shutdown.sh..."
./shutdown.sh 2>&1 | grep -E "✓|ERROR|WARNING" | head -10
echo ""

# Test 2: Startup (with timeout)
echo "✓ Test 2: Running startup.sh (backgrounded)..."
./startup.sh > /tmp/test_startup_output.log 2>&1 &
STARTUP_PID=$!
echo "   Startup PID: $STARTUP_PID"
echo ""

# Wait and monitor
echo "✓ Test 3: Waiting 60 seconds for services to start..."
sleep 60

# Check services
echo ""
echo "✓ Test 4: Checking service health..."
echo -n "   Backend:  "
curl -s -m 2 http://localhost:8000/health >/dev/null 2>&1 && echo "✅ UP" || echo "❌ DOWN"
echo -n "   MCP:      "
curl -s -m 2 http://localhost:8001/health >/dev/null 2>&1 && echo "✅ UP" || echo "❌ DOWN"
echo -n "   Frontend: "
curl -s -m 2 http://localhost:5173 >/dev/null 2>&1 && echo "✅ UP" || echo "❌ DOWN"
echo ""

# Show last 30 lines of startup log
echo "✓ Test 5: Last 30 lines of startup log:"
tail -30 /tmp/test_startup_output.log
echo ""

# Cleanup
echo "✓ Test 6: Running shutdown.sh..."
./shutdown.sh 2>&1 | grep -E "✓|ERROR" | head -10
echo ""

echo "===================================="
echo "✅ Test Complete!"
