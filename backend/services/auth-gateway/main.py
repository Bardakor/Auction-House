from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import sys
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from auth import verify_token

app = FastAPI(title="Auth Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "user": "http://localhost:8001",
    "auction": "http://localhost:8002",
    "bid": "http://localhost:8003"
}

PROTECTED_ROUTES = [
    "/auctions",
    "/bids"
]

@app.get("/")
async def root():
    """API Gateway root endpoint with service information"""
    return {
        "message": "Real-Time Auction Platform API Gateway",
        "version": "1.0.0",
        "services": {
            "user_service": "http://localhost:8001",
            "auction_service": "http://localhost:8002", 
            "bid_service": "http://localhost:8003"
        },
        "endpoints": {
            "documentation": "http://localhost:8000/docs",
            "health": "http://localhost:8000/health",
            "auctions": "http://localhost:8000/auctions",
            "register": "http://localhost:8000/register",
            "login": "http://localhost:8000/login"
        },
        "frontend": "http://localhost:3000"
    }

def requires_auth(path: str, method: str) -> bool:
    """Check if a route requires authentication"""
    if method == "GET" and path.startswith("/auctions"):
        return False
    
    for protected in PROTECTED_ROUTES:
        if path.startswith(protected):
            return True
    return False

async def validate_token(authorization: str = Header(None)):
    """Validate JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return authorization

async def forward_request(service_url: str, path: str, method: str, request: Request, headers: dict = None):
    """Forward request to the appropriate microservice"""
    
    forward_headers = {}
    if headers:
        forward_headers.update(headers)
    
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    query_params = str(request.url.query) if request.url.query else ""
    full_url = f"{service_url}{path}"
    if query_params:
        full_url += f"?{query_params}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=full_url,
                headers=forward_headers,
                content=body,
                timeout=30.0
            )
            
            return {
                "status_code": response.status_code,
                "content": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "headers": dict(response.headers)
            }
    
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")

@app.post("/register")
async def register(request: Request):
    result = await forward_request(SERVICES["user"], "/register", "POST", request)
    return result["content"]

@app.post("/login")
async def login(request: Request):
    result = await forward_request(SERVICES["user"], "/login", "POST", request)
    return result["content"]

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    result = await forward_request(SERVICES["user"], f"/users/{user_id}", "GET", request)
    return result["content"]

@app.get("/auctions")
async def get_auctions(request: Request):
    result = await forward_request(SERVICES["auction"], "/auctions", "GET", request)
    return result["content"]

@app.get("/auctions/{auction_id}")
async def get_auction(auction_id: int, request: Request):
    result = await forward_request(SERVICES["auction"], f"/auctions/{auction_id}", "GET", request)
    return result["content"]

@app.post("/auctions")
async def create_auction(request: Request, authorization: str = Header(...)):
    await validate_token(authorization)
    
    result = await forward_request(
        SERVICES["auction"], 
        "/auctions", 
        "POST", 
        request,
        headers={"Authorization": authorization}
    )
    return result["content"]

@app.delete("/auctions/{auction_id}")
async def delete_auction(auction_id: int, request: Request, authorization: str = Header(...)):
    await validate_token(authorization)
    
    result = await forward_request(
        SERVICES["auction"], 
        f"/auctions/{auction_id}", 
        "DELETE", 
        request,
        headers={"Authorization": authorization}
    )
    return result["content"]

@app.patch("/auctions/{auction_id}/status")
async def update_auction_status(auction_id: int, request: Request, authorization: str = Header(...)):
    await validate_token(authorization)
    
    result = await forward_request(
        SERVICES["auction"], 
        f"/auctions/{auction_id}/status", 
        "PATCH", 
        request,
        headers={"Authorization": authorization}
    )
    return result["content"]

@app.get("/auctions/manage/auto-update-status")
async def auto_update_auction_status(request: Request):
    result = await forward_request(SERVICES["auction"], "/auctions/manage/auto-update-status", "GET", request)
    return result["content"]

@app.post("/bids")
async def place_bid(request: Request, authorization: str = Header(...)):
    await validate_token(authorization)
    
    result = await forward_request(
        SERVICES["bid"], 
        "/bids", 
        "POST", 
        request,
        headers={"Authorization": authorization}
    )
    return result["content"]

@app.get("/bids/auction/{auction_id}")
async def get_auction_bids(auction_id: int, request: Request):
    result = await forward_request(SERVICES["bid"], f"/bids/auction/{auction_id}", "GET", request)
    return result["content"]

@app.get("/bids/user/{user_id}")
async def get_user_bids(user_id: int, request: Request):
    result = await forward_request(SERVICES["bid"], f"/bids/user/{user_id}", "GET", request)
    return result["content"]

@app.get("/bids/highest/{auction_id}")
async def get_highest_bid(auction_id: int, request: Request):
    result = await forward_request(SERVICES["bid"], f"/bids/highest/{auction_id}", "GET", request)
    return result["content"]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-gateway"}

@app.get("/health/services")
async def services_health():
    health_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                health_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response": response.json() if response.status_code == 200 else None
                }
        except Exception as e:
            health_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return {
        "gateway": "healthy",
        "services": health_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 