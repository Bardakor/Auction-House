#!/bin/bash

echo "Starting Real-Time Auction Platform..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "Error: $1 is not installed. Please install $1 and try again."
        exit 1
    fi
}

echo "Checking prerequisites..."
check_command python3
check_command npm
check_command pip

echo "Installing backend dependencies..."
cd backend

source venv/bin/activate

if [ ! -f .deps_installed ] || [ requirements.txt -nt .deps_installed ]; then
    pip install -r requirements.txt
    touch .deps_installed
    echo "Backend dependencies installed"
else
    echo "Backend dependencies already up to date"
fi

echo "Installing frontend dependencies..."
cd ../frontend/auction-app
if [ ! -d node_modules ] || [ package.json -nt node_modules ]; then
    npm install
    echo "Frontend dependencies installed"
else
    echo "Frontend dependencies already up to date"
fi

cd ../..

echo "Starting backend microservices..."
cd backend

echo "Starting User Service (port 8001)..."
cd services/user-service
../../venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../../logs/user-service.log 2>&1 &
USER_PID=$!
cd ../..

echo "Starting Auction Service (port 8002)..."
cd services/auction-service
../../venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8002 > ../../logs/auction-service.log 2>&1 &
AUCTION_PID=$!
cd ../..

echo "Starting Bid Service (port 8003)..."
cd services/bid-service
../../venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8003 > ../../logs/bid-service.log 2>&1 &
BID_PID=$!
cd ../..

echo "Starting Auth Gateway (port 8000)..."
cd services/auth-gateway
../../venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../../logs/auth-gateway.log 2>&1 &
GATEWAY_PID=$!
cd ../..

mkdir -p logs

echo $USER_PID > .user_service.pid
echo $AUCTION_PID > .auction_service.pid
echo $BID_PID > .bid_service.pid
echo $GATEWAY_PID > .gateway.pid

cd ..

echo "Waiting for backend services to start..."
sleep 3

check_service() {
    local port=$1
    local service_name=$2
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "$service_name is running"
        return 0
    else
        echo "$service_name is starting..."
        return 1
    fi
}

for i in {1..10}; do
    all_ready=true
    
    if ! check_service 8001 "User Service"; then all_ready=false; fi
    if ! check_service 8002 "Auction Service"; then all_ready=false; fi
    if ! check_service 8003 "Bid Service"; then all_ready=false; fi
    if ! check_service 8000 "Auth Gateway"; then all_ready=false; fi
    
    if $all_ready; then
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo "Some services may still be starting. Check logs in backend/logs/ if needed."
        break
    fi
    
    sleep 3
done

echo "Starting frontend application..."
cd frontend/auction-app

if [ ! -f .env.local ]; then
    echo "Creating environment configuration..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME="Auction Platform"
NEXT_PUBLIC_APP_DESCRIPTION="Real-time auction platform with microservices"
EOF
    echo "Environment file created"
fi

npm run dev > ../../backend/logs/frontend.log 2>&1 &
FRONTEND_PID=$!

cd ../..

echo $FRONTEND_PID > backend/.frontend.pid

echo "Auction Platform is starting!"
echo ""
echo "Access Points:"
echo "Frontend Application: http://localhost:3000"
echo "API Gateway: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Individual Services:"
echo "User Service: http://localhost:8001"
echo "Auction Service: http://localhost:8002"
echo "Bid Service: http://localhost:8003"
echo ""
echo "Management:"
echo "View logs: tail -f backend/logs/*.log"
echo "Stop all services: bash stop_all.sh"
echo ""
echo "Frontend is starting... Please wait 10-15 seconds then visit:"
echo "http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop this script (services will continue running)"
echo "Use 'bash stop_all.sh' to stop all services"

trap 'echo ""; echo "Services are still running. Use \"bash stop_all.sh\" to stop them."; exit 0' INT
while true; do sleep 1; done 