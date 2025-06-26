from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import sys
import httpx
from datetime import datetime
from typing import Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from models import BidCreate, Bid, ApiResponse
from auth import verify_token, extract_user_id

app = FastAPI(title="Bid Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "bids.db"
AUCTION_SERVICE_URL = "http://localhost:8002"

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            auction_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.replace("Bearer ", "")
    user_id = extract_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_id

async def get_auction_details(auction_id: int):
    """Get auction details from auction service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AUCTION_SERVICE_URL}/auctions/{auction_id}")
            if response.status_code == 200:
                data = response.json()
                return data['data']['auction']
            return None
    except Exception:
        return None

async def update_auction_price(auction_id: int, new_price: float):
    """Update auction current price"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{AUCTION_SERVICE_URL}/auctions/{auction_id}/price",
                params={"new_price": new_price}
            )
            return response.status_code == 200
    except Exception:
        return False

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/bids", response_model=ApiResponse)
async def place_bid(bid_data: BidCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    try:
        auction = await get_auction_details(bid_data.auction_id)
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        if auction['status'] != 'live':
            raise HTTPException(status_code=400, detail="Auction is not active")
        
        if bid_data.amount <= auction['current_price']:
            raise HTTPException(
                status_code=400, 
                detail=f"Bid amount must be higher than current price: ${auction['current_price']}"
            )
        
        if user_id == auction['owner_id']:
            raise HTTPException(status_code=400, detail="Cannot bid on your own auction")
        
        cursor = conn.execute("""
            INSERT INTO bids (user_id, auction_id, amount, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, bid_data.auction_id, bid_data.amount, datetime.now()))
        conn.commit()
        
        bid_id = cursor.lastrowid
        
        await update_auction_price(bid_data.auction_id, bid_data.amount)
        
        return ApiResponse(
            success=True,
            message="Bid placed successfully",
            data={
                "bid_id": bid_id,
                "auction_id": bid_data.auction_id,
                "amount": bid_data.amount,
                "user_id": user_id
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/bids/auction/{auction_id}", response_model=ApiResponse)
async def get_auction_bids(auction_id: int):
    conn = get_db()
    try:
        bids = conn.execute("""
            SELECT * FROM bids 
            WHERE auction_id = ? 
            ORDER BY amount DESC, timestamp DESC
        """, (auction_id,)).fetchall()
        
        bid_list = []
        for bid in bids:
            bid_list.append({
                "id": bid['id'],
                "user_id": bid['user_id'],
                "auction_id": bid['auction_id'],
                "amount": bid['amount'],
                "timestamp": bid['timestamp']
            })
        
        return ApiResponse(
            success=True,
            message="Auction bids retrieved successfully",
            data={"bids": bid_list}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/bids/user/{user_id}", response_model=ApiResponse)
async def get_user_bids(user_id: int):
    conn = get_db()
    try:
        bids = conn.execute("""
            SELECT * FROM bids 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        """, (user_id,)).fetchall()
        
        bid_list = []
        for bid in bids:
            bid_list.append({
                "id": bid['id'],
                "user_id": bid['user_id'],
                "auction_id": bid['auction_id'],
                "amount": bid['amount'],
                "timestamp": bid['timestamp']
            })
        
        return ApiResponse(
            success=True,
            message="User bids retrieved successfully",
            data={"bids": bid_list}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/bids/highest/{auction_id}", response_model=ApiResponse)
async def get_highest_bid(auction_id: int):
    conn = get_db()
    try:
        highest_bid = conn.execute("""
            SELECT * FROM bids 
            WHERE auction_id = ? 
            ORDER BY amount DESC, timestamp DESC 
            LIMIT 1
        """, (auction_id,)).fetchone()
        
        if not highest_bid:
            return ApiResponse(
                success=True,
                message="No bids found for this auction",
                data={"highest_bid": None}
            )
        
        return ApiResponse(
            success=True,
            message="Highest bid retrieved successfully",
            data={
                "highest_bid": {
                    "id": highest_bid['id'],
                    "user_id": highest_bid['user_id'],
                    "auction_id": highest_bid['auction_id'],
                    "amount": highest_bid['amount'],
                    "timestamp": highest_bid['timestamp']
                }
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "bid-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 