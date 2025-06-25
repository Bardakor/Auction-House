# 🏆 Real-Time Auction Platform

A modern, full-stack auction platform built with microservices architecture, featuring real-time bidding, JWT authentication, and a beautiful Next.js frontend.

## 🚀 Features

- **Real-time Bidding**: Live bid updates every 5 seconds
- **Secure Authentication**: JWT-based user authentication
- **Microservices Architecture**: Scalable backend with 4 specialized services
- **Modern UI**: Clean, responsive interface built with Next.js and shadcn/ui
- **Admin Controls**: Auction creators can manage auction status
- **RESTful APIs**: Well-documented APIs with automatic OpenAPI documentation

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **Auth Gateway** (Port 8000): API gateway with JWT validation and request routing
- **User Service** (Port 8001): User registration, authentication, and management
- **Auction Service** (Port 8002): Auction CRUD operations and status management
- **Bid Service** (Port 8003): Bid placement, validation, and tracking

### Frontend (Next.js + TypeScript)
- **Next.js 14**: Modern React framework with App Router
- **shadcn/ui**: Beautiful, accessible UI components
- **Tailwind CSS**: Utility-first CSS framework
- **TypeScript**: Type-safe development

## 📦 Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLite**: Lightweight database (separate DB per service)
- **Pydantic**: Data validation and settings management
- **PyJWT**: JSON Web Token implementation
- **httpx**: Async HTTP client for inter-service communication
- **uvicorn**: ASGI server implementation

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Static type checking
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: High-quality UI components
- **Sonner**: Toast notifications

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### One-Command Setup
```bash
# Start all services (backend + frontend)
bash start_all.sh

# Stop all services
bash stop_all.sh
```

### Manual Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
bash start_services.sh
```

#### Frontend Setup
```bash
cd frontend/auction-app
npm install
npm run dev
```

## 🌐 Access Points

- **Frontend Application**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **User Service**: http://localhost:8001
- **Auction Service**: http://localhost:8002
- **Bid Service**: http://localhost:8003

## 📚 API Documentation

### Authentication Endpoints
- `POST /register` - Register a new user
- `POST /login` - User login
- `GET /users/{id}` - Get user information

### Auction Endpoints
- `GET /auctions` - List all auctions (with optional status filter)
- `POST /auctions` - Create a new auction
- `GET /auctions/{id}` - Get auction details
- `DELETE /auctions/{id}` - Delete an auction
- `PATCH /auctions/{id}/status` - Update auction status
- `GET /auctions/manage/auto-update-status` - Auto-update all auction statuses

### Bid Endpoints
- `POST /bids` - Place a bid
- `GET /bids/auction/{auction_id}` - Get bids for an auction
- `GET /bids/user/{user_id}` - Get user's bids
- `GET /bids/highest/{auction_id}` - Get highest bid for an auction

## 🎯 Usage

### For Buyers
1. **Register/Login**: Create an account or sign in
2. **Browse Auctions**: View all available auctions
3. **Place Bids**: Bid on live auctions with real-time updates
4. **Track Bids**: Monitor your bidding activity

### For Sellers
1. **Create Auctions**: List items with title, description, starting price, and end date
2. **Manage Status**: Use admin controls to change auction status (pending → live → ended)
3. **Monitor Bids**: Watch real-time bidding activity

### Admin Features
- **Status Management**: Change auction status manually
- **Auto-Update**: Bulk update all auction statuses
- **Real-time Monitoring**: Live bid tracking and updates

## 🛠️ Development

### Backend Development
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Start individual services
python services/user-service/main.py
python services/auction-service/main.py
python services/bid-service/main.py
python services/auth-gateway/main.py
```

### Frontend Development
```bash
cd frontend/auction-app
npm install
npm run dev
```

### View Logs
```bash
tail -f backend/logs/*.log
```

## 📁 Project Structure

```
tp6/
├── backend/
│   ├── services/
│   │   ├── auth-gateway/         # API Gateway with JWT validation
│   │   ├── user-service/         # User management
│   │   ├── auction-service/      # Auction operations
│   │   └── bid-service/          # Bid management
│   ├── shared/
│   │   ├── models.py            # Pydantic data models
│   │   └── auth.py              # JWT utilities
│   ├── requirements.txt         # Python dependencies
│   ├── start_services.sh        # Backend startup script
│   └── stop_services.sh         # Backend cleanup script
├── frontend/
│   └── auction-app/             # Next.js application
│       ├── src/
│       │   ├── app/             # App Router pages
│       │   ├── components/      # React components
│       │   ├── contexts/        # React contexts
│       │   └── lib/             # Utilities and API client
│       └── package.json         # Frontend dependencies
├── start_all.sh                 # Complete startup script
├── stop_all.sh                  # Complete cleanup script
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables
Create `.env.local` in `frontend/auction-app/`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database
- Each service uses its own SQLite database
- Databases are created automatically on first run
- Located in each service directory

## 🚦 Service Health Checks

Check if all services are running:
```bash
curl http://localhost:8000/health  # Auth Gateway
curl http://localhost:8001/health  # User Service
curl http://localhost:8002/health  # Auction Service
curl http://localhost:8003/health  # Bid Service
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Frontend powered by [Next.js](https://nextjs.org/)

---

**Happy Bidding! 🎉** 