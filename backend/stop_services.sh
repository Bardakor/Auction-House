#!/bin/bash

# Real-Time Auction Platform - Stop All Services
echo "Stopping Auction Platform Microservices..."

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            rm "$pid_file"
        else
            echo "$service_name was not running"
            rm "$pid_file"
        fi
    else
        echo "No PID file found for $service_name"
    fi
}

# Stop all services
stop_service "Auth Gateway" ".gateway.pid"
stop_service "User Service" ".user_service.pid"
stop_service "Auction Service" ".auction_service.pid"
stop_service "Bid Service" ".bid_service.pid"

# Also kill any remaining uvicorn processes on our ports
echo "Checking for remaining processes..."
for port in 8000 8001 8002 8003; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing remaining process on port $port (PID: $pid)"
        kill $pid
    fi
done

echo "All services stopped!" 