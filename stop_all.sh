#!/bin/bash

# Real-Time Auction Platform - Stop Everything
echo "🛑 Stopping Real-Time Auction Platform..."
echo "=========================================="

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  🔄 Stopping $service_name (PID: $pid)..."
            kill "$pid"
            rm "$pid_file"
            echo "  ✅ $service_name stopped"
        else
            echo "  ℹ️  $service_name was not running"
            rm "$pid_file"
        fi
    else
        echo "  ℹ️  No PID file found for $service_name"
    fi
}

echo ""
echo "🔧 Stopping backend services..."

# Stop backend services
cd backend 2>/dev/null || true
stop_service "Auth Gateway" ".gateway.pid"
stop_service "User Service" ".user_service.pid"
stop_service "Auction Service" ".auction_service.pid"
stop_service "Bid Service" ".bid_service.pid"

echo ""
echo "🎨 Stopping frontend application..."
stop_service "Frontend" ".frontend.pid"

cd .. 2>/dev/null || true

echo ""
echo "🧹 Cleaning up remaining processes..."

# Kill any remaining processes on our ports
ports=(3000 8000 8001 8002 8003)
for port in "${ports[@]}"; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "  🔄 Killing remaining process on port $port (PID: $pid)"
        kill $pid 2>/dev/null || true
        sleep 1
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 $pid 2>/dev/null || true
            echo "  ⚡ Force killed process on port $port"
        else
            echo "  ✅ Process on port $port stopped"
        fi
    fi
done

# Clean up any remaining uvicorn processes
uvicorn_pids=$(pgrep -f "uvicorn.*main:app" 2>/dev/null)
if [ ! -z "$uvicorn_pids" ]; then
    echo "  🔄 Stopping remaining uvicorn processes..."
    echo $uvicorn_pids | xargs kill 2>/dev/null || true
    sleep 1
    # Check if any are still running and force kill
    remaining_uvicorn=$(pgrep -f "uvicorn.*main:app" 2>/dev/null)
    if [ ! -z "$remaining_uvicorn" ]; then
        echo "  ⚡ Force killing stubborn uvicorn processes..."
        echo $remaining_uvicorn | xargs kill -9 2>/dev/null || true
    fi
    echo "  ✅ Uvicorn processes stopped"
fi

# Clean up any remaining npm processes
npm_pids=$(pgrep -f "npm.*dev\|next.*dev" 2>/dev/null)
if [ ! -z "$npm_pids" ]; then
    echo "  🔄 Stopping remaining npm/next processes..."
    echo $npm_pids | xargs kill 2>/dev/null || true
    sleep 1
    echo "  ✅ npm processes stopped"
fi

echo ""
echo "🧹 Cleaning up log files..."
if [ -d "backend/logs" ]; then
    rm -f backend/logs/*.log
    echo "  ✅ Log files cleaned"
fi

echo ""
echo "✅ All services stopped successfully!"
echo "=========================================="
echo ""
echo "📊 Port Status:"
for port in "${ports[@]}"; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "  ❌ Port $port: Still in use"
    else
        echo "  ✅ Port $port: Available"
    fi
done

echo ""
echo "🚀 To start again, run: bash start_all.sh" 