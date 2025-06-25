from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import sys
from datetime import datetime
from typing import Optional

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from models import AuctionCreate, Auction, AuctionStatus, ApiResponse
from auth import verify_token, extract_user_id

app = FastAPI(title="Auction Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE = "auctions.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            starting_price REAL NOT NULL,
            current_price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            ends_at TIMESTAMP NOT NULL,
            owner_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/auctions", response_model=ApiResponse)
async def create_auction(auction_data: AuctionCreate, user_id: int = Depends(get_current_user)):
    conn = get_db()
    try:
        cursor = conn.execute("""
            INSERT INTO auctions (title, description, starting_price, current_price, status, ends_at, owner_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            auction_data.title,
            auction_data.description,
            auction_data.starting_price,
            auction_data.starting_price,
            AuctionStatus.PENDING,
            auction_data.ends_at,
            user_id
        ))
        conn.commit()
        
        auction_id = cursor.lastrowid
        
        return ApiResponse(
            success=True,
            message="Auction created successfully",
            data={
                "auction_id": auction_id,
                "title": auction_data.title,
                "starting_price": auction_data.starting_price
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/auctions", response_model=ApiResponse)
async def get_auctions(status: Optional[str] = None):
    conn = get_db()
    try:
        query = "SELECT * FROM auctions"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        auctions = conn.execute(query, params).fetchall()
        
        auction_list = []
        for auction in auctions:
            auction_list.append({
                "id": auction['id'],
                "title": auction['title'],
                "description": auction['description'],
                "starting_price": auction['starting_price'],
                "current_price": auction['current_price'],
                "status": auction['status'],
                "ends_at": auction['ends_at'],
                "owner_id": auction['owner_id']
            })
        
        return ApiResponse(
            success=True,
            message="Auctions retrieved successfully",
            data={"auctions": auction_list}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/auctions/{auction_id}", response_model=ApiResponse)
async def get_auction(auction_id: int):
    conn = get_db()
    try:
        auction = conn.execute(
            "SELECT * FROM auctions WHERE id = ?",
            (auction_id,)
        ).fetchone()
        
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        return ApiResponse(
            success=True,
            message="Auction found",
            data={
                "auction": {
                    "id": auction['id'],
                    "title": auction['title'],
                    "description": auction['description'],
                    "starting_price": auction['starting_price'],
                    "current_price": auction['current_price'],
                    "status": auction['status'],
                    "ends_at": auction['ends_at'],
                    "owner_id": auction['owner_id']
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/auctions/{auction_id}", response_model=ApiResponse)
async def delete_auction(auction_id: int, user_id: int = Depends(get_current_user)):
    conn = get_db()
    try:
        # Check if auction exists and belongs to user
        auction = conn.execute(
            "SELECT owner_id FROM auctions WHERE id = ?",
            (auction_id,)
        ).fetchone()
        
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        if auction['owner_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this auction")
        
        conn.execute("DELETE FROM auctions WHERE id = ?", (auction_id,))
        conn.commit()
        
        return ApiResponse(
            success=True,
            message="Auction deleted successfully",
            data={"auction_id": auction_id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.patch("/auctions/{auction_id}/price", response_model=ApiResponse)
async def update_auction_price(auction_id: int, new_price: float):
    """Internal endpoint for bid service to update auction price"""
    conn = get_db()
    try:
        # Update current price
        conn.execute(
            "UPDATE auctions SET current_price = ? WHERE id = ?",
            (new_price, auction_id)
        )
        conn.commit()
        
        return ApiResponse(
            success=True,
            message="Auction price updated",
            data={"auction_id": auction_id, "new_price": new_price}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.patch("/auctions/{auction_id}/status")
async def update_auction_status(auction_id: int, new_status: str):
    """Update auction status (pending -> live -> ended)"""
    if new_status not in ['pending', 'live', 'ended']:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    conn = get_db()
    try:
        # Check if auction exists
        auction = conn.execute(
            "SELECT id, status FROM auctions WHERE id = ?",
            (auction_id,)
        ).fetchone()
        
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        # Update status
        conn.execute(
            "UPDATE auctions SET status = ? WHERE id = ?",
            (new_status, auction_id)
        )
        conn.commit()
        
        return ApiResponse(
            success=True,
            message=f"Auction status updated to {new_status}",
            data={"auction_id": auction_id, "status": new_status}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/auctions/manage/auto-update-status")
async def auto_update_auction_status():
    """Auto-update auction statuses based on current time"""
    conn = get_db()
    try:
        from datetime import datetime
        now = datetime.now()
        
        # Update pending auctions to live (if current time >= start time)
        # For simplicity, we'll make auctions live immediately when created
        pending_updated = conn.execute("""
            UPDATE auctions 
            SET status = 'live' 
            WHERE status = 'pending'
        """).rowcount
        
        # Update live auctions to ended (if current time >= end time)
        ended_updated = conn.execute("""
            UPDATE auctions 
            SET status = 'ended' 
            WHERE status = 'live' AND datetime(ends_at) <= datetime('now')
        """).rowcount
        
        conn.commit()
        
        return ApiResponse(
            success=True,
            message="Auction statuses updated automatically",
            data={
                "pending_to_live": pending_updated,
                "live_to_ended": ended_updated
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auction-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 