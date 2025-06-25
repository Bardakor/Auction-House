from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class AuctionStatus(str, Enum):
    PENDING = "pending"
    LIVE = "live"
    ENDED = "ended"

# User Models
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: int
    name: str
    email: str

class UserResponse(BaseModel):
    user: User
    token: str

# Auction Models
class AuctionCreate(BaseModel):
    title: str
    description: str
    starting_price: float
    ends_at: datetime

class Auction(BaseModel):
    id: int
    title: str
    description: str
    starting_price: float
    current_price: float
    status: AuctionStatus
    ends_at: datetime
    owner_id: int

# Bid Models
class BidCreate(BaseModel):
    auction_id: int
    amount: float

class Bid(BaseModel):
    id: int
    user_id: int
    auction_id: int
    amount: float
    timestamp: datetime

# API Response Models
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None 