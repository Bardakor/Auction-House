from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import hashlib
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from models import UserCreate, UserLogin, User, UserResponse, ApiResponse
from auth import create_access_token

app = FastAPI(title="User Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "users.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/register", response_model=ApiResponse)
async def register(user_data: UserCreate):
    conn = get_db()
    try:
        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?", 
            (user_data.email,)
        ).fetchone()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        password_hash = hash_password(user_data.password)
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (user_data.name, user_data.email, password_hash)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        
        token = create_access_token({"user_id": user_id, "email": user_data.email})
        
        return ApiResponse(
            success=True,
            message="User registered successfully",
            data={
                "user": {
                    "id": user_id,
                    "name": user_data.name,
                    "email": user_data.email
                },
                "token": token
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/login", response_model=ApiResponse)
async def login(user_data: UserLogin):
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (user_data.email,)
        ).fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        password_hash = hash_password(user_data.password)
        if password_hash != user['password_hash']:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token({"user_id": user['id'], "email": user['email']})
        
        return ApiResponse(
            success=True,
            message="Login successful",
            data={
                "user": {
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email']
                },
                "token": token
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/users/{user_id}", response_model=ApiResponse)
async def get_user(user_id: int):
    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return ApiResponse(
            success=True,
            message="User found",
            data={
                "user": {
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email']
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 