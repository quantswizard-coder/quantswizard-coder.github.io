#!/bin/bash

# 🛑 Interactive Trading Simulator Stop Script
# This script stops both the React frontend and Python backend

echo "🛑 Stopping Interactive Trading Simulator..."
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if process is running
process_running() {
    kill -0 $1 2>/dev/null
}

# Function to kill process gracefully
kill_process() {
    local pid=$1
    local name=$2
    
    if process_running $pid; then
        echo -e "${YELLOW}🛑 Stopping $name (PID: $pid)...${NC}"
        kill $pid
        
        # Wait up to 10 seconds for graceful shutdown
        for i in {1..10}; do
            if ! process_running $pid; then
                echo -e "${GREEN}✅ $name stopped gracefully${NC}"
                return 0
            fi
            sleep 1
        done
        
        # Force kill if still running
        echo -e "${YELLOW}⚠️  Force killing $name...${NC}"
        kill -9 $pid 2>/dev/null
        
        if ! process_running $pid; then
            echo -e "${GREEN}✅ $name force stopped${NC}"
        else
            echo -e "${RED}❌ Failed to stop $name${NC}"
            return 1
        fi
    else
        echo -e "${BLUE}ℹ️  $name is not running${NC}"
    fi
}

# Stop services using saved PIDs
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    kill_process $BACKEND_PID "Backend"
    rm -f logs/backend.pid
else
    echo -e "${BLUE}ℹ️  No backend PID file found${NC}"
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    kill_process $FRONTEND_PID "Frontend"
    rm -f logs/frontend.pid
else
    echo -e "${BLUE}ℹ️  No frontend PID file found${NC}"
fi

# Also try to kill any processes on the ports
echo -e "${BLUE}🔍 Checking for processes on ports 3000 and 8000...${NC}"

# Kill processes on port 3000 (frontend)
FRONTEND_PORT_PID=$(lsof -ti :3000 2>/dev/null)
if [ ! -z "$FRONTEND_PORT_PID" ]; then
    echo -e "${YELLOW}🛑 Killing process on port 3000 (PID: $FRONTEND_PORT_PID)...${NC}"
    kill $FRONTEND_PORT_PID 2>/dev/null
    sleep 2
    if lsof -ti :3000 >/dev/null 2>&1; then
        kill -9 $FRONTEND_PORT_PID 2>/dev/null
    fi
fi

# Kill processes on port 8000 (backend)
BACKEND_PORT_PID=$(lsof -ti :8000 2>/dev/null)
if [ ! -z "$BACKEND_PORT_PID" ]; then
    echo -e "${YELLOW}🛑 Killing process on port 8000 (PID: $BACKEND_PORT_PID)...${NC}"
    kill $BACKEND_PORT_PID 2>/dev/null
    sleep 2
    if lsof -ti :8000 >/dev/null 2>&1; then
        kill -9 $BACKEND_PORT_PID 2>/dev/null
    fi
fi

# Verify ports are free
echo -e "${BLUE}🔍 Verifying ports are free...${NC}"

if lsof -ti :3000 >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 3000 is still in use${NC}"
else
    echo -e "${GREEN}✅ Port 3000 is free${NC}"
fi

if lsof -ti :8000 >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8000 is still in use${NC}"
else
    echo -e "${GREEN}✅ Port 8000 is free${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Interactive Trading Simulator stopped successfully!${NC}"
echo ""
echo -e "${BLUE}📝 Log files are preserved in the logs/ directory:${NC}"
echo -e "   Backend: logs/backend.log"
echo -e "   Frontend: logs/frontend.log"
echo ""
echo -e "${BLUE}🚀 To start again, run:${NC} ./start_trading_simulator.sh"
