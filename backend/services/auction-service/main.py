from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import sys
from datetime import datetime
from typing import Optional
import httpx

sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from models import AuctionCreate, Auction, AuctionStatus, ApiResponse
from auth import verify_token, extract_user_id

app = FastAPI(title="Auction Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "auctions.db"
BID_SERVICE_URL = "http://localhost:8003"

@app.get("/")
async def root():
    """Auction Service root endpoint"""
    return {
        "service": "Auction Service",
        "version": "1.0.0",
        "port": 8002,
        "endpoints": {
            "health": "/health",
            "get_auctions": "/auctions",
            "get_auction": "/auctions/{auction_id}",
            "create_auction": "/auctions",
            "delete_auction": "/auctions/{auction_id}",
            "update_status": "/auctions/{auction_id}/status",
            "auto_update": "/auctions/manage/auto-update-status",
            "get_winner": "/auctions/{auction_id}/winner"
        },
        "note": "Use the API Gateway at http://localhost:8000 for external access"
    }

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
            winner_id INTEGER,
            winning_amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    
    add_winner_column()

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
        auction = conn.execute(
            "SELECT id, status FROM auctions WHERE id = ?",
            (auction_id,)
        ).fetchone()
        
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
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
        
        auctions_to_end = conn.execute("""
            SELECT id, title FROM auctions 
            WHERE status = 'live' AND datetime(ends_at) <= datetime('now')
        """).fetchall()
        
        winner_notifications = []
        
        for auction in auctions_to_end:
            auction_id = auction['id']
            auction_title = auction['title']
            
            highest_bid = await get_highest_bid(auction_id)
            
            if highest_bid:
                conn.execute("""
                    UPDATE auctions 
                    SET status = 'ended', winner_id = ?, winning_amount = ?
                    WHERE id = ?
                """, (highest_bid['user_id'], highest_bid['amount'], auction_id))
                
                winner_notifications.append({
                    'auction_id': auction_id,
                    'auction_title': auction_title,
                    'winner_user_id': highest_bid['user_id'],
                    'winning_amount': highest_bid['amount']
                })
            else:
                conn.execute("""
                    UPDATE auctions 
                    SET status = 'ended'
                    WHERE id = ?
                """, (auction_id,))
        
        pending_updated = conn.execute("""
            UPDATE auctions 
            SET status = 'live' 
            WHERE status = 'pending'
        """).rowcount
        
        conn.commit()
        
        for notification in winner_notifications:
            await notify_winner(
                notification['auction_id'],
                notification['winner_user_id'], 
                notification['winning_amount'],
                notification['auction_title']
            )
        
        return ApiResponse(
            success=True,
            message="Auction statuses updated automatically",
            data={
                "pending_to_live": pending_updated,
                "live_to_ended": len(auctions_to_end),
                "winners_notified": len(winner_notifications)
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auction-service"}

async def get_highest_bid(auction_id: int):
    """Get the highest bid for an auction from bid service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BID_SERVICE_URL}/bids/highest/{auction_id}")
            if response.status_code == 200:
                data = response.json()
                return data['data']['highest_bid']
            return None
    except Exception:
        return None

async def notify_winner(auction_id: int, winner_user_id: int, winning_amount: float, auction_title: str):
    """Notify the winner of an auction (placeholder for future email/push notifications)"""
    print(f"WINNER NOTIFICATION:")
    print(f"   Auction: {auction_title} (ID: {auction_id})")
    print(f"   Winner: User ID {winner_user_id}")
    print(f"   Winning Bid: ${winning_amount}")
    print(f"   Time: {datetime.now()}")
    
    return True

def add_winner_column():
    """Add winner tracking to auctions table"""
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.execute("PRAGMA table_info(auctions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'winner_id' not in columns:
            conn.execute("ALTER TABLE auctions ADD COLUMN winner_id INTEGER")
            conn.execute("ALTER TABLE auctions ADD COLUMN winning_amount REAL")
            conn.commit()
            print("Added winner tracking columns to auctions table")
    except Exception as e:
        print(f"Error adding winner columns: {e}")
    finally:
        conn.close()

@app.patch("/auctions/{auction_id}/end-with-winner")
async def end_auction_with_winner(auction_id: int, user_id: int = Depends(get_current_user)):
    """Manually end an auction and determine the winner"""
    conn = get_db()
    try:
        auction = conn.execute(
            "SELECT * FROM auctions WHERE id = ?",
            (auction_id,)
        ).fetchone()
        
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        if auction['owner_id'] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to end this auction")
        
        if auction['status'] == 'ended':
            raise HTTPException(status_code=400, detail="Auction already ended")
        
        highest_bid = await get_highest_bid(auction_id)
        
        if highest_bid:
            conn.execute("""
                UPDATE auctions 
                SET status = 'ended', winner_id = ?, winning_amount = ?
                WHERE id = ?
            """, (highest_bid['user_id'], highest_bid['amount'], auction_id))
            
            conn.commit()
            
            await notify_winner(
                auction_id,
                highest_bid['user_id'], 
                highest_bid['amount'],
                auction['title']
            )
            
            return ApiResponse(
                success=True,
                message="Auction ended successfully with winner determined",
                data={
                    "auction_id": auction_id,
                    "status": "ended",
                    "winner_id": highest_bid['user_id'],
                    "winning_amount": highest_bid['amount']
                }
            )
        else:
            conn.execute("""
                UPDATE auctions 
                SET status = 'ended'
                WHERE id = ?
            """, (auction_id,))
            
            conn.commit()
            
            return ApiResponse(
                success=True,
                message="Auction ended with no bids",
                data={
                    "auction_id": auction_id,
                    "status": "ended",
                    "winner_id": None,
                    "winning_amount": None
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/auctions/{auction_id}/winner", response_model=ApiResponse)
async def get_auction_winner(auction_id: int):
    """Get winner information for a completed auction"""
    conn = get_db()
    try:
        auction = conn.execute("""
            SELECT id, title, status, winner_id, winning_amount, current_price
            FROM auctions 
            WHERE id = ?
        """, (auction_id,)).fetchone()
        
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        if auction['status'] != 'ended':
            return ApiResponse(
                success=True,
                message="Auction is still active",
                data={"winner": None, "status": auction['status']}
            )
        
        winner_data = None
        if auction['winner_id']:
            winner_data = {
                "auction_id": auction_id,
                "auction_title": auction['title'],
                "winner_id": auction['winner_id'],
                "winning_amount": auction['winning_amount']
            }
        
        return ApiResponse(
            success=True,
            message="Winner information retrieved",
            data={
                "winner": winner_data,
                "status": auction['status']
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 