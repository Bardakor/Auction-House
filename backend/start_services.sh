#!/bin/bash

# Real-Time Auction Platform - Start All Services
echo "Starting Auction Platform Microservices..."

# Install dependencies if requirements.txt is newer than the last install
if [ ! -f .deps_installed ] || [ requirements.txt -nt .deps_installed ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    touch .deps_installed
fi

# Start services in background
echo "Starting User Service on port 8001..."
cd services/user-service
python -m uvicorn main:app --host 0.0.0.0 --port 8001 &
USER_PID=$!
cd ../..

echo "Starting Auction Service on port 8002..."
cd services/auction-service
python -m uvicorn main:app --host 0.0.0.0 --port 8002 &
AUCTION_PID=$!
cd ../..

echo "Starting Bid Service on port 8003..."
cd services/bid-service
python -m uvicorn main:app --host 0.0.0.0 --port 8003 &
BID_PID=$!
cd ../..

echo "Starting Auth Gateway on port 8000..."
cd services/auth-gateway
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
GATEWAY_PID=$!
cd ../..

# Store PIDs for cleanup
echo $USER_PID > .user_service.pid
echo $AUCTION_PID > .auction_service.pid
echo $BID_PID > .bid_service.pid
echo $GATEWAY_PID > .gateway.pid

echo "All services started!"
echo "- Auth Gateway: http://localhost:8000"
echo "- User Service: http://localhost:8001"
echo "- Auction Service: http://localhost:8002"
echo "- Bid Service: http://localhost:8003"
echo ""
echo "Use 'bash stop_services.sh' to stop all services"
echo "Press Ctrl+C to view logs or stop this script"

# Wait for services and show logs
wait 