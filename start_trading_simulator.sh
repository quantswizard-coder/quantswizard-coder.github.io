#!/bin/bash

# 🚀 Interactive Trading Simulator Startup Script
# This script starts both the React frontend and Python backend

echo "🚀 Starting Interactive Trading Simulator..."
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 16+ first.${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed. Please install npm first.${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi

if ! command_exists pip3; then
    echo -e "${RED}❌ pip3 is not installed. Please install pip3 first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites found${NC}"

# Check if ports are available
if port_in_use 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is already in use. Please stop the process using port 3000.${NC}"
    exit 1
fi

if port_in_use 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use. Please stop the process using port 8000.${NC}"
    exit 1
fi

# Install frontend dependencies
echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
fi
cd ..

# Install backend dependencies
echo -e "${BLUE}📦 Installing backend dependencies...${NC}"
cd backend
if [ ! -f ".deps_installed" ]; then
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install backend dependencies${NC}"
        exit 1
    fi
    touch .deps_installed
else
    echo -e "${GREEN}✅ Backend dependencies already installed${NC}"
fi
cd ..

# Create log directory
mkdir -p logs

echo -e "${GREEN}🎉 Setup complete! Starting services...${NC}"
echo ""

# Start backend in background
echo -e "${BLUE}🐍 Starting Python backend on http://localhost:8000...${NC}"
cd backend
python3 api_server.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! port_in_use 8000; then
    echo -e "${RED}❌ Backend failed to start. Check logs/backend.log for details.${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ Backend started successfully (PID: $BACKEND_PID)${NC}"

# Start frontend in background
echo -e "${BLUE}⚛️  Starting React frontend on http://localhost:3000...${NC}"
cd frontend
npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

# Check if frontend started successfully
if ! port_in_use 3000; then
    echo -e "${RED}❌ Frontend failed to start. Check logs/frontend.log for details.${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID)${NC}"
echo ""

# Success message
echo -e "${GREEN}🎉 Interactive Trading Simulator is now running!${NC}"
echo ""
echo -e "${BLUE}📱 Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}🔧 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}📋 Process IDs:${NC}"
echo -e "   Backend PID: $BACKEND_PID"
echo -e "   Frontend PID: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Backend: logs/backend.log"
echo -e "   Frontend: logs/frontend.log"
echo ""

# Save PIDs for cleanup script
echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid

echo -e "${BLUE}🛑 To stop the services, run:${NC} ./stop_trading_simulator.sh"
echo -e "${BLUE}📊 To view logs, run:${NC} tail -f logs/backend.log or tail -f logs/frontend.log"
echo ""

# Wait for user input to keep script running
echo -e "${YELLOW}Press Ctrl+C to stop all services, or close this terminal to keep them running in background.${NC}"

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f logs/backend.pid logs/frontend.pid
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

trap cleanup INT

# Keep script running
while true; do
    sleep 1
done
